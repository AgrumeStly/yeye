"""保持直道真实相机许可运行，电机仍只由STM32 KEY启动并独立限时2秒。

仅运行当前生成器的StraightAssist v3许可副本，不写main.py，不发送START。
官方后端连接可能打断原IDE脚本，因此本工具用于主控已授权接管的现场试跑。
会话保持到相机10分钟窗口结束；不在启动后立即断开后端以免中断相机。
"""
import argparse
import hashlib
import json
from pathlib import Path
import queue
import time
from canmv_lap_bench import Session
from prepare_straight_bundle import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--confirmed-calibrated', action='store_true')
    args = parser.parse_args()
    if not args.confirmed_calibrated:
        raise ValueError('current STM32 phase2 and zero output must be established before camera takeover')
    args.output.mkdir(parents=True, exist_ok=False)
    source, manifest = build(True)
    if 'ALLOW_DRIVE = True' not in source or 'SHOW_PREVIEW = False' not in source:
        raise RuntimeError('unexpected straight drive source')
    (args.output / 'executed_source.py').write_bytes(source.encode('utf-8'))
    result = dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(), manifest=manifest,
                  main_py_written=False, automatic_motor_start=False, calibrated_confirmed=True,
                  camera_window_ms=600000, completed=False)
    (args.output / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    session = Session(args.output)
    owned_script = False
    stop_requested = False
    try:
        result['board'] = session.request('connectBoard', {'port': args.port, 'baudRate': 12000000}, timeout=25)
        status = session.request('scriptRunning')
        if status.get('running') is not False:
            raise RuntimeError('camera script still active after connect; do not overwrite it')
        # 清除连接时旧脚本的IDE interrupt标记；之后的错误只能来自本次已保存源码。
        session.tail = ''
        session.script_error = False
        session.running = True
        owned_script = True
        session.request('runScript', {'script': source}, timeout=35)
        print('[HOST STRAIGHT LIVE] camera enabled; NO START sent; STM32 KEY controls each 2s run', flush=True)
        deadline = time.monotonic() + 630
        next_status = time.monotonic() + 3
        while session.running is not False and time.monotonic() < deadline:
            try:
                session.record(session.messages.get(timeout=0.25))
            except queue.Empty:
                pass
            # 只接受本次独立证据目录中的停止标记；正常发送IDE停止请求，
            # 让相机finally发STOP并关日志，避免杀宿主进程留下SD缓冲未刷盘。
            if (args.output / 'stop.request').exists():
                stop_requested = True
                session.request('stopScript', timeout=15)
                session.running = session.request('scriptRunning').get('running', session.running)
                break
            if time.monotonic() >= next_status:
                status = session.request('scriptRunning')
                session.running = status.get('running', session.running)
                next_status = time.monotonic() + 3
        if session.running is not False:
            session.request('stopScript', timeout=15)
            raise TimeoutError('own straight camera exceeded session limit')
        if session.script_error and not stop_requested:
            raise RuntimeError('straight camera script raised; inspect terminal')
        result['completed'] = not stop_requested
        result['stopped_by_control_file'] = stop_requested
    except BaseException as exc:
        result['error'] = repr(exc)
        if owned_script and session.running is not False:
            try:
                session.request('stopScript', timeout=15)
            except BaseException:
                pass
        raise
    finally:
        session.close()
        (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
