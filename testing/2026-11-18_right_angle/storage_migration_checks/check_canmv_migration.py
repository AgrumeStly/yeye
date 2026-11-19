import binascii
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types

ROOT = Path('D:/projects/projectsyeye')
sys.path.insert(0, str(ROOT/'vision/tools'))
from migrate_canmv_data import BOARD_SOURCE
sys.modules['ubinascii'] = binascii

def check_case(corrupt_destination=False):
    with tempfile.TemporaryDirectory(prefix='canmv_data_check_') as folder:
        base=Path(folder)
        (base/'sdcard/captures/group').mkdir(parents=True)
        (base/'sdcard/straight_logs').mkdir()
        (base/'data').mkdir()
        (base/'sdcard/captures/group/frame.pgm').write_bytes(b'P5\n2 2\n255\n'+bytes(range(4)))
        (base/'sdcard/captures/group/meta.json').write_text('{}')
        (base/'sdcard/captures/group/script.py').write_text('program stays')
        (base/'sdcard/straight_logs/run_0001.jsonl').write_text('{"event":"original"}\n')
        (base/'sdcard/main.py').write_text('main stays')
        def translated(path):
            p=path.decode() if isinstance(path,bytes) else path
            if not (p=='/sdcard' or p.startswith('/sdcard/') or p=='/data' or p.startswith('/data/')):
                raise AssertionError(p)
            return base/p.lstrip('/')
        def ilistdir(path):
            entries=[]
            for p in translated(path).iterdir():
                entries.append((p.name.encode(),0x4000 if p.is_dir() else 0x8000,0))
            if path==b'/sdcard/captures': entries.append((b'\xae.invalid',0x4000,0))
            return iter(entries)
        deleted=[]
        def remove(path):
            assert path.startswith('/sdcard/')
            deleted.append(path)
            translated(path).unlink()
        def fake_open(path,mode='r'):
            if corrupt_destination and path.endswith('/frame.pgm') and path.startswith('/data/') and mode=='rb':
                return io.BytesIO(b'wrong contents')
            return translated(path).open(mode)
        fake_os=types.SimpleNamespace(stat=lambda p:translated(p).stat(),mkdir=lambda p:translated(p).mkdir(),
            ilistdir=ilistdir,remove=remove,exitpoint=lambda:None,sync=lambda:None,statvfs=lambda p:[512]*10)
        ns={'os':fake_os,'open':fake_open}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(BOARD_SOURCE.replace('import os, json, time','import json, time'),ns)
        archive=base/'data/migrated_20261119_sdcard/session_0001'
        assert (base/'sdcard/main.py').read_text()=='main stays'
        assert (base/'sdcard/captures/group/script.py').read_text()=='program stays'
        assert (archive/'straight_logs/run_0001.jsonl').read_text()=='{"event":"original"}\n'
        assert not (base/'sdcard/straight_logs/run_0001.jsonl').exists()
        assert (base/'sdcard/captures/group/frame.pgm').exists()==corrupt_destination
        records=[json.loads(s) for s in (archive/'migration.jsonl').read_text().splitlines()]
        assert any(r['event']=='retained_error' and 'Unicode' in r['error'] for r in records)
        verified={r['source'] for r in records if r['event']=='verified'}
        assert set(deleted)<=verified
        if corrupt_destination:
            assert '/sdcard/captures/group/frame.pgm' not in deleted
        return {'destination_mismatch':corrupt_destination,'deleted_only_after_verified':True,
                'programs_unchanged':True,'invalid_names_retained':True,'copied_bytes_match':True}

results=[check_case(False),check_case(True)]
out=ROOT/'testing/2026-11-18_right_angle/storage_migration_checks'
out.mkdir(exist_ok=True)
(out/'checks.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results))
