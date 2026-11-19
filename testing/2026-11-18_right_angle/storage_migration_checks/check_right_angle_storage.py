import hashlib
import json
import io
from pathlib import Path
import sys
import tempfile
import types

ROOT=Path('D:/projects/projectsyeye')
sys.path.insert(0,str(ROOT/'vision/tools'))
from prepare_right_angle_bundle import build

checks={}
source,manifest=build(False)
ns={'__name__':'storage_check'}
exec(source,ns)
stream=io.StringIO()
ns['_write_log'](stream,'{}\n')
assert stream.getvalue()=='{}\n'
try:
    ns['_write_log'](types.SimpleNamespace(write=lambda text:0),'{}\n')
except OSError:
    checks['short_log_write_rejected']=True
else:
    raise AssertionError('short log write accepted')
with tempfile.TemporaryDirectory(prefix='right_angle_storage_') as folder:
    base=Path(folder)
    (base/'data').mkdir()
    def translate(path):
        assert path.startswith('/data/')
        return base/path.lstrip('/')
    ns['os']=types.SimpleNamespace(stat=lambda p:translate(p).stat(),mkdir=lambda p:translate(p).mkdir())
    ns['open']=lambda p,m:translate(p).open(m)
    name,stream=ns['_open_log']()
    stream.write('preserved');stream.close()
    second,stream=ns['_open_log']()
    stream.write('new');stream.close()
    assert name=='/data/right_angle_logs/run_0001.jsonl'
    assert second=='/data/right_angle_logs/run_0002.jsonl'
    assert translate(name).read_text()=='preserved'
    checks['data_partition_and_increment_without_overwrite']=True
    def failing_stat(path):raise OSError(5,'storage IO error')
    ns['os'].stat=failing_stat
    try:ns['_open_log']()
    except OSError as exc:assert exc.errno==5
    else:raise AssertionError('storage errors must propagate')
    checks['storage_error_not_hidden']=True
baseline=ROOT/'testing/2026-11-18_right_angle/midturn_r6/source_final/vision/src'
for name in ('right_angle_grid.py','right_angle_route.py','right_angle_racing.py','right_angle_protocol.py'):
    assert (baseline/name).read_bytes()==(ROOT/'vision/src'/name).read_bytes()
    checks[name+'_unchanged']=True
for drive,filename in ((False,'right_angle_preview.py'),(True,'right_angle_drive.py')):
    generated,meta=build(drive)
    released=(ROOT/'testing/2026-11-18_right_angle/release_r7_storage'/filename).read_bytes()
    assert generated.encode()==released
    assert hashlib.sha256(released).hexdigest()==meta['bundle_sha256']
    checks[filename+'_matches_generator']=True
assert not ns['RightAngleSender'](allow_drive=False).path(dict(valid=True,source='current_pair',steering=0,bend=0,confidence=100),30,40)[6]&1
checks['preview_never_grants_drive']=True
out=ROOT/'testing/2026-11-18_right_angle/storage_migration_checks'
out.mkdir(exist_ok=True)
(out/'right_angle_storage_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks))
