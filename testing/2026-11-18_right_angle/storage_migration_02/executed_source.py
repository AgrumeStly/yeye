
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
