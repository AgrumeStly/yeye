"""复用五姿态原图／R5及现场预览审查方向；重复静态输入不充作实时证据。"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2

from prepare_lap_visual_link import R5, R5_SHA256, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--frames', type=int, choices=(4, 50), default=4)
    parser.add_argument('--yaw-only', action='store_true')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    assert hashlib.sha256(R5.read_bytes()).hexdigest() == R5_SHA256
    checked = json.loads((R5.parent.parent / 'runtime_r5_checks/checks.json').read_text(encoding='utf-8'))
    assert len(checked['checks']) == 42 and all(c['passed'] for c in checked['checks'])
    scope = {'__name__': 'direction_review_only'}
    exec(compile(R5.read_bytes(), str(R5), 'exec'), scope)
    paths = sorted((ROOT / 'vision/data/captures/final_mount_20261108').glob('*/data_*.jpg'))
    paths = [p for p in paths if p.parent.name in ('v03_center_0002', 'v03_offset_left_0001',
        'v03_offset_right_0001', 'v03_heading_left_0001', 'v03_heading_right_0001')]
    paths += sorted((ROOT / 'testing/2026-11-11_field_live/straight_center_01/preview').glob('*.jpg'))
    if args.yaw_only:
        paths = [p for p in paths if p.parent.name in ('v03_heading_left_0001', 'v03_heading_right_0001') and p.name == 'data_0001.jpg']
    rows = []
    for path in paths:
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        detector = scope['LiteLapRoute'](search_budget=scope['SEARCH_BUDGET'])
        results = [detector.update(image.tobytes(), 50*index) for index in range(args.frames)]
        r = results[-1]
        steer, bend = r['steering'], r['bend']
        base = 40 * (1 - .45 * bend / 1000)
        rows.append(dict(file=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            valid=r['valid'], source=r['source'], steering=steer, bend=bend, support=r['support'],
            first_valid_synthetic_index=next((i+1 for i, item in enumerate(results) if item['valid']), None),
            valid_synthetic_frames=sum(bool(item['valid']) for item in results), synthetic_frames=args.frames,
            modeled_left_rpm=base*(1+steer/1000) if r['valid'] else None,
            modeled_right_rpm=base*(1-steer/1000) if r['valid'] else None))
    summary = dict(frozen_r5_sha256=R5_SHA256, reused_existing_checks=42, images=rows,
        input='stored JPEG repeated at synthetic 50ms intervals; not camera stream',
        direction='right positive; left wheel target higher for positive steering',
        physical_direction_verified=False, new_camera_capture=False,
        limitations='JPEG preview is not raw sensor bytes; IDE frame ids are not algorithm indices; old yaw samples may remain invalid in L1')
    (output / 'review.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
