"""检查真实相机入口的许可边界和助手实际提交文本；不访问板卡／电机。"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

from prepare_lap_visual_link import prepare, R5, ROOT, BUNDLES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
        if not ok:
            raise AssertionError(name)
    flags = dict(suspended=True, mcu_revision=0x02110009, mcu_run_ms=3000, calibrated=True)
    for field, value in (('suspended', False), ('mcu_revision', 0x0211000A),
                         ('mcu_run_ms', 300000), ('calibrated', False)):
        rejected = False
        try:
            prepare('suspended', **dict(flags, **{field: value}))
        except ValueError:
            rejected = True
        check('reject_' + field, rejected)
    for mode, kwargs in (('isolated', {}), ('sd_replay', {}), ('fixture', {}),
                         ('no_drive', {'window_ms': 999999}), ('no_drive', {'bundle': 'arbitrary'})):
        rejected = False
        try:
            prepare(mode, **kwargs)
        except ValueError:
            rejected = True
        check('reject_' + mode + repr(kwargs), rejected)
    for mode, kwargs in (('no_drive', {}), ('isolated', {'power_isolated': True}),
                         ('suspended', flags)):
        source, info = prepare(mode, **kwargs)
        scope = {'__name__': 'host_visual_link_check'}
        exec(compile(source, '<checked>', 'exec'), scope)
        check(mode + '_live_camera_only', scope['MODE'] == 'live' and 'frame=sensor.snapshot(' in source)
        check(mode + '_duration', scope['DURATION_MS'] == (10000 if mode == 'no_drive' else 120000))
        check(mode + '_no_preview_when_permitted', mode == 'no_drive' or not scope['SHOW_PREVIEW'])
        check(mode + '_exact_hash', hashlib.sha256(source.encode()).hexdigest() == info['source_sha256'])
        packets = []
        sender = scope['LapSender'](lambda p: packets.append(p) or len(p), scope['ALLOW_DRIVE'])
        result = dict(valid=True, source='current_pair', confidence=70, steering=-182, bend=182)
        path = sender.path(result, 45, 50)
        check(mode + '_explicit_permission', bool(path[6] & 1) == (mode != 'no_drive'))
        check(mode + '_signed_steering', int.from_bytes(path[8:10], 'little', signed=True) == (-182 if mode != 'no_drive' else 0))
        for name, result_change, processing, age in (
            ('invalid_geometry', {'valid': False}, 45, 50),
            ('slow_processing', {}, 101, 110), ('old_camera', {}, 45, 150),
            ('expired_history', {'source': 'history', 'evidence_age_ms': 100}, 10, 20)):
            check(mode + '_' + name, not (sender.path(dict(result, **result_change), processing, age)[6] & 1))
        sender.stop()
        check(mode + '_only_STOP_commands', all(p[16] == 2 for p in packets if p[3] == 2))
        check(mode + '_all_CRCs', all(scope['crc16'](p[:18]) == int.from_bytes(p[18:], 'little') for p in packets))
        # 配置以外源码须与冻结R5逐字一致，防止放宽算法、时限或清理分支。
        restored = source.split('\n', 1)[1].replace("MODE='live'", "MODE='idle'").replace('UART_ENABLED=True', 'UART_ENABLED=False')
        restored = restored.replace('DURATION_MS=' + str(scope['DURATION_MS']), 'DURATION_MS=300000')
        if mode != 'no_drive':
            restored = restored.replace('\nALLOW_DRIVE=True\n', '\nALLOW_DRIVE=False\n').replace('\nSHOW_PREVIEW=False ', '\nSHOW_PREVIEW=True ')
        check(mode + '_all_other_R5_code_preserved', restored == R5.read_text(encoding='utf-8'))
    for mode, kwargs in (('no_drive', {}), ('isolated', {'power_isolated': True}), ('suspended', flags)):
        source, info = prepare(mode, bundle='r6', **kwargs)
        check('r6_' + mode + '_pinned_bundle', info['base_bundle_sha256'] == BUNDLES['r6'][1])
        check('r6_' + mode + '_correct_permission', ('\nALLOW_DRIVE=True\n' in source) == (mode != 'no_drive'))
        check('r6_' + mode + '_actual_fix_present', 'top_cells=sum(1 for index in queue' in source)
    spec = importlib.util.spec_from_file_location('helper_visual_test', ROOT / 'vision/tools/canmv_lap_bench.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    sessions = []
    class FakeSession:
        def __init__(self, folder):
            self.requests = []; self.running = False; self.script_error = False
            self.tail = '[L1 DONE] HOST FAKE ONLY'; self.closed = False; sessions.append(self)
        def request(self, method, params=None, timeout=None):
            self.requests.append((method, params))
            if method == 'runScript':
                self.running = False
            return {'running': False} if method == 'scriptRunning' else {}
        def close(self):
            self.closed = True
    with patch.object(helper, 'Session', FakeSession), patch.object(helper.time, 'sleep', lambda _: None):
        for mode, mode_flags in (('live_link_isolated', ['--confirmed-power-isolated']),
                                  ('live_link_suspended', ['--confirmed-suspended', '--confirmed-mcu-revision',
                                   '0x02110009', '--confirmed-mcu-run-ms', '3000', '--confirmed-calibrated'])):
            folder = output / mode
            with patch.object(sys, 'argv', ['helper', mode, '--output', str(folder), *mode_flags]), contextlib.redirect_stdout(io.StringIO()):
                helper.main()
            session = sessions[-1]
            submitted = [p['script'] for m, p in session.requests if m == 'runScript']
            check(mode + '_exact_submitted_bytes', len(submitted) == 1 and submitted[0].encode() == (folder / 'executed_source.py').read_bytes())
            check(mode + '_only_bounded_RPCs', {m for m, _ in session.requests} <= {'connectBoard', 'scriptRunning', 'runScript'})
            check(mode + '_closed', session.closed)
            before = len(sessions)
            rejected = False
            with patch.object(sys, 'argv', ['helper', mode, '--output', str(output / (mode + '_rejected'))]):
                try:
                    helper.main()
                except ValueError:
                    rejected = True
            check(mode + '_missing_conditions_before_connection', rejected and len(sessions) == before)
    (output / 'checks.json').write_text(json.dumps(dict(checks=checks, physical_board_used=False,
        motor_verified=False, fake_session_only=True), ensure_ascii=False, indent=2), encoding='utf-8')
    print(len(checks), 'visual entry checks PASS; no board or motor')


if __name__ == '__main__':
    main()
