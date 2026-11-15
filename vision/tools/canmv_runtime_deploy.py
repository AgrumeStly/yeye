"""部署一个固定哈希持续入口：仅在主控明确授权及动力隔离后使用。

先备份并逐字节比对当前10秒入口，再写固定候选并读回；不执行脚本、
不发START、不改boot.py／采集许可。不提供任意路径或任意源文件参数。
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time

from canmv_lap_bench import Session, ROOT
from canmv_runtime_probe import CANDIDATE, CANDIDATE_HASH, CONTINUOUS_CANDIDATE, CONTINUOUS_HASH, VERSIONS, read_file, runtime_candidate

BACKUP = ROOT / 'testing/2026-11-12_field_resume/runtime_log_probe_01/before_main.py'
BACKUP_HASH = 'c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269'
CONTINUOUS_BACKUP = ROOT / 'testing/2026-11-12_field_resume/runtime_window_stop_01/board_readback_02/before_main.py'
TRACE_BACKUP = ROOT / 'testing/2026-11-12_field_resume/ground_straight_01/board_readback_01/before_main.py'


def deploy(session, folder, approved_hash, version='bounded-v1'):
    """只写已获本次具体授权的候选；任何未知当前入口先保存并拒绝覆盖。"""
    if version not in VERSIONS:
        raise ValueError('unknown reviewed deployment version')
    candidate, candidate_hash = runtime_candidate(version)
    backup_path, backup_hash = {'bounded-v1': (BACKUP, BACKUP_HASH),
        'continuous-v2': (CONTINUOUS_BACKUP, CANDIDATE_HASH),
        'trace-v3': (TRACE_BACKUP, CONTINUOUS_HASH)}[version]
    if approved_hash != candidate_hash:
        raise ValueError('explicit approval must name the reviewed candidate hash')
    source, backup = candidate.read_bytes(), backup_path.read_bytes()
    if hashlib.sha256(source).hexdigest() != candidate_hash or hashlib.sha256(backup).hexdigest() != backup_hash:
        raise RuntimeError('reviewed candidate or true backup changed')
    status = session.request('scriptRunning')
    if status.get('running', status.get('scriptRunning')) is not False:
        raise RuntimeError('existing script running; no interruption or write')
    before, _ = read_file(session, '/sdcard/main.py')
    if before is not None:
        (folder / 'before_main.py').write_bytes(before)
    if before != backup:
        raise RuntimeError('current entry differs from true backup; no write')
    boot, _ = read_file(session, '/sdcard/boot.py')
    if boot is not None:
        (folder / 'unexpected_boot.py').write_bytes(boot)
        raise RuntimeError('unexpected boot.py exists; no write')
    # 使用本固件已实际验证过的官方完整写入RPC，不经编辑器自动压缩。
    result = session.request('io.writeFile', {'path': '/sdcard/main.py',
        'dataBase64': base64.b64encode(source).decode('ascii')}, timeout=30)
    if result.get('success') is not True:
        raise RuntimeError('board rejected startup write; physical power remains isolated')
    after, stat = read_file(session, '/sdcard/main.py')
    if after is not None:
        (folder / 'readback_main.py').write_bytes(after)
    if after != source:
        raise RuntimeError('startup readback differs; do not power motors or cold boot')
    boot_after, _ = read_file(session, '/sdcard/boot.py')
    if boot_after is not None:
        raise RuntimeError('boot.py unexpectedly changed')
    status = session.request('scriptRunning')
    if status.get('running', status.get('scriptRunning')) is not False:
        raise RuntimeError('unexpected script activity after write')
    return dict(candidate_sha256=candidate_hash, runtime_version=version, bytes=len(source), stat=stat,
        backup_sha256=backup_hash, exact_readback=True, main_py_written=True,
        script_executed=False, automatic_motor_start=False, physical_power_isolated=True,
        cold_boot_verified=False, ground_motion_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--approved-candidate-sha256', required=True)
    parser.add_argument('--confirmed-power-isolated', action='store_true')
    parser.add_argument('--runtime-version', choices=VERSIONS, default='bounded-v1')
    args = parser.parse_args()
    _, expected_hash = runtime_candidate(args.runtime_version)
    if not args.confirmed_power_isolated or args.approved_candidate_sha256 != expected_hash:
        raise ValueError('physical isolation and exact candidate authorization required before connection')
    args.output.mkdir(parents=True, exist_ok=False)
    session = Session(args.output)
    result = dict(passed=False, action='deploy_fixed_runtime_candidate')
    try:
        result['board'] = session.request('connectBoard', {'port': args.port, 'baudRate': 12000000}, timeout=25)
        time.sleep(.25)
        result.update(deploy(session, args.output, args.approved_candidate_sha256, args.runtime_version))
        result['passed'] = True
    except BaseException as exc:
        result['error'] = repr(exc)
        raise
    finally:
        (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        session.close()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
