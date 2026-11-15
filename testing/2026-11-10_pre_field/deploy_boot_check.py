"""执行主控明确授权的K230十秒无驱动main.py切换并逐字节回读。

固定候选／路径／端口；当前入口必须仍与本轮真实备份一致才允许写入。
不运行任意脚本、不改boot.py／采集许可、不启动电机或切换实际供电。
"""
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'vision/tools'))
from canmv_lap_bench import Session

EXPECTED = 'c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269'


def read_remote(session, path):
    """只读原始文件字节；最多128KiB，拒绝目录、未知尺寸和不完整分块。"""
    stat = session.request('io.queryFileStat', {'path': path})
    if not stat.get('exists') or stat.get('type') == 'directory':
        raise RuntimeError('expected existing file: ' + path)
    size = stat.get('size')
    if not isinstance(size, int) or not 0 <= size <= 131072:
        raise RuntimeError('unexpected file size: ' + path)
    data = bytearray()
    while len(data) < size:
        count = min(32768, size - len(data))
        reply = session.request('io.readFile', {'path': path, 'offset': len(data), 'size': count}, timeout=30)
        chunk = base64.b64decode(reply['dataBase64']) if isinstance(reply.get('dataBase64'), str) else bytes(reply.get('data', []))
        if not 0 < len(chunk) <= count:
            raise RuntimeError('incomplete read: ' + path)
        data.extend(chunk)
    return bytes(data)


def main():
    """先核对软件证据和板上旧字节，再只写一次main.py；保存失败阶段便于恢复。"""
    folder = Path(__file__).resolve().parent
    candidate = (folder / 'cold_boot_candidate/main.py').read_bytes()
    if hashlib.sha256(candidate).hexdigest() != EXPECTED:
        raise RuntimeError('authorized candidate changed')
    compile(candidate, 'authorized_main.py', 'exec')
    for name, count in (('cold_boot_checks', 16), ('cold_boot_protocol_checks', 42)):
        checks = json.loads((folder / name / 'checks.json').read_text(encoding='utf-8'))['checks']
        if len(checks) != count or not all(row['passed'] for row in checks):
            raise RuntimeError('candidate checks missing or failed')
    ram = json.loads((folder / 'cold_boot_ram_01/result.json').read_text(encoding='utf-8'))
    if ram['source_sha256'] != EXPECTED or not ram['invalid_paths_only']:
        raise RuntimeError('candidate differs from RAM-tested no-drive bytes')
    backup = (folder / 'startup_backup/main.py').read_bytes()
    backup_info = json.loads((folder / 'startup_backup/manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(backup).hexdigest() != backup_info['files']['/sdcard/main.py']['sha256']:
        raise RuntimeError('original backup changed')
    output = folder / 'boot_deploy_01'
    output.mkdir(exist_ok=False)
    state = dict(authorized_by_operator=True, remote_path='/sdcard/main.py', candidate_sha256=EXPECTED,
                 write_requested=False, readback_verified=False, script_run_requested=False,
                 motor_started=False, physical_power_cycle_tested=False, battery_power_verified=False)
    session = Session(output)
    try:
        state['board'] = session.request('connectBoard', {'port': 'COM10', 'baudRate': 12000000}, timeout=25)
        state['initial_status'] = session.request('scriptRunning')
        if state['initial_status'].get('running') is not False:
            raise RuntimeError('board not idle; existing script will not be stopped')
        before = read_remote(session, '/sdcard/main.py')
        if before != backup:
            raise RuntimeError('current main.py changed since backup; refusing overwrite')
        (output / 'previous_main.py').write_bytes(before)
        state['before_sha256'] = hashlib.sha256(before).hexdigest()
        protected = {}
        for path in ('/sdcard/boot.py', '/sdcard/full_lap_capture.arm', '/sdcard/push_capture.arm'):
            info = session.request('io.queryFileStat', {'path': path})
            if info.get('exists'):
                raise RuntimeError('protected startup/arm state differs from backup: ' + path)
            protected[path] = info
        state['protected_before'] = protected
        state['write_requested'] = True
        (output / 'attempt.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        state['write_reply'] = session.request('io.writeFile', {'path': '/sdcard/main.py',
            'dataBase64': base64.b64encode(candidate).decode('ascii')}, timeout=45)
        after = read_remote(session, '/sdcard/main.py')
        (output / 'readback_main.py').write_bytes(after)
        state['after_sha256'] = hashlib.sha256(after).hexdigest()
        state['readback_verified'] = after == candidate
        state['bytes'] = len(after)
        if not state['readback_verified']:
            raise RuntimeError('main.py readback mismatch; do not power cycle')
        protected_after = {}
        for path in protected:
            info = session.request('io.queryFileStat', {'path': path})
            protected_after[path] = info
            if info.get('exists'):
                raise RuntimeError('protected file unexpectedly appeared: ' + path)
        state['protected_after'] = protected_after
        state['final_status'] = session.request('scriptRunning')
        (output / 'result.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print('DEPLOYED and byte-for-byte VERIFIED:', len(after), 'bytes;', state['after_sha256'])
        print('No runScript, motor start, power change or physical cold boot performed.')
    except BaseException as exc:
        state['error'] = repr(exc)
        (output / 'failure.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        raise
    finally:
        session.close()


if __name__ == '__main__':
    main()
