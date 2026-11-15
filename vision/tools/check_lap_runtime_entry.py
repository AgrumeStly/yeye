"""核对持续入口的真实封包、日志与失败边界；相机替身不代表实板证据。"""
import argparse
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path

from prepare_lap_runtime_entry import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--trace', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
        if not ok:
            raise AssertionError(name)
    source, info = build(True, args.continuous, args.trace)
    check('candidate_matches_current_generator', args.candidate.read_bytes() == source.encode('utf-8'))
    scope = {'__name__': 'runtime_entry_host_model'}
    exec(compile(source, str(args.candidate), 'exec'), scope)
    check('expected_input_lifetime_live_not_automatic_START', scope['MODE'] == 'live' and scope['DURATION_MS'] == (0 if args.continuous else 600000)
          and scope['UART_ENABLED'] and scope['ALLOW_DRIVE'] and not info['automatic_motor_start'])
    if args.continuous:
        for elapsed in (0, 300000, 600000, 600001, 1800000):
            check('camera_continues_at_' + str(elapsed), not scope['_runtime_duration_elapsed'](elapsed))
        check('main_loop_uses_actual_lifetime_predicate', "if MODE=='live' and _runtime_duration_elapsed(time.ticks_diff(started,origin)):" in source)
        saved_duration = scope['DURATION_MS']
        scope['DURATION_MS'] = 30000
        check('bounded_probe_can_still_stop', not scope['_runtime_duration_elapsed'](29999) and scope['_runtime_duration_elapsed'](30000))
        scope['DURATION_MS'] = saved_duration
    check('IDE_display_transmission_disabled', not scope['SHOW_PREVIEW'] and 'to_ide=False' in source)
    if args.trace:
        old, _ = build(True, True)
        check('previous_v2_exact_source_preserved', hashlib.sha256(old.encode()).hexdigest() ==
              '838c5e9a4d14d42840c54526b1f3c4d4a848e93654de8bca5faf45f85fb2968f')
        def functions(text):
            return {node.name: ast.dump(node) for node in ast.parse(text).body
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        before, after = functions(old), functions(source)
        for name in ('_threshold','_grid','_pair_anchors','_anchor_distance','_template','LiteLapRoute','LapSender'):
            check(name+'_logic_exactly_unchanged', before[name] == after[name])
        check('per_frame_trace_enabled', scope['TRACE_ALL_FRAMES'] and
              "or TRACE_ALL_FRAMES or index%10==0" in source)
        check('real_session_clock_and_actual_wire_fields_logged',
              'elapsed_ms=time.ticks_diff(started,origin)' in source and
              'wire_sequence=packet[5]' in source and 'wire_age_ms=packet[10]|(packet[11]<<8)' in source)
        disabled, _ = build(False, True, True)
        check('trace_default_permission_still_denied', '\nALLOW_DRIVE=False\n' in disabled)
        try:
            build(True, False, True)
            rejected = False
        except ValueError:
            rejected = True
        check('trace_without_continuous_rejected', rejected)
    default, _ = build()
    default_scope = {'__name__': 'runtime_default_host_model'}
    exec(compile(default, '<runtime_default>', 'exec'), default_scope)
    check('generator_default_denies_drive', not default_scope['ALLOW_DRIVE'])
    packets = []
    sender = scope['LapSender'](lambda p: packets.append(bytes(p)) or len(p), True)
    geometry = dict(valid=True, source='current_pair', confidence=70, steering=286, bend=286)
    packet = sender.path(geometry, 50, 60)
    check('real_sender_accepts_explicit_current_pair', packet[6] == 1 and int.from_bytes(packet[8:10], 'little', signed=True) == 286)
    for name, change, processing, age in (('invalid_geometry', {'valid': False}, 50, 60),
                                        ('slow_processing', {}, 101, 110), ('old_frame', {}, 50, 150),
                                        ('expired_history', {'source': 'history', 'evidence_age_ms': 100}, 10, 20)):
        check(name + '_denies_drive', not sender.path(dict(geometry, **change), processing, age)[6] & 1)
    default_packet = default_scope['LapSender'](allow_drive=False).path(geometry, 50, 60)
    check('default_even_good_geometry_invalid', default_packet[6] == 0)
    sender.stop()
    check('commands_STOP_only', all(p[16] == 2 for p in packets if p[3] == 2))
    check('all_actual_packet_CRCs', all(scope['crc16'](p[:18]) == int.from_bytes(p[18:], 'little') for p in packets))
    sd = args.output.resolve() / 'model_sd'
    sd.mkdir()
    scope['RUNTIME_SD_ROOT'] = str(sd)
    frames = [dict(index=1, source='unknown', wire_valid=False, drive_allowed=True),
              dict(index=10, source='current_pair', wire_valid=True, drive_allowed=True)]
    calls = []
    def fake_camera():
        calls.append('camera')
        for frame in frames:
            scope['_runtime_record'](frame)
    scope['main'] = fake_camera
    def run():
        with contextlib.redirect_stdout(io.StringIO()):
            return Path(scope['_runtime_boot']())
    first = run()
    original = first.read_bytes()
    data = [json.loads(line) for line in first.read_text(encoding='utf-8').splitlines()]
    check('begin_records_true_camera_permission_and_no_start', data[0]['event'] == 'begin' and data[0]['drive_allowed']
          and data[0]['input_kind'] == 'real_camera' and not data[0]['automatic_motor_start'])
    check('original_frame_records_saved_in_order', data[1:3] == frames)
    check('completion_not_lap_acceptance', data[-1] == dict(event='completed', lap_acceptance=False))
    check('stream_cleared_after_success', scope['_runtime_stream'] is None)
    second = run()
    check('new_number_each_boot', first.name == 'run_0001.jsonl' and second.name == 'run_0002.jsonl')
    check('previous_log_bytes_preserved', first.read_bytes() == original)
    def fail_camera():
        calls.append('failure')
        scope['_runtime_record'](frames[0])
        raise OSError('injected camera failure')
    scope['main'] = fail_camera
    before = len(calls)
    try:
        run()
        rejected = False
    except OSError:
        rejected = True
    failed = [json.loads(line) for line in (first.parent / 'run_0003.jsonl').read_text(encoding='utf-8').splitlines()]
    check('camera_exception_propagates_without_retry', rejected and calls[before:] == ['failure'])
    check('failure_saved_without_completion', failed[-1]['event'] == 'failed' and not any(r.get('event') == 'completed' for r in failed))
    check('stream_cleared_after_failure', scope['_runtime_stream'] is None)
    scope['main'] = fake_camera
    for field, wrong in (('MODE', 'sd_replay'), ('UART_ENABLED', False), ('DURATION_MS', 300000), ('SHOW_PREVIEW', True)):
        previous = scope[field]
        scope[field] = wrong
        before = len(calls)
        try:
            run()
            rejected = False
        except RuntimeError:
            rejected = True
        check(field + '_refused_before_camera_and_log', rejected and len(calls) == before and not (first.parent / 'run_0004.jsonl').exists())
        scope[field] = previous
    scope['RUNTIME_LOG_LIMIT'] = 1
    before = len(calls)
    try:
        run()
        rejected = False
    except RuntimeError:
        rejected = True
    check('exhausted_slots_refuse_and_keep_evidence', rejected and len(calls) == before and first.read_bytes() == original)
    scope['RUNTIME_LOG_LIMIT'] = 1000
    scope['RUNTIME_SD_ROOT'] = str(sd / 'missing_mount')
    before = len(calls)
    try:
        run()
        rejected = False
    except OSError:
        rejected = True
    check('missing_SD_refused_before_camera', rejected and len(calls) == before)
    result = dict(checks=checks, candidate_sha256=hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
                  camera_replaced_by_model=True, physical_board_used=False, motor_verified=False,
                  main_py_deployed=False, SD_timing_verified=False)
    (args.output / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(len(checks), 'runtime entry checks PASS; camera replaced by host model')


if __name__ == '__main__':
    main()
