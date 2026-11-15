"""汇总V-06首轮静态证据；只读原件并核对冻结版本，拒绝覆盖既有汇总。"""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, 'vision/tools')
from verify_capture import verify

root = Path('testing/2026-11-08_vision_restart')
target = root/'v06_round1_summary.json'
if target.exists():
    raise FileExistsError('保留首轮汇总，不重复覆盖：' + str(target))
frozen = json.loads((root/'static_summary/summary.json').read_text(encoding='utf-8'))
hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in frozen['frozen_code_hashes']}
assert hashes == frozen['frozen_code_hashes'], '冻结算法／回放器／校验器发生变化'
names = ['v06_77deg_entry_0007', 'v06_77deg_entry_0008', 'v06_77deg_mid_0009',
         'v06_77deg_exit_heading_0010', 'v06_77deg_exit_forward_0011', 'v06_no_boundary_text_0012']
groups = []
for name in names:
    folder = root/name
    evidence = json.loads((folder/'evidence.json').read_text(encoding='utf-8'))
    assert evidence['frozen_code_hashes'] == hashes
    assert evidence['parameter_sha256'] == frozen['parameter_sha256']
    assert hashlib.sha256((folder/'parameters.json').read_bytes()).hexdigest() == frozen['parameter_sha256']
    for source in evidence['source_manifest']:
        path = Path(source['path'])
        assert path.stat().st_size == source['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256']
    source_dir = Path(evidence['source_manifest'][0]['path']).parent
    checked = verify(source_dir)
    rows = [json.loads(line) for line in (folder/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    for row in rows:
        assert row['source_sha256'] == hashlib.sha256(Path(row['source']).read_bytes()).hexdigest()
        if not row['valid']:
            assert row['centerline'] == [] and row['deviation_px'] is None and row['deviation_normalized'] is None
    groups.append(dict(name=name, scene=evidence['scene'], verification=checked,
                       valid=sum(r['valid'] for r in rows), frames=len(rows),
                       deviations_px=[r['deviation_px'] for r in rows],
                       reasons=[r['reasons'] for r in rows]))
result = dict(groups=groups, frame_count=sum(g['frames'] for g in groups), source_file_count=30,
              frozen_code_hashes=hashes, parameter_sha256=frozen['parameter_sha256'],
              scope='6 static placements with 3 repeats each; not accuracy, continuous motion, turn-path or vehicle acceptance')
target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(frame_count=result['frame_count'], groups=[dict(name=g['name'], valid=g['valid']) for g in groups]), ensure_ascii=False))
