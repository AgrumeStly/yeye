"""用官方已安装后端运行十秒直道无驱动诊断，保存原图和逐帧日志。

只允许preview派生脚本，ALLOW_DRIVE=False；不写main.py，不发START。
connectBoard可能中断原IDE脚本，因此先保存连接状态并明确用于本次悬空诊断。
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import queue
import re
import time
from canmv_lap_bench import Session
from canmv_runtime_probe import read_file
from prepare_straight_bundle import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--confirmed-suspended', action='store_true')
    args = parser.parse_args()
    if not args.confirmed_suspended:
        raise ValueError('operator must confirm both drive wheels completely suspended')
    args.output.mkdir(parents=True, exist_ok=False)
    source, manifest = build(False)
    source = source.replace('DURATION_MS = 600000', 'DURATION_MS = 10000')
    source += "\nprint('[STRAIGHT PROBE DONE] no START; drive disabled')\n"
    if 'ALLOW_DRIVE = False' not in source or 'ALLOW_DRIVE = True' in source:
        raise RuntimeError('no-drive source required')
    (args.output / 'executed_source.py').write_bytes(source.encode('utf-8'))
    result = dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  parent_manifest=manifest, main_py_written=False, automatic_motor_start=False,
                  allow_drive=False, confirmed_suspended=True, passed=False)
    session = Session(args.output)
    session.capture_preview = True
    preview = False
    owned_script = False
    try:
        result['board'] = session.request('connectBoard', {'port': args.port, 'baudRate': 12000000}, timeout=25)
        result['initial_status'] = session.request('scriptRunning')
        if result['initial_status'].get('running') is not False:
            raise RuntimeError('board script still active; do not replace it silently')
        before, _ = read_file(session, '/sdcard/main.py')
        if before is not None:
            (args.output / 'before_main.py').write_bytes(before)
            result['main_sha256_before'] = hashlib.sha256(before).hexdigest()
        session.running = True
        owned_script = True
        session.request('runScript', {'script': source}, timeout=35)
        started = time.monotonic()
        deadline = started + 35
        next_status = started + 2
        while session.running is not False and time.monotonic() < deadline:
            try:
                session.record(session.messages.get(timeout=0.1))
            except queue.Empty:
                pass
            if not preview and time.monotonic() - started > 0.5:
                session.request('startPreview', {}, timeout=5)
                preview = True
            if time.monotonic() >= next_status:
                state = session.request('scriptRunning')
                session.running = state.get('running', session.running)
                next_status = time.monotonic() + 2
        if session.running is not False:
            session.request('stopScript', timeout=15)
            raise TimeoutError('own no-drive probe exceeded time limit')
        if session.script_error or '[STRAIGHT PROBE DONE]' not in session.tail:
            raise RuntimeError('real board probe raised or did not complete')
        match = re.search(r'\[STRAIGHT LOG\]\s+(/sdcard/straight_logs/run_\d{4}\.jsonl)', session.tail)
        if match is None:
            raise RuntimeError('actual new SD log name not received')
        remote = match.group(1)
        stat = session.request('io.queryFileStat', {'path': remote})
        size = stat.get('size')
        if stat.get('type') != 'file' or not isinstance(size, int) or not 0 < size < 1024 * 1024:
            raise RuntimeError('invalid straight log metadata')
        data = bytearray()
        while len(data) < size:
            count = min(32768, size - len(data))
            payload = session.request('io.readFile', {'path': remote, 'offset': len(data), 'size': count})
            chunk = base64.b64decode(payload['dataBase64'], validate=True) if isinstance(payload.get('dataBase64'), str) else bytes(payload.get('data', []))
            if len(chunk) != count:
                raise RuntimeError('short log read')
            data.extend(chunk)
        (args.output / 'camera.jsonl').write_bytes(data)
        rows = [json.loads(line) for line in data.decode('utf-8').splitlines()]
        frames = [r for r in rows if 'index' in r]
        if not frames or any(r['wire_valid'] for r in frames):
            raise RuntimeError('no frames or unexpected drive permission')
        after, _ = read_file(session, '/sdcard/main.py')
        if after != before:
            raise RuntimeError('main.py changed during probe')
        tail = [r for r in frames if r['elapsed_ms'] >= frames[-1]['elapsed_ms'] - 2000]
        result.update(passed=True, frames=len(frames), valid_geometry=sum(bool(r['valid']) for r in frames),
                      scope='diagnostic execution only; not motor or ground acceptance',
                      stable_geometry_last_2s=bool(tail) and all(r['valid'] for r in tail),
                      motion_ready=False,  # 禁驱动探针只报告观察，不替代接收／动力／现场放行。
                      source_log=remote, all_wire_invalid=True, main_bytes_unchanged=True,
                      max_processing_ms=max(r['processing_ms'] for r in frames),
                      max_to_send_ms=max(r['to_send_ms'] for r in frames),
                      max_interval_ms=max((r['interval_ms'] or 0) for r in frames), preview_frames=session.preview_saved)
    except BaseException as exc:
        result['error'] = repr(exc)
        if owned_script and session.running is not False:
            try:
                session.request('stopScript', timeout=15)
            except BaseException:
                pass
        raise
    finally:
        if preview:
            try:
                session.request('stopPreview', {}, timeout=5)
            except BaseException:
                pass
        session.close()
        (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
