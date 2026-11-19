"""已保存MCU零输出现场后的5秒禁驱动相机计时，不要求新的人工初始化测试。

只执行当前生成器的ALLOW_DRIVE=False副本，不发START或写main.py。
真实日志和原图由/data取回；纯无效视野不能证明有效近弯时序通过。
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
    parser.add_argument('--capture', type=Path, default=ROOT/'testing/2026-11-18_right_angle/ground_01_capture/capture.json')
    parser.add_argument('--capture-frame', action='store_true')
    args=parser.parse_args()
    captured=json.loads(args.capture.read_text(encoding='utf-8'))
    # WAIT／STOPPED／FAULT均为停止态，且必须实读确认双轮PWM为0。
    # 诊断副本仍为ALLOW_DRIVE=False，不依赖过期故障快照假设现场安全。
    if not captured['flash_matches_bin'] or not captured.get('samples') or not all(s['lap']['state'] in (1,5,6) and s['lap']['left_pwm']==0 and
            s['lap']['right_pwm']==0 for s in captured['samples']):
        raise RuntimeError('saved zero-output stopped MCU evidence required')
    args.output.mkdir(parents=True,exist_ok=False)
    source=build(False)[0].replace('DURATION_MS = 600000','DURATION_MS = 5000').replace('SHOW_PREVIEW = True','SHOW_PREVIEW = False')
    if args.capture_frame:
        # 仅禁驱动诊断在第10帧发送无效包后向/data保存原始灰度，不改像素。
        source=source.replace('            record = dict(result)', '''            if index == 10:
                diagnostic = name[:-6] + '_view.pgm'
                with open(diagnostic, 'wb') as snapshot:
                    snapshot.write(b'P5\\n320 240\\n255\\n')
                    snapshot.write(pixels)
                print('RIGHT_ANGLE_VIEW', diagnostic)
            record = dict(result)''')
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
        match=re.search(r'\[RIGHT ANGLE LOG\]\s+(/data/right_angle_logs/run_\d{4}\.jsonl)',session.tail)
        if match is None:raise RuntimeError('/data log missing')
        remote=match.group(1);size=session.request('io.queryFileStat',{'path':remote})['size']
        if not 0<size<1024*1024:raise RuntimeError('invalid short diagnostic log size')
        data=bytearray()
        while len(data)<size:
            count=min(32768,size-len(data));r=session.request('io.readFile',{'path':remote,'offset':len(data),'size':count})
            chunk=base64.b64decode(r['dataBase64'],validate=True) if isinstance(r.get('dataBase64'),str) else bytes(r.get('data',[]))
            if len(chunk)!=count:raise RuntimeError('short read')
            data.extend(chunk)
        (args.output/'camera.jsonl').write_bytes(data)
        if args.capture_frame:
            match=re.search(r'RIGHT_ANGLE_VIEW\s+(/data/right_angle_logs/run_\d{4}_view.pgm)',session.tail)
            if match is None:raise RuntimeError('diagnostic raw frame absent')
            remote_frame=match.group(1)
            length=session.request('io.queryFileStat',{'path':remote_frame})['size']
            if not 76800<length<76900:raise RuntimeError('unexpected PGM size')
            image_bytes=bytearray()
            while len(image_bytes)<length:
                count=min(32768,length-len(image_bytes));reply=session.request('io.readFile',{'path':remote_frame,'offset':len(image_bytes),'size':count})
                chunk=base64.b64decode(reply['dataBase64'],validate=True) if isinstance(reply.get('dataBase64'),str) else bytes(reply.get('data',[]))
                if len(chunk)!=count:raise RuntimeError('short image read')
                image_bytes.extend(chunk)
            (args.output/'frame.pgm').write_bytes(image_bytes)
        rows=[json.loads(line) for line in data.decode('utf-8').splitlines()]
        frames=[r for r in rows if 'index' in r]
        if not frames or any(r['wire_valid'] for r in frames):raise RuntimeError('invalid no-drive execution')
        report=dict(frames=len(frames),geometry_valid=sum(r['valid'] for r in frames),all_wire_invalid=True,
            max_processing_ms=max(r['processing_ms'] for r in frames),max_to_send_ms=max(r['to_send_ms'] for r in frames),
            max_interval_ms=max(r['interval_ms'] or 0 for r in frames),source_log=remote,
            max_send_interval_ms=max(r.get('send_interval_ms') or 0 for r in frames),
            max_log_ms=max(r.get('previous_log_ms') or 0 for r in frames),
            max_gc_ms=max(r.get('previous_gc_ms') or 0 for r in frames),
            max_evidence_ms=max(r.get('evidence_ms') or 0 for r in frames),
            source_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),motor_started=False)
        (args.output/'review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report))
    finally:session.close()


if __name__=='__main__':main()
