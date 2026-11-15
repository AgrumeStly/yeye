"""从冻结R5准备真实相机联动文本；仅写电脑，不连接设备或替换main.py。

no_drive默认不许可有效PATH。isolated须明确动力物理隔离；suspended须核对
完全悬空、09固件3000ms及当前校准。两个许可模式仍只读实时相机，不发START。
此处的确认参数记录人工事实，不会通过软件验证接线、版本或物理悬空。
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R5 = ROOT / 'testing/2026-11-09_low_speed_lap/board_bundle_runtime_r5/low_speed_lap_canmv.py'
R5_SHA256 = '54e71bcc4346710300c0302a77f6bba86609baca5c937772d4282fc874175f4d'
MODES = ('no_drive', 'isolated', 'suspended')
BUNDLES = {
    'r5': (R5, R5_SHA256),
    'r6': (ROOT / 'testing/2026-11-11_field_live/board_bundle_runtime_r6/low_speed_lap_canmv.py',
           'de2341cafcdadf2d843a566dafeef28ae4439c041aec15f7ee709e7afd738fcf'),
}


def prepare(mode='no_drive', *, power_isolated=False, suspended=False,
            mcu_revision=None, mcu_run_ms=None, calibrated=False, window_ms=120000, bundle='r5'):
    """返回精确执行源码和审查信息；不访问板卡。

    window_ms只是相机输入等待窗口，不是电机运行时长。悬空模式固定要求
    人工实读09／3000ms／校准正常；复位后必须重新确认，不沿用旧phase。
    默认模式保持R5的10秒禁止驱动诊断和原图预览，许可模式禁用IDE图传。
    仅替换配置，不改变检测器、协议门槛、初始化／清理STOP或故障监督。
    """
    if mode not in MODES or window_ms not in (120000, 600000) or bundle not in BUNDLES:
        raise ValueError('unknown visual mode or bounded input window')
    if mode == 'isolated' and not power_isolated:
        raise ValueError('physical XT30 isolation and driver OFF must be confirmed')
    if mode == 'suspended' and not (suspended and mcu_revision == 0x02110009
                                    and mcu_run_ms == 3000 and calibrated):
        raise ValueError('actual suspension, revision09, 3000ms and current calibration required')
    base_path, expected_hash = BUNDLES[bundle]
    raw = base_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError('checked visual bundle changed; review and checks required')
    source = raw.decode('utf-8').replace('\r\n', '\n')
    def change(old, new):
        nonlocal source
        if source.count(old) != 1:
            raise ValueError('unexpected R5 configuration: ' + old)
        source = source.replace(old, new)
    change("MODE='idle'", "MODE='live'")
    change('UART_ENABLED=False', 'UART_ENABLED=True')
    duration = 10000 if mode == 'no_drive' else window_ms
    change('DURATION_MS=300000', 'DURATION_MS=' + str(duration))
    if mode != 'no_drive':
        change('ALLOW_DRIVE=False', 'ALLOW_DRIVE=True')
        change('SHOW_PREVIEW=True', 'SHOW_PREVIEW=False')
    # 保留实时snapshot路径和全部发送保护。此标识明确区分fixture与相机来源。
    source = '# REAL CAMERA; operator KEY only; no START; bounded visual link\n' + source
    compile(source, '<prepared_real_camera>', 'exec')
    info = dict(mode=mode, input_kind='real_camera', input_window_ms=duration,
                source_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
                base_bundle=bundle, base_bundle_sha256=expected_hash,
                frozen_r5_sha256=R5_SHA256, confirmed_power_isolated=power_isolated,
                confirmed_suspended=suspended, confirmed_mcu_revision=mcu_revision,
                confirmed_mcu_run_ms=mcu_run_ms, confirmed_calibrated=calibrated,
                automatic_motor_start_permitted=False, main_py_written=False,
                board_used=False, physical_result='pending')
    return source, info


def main():
    """离线生成候选；缺少许可前提即拒绝，不把生成成功算板级验收。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=MODES, nargs='?', default='no_drive')
    parser.add_argument('--output', required=True)
    parser.add_argument('--bundle', choices=tuple(BUNDLES), default='r5')
    parser.add_argument('--confirmed-power-isolated', action='store_true')
    parser.add_argument('--confirmed-suspended', action='store_true')
    parser.add_argument('--confirmed-mcu-revision', type=lambda text: int(text, 0))
    parser.add_argument('--confirmed-mcu-run-ms', type=int)
    parser.add_argument('--confirmed-calibrated', action='store_true')
    parser.add_argument('--window-ms', type=int, choices=(120000, 600000), default=120000)
    args = parser.parse_args()
    source, info = prepare(args.mode, power_isolated=args.confirmed_power_isolated,
                           suspended=args.confirmed_suspended, mcu_revision=args.confirmed_mcu_revision,
                           mcu_run_ms=args.confirmed_mcu_run_ms, calibrated=args.confirmed_calibrated,
                           window_ms=args.window_ms, bundle=args.bundle)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'executed_source.py').write_bytes(source.encode('utf-8'))
    (output / 'intent.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False))


if __name__ == '__main__':
    main()
