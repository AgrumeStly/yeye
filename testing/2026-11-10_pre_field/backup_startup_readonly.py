"""只读备份K230已存在的启动文件与已知采集许可，不运行／改写板上脚本。

独占COM10；若板上非空闲立即退出，不自动停止其它脚本。
输出写入本轮新的startup_backup目录，拒绝覆盖历史备份。
"""
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'vision/tools'))
from canmv_lap_bench import Session


def main():
    """按后端原始字节读取已知文件，保存哈希；最大128KiB，超限停止。"""
    output = Path(__file__).resolve().parent / 'startup_backup'
    output.mkdir(exist_ok=False)
    session = Session(output)
    try:
        board = session.request('connectBoard', {'port': 'COM10', 'baudRate': 12000000}, timeout=25)
        status = session.request('scriptRunning')
        if status.get('running') is not False:
            raise RuntimeError('board not confirmed idle; no script stopped')
        records = {}
        for name in ('main.py', 'boot.py', 'full_lap_capture.arm', 'push_capture.arm'):
            remote = '/sdcard/' + name
            info = session.request('io.queryFileStat', {'path': remote})
            records[remote] = dict(stat=info)
            if not info.get('exists'):
                continue
            if info.get('type') == 'directory' or not isinstance(info.get('size'), int) or not 0 <= info['size'] <= 131072:
                raise RuntimeError('unexpected startup file type/size: ' + remote)
            data = bytearray()
            while len(data) < info['size']:
                count = min(32768, info['size'] - len(data))
                reply = session.request('io.readFile', {'path': remote, 'offset': len(data), 'size': count}, timeout=30)
                chunk = base64.b64decode(reply['dataBase64']) if isinstance(reply.get('dataBase64'), str) else bytes(reply.get('data', []))
                if not 0 < len(chunk) <= count:
                    raise RuntimeError('incomplete startup read: ' + remote)
                data.extend(chunk)
            (output / name).write_bytes(data)
            records[remote].update(local=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        result = dict(board=board, initial_status=status, files=records,
                      remote_files_written=False, script_run_requested=False, motor_started=False)
        (output / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print('Startup read-only backup complete:', {name: row.get('bytes') for name, row in records.items()})
    finally:
        session.close()


if __name__ == '__main__':
    main()
