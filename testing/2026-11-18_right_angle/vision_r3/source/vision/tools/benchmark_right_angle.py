"""K230上对同一归档近弯图比较旧／新处理时间，不初始化UART或发送路径。

仅用SD已有图片作处理计时，不把它当实时相机／地面验证；不操作STM32。
"""
import argparse
import json
from pathlib import Path
import queue
import time
from canmv_lap_bench import Session, ROOT
from prepare_right_angle_bundle import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    old = (ROOT/'testing/2026-11-18_right_angle/release_r2/right_angle_drive.py').read_text(encoding='utf-8')
    new = build(False)[0]
    source = 'import image, time, json, gc\n'
    source += 'old_scope={"__name__":"timing_old"}\nexec('+repr(old)+',old_scope)\n'
    source += 'new_scope={"__name__":"timing_new"}\nexec('+repr(new)+',new_scope)\n'
    source += '''
frame=image.Image('/sdcard/captures/push_full_lap_0001/data_0101.jpg').to_grayscale()
pixels=frame.bytearray()
for label,scope in (('old',old_scope),('new',new_scope)):
    detector=scope['RightAngleRoute']()
    if label=='new': detector.clock=time.ticks_ms
    origin=time.ticks_ms()
    for index in range(16):
        gc.collect()
        start=time.ticks_ms()
        result=detector.update(pixels,time.ticks_diff(start,origin))
        elapsed=time.ticks_diff(time.ticks_ms(),start)
        print('TIMING_FRAME '+json.dumps(dict(label=label,index=index,ms=elapsed,valid=result['valid'],
            source=result['source'],bend=result['bend'],mode=result.get('search_mode'),profile=result.get('profile_ms'))))
print('TIMING_DONE NO_UART NO_START')
'''
    (args.output/'executed_source.py').write_bytes(source.encode('utf-8'))
    session = Session(args.output)
    try:
        session.request('connectBoard', {'port':'COM10','baudRate':12000000}, timeout=25)
        if session.request('scriptRunning').get('running') is not False:
            raise RuntimeError('active camera not interrupted by timing probe')
        session.tail=''; session.script_error=False; session.running=True
        session.request('runScript', {'script':source}, timeout=35)
        deadline=time.monotonic()+30
        while session.running is not False and time.monotonic()<deadline:
            try: session.record(session.messages.get(timeout=0.2))
            except queue.Empty: pass
        if session.running is not False:
            session.request('stopScript', timeout=15)
            raise TimeoutError('SD timing did not finish')
        if session.script_error or 'TIMING_DONE' not in session.tail:
            raise RuntimeError('SD timing failed')
        rows=[json.loads(line.split('TIMING_FRAME ',1)[1]) for line in session.tail.splitlines() if line.startswith('TIMING_FRAME ')]
        if len(rows)!=32: raise RuntimeError('incomplete timing rows')
        (args.output/'review.json').write_text(json.dumps(dict(frames=rows,uart_initialized=False,
            motor_started=False,source_kind='stored SD frame; processing timing only'),indent=2),encoding='utf-8')
    finally:
        session.close()


if __name__=='__main__':
    main()
