"""独立V-06弯道候选回放；不修改冻结R1入口，不访问板卡／串口。"""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from offline_boundary import BoundaryConfig
from offline_curve import CurveConfig, CurveDetector
from replay_offline import overlay, save_json


def curve_overlay(gray, result, frame_id, config):
    """在副本叠加；青色为有双边支持的近场中点，黄圈为观测轮廓肘部。

    紫色仍是R1固定参考行可用中线。只标观测支持范围，不把两侧转角
    相连成出弯轨迹；字幕明确没有整弯轨迹／控制就绪证据。
    """
    canvas = overlay(gray, result, frame_id, config)
    observation = result['curve_observation']
    for p in observation['near_field']['centerline']:
        cv2.circle(canvas, (round(p['x']), p['y']), 2, (255, 255, 0), -1)
    for corner in observation['corners']:
        vertex = corner['vertex']
        cv2.circle(canvas, (vertex['x'], vertex['y']), 6, (0, 255, 255), 1)
        cv2.putText(canvas, corner['side'][0].upper(), (vertex['x']+7, vertex['y']),
                    cv2.FONT_HERSHEY_SIMPLEX, .35, (0, 255, 255), 1)
    canvas = cv2.copyMakeBorder(canvas, 0, 80, 0, 0, cv2.BORDER_CONSTANT)
    lines = [f"C1 near={observation['near_field']['y_range']} turn={observation['turn_hint']}",
             observation['status'],
             'cyan=observed near midpoint yellow=corner',
             'full turn path: NO   control ready: NO']
    for i, line in enumerate(lines):
        cv2.putText(canvas, line, (4, 344+i*18), cv2.FONT_HERSHEY_SIMPLEX, .32, (255, 255, 255), 1)
    return canvas


def replay(inputs, output, detector=None):
    """回放一个或多个采集目录，返回逐帧记录与统计；已有输出拒绝覆盖。

    原图仅接受data_数字.jpg，不使用dbg／损坏日志。输出与输入树分离，
    会话名必须唯一，避免同名原图相互覆盖；所有原图路径和哈希留证。
    视频实际重解码验帧，人工10fps不表示采集速度或K230性能。
    """
    detector = detector or CurveDetector()
    output = output.resolve()
    folders = [p.resolve() for p in inputs]
    if output.exists():
        raise FileExistsError(f'保留已有证据，请使用新输出目录：{output}')
    if len({p.name for p in folders}) != len(folders):
        raise ValueError('input session names must be unique')
    files = []
    for folder in folders:
        if not folder.is_dir() or folder == output or folder in output.parents or output in folder.parents:
            raise ValueError('input/output must be separate directory trees')
        selected = sorted((p for p in folder.iterdir() if re.fullmatch(r'data_\d+\.jpg', p.name)),
                          key=lambda p: int(p.stem.split('_')[1]))
        if not selected or len({int(p.stem.split('_')[1]) for p in selected}) != len(selected):
            raise ValueError(f'empty or duplicate numeric data frame IDs: {folder}')
        files.extend(selected)
    if not files:
        raise ValueError('at least one input session required')
    output.mkdir(parents=True)
    save_json(output/'parameters.json', detector.parameters())
    writer = cv2.VideoWriter(str(output/'preview.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 10, (320, 410))
    if not writer.isOpened():
        raise RuntimeError('cannot open mp4v writer')
    records, timings = [], []
    try:
        for file in files:
            image = cv2.imread(str(file), cv2.IMREAD_UNCHANGED)
            start = time.perf_counter_ns()
            result = detector.detect(image)
            elapsed = (time.perf_counter_ns()-start)/1e6
            timings.append(elapsed)
            frame_id = int(file.stem.split('_')[1])
            source = str(file.relative_to(Path.cwd())) if file.is_relative_to(Path.cwd()) else str(file)
            result.update(source=source, source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                          frame_id=frame_id, session=file.parent.name, processing_ms=elapsed,
                          read_ok=image is not None)
            display = image if image is not None and image.dtype == np.uint8 and image.shape == (240, 320) else np.zeros((240, 320), np.uint8)
            canvas = curve_overlay(display, result, frame_id, detector.baseline.config)
            relative = Path('overlays')/file.parent.name/(file.stem+'.png')
            target = output/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(target), canvas):
                raise RuntimeError(f'overlay write failed: {target}')
            result['overlay'] = relative.as_posix()
            writer.write(canvas)
            records.append(result)
    finally:
        writer.release()
    with (output/'frames.jsonl').open('w', encoding='utf-8') as stream:
        for row in records:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
    columns = ['session', 'frame_id', 'valid_y120', 'near_available', 'near_y_range', 'turn_hint', 'status', 'source_sha256']
    with (output/'comparison.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        csv_writer = csv.DictWriter(stream, fieldnames=columns)
        csv_writer.writeheader()
        for r in records:
            o = r['curve_observation']
            csv_writer.writerow(dict(session=r['session'], frame_id=r['frame_id'], valid_y120=r['valid'],
                                      near_available=o['near_field']['available'], near_y_range=o['near_field']['y_range'],
                                      turn_hint=o['turn_hint'], status=o['status'], source_sha256=r['source_sha256']))
    video = cv2.VideoCapture(str(output/'preview.mp4'))
    decoded = 0
    while video.isOpened():
        ok, _ = video.read()
        if not ok:
            break
        decoded += 1
    video.release()
    groups = []
    for folder in folders:
        group = [r for r in records if r['session'] == folder.name]
        groups.append(dict(session=folder.name, frames=len(group), fixed_reference_valid=sum(r['valid'] for r in group),
                           near_available=sum(r['curve_observation']['near_field']['available'] for r in group),
                           turns=dict(Counter(r['curve_observation']['turn_hint'] or 'none' for r in group))))
    summary = dict(frames=len(records), groups=groups, fixed_reference_valid=sum(r['valid'] for r in records),
                   video_decoded_frames=decoded, read_failed=sum(not r['read_ok'] for r in records),
                   algorithm_ms=dict(mean=float(np.mean(timings)), p95=float(np.percentile(timings, 95))),
                   preview_fps=10, scope='published static/hand-pushed regression; not accuracy, motion, physical turn angle or control acceptance')
    save_json(output/'summary.json', summary)
    if decoded != len(records) or summary['read_failed']:
        raise RuntimeError('read/video verification failed; inspect summary.json')
    return records, summary


def main():
    """新候选显式入口；未指定参数时使用C1默认配置，绝不改变R1默认入口。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8')) if args.config else {}
    if set(config)-{'boundary', 'curve'}:
        parser.error('unknown config sections')
    detector = CurveDetector(BoundaryConfig(**config.get('boundary', {})), CurveConfig(**config.get('curve', {})))
    _, summary = replay(args.input, args.output, detector)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
