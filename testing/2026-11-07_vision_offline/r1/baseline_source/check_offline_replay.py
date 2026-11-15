"""V-02有意义的边界检查：实际有效帧后失线、输入不可变、产物可追溯。

运行于电脑，不导入串口模块，不连接任何硬件。合成图只用于检查失效行为，
不作为实际赛道识别准确性的证据。检查结果以JSON保存供原对话复核。
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from offline_boundary import BoundaryDetector


def main():
    """按回放同一入口detect检查，无私有初始化捷径；断言失败返回非零。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('vision/build/offline_v02'))
    parser.add_argument('--evidence', type=Path, default=Path('testing/2026-11-07_vision_offline'))
    args = parser.parse_args()
    records = [json.loads(s) for s in (args.output/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(records) == 325
    assert [r['frame_id'] for r in records] == list(range(1,326))
    detector = BoundaryDetector()
    valid_record = next(r for r in records if r['valid'])
    real = cv2.imread(valid_record['source'], cv2.IMREAD_GRAYSCALE)
    before = real.copy()
    assert detector.detect(real)['valid']
    assert np.array_equal(real, before), 'detector mutated input pixels'
    sequence_results = []
    # 同一个检测器反复有效→全白→有效→全黑，失线后中线和偏差必须清空。
    for name, image in [('real_valid',real), ('white',np.full_like(real,255)),
                        ('real_valid_again',real), ('black',np.zeros_like(real)),
                        ('read_failure',None), ('wrong_shape',np.zeros((20,30),np.uint8))]:
        result = detector.detect(image)
        if name.startswith('real_valid'):
            assert result['valid']
        else:
            assert not result['valid']
            assert result['centerline'] == []
            assert result['deviation_px'] is None and result['deviation_normalized'] is None
        sequence_results.append(dict(case=name,valid=result['valid'],reasons=result['reasons'],
                                     centerline_count=len(result['centerline'])))
    for r in records:
        assert hashlib.sha256(Path(r['source']).read_bytes()).hexdigest() == r['source_sha256']
        assert cv2.imread(str(args.output/r['overlay'])).shape == (330,320,3)
        if not r['valid']:
            assert r['centerline'] == [] and r['deviation_px'] is None
        for side in ('left','right'):
            for p in r[side]:
                assert 0 < p['x'] < 319 and 0 <= p['y'] < 240
    # 留出片段新建实例重新处理，逐点结果应与批处理完全一致，证明无历史依赖。
    heldout = BoundaryDetector()
    for r in records[200:]:
        result = heldout.detect(cv2.imread(r['source'], cv2.IMREAD_GRAYSCALE))
        for key in result:
            assert result[key] == r[key], f"held-out mismatch: {r['frame_id']} {key}"
    before_hashes = json.loads((args.evidence/'input_sha256_before.json').read_text(encoding='utf-8'))
    source = Path(records[0]['source']).parent
    after_hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.iterdir()) if p.is_file()}
    (args.evidence/'input_sha256_after.json').write_text(json.dumps(after_hashes,indent=2)+'\n',encoding='utf-8')
    assert before_hashes == after_hashes, 'capture files changed'
    summary = dict(passed=True, sequence_checks=sequence_results, captures_unchanged=len(after_hashes),
                   frame_lineage_checked=len(records), overlays_decoded=len(records),
                   heldout_fresh_detector_matching=125, detector_input_unchanged=True,
                   synthetic_scope='failure behavior only, not real-scene recognition evidence')
    (args.evidence/'validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
