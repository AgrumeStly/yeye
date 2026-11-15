"""针对R5误删斜线的原图回归；不采新图、不连接板卡、不当真实动态证据。"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2

from prepare_lap_visual_link import R5, ROOT


def load(path):
    """独立加载合并包，禁止触发其main，保留各自网格常量。"""
    scope = {'__name__': 'yaw_background_host_check'}
    exec(compile(path.read_bytes(), str(path), 'exec'), scope)
    return scope


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    old, new = load(R5), load(args.candidate)
    checks, examples = [], []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
        if not ok:
            raise AssertionError(name)
    base = ROOT / 'vision/data/captures/final_mount_20261108'
    for pose, sign in (('heading_left', 1), ('heading_right', -1)):
        for path in sorted((base / ('v03_' + pose + '_0001')).glob('data_*.jpg')):
            data = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE).tobytes()
            digest = hashlib.sha256(data).hexdigest()
            before = old['_grid'](data, old['_threshold'](data))[0]
            after = new['_grid'](data, new['_threshold'](data))[0]
            old_anchors = old['_pair_anchors'](before)
            anchors = new['_pair_anchors'](after)
            detector = new['LiteLapRoute'](search_budget=new['SEARCH_BUDGET'])
            first = detector.update(data, 0)
            second = detector.update(data, 50)
            tag = path.parent.name + '/' + path.name
            check(tag + '_R5_failure_reproduced', len(old_anchors) == 0)
            check(tag + '_real_pair_anchors_retained', len(anchors) >= 3)
            check(tag + '_first_frame_still_cannot_start', not first['valid'])
            check(tag + '_current_pair_second_frame', second['valid'] and second['source'] == 'current_pair')
            check(tag + '_correct_correction_sign', second['steering'] * sign > 0)
            # 重新核对保留的每个黑格都有原灰度采样，不允许补画画外边界。
            observed_only = True
            for i, dark in enumerate(after):
                if dark:
                    y, x = divmod(i, new['GW'])
                    pixel = y*new['GRID_STEP']*320 + x*new['GRID_STEP']
                    observed_only &= sum(data[pixel+delta] <= second['threshold'] for delta in (0, 2, 640, 642)) >= 2
            check(tag + '_no_invented_black_cells', observed_only and hashlib.sha256(data).hexdigest() == digest)
            examples.append(dict(file=str(path.relative_to(ROOT)), raw_jpeg_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                old_black_cells=sum(before), new_black_cells=sum(after), old_anchors=len(old_anchors),
                new_anchors=len(anchors), second_steering=second['steering']))
    check('exactly_six_existing_yaw_images', len(examples) == 6)
    result = dict(checks=checks, examples=examples, candidate_sha256=hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        physical_board_used=False, camera_stream=False, ground_motion_verified=False)
    (args.output / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(len(checks), 'yaw background checks PASS; stored images only')


if __name__ == '__main__':
    main()
