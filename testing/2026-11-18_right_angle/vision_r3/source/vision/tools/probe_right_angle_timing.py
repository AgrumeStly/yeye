"""已保存MCU故障现场后的5秒禁驱动相机计时，不要求新的人工初始化测试。

只执行当前生成器的ALLOW_DRIVE=False副本，不发START或写main.py。
真实日志由SD取回；纯无效视野不能证明有效近弯或单侧时序通过。
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import queue
import re
import time
from canmv_lap_bench import Session, ROOT
from prepare_right_angle_bundle import build


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    captured=json.loads((ROOT/'testing/2026-11-18_right_angle/ground_01_capture/capture.json').read_text(encoding='utf-8'))
    if not captured['flash_matches_bin'] or not all(s['lap']['state']==6 and s['lap']['left_pwm']==0 and
            s['lap']['right_pwm']==0 for s in captured['samples']):
        raise RuntimeError('saved zero-output MCU fault evidence required')
    args.output.mkdir(parents=True,exist_ok=False)
    source=build(False)[0].replace('DURATION_MS = 600000','DURATION_MS = 5000').replace('SHOW_PREVIEW = True','SHOW_PREVIEW = False')
    if 'ALLOW_DRIVE = True' in source: raise RuntimeError('no drive required')
    (args.output/'executed_source.py').write_bytes(source.encode('utf-8'))
    session=Session(args.output)
    try:
        session.request('connectBoard',{'port':'COM10','baudRate':12000000},timeout=25)
        if session.request('scriptRunning').get('running') is not False: raise RuntimeError('camera already active')
        session.tail=''; session.script_error=False; session.running=True
        session.request('runScript',{'script':source},timeout=35)
        deadline=time.monotonic()+20
        while session.running is not False and time.monotonic()<deadline:
            try:session.record(session.messages.get(timeout=0.2))
            except queue.Empty:pass
        if session.running is not False:
            session.request('stopScript',timeout=15);raise TimeoutError('camera probe exceeded limit')
        if session.script_error:raise RuntimeError('camera probe raised')
        match=re.search(r'\[RIGHT ANGLE LOG\]\s+(/sdcard/right_angle_logs/run_\d{4}\.jsonl)',session.tail)
        if match is None:raise RuntimeError('SD log missing')
        remote=match.group(1);size=session.request('io.queryFileStat',{'path':remote})['size']
        if not 0<size<1024*1024:raise RuntimeError('invalid short diagnostic log size')
        data=bytearray()
        while len(data)<size:
            count=min(32768,size-len(data));r=session.request('io.readFile',{'path':remote,'offset':len(data),'size':count})
            chunk=base64.b64decode(r['dataBase64'],validate=True) if isinstance(r.get('dataBase64'),str) else bytes(r.get('data',[]))
            if len(chunk)!=count:raise RuntimeError('short read')
            data.extend(chunk)
        (args.output/'camera.jsonl').write_bytes(data)
        rows=[json.loads(line) for line in data.decode('utf-8').splitlines()]
        frames=[r for r in rows if 'index' in r]
        if not frames or any(r['wire_valid'] for r in frames):raise RuntimeError('invalid no-drive execution')
        report=dict(frames=len(frames),geometry_valid=sum(r['valid'] for r in frames),all_wire_invalid=True,
            max_processing_ms=max(r['processing_ms'] for r in frames),max_to_send_ms=max(r['to_send_ms'] for r in frames),
            max_interval_ms=max(r['interval_ms'] or 0 for r in frames),source_log=remote,
            source_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),motor_started=False)
        (args.output/'review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report))
    finally:session.close()


if __name__=='__main__':main()
