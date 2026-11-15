"""LowSpeedLap无复位SWD现场读取，不下载、不暂停、不恢复CPU、不发运动命令。

用于Keil退出后灯态异常，避免重新进入GUI自动复位抹去现场。只选择已确认
CMSIS-DAP，使用现有AXF符号及BIN字节核对；程序仍在运行时各字段不是原子快照。
物理连接由主控完成：目标车载供电、轮子悬空，DAP仅SWDIO/SWCLK/GND，电源
输出和NRST不接。不是其它板卡的Flash算法入口，也不自行解锁器件。
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import time

from elftools.elf.elffile import ELFFile
from pyocd.core.helpers import ConnectHelper

ROOT = Path(__file__).resolve().parents[2]
PROBE_ID = '00010001066cff554954657287234218a5a5a5a597969908'
AXF = ROOT/'control/build/firmware/low_speed_lap/low_speed_lap.axf'


def symbols():
    """从当前独立目标取得地址和大小；不依靠历史截图猜RAM地址。"""
    names = ('g_speed_revision', 'g_speed_fault', 'g_speed_ms', 'g_speed_watchdog_started',
             'g_speed_watchdog_stage', 'g_lap', 'g_lap_config', 'g_lap_last',
             'g_speed_match', 'g_lap_uart_errors', 'g_lap_uart_diag', 'g_lap_diag', 'g_lap_timing')
    with AXF.open('rb') as stream:
        table = ELFFile(stream).get_section_by_name('.symtab')
        found = {s.name: dict(address=int(s['st_value']), size=int(s['st_size'])) for s in table.iter_symbols() if s.name in names}
    if set(found) != set(names) and set(found) != set(names)-{'g_lap_diag'}:
        raise RuntimeError('required LowSpeedLap symbols absent')
    # ARMCC当前工程使用短枚举，不能按主机int大小推算state/reason偏移。
    for name, size in (('g_lap', 68), ('g_lap_config', 12), ('g_lap_last', 40), ('g_lap_uart_diag', 40), ('g_speed_match', 112)):
        if found[name]['size'] != size:
            raise RuntimeError('struct layout changed: '+name)
    if found['g_lap_timing']['size'] != 16 or ('g_lap_diag' in found and found['g_lap_diag']['size'] != 1952):
        raise RuntimeError('timing or diagnostic layout changed')
    return found


def lap_view(data):
    """按已核对ARM枚举/对齐解码；时间ms，轮速RPM，PWM千分比。"""
    result = dict(zip(('state', 'reason'), struct.unpack_from('<BB', data)))
    result.update(zip(('run_since', 'path_at', 'received', 'rejected', 'duplicates', 'starts_rejected'), struct.unpack_from('<6I', data, 4)))
    result.update(zip(('left_target', 'right_target', 'left_rpm', 'right_rpm'), struct.unpack_from('<4f', data, 28)))
    result.update(zip(('left_pwm', 'right_pwm', 'steering', 'bend', 'path_valid', 'history', 'single'), struct.unpack_from('<HHhHBBB', data, 44)))
    return result


def lap_result_view(data):
    """解码停车前锁存值：时间ms、轮速RPM、PWM千分比；不表示当前驱动。

    按当前AXF的DWARF核对40字节布局：短枚举reason在8，浮点从12开始，
    PWM在28／30，补偿样本在32／36。valid为0时不把其余字段当运行证据。
    仅观察RAM，不启动新RUN；新RUN或复位会覆盖这份结果，取证前须避免。
    """
    result = dict(zip(('valid', 'elapsed_ms'), struct.unpack_from('<2I', data)))
    result['reason'] = data[8]
    result.update(zip(('left_target', 'right_target', 'left_rpm', 'right_rpm'), struct.unpack_from('<4f', data, 12)))
    result.update(zip(('left_pwm', 'right_pwm'), struct.unpack_from('<2H', data, 28)))
    result.update(zip(('left_boost_samples', 'right_boost_samples'), struct.unpack_from('<2I', data, 32)))
    return result


def diagnostic_view(data):
    """按0B AXF核对的1952字节布局解码；环槽按真实样本顺序输出。

    frozen=1才是已停止写入的故障／LIMIT记录；未冻结的SWD读取有竞态，
    不能代替实时闭环采样。delta保留电气通道符号，raw_rpm已乘校准符号。
    """
    if len(data) != 1952:
        raise RuntimeError('diagnostic layout changed')
    result = dict(zip(('total_samples','frozen','stop_at_ms','stop_reason',
                      'left_channel','right_channel','left_sign','right_sign'),
                      struct.unpack_from('<6I2i', data)))
    names = ('at_ms','dt_ms','received','path_at','left_delta','right_delta',
             'left_counts_per_s','right_counts_per_s','left_raw_rpm','right_raw_rpm',
             'left_target','right_target','left_pwm','right_pwm','steering','bend',
             'history','single','path_valid','reserved')
    total = result['total_samples']
    result['samples'] = [dict(zip(names,struct.unpack_from('<4I4i4fHHhH4B',data,32+(i%32)*60)))
                         for i in range(max(0,total-32),total)]
    return result


def capture(target, addresses):
    """仅通过读寄存器/RAM观察当前CPU和应用；不调用halt/resume/reset。"""
    def data(name, count=None):
        item = addresses[name]
        return bytes(target.read_memory_block8(item['address'], count or item['size']))
    single = {name: struct.unpack('<I', data(name))[0] for name in addresses if addresses[name]['size'] == 4}
    dhcsr = target.read32(0xE000EDF0)
    result = dict(capture_time_utc=datetime.now(timezone.utc).isoformat(),
                  cpu_state=str(target.get_state()), dhcsr=hex(dhcsr), halted=bool(dhcsr & (1 << 17)), **single)
    result['lap'] = lap_view(data('g_lap'))
    result['last_run'] = lap_result_view(data('g_lap_last'))
    if 'g_lap_diag' in addresses:
        result['diagnostic_trace'] = diagnostic_view(data('g_lap_diag'))
    result['timing'] = dict(zip(('counter_ready','clock_hz','systick_max_cycles','motion_lock_max_cycles'),
                               struct.unpack('<4I',data('g_lap_timing'))))
    cal = data('g_speed_match', 8)
    result['calibrator'] = dict(state=cal[0], error=cal[1], phase=struct.unpack_from('<I', cal, 4)[0])
    result['config'] = dict(zip(('straight_rpm', 'run_ms', 'min_feedforward'), struct.unpack('<fIf', data('g_lap_config'))))
    result['uart'] = dict(zip(('overrun', 'noise', 'frame', 'parity', 'ring_full', 'first_mask', 'last_mask', 'first_at_ms', 'last_at_ms', 'isr_max_cycles'), struct.unpack('<10I', data('g_lap_uart_diag'))))
    result['core_faults'] = {name: hex(target.read32(address)) for name, address in (
        ('ICSR', 0xE000ED04), ('CFSR', 0xE000ED28), ('HFSR', 0xE000ED2C),
        ('DFSR', 0xE000ED30), ('DBGMCU_CR', 0xE0042004), ('DBGMCU_APB1_FZ', 0xE0042008), ('RCC_CSR', 0x40023874))}
    # 不读USART DR，避免取走真实协议字节；GPIO IDR/ODR只读，不改变KEY和灯。
    result['gpio'] = dict(KEY_PA0=target.read32(0x40020010) & 1, PB2_ODR=(target.read32(0x40020414) >> 2) & 1)
    if result['halted']:
        result['pc'] = hex(target.read_core_register('pc'))
        result['lr'] = hex(target.read_core_register('lr'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    addresses = symbols()
    args.output.mkdir(parents=True, exist_ok=False)
    result = dict(probe_id=PROBE_ID, reset_requested=False, halt_requested=False, resume_requested=False,
                  flash_written=False, source_symbols=addresses, samples=[])
    session = ConnectHelper.session_with_chosen_probe(blocking=False, unique_id=PROBE_ID,
        options={'target_override': 'cortex_m', 'connect_mode': 'attach', 'frequency': 1000000,
                 'auto_unlock': False, 'resume_on_disconnect': False})
    if session is None:
        raise RuntimeError('expected CMSIS-DAP not available; no other probe selected')
    try:
        with session:
            target = session.target
            binary = AXF.with_suffix('.bin').read_bytes()
            flash = bytes(target.read_memory_block8(0x08000000, len(binary)))
            result['flash_matches_bin'] = flash == binary
            result['bin_sha256'] = hashlib.sha256(binary).hexdigest()
            # 先比Flash再依AXF地址读RAM：避免主控尚未下载新版本时，
            # 把旧固件RAM按新符号地址解码成貌似有效的现场证据。
            if not result['flash_matches_bin']:
                raise RuntimeError('Flash differs from current AXF/BIN; no RAM decoded')
            result['samples'].append(capture(target, addresses))
            time.sleep(1)
            result['samples'].append(capture(target, addresses))
    except BaseException as exc:
        result['error'] = repr(exc)
        raise
    finally:
        (args.output/'capture.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__': main()
