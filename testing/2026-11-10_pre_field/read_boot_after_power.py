"""主控物理断电重接后只读下载新启动日志；不触发运行、复位或写文件。

连接／断开由官方CanMV后端执行，原始输出保留；若已有脚本运行则不停止。
旧check_0001为RAM基线，必须单独校验，不能当本次上电证据。
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(FOLDER))
from deploy_boot_check import EXPECTED, read_remote
from canmv_lap_bench import Session


def main():
    """只读目录／主入口／日志；输出到新证据目录，保留失败和不完整组。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-name', default='cold_boot_power_01')
    parser.add_argument('--after-log', default='check_0001.jsonl')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_]+', args.output_name) or not re.fullmatch(r'check_\d{4}\.jsonl', args.after_log):
        raise ValueError('output must be a simple evidence folder name; baseline must be a numbered log')
    output = FOLDER / args.output_name
    output.mkdir(exist_ok=False)
    session = Session(output)
    try:
        board = session.request('connectBoard', {'port': 'COM10', 'baudRate': 12000000}, timeout=25)
        status = session.request('scriptRunning')
        (output / 'board.json').write_text(json.dumps(dict(board=board, status=status), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        if status.get('running') is not False:
            raise RuntimeError('board busy; own script will not be run and existing script will not be stopped')
        startup = read_remote(session, '/sdcard/main.py')
        if hashlib.sha256(startup).hexdigest() != EXPECTED:
            raise RuntimeError('installed main.py differs from authorized bytes')
        listing = session.request('io.listDir', {'path': '/sdcard/lap_boot_checks', 'offset': 0})
        (output / 'listing.json').write_text(json.dumps(listing, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        entries = listing.get('entries')
        if not isinstance(entries, list):
            raise RuntimeError('unexpected directory listing shape')
        names = sorted(item['name'] for item in entries if isinstance(item.get('name'), str) and re.fullmatch(r'check_\d{4}\.jsonl', item['name']))
        old = read_remote(session, '/sdcard/lap_boot_checks/check_0001.jsonl')
        ram = json.loads((FOLDER / 'cold_boot_ram_01/result.json').read_text(encoding='utf-8'))
        if hashlib.sha256(old).hexdigest() != ram['log_sha256']:
            raise RuntimeError('original RAM log changed')
        new_names = [name for name in names if name > args.after_log]
        if not new_names:
            raise RuntimeError('no new startup log: physical boot not verified')
        results = []
        # 最早的新编号用于本次首次上电；若另有较新组，一并保留以发现重复启动。
        selected = sorted({new_names[0], new_names[-1]})
        for name in selected:
            raw = read_remote(session, '/sdcard/lap_boot_checks/' + name)
            (output / name).write_bytes(raw)
            rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
            frames = [row for row in rows if 'index' in row]
            complete = bool(rows and rows[0].get('event') == 'begin' and rows[-1].get('event') == 'completed')
            no_drive = bool(frames and all(row.get('wire_valid') is False and row.get('drive_allowed') is False for row in frames))
            results.append(dict(file=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                                frames=len(frames), complete=complete, no_drive=no_drive,
                                processing_ms_min=min((row['processing_ms'] for row in frames), default=None),
                                processing_ms_max=max((row['processing_ms'] for row in frames), default=None),
                                interval_ms_max=max((row['interval_ms'] for row in frames if row['interval_ms'] is not None), default=None),
                                to_send_ms_max=max((row['to_send_ms'] for row in frames), default=None)))
        summary = dict(user_reported_physical_power_cycle=True, power_source='existing computer USB Type-C',
                       initial_status=status, installed_main_sha256=EXPECTED, original_RAM_log_unchanged=True,
                       log_names=names, baseline_log=args.after_log, new_log_count=len(new_names), downloaded=results,
                       attachment_output_has_boot_log_marker='[BOOT CHECK LOG]' in session.tail,
                       startup_check_passed=all(row['complete'] and row['no_drive'] for row in results),
                       script_run_requested=False, remote_write_requested=False, motor_started=False,
                       stm32_receive_checked_this_run=False, battery_power_verified=False, autonomous_lap_verified=False)
        (output / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not summary['startup_check_passed']:
            raise RuntimeError('new startup log incomplete or drive prohibition failed; original preserved')
    finally:
        session.close()


if __name__ == '__main__':
    main()
