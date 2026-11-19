"""本轮R8固定发布部署：不运行程序，不改启动入口，不复位STM32。"""
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('D:/projects/projectsyeye')
sys.path.insert(0, str(ROOT/'vision/tools'))
from canmv_lap_bench import Session

out = ROOT/'testing/2026-11-18_right_angle/r8_program_deploy_01'
source = (ROOT/'testing/2026-11-18_right_angle/release_r8_entry/right_angle_drive.py').read_bytes()
digest = hashlib.sha256(source).hexdigest()
if digest != '23c812b040d4b71faa986616ae2cfb3cf1fca3c7090ef99b27b36ddc75d8f96b':
    raise RuntimeError('reviewed R8 changed')
out.mkdir(exist_ok=False)
session = Session(out)
result = dict(main_py_written=False, script_executed=False, stm32_reset=False,
              automatic_motor_start=False, completed=False)

def read(remote):
    """按实际文件长度分块读原字节，拒绝短读及异常文件元数据。"""
    metadata = session.request('io.queryFileStat', {'path': remote})
    if not metadata.get('exists'):
        return None
    size = metadata['size']
    if metadata.get('type') != 'file' or type(size) is not int or not 0 <= size <= 512*1024:
        raise ValueError('unexpected file metadata')
    data = bytearray()
    while len(data) < size:
        count = min(32768, size-len(data))
        reply = session.request('io.readFile', {'path': remote, 'offset': len(data), 'size': count})
        part = base64.b64decode(reply['dataBase64'], validate=True)
        if len(part) != count:
            raise RuntimeError('short read')
        data.extend(part)
    return bytes(data)

try:
    result['board'] = session.request('connectBoard', {'port': 'COM10', 'baudRate': 12000000}, timeout=25)
    result['initial_status'] = session.request('scriptRunning')
    if result['initial_status'].get('running') is not False:
        raise RuntimeError('existing camera active; retained')
    result['data_directory'] = session.request('io.queryFileStat', {'path': '/data/right_angle_logs'})
    if not result['data_directory'].get('exists'):
        raise RuntimeError('data log directory absent')
    before = read('/sdcard/main.py')
    if before is not None:
        (out/'before_main.py').write_bytes(before)
    remote = '/sdcard/right_angle_drive_r8.py'
    existing = read(remote)
    if existing is not None and existing != source:
        (out/'unexpected_existing_r8.py').write_bytes(existing)
        raise RuntimeError('existing different R8 retained')
    if existing is None:
        reply = session.request('io.writeFile', {'path': remote, 'dataBase64': base64.b64encode(source).decode('ascii')}, timeout=30)
        if reply.get('success') is not True:
            raise RuntimeError('write rejected')
    after = read(remote)
    if after is not None:
        (out/'readback_right_angle_drive_r8.py').write_bytes(after)
    if after != source:
        raise RuntimeError('program readback mismatch')
    if read('/sdcard/main.py') != before:
        raise RuntimeError('main changed unexpectedly')
    result.update(completed=True, program_path=remote, program_bytes=len(source),
                  program_sha256=digest, main_unchanged=True,
                  main_sha256=hashlib.sha256(before).hexdigest() if before else None)
except BaseException as exc:
    result['error'] = repr(exc)
    raise
finally:
    session.close()
    (out/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
