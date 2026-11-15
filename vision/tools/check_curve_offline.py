"""C1公开旧图回归及失效检查；不连接硬件，证据写入新目录并拒绝覆盖。"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from offline_curve import CurveDetector
from replay_curve_offline import replay
from replay_offline import save_json


def digest(path):
    """对实际字节取SHA-256，不依赖时间戳或Git是否跟踪。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def run(output):
    """执行358张完整回放、冻结语义比对、来源保护及合成失效序列。

    数据均已公开，仅为开发回归，不能作为独立测试准确率。原始数据、
    既有证据和冻结源码在前后逐字节哈希比较；自身源码另存快照。
    """
    root = Path('testing/2026-11-08_vision_restart')
    capture_root = Path('vision/data/captures/final_mount_20261108')
    static = json.loads((root/'static_summary/summary.json').read_text(encoding='utf-8'))
    v06_names = ['v06_77deg_entry_0007', 'v06_77deg_entry_0008', 'v06_77deg_mid_0009',
                 'v06_77deg_exit_heading_0010', 'v06_77deg_exit_forward_0011', 'v06_no_boundary_text_0012']
    inputs = [Path('vision/data/captures/d01_straight_run01')]
    expected = load_rows(Path('vision/build/offline_v02_r1/frames.jsonl'))
    for group in static['groups']:
        inputs.append(capture_root/group['session'])
        expected.extend(load_rows(root/group['session'].removeprefix('v03_')/'frames.jsonl'))
    for i, name in enumerate(v06_names, 7):
        inputs.append(capture_root/f'v03_center_{i:04d}')
        expected.extend(load_rows(root/name/'frames.jsonl'))
    assert len(expected) == 358
    expected_map = {(Path(r['source']).parent.name, Path(r['source']).name): r for r in expected}
    assert len(expected_map) == 358
    if output.exists():
        raise FileExistsError(f'保留已有检查，改用新目录：{output}')
    # 覆盖整个现有首轮证据树，连同原采集日志／dbg均保护，不只抽查原图。
    protected = set(p for folder in inputs+[root] for p in folder.rglob('*') if p.is_file()
                    and '__pycache__' not in p.parts)
    protected.update(Path(p) for p in static['frozen_code_hashes'])
    protected.update([Path('vision/build/offline_v02_r1/frames.jsonl'), Path('vision/build/offline_v02_r1/parameters.json')])
    before = {str(p): digest(p) for p in sorted(protected)}
    for path, sha in static['frozen_code_hashes'].items():
        assert before[str(Path(path))] == sha, f'frozen source changed: {path}'
    detector = CurveDetector()
    rows, summary = replay(inputs, output, detector)
    keyset = set(detector.baseline.detect(None))
    checked_sources, rejected_raw_pairs = 0, 0
    for row in rows:
        source = Path(row['source'])
        prior = expected_map[(source.parent.name, source.name)]
        assert row['source_sha256'] == prior['source_sha256'] == digest(source)
        for key in keyset:
            assert row[key] == prior[key], f'R1 semantics changed: {source} {key}'
        obs = row['curve_observation']
        near = obs['near_field']
        assert not obs['control_ready'] and not obs['full_turn_path_available']
        if not row['valid']:
            assert row['centerline'] == [] and row['deviation_px'] is None and row['deviation_normalized'] is None
        if near['available']:
            assert near['y_range'] == [row['pair_samples'][0]['y'], row['pair_samples'][-1]['y']]
            assert obs['accepted_pair_samples'] == row['pair_samples']
            assert len(near['centerline']) == len(row['pair_samples'])
            for middle, pair in zip(near['centerline'], row['pair_samples']):
                assert middle == dict(x=(pair['left']+pair['right'])/2, y=pair['y'])
        else:
            assert near['centerline'] == [] and near['y_range'] is None
            assert obs['accepted_pair_samples'] == [] and obs['turn_hint'] is None
        if obs['turn_hint']:
            assert near['available']
            for side in ('left', 'right'):
                assert any(c['side'] == side and c['direction'] == obs['turn_hint'] for c in obs['corners'])
        if row['session'] in ('v03_center_0009', 'v03_center_0012'):
            assert not near['available'] and not obs['corners'] and obs['turn_hint'] is None
            rejected_raw_pairs += bool(row['pair_samples'])
        if row['session'] in ('v03_center_0007', 'v03_center_0008'):
            assert near['available'] and obs['turn_hint'] == 'right'
        if row['session'].startswith('v03_') and row['session'] not in ('v03_center_0007', 'v03_center_0008'):
            assert obs['turn_hint'] is None, f'false turn on final-mount control: {source}'
        if row['session'] == 'd01_straight_run01' and row['frame_id'] in (80,81,82,190,191,192,250,251,252):
            assert not row['valid'] and not near['available'] and obs['turn_hint'] is None
        rendered = cv2.imread(str(output/row['overlay']))
        assert rendered is not None and rendered.shape == (410, 320, 3)
        checked_sources += 1
    # 实图镜像只验证左右对称，不代表采到了真实左弯或增加独立工况。
    entry = cv2.imread(str(capture_root/'v03_center_0008/data_0001.jpg'), cv2.IMREAD_UNCHANGED)
    entry_before = entry.copy()
    mirrored = detector.detect(np.ascontiguousarray(entry[:, ::-1]))
    assert mirrored['curve_observation']['turn_hint'] == 'left'
    mid = cv2.imread(str(capture_root/'v03_center_0009/data_0001.jpg'), cv2.IMREAD_UNCHANGED)
    text = cv2.imread(str(capture_root/'v03_center_0012/data_0001.jpg'), cv2.IMREAD_UNCHANGED)
    stripe = np.full_like(entry, 180)
    stripe[150:172] = 40
    wall = np.full_like(entry, 180)
    wall[:105] = 40
    parallel = np.full_like(entry, 180)
    for y in range(65, 216):
        x = 45+round((y-65)*.2)
        parallel[y, x:x+12] = 40
        parallel[y, x+110:x+122] = 40
    sequence = []
    for name, image, available in [('entry', entry, True), ('single_real_band', mid, False),
                                  ('entry_again', entry, True), ('text', text, False),
                                  ('white', np.full_like(entry, 255), False), ('black', np.zeros_like(entry), False),
                                  ('none', None, False), ('wrong_shape', np.zeros((20, 30), np.uint8), False),
                                  ('wrong_dtype', entry.astype(float), False), ('single_horizontal', stripe, False),
                                  ('wall', wall, False), ('parallel_false_pair', parallel, False)]:
        image_before = image.copy() if image is not None else None
        result = detector.detect(image)
        obs = result['curve_observation']
        assert obs['near_field']['available'] == available, name
        if not available:
            assert not obs['near_field']['centerline'] and not obs['accepted_pair_samples']
            assert obs['turn_hint'] is None and not obs['corners']
            assert not result['valid'] and not result['centerline'] and result['deviation_px'] is None
        else:
            assert obs['turn_hint'] == 'right'
        if image is not None:
            assert np.array_equal(image, image_before), f'input mutated: {name}'
        sequence.append(dict(case=name, near_available=available, turn_hint=obs['turn_hint']))
    assert np.array_equal(entry, entry_before)
    after = {str(p): digest(p) for p in sorted(protected)}
    assert before == after, 'protected originals, evidence or frozen source changed'
    save_json(output/'protected_hashes.json', before)
    snapshot = output/'source_snapshot'
    snapshot.mkdir()
    code = ['vision/src/offline_curve.py', 'vision/tools/replay_curve_offline.py', 'vision/tools/check_curve_offline.py']
    hashes = {}
    for path in code:
        shutil.copy2(path, snapshot/Path(path).name)
        hashes[path] = digest(Path(path))
    # 全部18张分别保留并展示；六次摆位各3张，不能称18种独立场景。
    for index in range(1, 4):
        cards = [cv2.imread(str(output/r['overlay'])) for session in range(7, 13)
                 for r in rows if r['session'] == f'v03_center_{session:04d}' and r['frame_id'] == index]
        assert len(cards) == 6
        assert cv2.imwrite(str(output/f'v06_contact_{index:02d}.png'),
                           np.vstack([np.hstack(cards[:3]), np.hstack(cards[3:])]))
    old = [r for r in rows if r['session'] == 'd01_straight_run01']
    findings = dict(passed=True, frame_count=checked_sources, protected_files_unchanged=len(before),
                    frozen_source_hashes=static['frozen_code_hashes'], candidate_code_hashes=hashes,
                    r1_result_fields_identical=len(rows), invalid_reference_output_cleared=sum(not r['valid'] for r in rows),
                    negative_short_raw_pairs_excluded=rejected_raw_pairs, sequence_checks=sequence,
                    mirror_turn_hint='left', video_decoded_frames=summary['video_decoded_frames'],
                    old_near_only=[r['frame_id'] for r in old if not r['valid'] and r['curve_observation']['near_field']['available']],
                    old_turn_hints=[dict(frame_id=r['frame_id'], turn=r['curve_observation']['turn_hint'])
                                    for r in old if r['curve_observation']['turn_hint']],
                    scope='development regression on published data; candidate observations only; no full-turn/vehicle acceptance')
    save_json(output/'validation.json', findings)
    print(json.dumps(dict(validation=findings, groups=summary['groups']), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
