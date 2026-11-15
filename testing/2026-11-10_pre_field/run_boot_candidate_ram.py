"""在原USB逻辑供电／动力隔离条件下验证新日志入口，只在RAM执行。

只运行本轮已验字节候选，不写main.py／boot.py／采集许可，不发START。
文件写入仅由候选新增编号日志完成；执行后只读下载该次日志。
"""
import base64
import hashlib
import json
from pathlib import Path
import queue
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'vision/tools'))
from canmv_lap_bench import Session


def main():
    """独占COM10、拒绝已有脚本；本次脚本最多60秒，超时只停止自己的任务。"""
    folder = Path(__file__).resolve().parent
    candidate = folder / 'cold_boot_candidate/main.py'
    manifest = json.loads((candidate.parent / 'manifest.json').read_text(encoding='utf-8'))
    source = candidate.read_bytes()
    if hashlib.sha256(source).hexdigest() != manifest['candidate_sha256'] or manifest['allow_drive']:
        raise RuntimeError('checked candidate mismatch or drive enabled')
    output = folder / 'cold_boot_ram_01'
    output.mkdir(exist_ok=False)
    session = Session(output)
    try:
        board = session.request('connectBoard', {'port': 'COM10', 'baudRate': 12000000}, timeout=25)
        if session.request('scriptRunning').get('running') is not False:
            raise RuntimeError('board must be idle; existing script retained')
        (output / 'executed_source.py').write_bytes(source)
        session.running = True
        session.request('runScript', {'script': source.decode('utf-8')}, timeout=35)
        deadline = time.monotonic() + 60
        next_status = time.monotonic() + 2
        while session.running is not False and time.monotonic() < deadline:
            try:
                session.record(session.messages.get(timeout=.25))
            except queue.Empty:
                pass
            if time.monotonic() >= next_status:
                status = session.request('scriptRunning')
                session.running = status.get('running', session.running)
                next_status = time.monotonic() + 2
        if session.running is not False:
            session.request('stopScript', timeout=15)
            raise TimeoutError('own boot diagnostic timed out')
        if session.script_error or '[L1 DONE]' not in session.tail:
            raise RuntimeError('boot diagnostic failed; original terminal retained')
        matches = re.findall(r'\[BOOT CHECK LOG\] (/sdcard/lap_boot_checks/check_\d{4}\.jsonl)', session.tail)
        if len(matches) != 1:
            raise RuntimeError('unique log path not reported')
        remote = matches[0]
        stat = session.request('io.queryFileStat', {'path': remote})
        if not stat.get('exists') or not 0 < stat.get('size', 0) <= 262144:
            raise RuntimeError('unexpected diagnostic log size')
        data = bytearray()
        while len(data) < stat['size']:
            count = min(32768, stat['size'] - len(data))
            reply = session.request('io.readFile', {'path': remote, 'offset': len(data), 'size': count}, timeout=30)
            chunk = base64.b64decode(reply['dataBase64']) if isinstance(reply.get('dataBase64'), str) else bytes(reply.get('data', []))
            if not 0 < len(chunk) <= count:
                raise RuntimeError('short log read')
            data.extend(chunk)
        (output / 'boot_log.jsonl').write_bytes(data)
        records = [json.loads(line) for line in data.decode('utf-8').splitlines()]
        frames = [row for row in records if 'index' in row]
        if not frames or records[-1].get('event') != 'completed' or any(row.get('wire_valid') or row.get('drive_allowed') for row in frames):
            raise RuntimeError('log completion/no-drive check failed')
        result = dict(board=board, remote_log=remote, source_sha256=hashlib.sha256(source).hexdigest(),
                      log_sha256=hashlib.sha256(data).hexdigest(), frames=len(frames),
                      processing_ms_min=min(row['processing_ms'] for row in frames),
                      processing_ms_max=max(row['processing_ms'] for row in frames),
                      interval_ms_max=max(row['interval_ms'] for row in frames if row['interval_ms'] is not None),
                      to_send_ms_max=max(row['to_send_ms'] for row in frames),
                      invalid_paths_only=True, main_py_written=False, physical_power_cycle_tested=False,
                      battery_power_verified=False, motor_started=False, stm32_receive_verified=False)
        (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print('RAM boot-log check PASS:', len(frames), 'frames; no main.py replacement or physical cold boot')
    finally:
        session.close()


if __name__ == '__main__':
    main()
