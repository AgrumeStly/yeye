"""V-02电脑离线回放入口；只读取data_数字.jpg，不读取dbg或采集日志。"""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from offline_boundary import BoundaryConfig, BoundaryDetector


def save_json(path, value):
    """UTF-8保存可审核元数据；禁止NaN，以null表示不可用量。"""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def overlay(gray, result, frame_id, config):
    """在原图副本画点；线段只连接相邻支持行，不跨大缺口，不改原始数组。

    左边界绿、右边界橙、中线紫，黄色水平线为偏差参考行；ROI为灰色框。
    字幕放在原图下方以免遮挡边界。无效帧只画已观察边界，不画可用中线。
    """
    canvas = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(canvas, (0, config.roi_top), (config.width-1, config.roi_bottom), (95,95,95), 1)
    cv2.line(canvas, (0, config.reference_y), (config.width-1, config.reference_y), (0,140,140), 1)
    cv2.drawMarker(canvas, (round((config.width-1)/2), config.reference_y), (255,255,0), cv2.MARKER_CROSS, 9, 1)
    for field, color in [('left',(0,255,0)), ('right',(0,150,255)), ('centerline',(255,0,255))]:
        points = result[field]
        for i, p in enumerate(points):
            xy = (round(p['x']), p['y'])
            cv2.circle(canvas, xy, 2, color, -1)
            if i and abs(p['y']-points[i-1]['y']) <= config.row_step*2:
                cv2.line(canvas, (round(points[i-1]['x']),points[i-1]['y']), xy, color, 1)
    # R1近水平条带两侧轮廓用青色散点，仅是可见候选，侧别未确定；
    # 不把该轮廓连成控制中线，避免把单条横线冒充双侧道路。
    for ribbon in result.get('visible_ribbons', []):
        for edge in ('upper','lower'):
            for p in ribbon[edge]:
                cv2.circle(canvas, (p['x'],p['y']), 1, (255,255,0), -1)
    if not result['valid'] and result.get('unpaired_boundary'):
        for p in result['unpaired_boundary']['points']:
            cv2.circle(canvas, (p['x'],p['y']), 1, (210,180,140), -1)
    canvas = cv2.copyMakeBorder(canvas, 0, 90, 0, 0, cv2.BORDER_CONSTANT)
    text_lines = [f"data_{frame_id:04d} {'VALID' if result['valid'] else 'INVALID'} Q={result['quality']:.2f}",
                  f"y={config.reference_y} dx={result['deviation_px']} norm={result['deviation_normalized']}",
                  ','.join(result['reasons']) or 'same-frame measured pair',
                  'L=green R=orange C=magenta cyan=ribbon']
    for i, line in enumerate(text_lines):
        # 长原因不省略；完整字符串始终另存于JSONL，这里分两行显示。
        cv2.putText(canvas, line[:66], (4, 255+i*20), cv2.FONT_HERSHEY_SIMPLEX, .29, (255,255,255), 1)
    return canvas


