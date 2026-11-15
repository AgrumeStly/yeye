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
from offline_boundary import BoundaryConfig, BoundaryDetector


def main():
    """按回放同一入口detect检查，无私有初始化捷径；断言失败返回非零。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('vision/build/offline_v02_r1'))
    parser.add_argument('--evidence', type=Path, default=Path('testing/2026-11-07_vision_offline/r1'))
    args = parser.parse_args()
    records = [json.loads(s) for s in (args.output/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(records) == 325
    assert [r['frame_id'] for r in records] == list(range(1,326))
    config = BoundaryConfig(**json.loads((args.output/'parameters.json').read_text(encoding='utf-8')))
    detector = BoundaryDetector(config)
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
        for ribbon in r.get('visible_ribbons',[]):
            assert ribbon['side'] == 'unassigned' and ribbon['road_side_ambiguous']
            for edge in ('upper','lower'):
                for p in ribbon[edge]:
                    assert 0 < p['x'] < 319 and 0 <= p['y'] < 240 and p['state'] == 'visible'
    # R1的201–325已公开，只是旧数据回归。新建实例复算验证无历史依赖，
    # 不能把结果写成新盲测；首版证据保持原文件不变。
    regression = BoundaryDetector(config)
    for r in records[200:]:
        result = regression.detect(cv2.imread(r['source'], cv2.IMREAD_GRAYSCALE))
        for key in result:
            assert result[key] == r[key], f"regression mismatch: {r['frame_id']} {key}"
    geometry_checks = []
    # 真实审核拒绝案例及相邻帧仍不得被新局部阈值提升成有效中线。
    for center in [81,191,251]:
        for n in range(center-1,center+2):
            r = records[n-1]
            assert not r['valid'] and r['centerline'] == []
            geometry_checks.append(dict(case=f'real_ambiguity_{n}',valid=False,reasons=r['reasons']))
    for n in [1,31,71,131,201,241]:
        assert records[n-1]['valid'], f'baseline success regressed: {n}'
    for n in [41,171,211,301]:
        assert not records[n-1]['valid'] and records[n-1]['reference_y'] == 120
    for n in [60,61,62,110,111,112]:
        assert records[n-1]['visible_ribbons'], f'near-horizontal ribbon missing: {n}'
        assert not records[n-1]['valid']
    # 真实近水平边界不能靠无条件放大横扫黑段上限恢复。用无对边条带检查
    # 补充轮廓只作可见候选，墙体触ROI顶部则不能进入该补充轮廓集合。
    stripe = np.full_like(real,180)
    stripe[150:172] = 40
    wall = np.full_like(real,180)
    wall[:105] = 40
    parallel = np.full_like(real,180)
    for y in range(config.roi_top,config.roi_bottom+1):
        x = 45+round((y-config.roi_top)*0.2)
        parallel[y,x:x+12] = 40
        parallel[y,x+110:x+122] = 40
    for name,image in [('horizontal_single_stripe',stripe),('top_wall',wall),('parallel_false_pair',parallel)]:
        r = detector.detect(image)
        assert not r['valid'] and not r['centerline'] and r['deviation_px'] is None
        if name == 'horizontal_single_stripe':
            assert r['visible_ribbons']
        if name == 'top_wall':
            assert not r['visible_ribbons']
        if name == 'parallel_false_pair':
            assert 'pair_not_widening_toward_camera' in r['reasons']
        geometry_checks.append(dict(case=name,valid=r['valid'],reasons=r['reasons'],
                                    ribbon_count=len(r['visible_ribbons'])))
    before_hashes = json.loads((args.evidence/'input_sha256_before.json').read_text(encoding='utf-8'))
    source = Path(records[0]['source']).parent
    after_hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.iterdir()) if p.is_file()}
    (args.evidence/'input_sha256_after.json').write_text(json.dumps(after_hashes,indent=2)+'\n',encoding='utf-8')
    assert before_hashes == after_hashes, 'capture files changed'
    summary = dict(passed=True, sequence_checks=sequence_results, captures_unchanged=len(after_hashes),
                   frame_lineage_checked=len(records), overlays_decoded=len(records),
                   published_regression_fresh_detector_matching=125, detector_input_unchanged=True,
                   geometry_checks=geometry_checks,baseline_successes_preserved=[1,31,71,131,201,241],
                   synthetic_scope='failure behavior only, not real-scene recognition evidence')
    (args.evidence/'validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
