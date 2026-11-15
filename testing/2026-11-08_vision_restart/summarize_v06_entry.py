"""保存V-06静态采样检查证据；从项目根目录运行，不改原图／冻结算法，拒绝覆盖既有证据。"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys

sys.path.insert(0, 'vision/tools')
from verify_capture import verify

# 默认仍复现首组；后续组显式指定会话、证据名称和距离说明，不覆盖前序摆位事实。
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--session', default='v03_center_0007')
parser.add_argument('--name', default='v06_77deg_entry_0007')
parser.add_argument('--distance-note', default='40cm suggested placement only; no independent measurement')
parser.add_argument('--scene', default='77 degree right turn approach; center pose is operator label')
args = parser.parse_args()
source = Path('vision/data/captures/final_mount_20261108')/args.session
build = Path('vision/build/final_mount_20261108')/(args.name+'_r1')
output = Path('testing/2026-11-08_vision_restart')/args.name
if output.exists():
    raise FileExistsError('保留既有证据，不重复覆盖：' + str(output))
verification = verify(source)
frozen = json.loads(Path('testing/2026-11-08_vision_restart/static_summary/summary.json').read_text(encoding='utf-8'))
hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in frozen['frozen_code_hashes']}
assert hashes == frozen['frozen_code_hashes'], '算法／回放器／校验器与冻结版本不同'
assert hashlib.sha256((build/'parameters.json').read_bytes()).hexdigest() == frozen['parameter_sha256']
rows = [json.loads(line) for line in (build/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
result = dict(
    scene=args.scene,
    distance_note=args.distance_note,
    frozen_code_hashes=hashes, parameter_sha256=frozen['parameter_sha256'],
    source_manifest=[dict(path=p.as_posix(), bytes=p.stat().st_size,
                          sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                     for p in sorted(source.iterdir()) if p.is_file()],
    frames=[dict(frame_id=r['frame_id'], valid=r['valid'], quality=r['quality'],
                 deviation_px=r['deviation_px'], support_rows=[p['y'] for p in r['left']]) for r in rows],
    scope='3 static repeats of one pose; valid near-field pair does not establish turn path or drive acceptance')
output.mkdir()
for name in ['frames.jsonl', 'frames.csv', 'summary.json', 'parameters.json']:
    shutil.copyfile(build/name, output/name)
shutil.copytree(build/'overlays', output/'overlays')
for name, value in [('verification.json', verification), ('evidence.json', result)]:
    (output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(verification=verification, frames=result['frames'], evidence=str(output)), ensure_ascii=False))
