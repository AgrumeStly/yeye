"""将CanMV程序分区内的照片／日志迁至/data，校验后逐文件清理原副本。

主控2026-11-19明确要求数据放/data、程序放/sdcard。只处理列明的数据
目录及数据扩展名，不格式化、不删除程序、不递归删除目录或异常条目。
官方后端串行占用COM10；不初始化相机／UART，不发START，不复位STM32。
"""
import argparse
import json
from pathlib import Path
import queue
import time

from canmv_lap_bench import Session


BOARD_SOURCE = r'''
import os, json, time
try:
    import hashlib
except ImportError:
    import uhashlib as hashlib
import ubinascii

SOURCES = ('captures', 'lap_boot_checks', 'lap_runtime_logs', 'straight_logs', 'right_angle_logs')
DATA_SUFFIXES = ('.json', '.jsonl', '.pgm', '.ppm', '.png', '.jpg', '.jpeg', '.bmp', '.txt', '.csv')

def digest(path):
    # 分块读取，单文件上限64MiB；不将整个图片组装进128MiB设备内存。
    value = hashlib.sha256()
    count = 0
    with open(path, 'rb') as stream:
        while True:
            os.exitpoint()
            block = stream.read(32768)
            if not block:
                break
            count += len(block)
            if count > 64*1024*1024:
                raise ValueError('file exceeds migration bound')
            value.update(block)
    return count, ubinascii.hexlify(value.digest()).decode()

def make_directory(path):
    try:
        info = os.stat(path)
    except OSError as exc:
        if not exc.args or exc.args[0] != 2:
            raise
        os.mkdir(path)
        return
    if not info[0] & 0x4000:
        raise ValueError('destination is not a directory')

def main():
    # 独立英文归档目录，不覆盖/data已有照片、模型或之前迁移。
    base = '/data/migrated_20261119_sdcard'
    make_directory(base)
    destination = None
    for index in range(1, 1000):
        candidate = base+'/session_%04d' % index
        try:
            os.stat(candidate)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
            os.mkdir(candidate)
            destination = candidate
            break
    if destination is None:
        raise ValueError('archive slots exhausted')
    totals = dict(copied=0, removed=0, bytes=0, errors=0, skipped=0)
    manifest = open(destination+'/migration.jsonl', 'w')
    def emit(event):
        manifest.write(json.dumps(event)+'\n')
        manifest.flush()
        print('DATA_MIGRATION', json.dumps(event))
    def walk(source, target, depth=0):
        if depth > 8:
            raise ValueError('directory depth bound')
        make_directory(target)
        entries = list(os.ilistdir(source.encode()))
        for entry in entries:
            os.exitpoint()
            original = None
            try:
                # 字节形式枚举允许记录损坏文件名；不猜测编码或删除未知路径。
                name = entry[0].decode('utf-8')
                if name in ('.', '..') or '/' in name or '\\' in name or '\x00' in name:
                    raise ValueError('unsafe entry name')
                original = source+'/'+name
                copied = target+'/'+name
                if entry[1] == 0x4000:
                    walk(original, copied, depth+1)
                    continue
                # CanMV的MicroPython str.endswith不支持CPython的元组参数。
                if entry[1] != 0x8000 or not any(name.lower().endswith(suffix) for suffix in DATA_SUFFIXES):
                    totals['skipped'] += 1
                    emit(dict(event='retained', path=original))
                    continue
                expected = os.stat(original)[6]
                if not 0 <= expected <= 64*1024*1024:
                    raise ValueError('file size bound')
                # 目标归档独占且文件必须不存在；从不覆盖原图或程序。
                try:
                    os.stat(copied)
                except OSError as exc:
                    if not exc.args or exc.args[0] != 2:
                        raise
                else:
                    raise ValueError('destination exists')
                value = hashlib.sha256()
                count = 0
                with open(original, 'rb') as incoming:
                    with open(copied, 'wb') as outgoing:
                        while True:
                            os.exitpoint()
                            block = incoming.read(32768)
                            if not block:
                                break
                            count += len(block)
                            if count > expected:
                                raise ValueError('source size changed')
                            written = outgoing.write(block)
                            if written != len(block):
                                raise OSError('short destination write')
                            value.update(block)
                        outgoing.flush()
                original_hash = ubinascii.hexlify(value.digest()).decode()
                if count != expected or digest(copied) != (count, original_hash):
                    raise ValueError('destination verification failed; source retained')
                if hasattr(os, 'sync'):
                    os.sync()
                totals['copied'] += 1
                totals['bytes'] += count
                emit(dict(event='verified', source=original, destination=copied,
                          bytes=count, sha256=original_hash))
                # 仅对已完整读回且哈希一致的文件执行删除，不删除目录。
                os.remove(original)
                totals['removed'] += 1
                emit(dict(event='removed_verified_source', path=original))
            except Exception as exc:
                totals['errors'] += 1
                emit(dict(event='retained_error', source=source, entry=repr(entry),
                          path=original, error=repr(exc)))
    try:
        emit(dict(event='begin', destination=destination,
                  sdcard_vfs=os.statvfs('/sdcard'), data_vfs=os.statvfs('/data')))
        for folder in SOURCES:
            try:
                walk('/sdcard/'+folder, destination+'/'+folder)
            except Exception as exc:
                totals['errors'] += 1
                emit(dict(event='retained_directory_error', path='/sdcard/'+folder, error=repr(exc)))
        if hasattr(os, 'sync'):
            os.sync()
        emit(dict(event='finished', totals=totals,
                  sdcard_vfs=os.statvfs('/sdcard'), data_vfs=os.statvfs('/data')))
        print('DATA_MIGRATION_DONE')
    finally:
        manifest.close()

main()
'''


def main():
    """只在相机空闲时执行固定迁移脚本，保存全部原始终端及准确执行源。

    主机等待时不向运行中的迁移脚本发送文件查询；断连或超时保存失败，
    不能伪称迁移完成。每个成功删除项均可在/data和主机双份清单追溯。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', default='COM10')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'executed_source.py').write_bytes(BOARD_SOURCE.encode('utf-8'))
    compile(BOARD_SOURCE, 'migration_board_source', 'exec')
    session = Session(args.output)
    result = dict(no_uart=True, no_camera=True, no_start=True, no_format=True,
                  stm32_reset=False, program_files_retained=True, completed=False)
    owned = False
    try:
        result['board'] = session.request('connectBoard', {'port': args.port, 'baudRate': 12000000}, timeout=25)
        result['initial_status'] = session.request('scriptRunning')
        if result['initial_status'].get('running') is not False:
            raise RuntimeError('existing script active; left untouched')
        session.running = True
        owned = True
        session.request('runScript', {'script': BOARD_SOURCE}, timeout=35)
        deadline = time.monotonic()+1800
        while session.running is not False and time.monotonic() < deadline:
            try:
                message = session.messages.get(timeout=.25)
                session.record(message)
                if 'reader_error' in message:
                    raise RuntimeError(message['reader_error'])
            except queue.Empty:
                pass
        result['completed'] = session.running is False and 'DATA_MIGRATION_DONE' in session.tail and not session.script_error
        if not result['completed']:
            raise RuntimeError('migration incomplete; inspect preserved manifest and terminal')
    except BaseException as exc:
        result['error'] = repr(exc)
        if owned and session.running is not False:
            try:
                session.request('stopScript', timeout=15)
            except BaseException:
                pass
        raise
    finally:
        session.close()
        (args.output/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