def main():
    """批处理、逐帧JSONL/CSV、叠加图、MP4及独立统计；错误返回非零退出码。

    算法计时只包围detect，不含读图、画图、保存及编码；视频速度人为指定。
    输入/输出目录互不包含，以防派生文件覆盖原始采集。无硬件/串口入口。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--headless', action='store_true', help='兼容显式无窗口批处理；默认也无窗口')
    parser.add_argument('--fps', type=float, default=10, help='人为预览播放速度，不是采集帧率')
    parser.add_argument('--config', type=Path, help='可选参数JSON，未知字段会报错')
    args = parser.parse_args()
    source, output = args.input.resolve(), args.output.resolve()
    if source == output or source in output.parents or output in source.parents:
        parser.error('input and output must be separate trees')
    if not source.is_dir() or not np.isfinite(args.fps) or not 0 < args.fps <= 120:
        parser.error('input directory and finite preview fps in (0,120] required')
    config = BoundaryConfig(**json.loads(args.config.read_text(encoding='utf-8'))) if args.config else BoundaryConfig()
    detector = BoundaryDetector(config)
    files = sorted((p for p in source.iterdir() if re.fullmatch(r'data_\d+\.jpg', p.name)),
                   key=lambda p: int(p.stem.split('_')[1]))
    if not files:
        parser.error('no data_*.jpg inputs')
    ids = [int(p.stem.split('_')[1]) for p in files]
    if len(ids) != len(set(ids)):
        parser.error('duplicate numeric frame identifiers')
    output.mkdir(parents=True, exist_ok=True)
    (output/'overlays').mkdir(exist_ok=True)
    save_json(output/'parameters.json', detector.parameters())
    started = time.perf_counter()
    records, times, reasons = [], [], Counter()
    writer = cv2.VideoWriter(str(output/'preview.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), args.fps,
                             (config.width,config.height+90))
    video_error = None if writer.isOpened() else 'OpenCV mp4v VideoWriter could not open'
    try:
        for file, frame_id in zip(files, ids):
            gray = cv2.imread(str(file), cv2.IMREAD_UNCHANGED)
            read_ok = gray is not None
            t0 = time.perf_counter_ns()
            result = detector.detect(gray)
            elapsed = (time.perf_counter_ns()-t0)/1e6
            if not read_ok:
                result['reasons'] = ['read_failed']
            times.append(elapsed)
            result.update(frame_id=frame_id, source=str(file.relative_to(Path.cwd())) if file.is_relative_to(Path.cwd()) else str(file),
                          source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                          read_ok=read_ok, processing_ms=elapsed)
            reasons.update(result['reasons'])
            # 读取失败/尺寸不符也保留明确占位叠加，逐帧结果不能悄悄消失。
            display = gray if read_ok and gray.shape == (config.height,config.width) else np.zeros((config.height,config.width),np.uint8)
            rendered = overlay(display, result, frame_id, config)
            image_path = output/'overlays'/f'data_{frame_id:04d}.png'
            if not cv2.imwrite(str(image_path), rendered):
                raise RuntimeError(f'overlay write failed: {image_path}')
            result['overlay'] = str(image_path.relative_to(output))
            if writer.isOpened():
                writer.write(rendered)
            records.append(result)
    finally:
        writer.release()
    with (output/'frames.jsonl').open('w', encoding='utf-8') as stream:
        for result in records:
            stream.write(json.dumps(result,ensure_ascii=False,allow_nan=False)+'\n')
    columns = ['frame_id','source','read_ok','valid','quality','left_state','right_state','reference_y',
               'deviation_px','deviation_normalized','processing_ms','reasons']
    with (output/'frames.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        csv_writer = csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore')
        csv_writer.writeheader()
        for r in records:
            csv_writer.writerow({**r,'reasons':';'.join(r['reasons'])})
    # 不只检查视频文件存在，实际重新解码每一帧，统计可播放总帧数。
    decoded = 0
    capture = cv2.VideoCapture(str(output/'preview.mp4'))
    while capture.isOpened():
        ok, _ = capture.read()
        if not ok:
            break
        decoded += 1
    capture.release()
    if decoded != len(files):
        video_error = video_error or f'video decoded {decoded} frames, expected {len(files)}'
    valid = sum(r['valid'] for r in records)
    read_fail = sum(not r['read_ok'] for r in records)
    stats = dict(input_count=len(files), processed_ok=len(files)-read_fail, valid=valid,
                 invalid=sum(r['read_ok'] and not r['valid'] for r in records), read_failed=read_fail,
                 overlay_count=len(records), video_decoded_frames=decoded, preview_fps=args.fps,
                 preview_is_capture_fps=False, video_error=video_error, invalid_reasons=dict(reasons),
                 algorithm_ms=dict(mean=float(np.mean(times)),median=float(np.median(times)),
                                   p95=float(np.percentile(times,95)),maximum=float(np.max(times))),
                 timing_excludes=['image_read','drawing','image_write','video_encoding'],
                 wall_seconds=time.perf_counter()-started, temporal_state='none',
                 interpretation='output validity statistics, not accuracy; PC timing is not K230D or end-to-end latency')
    save_json(output/'summary.json', stats)
    if video_error:
        (output/'VIDEO_ERROR.txt').write_text(video_error+'\nInspect overlays/data_*.png in numeric order.\n', encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=True,indent=2))
    return 1 if video_error or read_fail else 0


if __name__ == '__main__':
    raise SystemExit(main())
