"""归档I-02出发前已验证候选；只读源码／日志，不访问板卡或远端。

从工作区复制BIN、HEX、K230工作包与本轮检查证据并计算原始字节SHA256。
输出必须是工作区testing内的新子目录，拒绝覆盖；检查失败不产出通过清单。
使用方式：vision/.venv/Scripts/python.exe hardware_preparation/source/prepare_pre_field_evidence.py
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'testing/2026-11-10_pre_field'


def digest(path):
    """按文件原始字节计算哈希，避免CRLF归一化造成副本误报。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    """核对已执行检查和历史固件哈希，再保存本地候选及物理待验标记。"""
    checks = {}
    for folder, count in (('motor_fixture_checks', 19), ('helper_checks', 18), ('vision_protocol_checks', 42)):
        data = json.loads((OUTPUT / folder / 'checks.json').read_text(encoding='utf-8'))
        entries = data['checks']
        if len(entries) != count or not all(item['passed'] for item in entries):
            raise RuntimeError('检查未通过：' + folder)
        checks[folder] = count
    model = ROOT / 'control/build/low_speed_lap_tests.log'
    uart = ROOT / 'control/build/low_speed_lap_uart_tests.log'
    # PowerShell Tee-Object可能输出UTF-16；仅识别本机已有两种编码，不忽略乱码。
    def log_text(path):
        raw = path.read_bytes()
        return raw.decode('utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig')
    if '316 scenario assertions PASS' not in log_text(model):
        raise RuntimeError('缺少本轮控制检查通过日志')
    if 'UART production driver checks PASS' not in log_text(uart):
        raise RuntimeError('缺少UART检查通过日志')
    expected = json.loads((ROOT / 'testing/2026-11-09_low_speed_lap/low_speed_feedforward_build_01.json').read_text(encoding='utf-8'))
    files = {}
    for target, base in (('LowSpeedLap', 'low_speed_lap'), ('LowSpeedLapTrack', 'low_speed_lap_track')):
        bin_path = ROOT / 'control/build/firmware' / base / (base + '.bin')
        if digest(bin_path) != expected[target]['bin_sha256']:
            raise RuntimeError('固件与09/0A实物候选基线不一致：' + target)
        log = ROOT / 'control/build/firmware' / (target + '_build.log')
        if '0 Error(s), 0 Warning(s).' not in log_text(log):
            raise RuntimeError('ARM构建未通过：' + target)
        for suffix in ('.bin', '.hex'):
            files['firmware/' + base + suffix] = bin_path.with_suffix(suffix)
        files['software_logs/' + target + '_build.log'] = log
    files['software_logs/control_model.log'] = model
    files['software_logs/uart_driver.log'] = uart
    for folder, name in (('board_bundle_runtime_r5', 'low_speed_lap_canmv.py'),
                         ('motor_bench_bundle_r2', 'lap_motor_bench_canmv.py')):
        source = ROOT / 'testing/2026-11-09_low_speed_lap' / folder
        manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
        if digest(source / name) != manifest['bundle_sha256']:
            raise RuntimeError('K230工作包已偏离已验字节：' + folder)
        files['k230/' + folder + '/' + name] = source / name
        files['k230/' + folder + '/manifest.json'] = source / 'manifest.json'
    # 先检查全部输出没有同名文件；不覆盖历史证据，也不切换工程／烧录。
    for name, source in files.items():
        if not source.is_file() or (OUTPUT / name).exists():
            raise RuntimeError('来源缺失或输出已存在：' + name)
    manifest_path = OUTPUT / 'artifact_manifest.json'
    if manifest_path.exists():
        raise RuntimeError('清单已存在，拒绝覆盖')
    records = {}
    for name, source in files.items():
        destination = OUTPUT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        sha = digest(source)
        if digest(destination) != sha:
            raise RuntimeError('复制字节不一致：' + name)
        records[name] = dict(source=source.relative_to(ROOT).as_posix(), sha256=sha, bytes=destination.stat().st_size)
    sources = {}
    for parent in ('control/Core', 'control/App', 'control/Algorithms', 'control/Drivers_Custom', 'control/Tests/Host'):
        for source in (ROOT / parent).rglob('*'):
            if source.is_file() and source.suffix in ('.c', '.h', '.s'):
                sources[source.relative_to(ROOT).as_posix()] = digest(source)
    for name in ('control/MDK-ARM/low_speed_lap.uvprojx', 'vision/tools/canmv_lap_bench.py',
                 'vision/src/lap_uart_probe_canmv.py', 'competition/比赛文档.pdf',
                 'hardware_preparation/pre_field_checklist.md'):
        sources[name] = digest(ROOT / name)
    status = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True, encoding='utf-8')
    # 只枚举，不打开串口；缺少K230不等同板卡故障。
    from serial.tools.list_ports import comports
    ports = [dict(device=p.device, vid=p.vid, pid=p.pid, serial_number=p.serial_number) for p in comports()]
    manifest = dict(created=datetime.now().astimezone().isoformat(),
                    head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
                    workspace_dirty=bool(status), workspace_status=status, artifacts=records, source_hashes=sources,
                    checks=checks, control_assertions=316, uart_host_checks_passed=True, enumerated_ports=ports,
                    hardware_flashed_this_run=False, motor_started_this_run=False, new_battery_motor_verified=False,
                    disconnect_stop_verified=False, autonomous_lap_verified=False,
                    purpose='Local reproducible candidate copies; not hardware or race acceptance')
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Archived', len(records), 'verified artifacts; no device operation')


if __name__ == '__main__':
    main()
