"""检查脱机无动力候选的真实封包与日志异常边界；不访问板卡。

相机主流程由已知输入替身代替，明确不能作为板上API／时序／供电验收。
执行生成文件中的真实LapSender、启动门、日志编号和异常处理。
"""
import argparse
import contextlib
import io
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    scope = {'__name__': 'boot_check_host_model'}
    exec(compile(args.candidate.read_bytes(), str(args.candidate), 'exec'), scope)
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(dict(name=name, passed=True))

    check('10s_no_drive_configuration', scope['MODE'] == 'live' and scope['DURATION_MS'] == 10000
          and scope['UART_ENABLED'] and not scope['ALLOW_DRIVE'] and not scope['SHOW_PREVIEW'])
    # 用真实发送器处理即便“识别有效”的输入，仍必须发送flags0，命令仅STOP。
    packets = []
    sender = scope['LapSender'](lambda data: packets.append(bytes(data)) or len(data), scope['ALLOW_DRIVE'])
    packet = sender.path(dict(valid=True, source='current_pair', confidence=100, steering=500, bend=0), 10, 20)
    check('valid_geometry_still_sends_invalid_path', packet[3] == 1 and packet[6] == 0)
    sender.stop()
    check('command_is_STOP_only', packets[-1][3] == 2 and packets[-1][16] == 2)
    check('actual_packet_CRC', all(scope['crc16'](p[:18]) == int.from_bytes(p[18:], 'little') for p in packets))
    sd = args.output.resolve() / 'model_sd'
    sd.mkdir()
    scope['BOOT_SD_ROOT'] = str(sd)
    frames = [dict(index=1, source='unknown', wire_valid=False, drive_allowed=False),
              dict(index=10, source='unknown', wire_valid=False, drive_allowed=False)]

    def fake_camera_main():
        for frame in frames:
            scope['_boot_record'](frame)

    scope['main'] = fake_camera_main
    with contextlib.redirect_stdout(io.StringIO()):
        first = Path(scope['_boot_check']())
    first_bytes = first.read_bytes()
    data = [json.loads(line) for line in first.read_text(encoding='utf-8').splitlines()]
    check('begin_record_has_no_drive', data[0]['event'] == 'begin' and not data[0]['drive_allowed'])
    check('frames_saved_in_order', data[1:3] == frames)
    check('completed_is_not_motor_acceptance', data[-1]['event'] == 'completed' and not data[-1]['motor_acceptance'])
    check('stream_closed_after_success', scope['_boot_stream'] is None)
    with contextlib.redirect_stdout(io.StringIO()):
        second = Path(scope['_boot_check']())
    check('repeat_boot_uses_new_file', second != first and second.name == 'check_0002.jsonl')
    check('previous_log_bytes_preserved', first.read_bytes() == first_bytes)

    def fail_camera_main():
        raise OSError('injected camera failure')

    scope['main'] = fail_camera_main
    rejected = False
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            scope['_boot_check']()
        except OSError:
            rejected = True
    failed = [json.loads(line) for line in (first.parent / 'check_0003.jsonl').read_text(encoding='utf-8').splitlines()]
    check('camera_failure_propagated_and_saved', rejected and failed[-1]['event'] == 'failed')
    check('no_completed_record_after_failure', not any(row.get('event') == 'completed' for row in failed))
    check('stream_closed_after_failure', scope['_boot_stream'] is None)
    # 空间编号用尽时不得进入相机；拒绝发生在main调用之前。
    scope['BOOT_LOG_LIMIT'] = 1
    scope['main'] = lambda: (_ for _ in ()).throw(AssertionError('must not run camera'))
    rejected = False
    try:
        scope['_boot_check']()
    except RuntimeError:
        rejected = True
    check('full_log_slots_refuse_without_overwrite', rejected and first.read_bytes() == first_bytes)
    scope['BOOT_LOG_LIMIT'] = 1000
    scope['ALLOW_DRIVE'] = True
    rejected = False
    try:
        scope['_boot_check']()
    except RuntimeError:
        rejected = True
    check('drive_enable_configuration_rejected', rejected and not (first.parent / 'check_0004.jsonl').exists())
    scope['ALLOW_DRIVE'] = False
    scope['BOOT_SD_ROOT'] = str(sd / 'missing_mount')
    rejected = False
    try:
        scope['_boot_check']()
    except OSError:
        rejected = True
    check('missing_SD_refuses_before_camera', rejected)
    result = dict(checks=checks, camera_replaced_by_model=True, board_tested=False,
                  power_verified=False, main_py_deployed=False, motor_operated=False)
    (args.output / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(len(checks), 'boot candidate checks PASS; host model only')


if __name__ == '__main__':
    main()
