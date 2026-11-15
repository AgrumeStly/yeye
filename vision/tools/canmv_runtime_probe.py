"""官方后端受限入口：只读备份启动文件，或30秒禁止驱动的真实相机写盘。

必须先人工确认动力物理隔离；没有任意脚本／文件路径／main.py写入能力。
复用已有Session保持单一端口所有者，已有脚本运行时直接拒绝，不自动打断。
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import queue
import re
import time

from canmv_lap_bench import Session, ROOT, replacement

CANDIDATE = ROOT / 'testing/2026-11-11_field_live/runtime_r6_cold_boot_candidate/main.py'
CANDIDATE_HASH = '397d6a7d91983bffe7655704e727e458ca35f2b0910982dcdf53ad72e8aa5db1'
CONTINUOUS_CANDIDATE = ROOT / 'testing/2026-11-12_field_resume/runtime_continuous_candidate_02/main.py'
CONTINUOUS_HASH = '838c5e9a4d14d42840c54526b1f3c4d4a848e93654de8bca5faf45f85fb2968f'
TRACE_CANDIDATE = ROOT / 'testing/2026-11-12_field_resume/runtime_trace_candidate_03/main.py'
TRACE_HASH = 'f9a12f4ec10d1fec6ab629f3415858403b2a4d0ed4df16dfb76482f4c5fe16d8'
VERSIONS = ('bounded-v1', 'continuous-v2', 'trace-v3')


def runtime_candidate(version):
    """固定候选白名单；新增取证版也不能传入任意文件／哈希。"""
    return {'bounded-v1': (CANDIDATE, CANDIDATE_HASH),
            'continuous-v2': (CONTINUOUS_CANDIDATE, CONTINUOUS_HASH),
            'trace-v3': (TRACE_CANDIDATE, TRACE_HASH)}[version]


def classify_failures(rows, terminal_text):
    """只识别明确外部中断；IDE异常须同时有本次接收终端的确切异常行。

    本固件使用Exception('IDE interrupt',)，不是KeyboardInterrupt。相机／SD
    异常仍返回运行失败，不能因为文本里包含interrupt就一概忽略。
    """
    failures = [row for row in rows if row.get('event') == 'failed']
    def external(row):
        error = row.get('error', '')
        return error in ('KeyboardInterrupt()', 'KeyboardInterrupt') or (
            error in ("Exception('IDE interrupt',)", "Exception('IDE interrupt')")
            and 'Exception: IDE interrupt' in terminal_text)
    return failures, [row for row in failures if not external(row)]


def probe_source(version='bounded-v1'):
    """固定白名单候选只改为30秒、禁止驱动；日志／清理／时序代码保持。"""
    if version not in VERSIONS:
        raise ValueError('unknown reviewed runtime version')
    candidate, digest = runtime_candidate(version)
    raw = candidate.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise RuntimeError('reviewed runtime candidate changed')
    source = raw.decode('utf-8').replace('\r\n', '\n')
    changes = [('\nALLOW_DRIVE=True\n', '\nALLOW_DRIVE=False\n')]
    if version == 'bounded-v1':
        changes += [('\nDURATION_MS=600000\n', '\nDURATION_MS=30000\n'), ('DURATION_MS!=600000', 'DURATION_MS!=30000')]
    else:
        changes += [('\nDURATION_MS=0  # 0仅表示持续相机输入，绝不延长STM32单次运动期限。\n',
                     '\nDURATION_MS=30000  # 仅本次短诊断；正式入口持续相机输入，STM32时限独立。\n'),
                    ('DURATION_MS!=0', 'DURATION_MS!=30000')]
    for old, new in changes:
        source = replacement(source, old, new)
    compile(source, '<30s_runtime_probe>', 'exec')
    return source


def read_file(session, remote):
    """按官方扩展协议分块读原字节；仅固定启动路径及本次新编号日志。"""
    if remote not in ('/sdcard/main.py', '/sdcard/boot.py') and not re.fullmatch(r'/sdcard/lap_runtime_logs/run_\d{4}\.jsonl', remote):
        raise ValueError('remote read path outside task allowlist')
    stat = session.request('io.queryFileStat', {'path': remote})
    if not stat.get('exists'):
        return None, stat
    size = stat.get('size')
    # 原始启动文件仍限512KiB；十分钟全量无效帧日志可超过该值，日志单独
    # 限8MiB并继续32KiB分块读取，不能因取证上限不足要求重跑真实试验。
    limit = 8*1024*1024 if remote.startswith('/sdcard/lap_runtime_logs/') else 512*1024
    if stat.get('type') != 'file' or type(size) is not int or not 0 <= size <= limit:
        raise RuntimeError('unexpected file metadata or oversized task file')
    result = bytearray()
    while len(result) < size:
        count = min(32768, size-len(result))
        payload = session.request('io.readFile', {'path': remote, 'offset': len(result), 'size': count})
        chunk = base64.b64decode(payload['dataBase64'], validate=True) if isinstance(payload.get('dataBase64'), str) else bytes(payload.get('data', []))
        if len(chunk) != count:
            raise RuntimeError('short board file read; no backup success claimed')
        result.extend(chunk)
    return bytes(result), stat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('snapshot', 'probe', 'cold_boot_readback'))
    parser.add_argument('--port', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--confirmed-power-isolated', action='store_true')
    parser.add_argument('--expected-log-number', type=int)
    parser.add_argument('--runtime-version', choices=VERSIONS, default='bounded-v1')
    args = parser.parse_args()
    if args.expected_log_number is not None and (args.action != 'cold_boot_readback' or not 2 <= args.expected_log_number <= 9999):
        raise ValueError('explicit boot-log selection only supports numbered persistent readback')
    if not args.confirmed_power_isolated:
        raise ValueError('driver OFF and physical XT30 isolation required before connection')
    source = probe_source(args.runtime_version) if args.action == 'probe' else None
    args.output.mkdir(parents=True, exist_ok=False)
    result = dict(action=args.action, power_isolated_confirmed=True, main_py_written=False,
                  automatic_motor_start=False, files={}, passed=False)
    session = Session(args.output)
    try:
        result['runtime_version'] = args.runtime_version
        result['board'] = session.request('connectBoard', {'port': args.port, 'baudRate': 12000000}, timeout=25)
        time.sleep(.25)
        status = session.request('scriptRunning')
        result['initial_status'] = status
        if status.get('running', status.get('scriptRunning')) is not False and args.action != 'cold_boot_readback':
            raise RuntimeError('board not idle; existing script retained')
        for remote in ('/sdcard/main.py', '/sdcard/boot.py'):
            raw, stat = read_file(session, remote)
            row = dict(stat=stat)
            if raw is not None:
                local = 'before_' + Path(remote).name
                (args.output / local).write_bytes(raw)
                row.update(local=local, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            result['files'][remote] = row
        if args.action == 'cold_boot_readback':
            if result['files']['/sdcard/main.py'].get('sha256') not in (CANDIDATE_HASH, CONTINUOUS_HASH, TRACE_HASH):
                raise RuntimeError('cold boot entry hash differs from deployed candidate')
            listing = session.request('io.listDir', {'path': '/sdcard/lap_runtime_logs', 'offset': 0})
            result['directory_listing'] = listing
            if listing.get('nextOffset') is not None:
                raise RuntimeError('paged log directory needs explicit continuation; no incomplete selection')
            names = sorted(entry['name'] for entry in listing.get('entries', [])
                           if re.fullmatch(r'run_\d{4}\.jsonl', entry.get('name', '')))
            if not names:
                raise RuntimeError('no persistent runtime boot log')
            selected = names[-1] if args.expected_log_number is None else 'run_%04d.jsonl' % args.expected_log_number
            if selected not in names:
                raise RuntimeError('expected power-cycle log absent; later USB log cannot substitute')
            result['selection'] = dict(expected_number=args.expected_log_number, selected=selected,
                latest=names[-1], power_origin_requires_operator_timeline=True)
            remote = '/sdcard/lap_runtime_logs/' + selected
            raw, stat = read_file(session, remote)
            if raw is None:
                raise RuntimeError('new boot log disappeared')
            (args.output / 'runtime_log.jsonl').write_bytes(raw)
            result['runtime_log'] = dict(remote=remote, stat=stat, bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(), name=selected)
            # 恢复电脑USB可能另起一个日志。保留后续日志原件和编号，不能选
            # “最新”就冒充之前的电池供电；实际电源归属仍依据人工操作顺序。
            later = [name for name in names if name > selected]
            if len(later) > 4:
                raise RuntimeError('too many untracked later boots; preserve listing and clarify timeline')
            result['later_logs'] = []
            for name in later:
                data, later_stat = read_file(session, '/sdcard/lap_runtime_logs/' + name)
                if data is None:
                    raise RuntimeError('later boot log disappeared')
                (args.output / ('later_' + name)).write_bytes(data)
                result['later_logs'].append(dict(name=name, stat=later_stat, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
            rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
            if selected == 'run_0001.jsonl' or not rows or rows[0].get('duration_ms') not in (0, 600000) or not rows[0].get('drive_allowed'):
                raise RuntimeError('new reviewed runtime boot log not evidenced; old 30s probe insufficient')
            samples = [row for row in rows if 'index' in row]
            if not samples:
                raise RuntimeError('new boot log has no actual camera frame samples')
            failures, unexpected = classify_failures(rows, session.tail)
            result['runtime_samples'] = len(samples)
            result['highest_observed_algorithm_index'] = max(row['index'] for row in samples)
            result['log_failure_events'] = failures
            # 主动连接IDE可能中断正在运行的脚本；原样保留该边界，不把其它
            # 相机/SD异常当作持续运行正常。600秒窗口未到也不要求completed。
            if unexpected:
                raise RuntimeError('cold boot runtime recorded a non-interruption failure')
            result['readout_interruption_possible'] = bool(failures)
            result['operator_physical_cold_boot_context_required'] = True
            result['no_runScript_sent'] = True
        if source is not None:
            if result['files']['/sdcard/main.py'].get('sha256') not in (
                    'c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269', CANDIDATE_HASH, CONTINUOUS_HASH, TRACE_HASH):
                raise RuntimeError('current startup file differs from reviewed entries; backup retained, no probe started')
            (args.output / 'executed_source.py').write_bytes(source.encode('utf-8'))
            result['source_sha256'] = hashlib.sha256(source.encode('utf-8')).hexdigest()
            session.running = True
            session.request('runScript', {'script': source}, timeout=35)
            deadline = time.monotonic()+70
            while session.running is not False and time.monotonic() < deadline:
                try:
                    session.record(session.messages.get(timeout=.25))
                except queue.Empty:
                    pass
            if session.running is not False:
                session.request('stopScript', timeout=15)
                raise TimeoutError('own 30s probe exceeded bound; interrupted')
            if session.script_error or '[L1 DONE]' not in session.tail:
                raise RuntimeError('camera probe did not complete normally; original terminal retained')
            matches = re.findall(r'\[LAP RUNTIME LOG\]\s+(/sdcard/lap_runtime_logs/run_\d{4}\.jsonl)', session.tail)
            if len(matches) != 1:
                raise RuntimeError('new runtime log path not unambiguous')
            raw, stat = read_file(session, matches[0])
            if raw is None:
                raise RuntimeError('runtime log absent')
            (args.output / 'runtime_log.jsonl').write_bytes(raw)
            rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
            if rows[0].get('event') != 'begin' or rows[-1].get('event') != 'completed' or any(r.get('wire_valid') or r.get('drive_allowed') for r in rows):
                raise RuntimeError('runtime log incomplete or drive prohibition violated')
            result['runtime_log'] = dict(remote=matches[0], stat=stat, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), records=len(rows))
            after, _ = read_file(session, '/sdcard/main.py')
            if after != (args.output / 'before_main.py').read_bytes():
                raise RuntimeError('startup file unexpectedly changed')
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
