"""离线复核已取得的冷启动证据和取证中断；不重启／重跑／改写原始结果。"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from canmv_runtime_probe import classify_failures, CANDIDATE_HASH


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    folder = args.folder
    result = json.loads((folder/'result.json').read_text(encoding='utf-8'))
    rows = [json.loads(line) for line in (folder/'runtime_log.jsonl').read_text(encoding='utf-8').splitlines()]
    terminal = (folder/'terminal.txt').read_text(encoding='utf-8')
    events = [json.loads(line) for line in (folder/'backend.jsonl').read_text(encoding='utf-8').splitlines()]
    requests = [(i, e['request']) for i, e in enumerate(events) if 'request' in e]
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
        if not ok: raise AssertionError(name)
    check('no_run_write_or_start_RPC', {r['method'] for _, r in requests} <= {'connectBoard', 'scriptRunning', 'io.queryFileStat', 'io.readFile', 'io.listDir', 'disconnectBoard'})
    check('deployed_main_hash_unchanged', hashlib.sha256((folder/'before_main.py').read_bytes()).hexdigest() == CANDIDATE_HASH)
    check('new_persistent_log_not_old_probe', result['runtime_log']['name'] != 'run_0001.jsonl' and rows[0]['duration_ms'] == 600000 and rows[0]['drive_allowed'])
    first_read = next(i for i, r in requests if r['method'] == 'io.queryFileStat')
    check('IDE_interrupt_arrived_during_attach_before_file_read', any(i < first_read and e.get('event') == 'scriptOutput'
          and 'Exception: IDE interrupt' in e.get('params', {}).get('text', '') for i, e in enumerate(events)))
    failures, unexpected = classify_failures(rows, terminal)
    check('actual_failure_is_external_readout_interruption', len(failures) == 1 and not unexpected)
    for error, text in (("OSError('camera failed')", terminal), ("Exception('IDE interrupt',)", ''),
                        ("OSError('IDE interrupt')", terminal), ("Exception('unknown interrupt')", terminal)):
        _, failed = classify_failures([dict(event='failed', error=error)], text)
        check('reject_unproven_or_other_error_' + error, bool(failed))
    frames = [row for row in rows if 'index' in row]
    check('real_camera_frames_precede_readout', len(frames) > 0 and max(row['index'] for row in frames) > 10)
    def stats(key):
        values = [r[key] for r in frames if r.get(key) is not None]
        return dict(min=min(values), median=statistics.median(values), max=max(values))
    review = dict(checks=checks, original_tool_passed=result['passed'], original_error=result.get('error'),
        cold_boot_entry_evidenced=True, evidence_basis='主控物理重启反馈＋新编号持久相机日志＋本会话无runScript／写入',
        source_sha256=CANDIDATE_HASH, runtime_log=result['runtime_log'], logged_samples=len(frames),
        highest_observed_algorithm_index=max(r['index'] for r in frames), actual_total_frames=None,
        invalid_logged_indices=[r['index'] for r in frames if not r['valid']],
        logged_wire_valid=sum(bool(r['wire_valid']) for r in frames), metrics={k: stats(k) for k in ('processing_ms', 'to_send_ms', 'interval_ms')},
        interrupted_by_readout=True, continuous_600s_verified=False, STM32_cold_boot_communication_verified=False,
        onboard_power_verified=False, motor_operated=False, lap_verified=False)
    (folder/'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(review, ensure_ascii=False))


if __name__ == '__main__': main()
