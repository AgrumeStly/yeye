"""按主控明确指令启动并保持首弯真实视觉，不发START、不写main.py。

沿用官方CanMV后端和已交付v4代码，车轮动作仍由STM32 KEY决定。
首次双轮测试是否完成不由本工具伪造；地面启动资格由STM32自身检查。
"""
import argparse
import hashlib
import json
from pathlib import Path
import queue
import time
from canmv_lap_bench import Session
from prepare_right_angle_bundle import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default='COM10')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source, manifest = build(True)
    root = Path(__file__).resolve().parents[2]
    reviewed = root/'testing/2026-11-18_right_angle/release_r4_final/right_angle_drive.py'
    if source.encode('utf-8') != reviewed.read_bytes():
        raise RuntimeError('current generator differs from reviewed release; no script executed')
    (args.output/'executed_source.py').write_bytes(source.encode('utf-8'))
    result = dict(port=args.port, manifest=manifest, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  main_py_written=False, automatic_motor_start=False,
                  operator_camera_start_authorized=True, completed=False)
    def save(name):
        (args.output/name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    save('run.json')
    session = Session(args.output)
    owned = False
    stopped = False
    try:
        result['board'] = session.request('connectBoard', {'port':args.port, 'baudRate':12000000}, timeout=25)
        result['initial_status'] = session.request('scriptRunning')
        if result['initial_status'].get('running') is True:
            # 主控已要求自动启动最终弯道视觉；旧入口先正常停止，让finally发STOP。
            session.request('stopScript', timeout=15)
        if session.request('scriptRunning').get('running') is not False:
            raise RuntimeError('board idle not confirmed')
        session.tail = ''; session.script_error = False; session.running = True
        owned = True
        session.request('runScript', {'script':source}, timeout=35)
        result['started'] = True
        save('status.json')
        print('[HOST RIGHT ANGLE LIVE] actual camera running; v4; NO START sent', flush=True)
        deadline = time.monotonic()+630
        next_status = time.monotonic()+3
        while session.running is not False and time.monotonic() < deadline:
            try:
                session.record(session.messages.get(timeout=0.25))
            except queue.Empty:
                pass
            if (args.output/'stop.request').exists():
                stopped = True
                session.request('stopScript', timeout=15)
                session.running = session.request('scriptRunning').get('running', session.running)
                break
            if time.monotonic() >= next_status:
                result['current_status'] = session.request('scriptRunning')
                session.running = result['current_status'].get('running', session.running)
                result['last_observed_at'] = time.time()
                result['terminal_tail'] = session.tail[-3000:]
                save('status.json')
                next_status = time.monotonic()+3
        if session.running is not False:
            session.request('stopScript', timeout=15)
            raise TimeoutError('own camera exceeded ten-minute window')
        if session.script_error and not stopped:
            raise RuntimeError('right-angle camera raised; inspect terminal.txt')
        result['completed'] = not stopped
    except BaseException as exc:
        result['error'] = repr(exc)
        if owned and session.running is not False:
            try: session.request('stopScript', timeout=15)
            except BaseException: pass
        raise
    finally:
        session.close()
        result['stopped_by_control_file'] = stopped
        save('result.json')


if __name__ == '__main__':
    main()
