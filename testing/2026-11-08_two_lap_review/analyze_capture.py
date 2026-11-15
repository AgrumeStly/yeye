"""两圈手推资料：只读校验原件、冻结C1回放、抽样审核页和按软件时间生成预览。"""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path('vision/tools').resolve()))
from verify_push_capture import verify
from replay_curve_offline import replay


def write_json(path, value):
    """证据只写新文件，已存在即停止，防止覆盖已归档分析。"""
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def digest(path):
    """以实际字节计算SHA-256；不以未校准的板上时间判断采样日期。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spans(records, predicate):
    """按逐帧软件时间保留输出有效／失效区间；不是人工正确率或真实运动轨迹。"""
    result, first = [], None
    for i, row in enumerate(records):
        selected = predicate(row)
        if selected and first is None:
            first = i
        if first is not None and (not selected or i == len(records)-1):
            last = i if selected else i-1
            result.append(dict(first_frame=records[first]['frame_id'], last_frame=records[last]['frame_id'],
                               first_ms=records[first]['capture_elapsed_ms'],
                               last_ms=records[last]['capture_elapsed_ms'], frames=last-first+1))
            first = None
    return result


def main():
    """先验证全部原件，再生成派生图；最后复核新原件和既有保护文件未改变。"""
    root = Path('testing/2026-11-08_two_lap_review')
    source = Path('vision/data/captures/final_mount_20261108/push_full_lap_0001')
    if (root/'analysis.json').exists() or (root/'replay_c1').exists():
        raise FileExistsError('保留既有分析，请使用新目录')
    verification = verify(source)
    write_json(root/'verification.json', verification)
    manifest = {str(p): dict(bytes=p.stat().st_size, sha256=digest(p)) for p in sorted(source.iterdir()) if p.is_file()}
    write_json(root/'source_manifest.json', manifest)
    rows = [json.loads(line) for line in (source/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    records, summary = replay([source], root/'replay_c1')
    assert len(rows) == len(records) == verification['frames']
    images, changes, previous = [], [], None
    for row, record in zip(rows, records):
        assert row['frame_id'] == record['frame_id'] and row['sha256'] == record['source_sha256']
        record['capture_elapsed_ms'] = row['elapsed_ms']
        image = cv2.imread(str(source/row['file']), cv2.IMREAD_GRAYSCALE)
        if previous is not None:
            changes.append(dict(frame_id=row['frame_id'], elapsed_ms=row['elapsed_ms'],
                                mean_absolute_difference=float(cv2.absdiff(previous, image).mean())))
        images.append(image)
        previous = image
    write_json(root/'frame_changes.json', changes)
    write_json(root/'frames_with_timing.json', records)

    # 每6张抽一张，仅作为人工初查；页中标题包含帧号、软件时间及C1输出状态。
    indices = sorted(set(range(0, len(rows), 6)) | {len(rows)-1})
    sheets = []
    for start in range(0, len(indices), 16):
        cards = []
        for i in indices[start:start+16]:
            record = records[i]
            card = cv2.cvtColor(images[i], cv2.COLOR_GRAY2BGR)
            card = cv2.copyMakeBorder(card, 24, 0, 0, 0, cv2.BORDER_CONSTANT)
            obs = record['curve_observation']
            title = 'f%d t%.2fs V%d N%d' % (rows[i]['frame_id'], rows[i]['elapsed_ms']/1000,
                                           record['valid'], obs['near_field']['available'])
            cv2.putText(card, title, (4, 17), cv2.FONT_HERSHEY_SIMPLEX, .42, (255, 255, 255), 1)
            cards.append(card)
        while len(cards) < 16:
            cards.append(np.zeros_like(cards[0]))
        path = root/('raw_contact_%02d.jpg' % (start//16+1))
        assert cv2.imwrite(str(path), np.vstack([np.hstack(cards[j:j+4]) for j in range(0, 16, 4)]))
        sheets.append(str(path))

    # 按软件采集起点重采样为10fps展示：重复前一原图填充间隔，不伪造新曝光帧。
    duration = verification['capture_elapsed_ms']
    preview = root/'raw_software_time.mp4'
    writer = cv2.VideoWriter(str(preview), cv2.VideoWriter_fourcc(*'mp4v'), 10, (320, 266))
    if not writer.isOpened():
        raise RuntimeError('Cannot open video writer')
    index = 0
    video_frames = math.ceil(duration/100)
    try:
        for t in range(video_frames):
            ms = t*100
            while index+1 < len(rows) and rows[index+1]['elapsed_ms'] <= ms:
                index += 1
            card = cv2.cvtColor(images[index], cv2.COLOR_GRAY2BGR)
            card = cv2.copyMakeBorder(card, 26, 0, 0, 0, cv2.BORDER_CONSTANT)
            cv2.putText(card, 't%.1fs f%d (held frame)' % (ms/1000, rows[index]['frame_id']),
                        (4, 18), cv2.FONT_HERSHEY_SIMPLEX, .4, (255, 255, 255), 1)
            writer.write(card)
    finally:
        writer.release()
    decoder, decoded = cv2.VideoCapture(str(preview)), 0
    try:
        while decoder.read()[0]:
            decoded += 1
    finally:
        decoder.release()
    assert decoded == video_frames
    snapshots = root/'source_snapshot'
    snapshots.mkdir()
    code = ['vision/src/offline_boundary.py', 'vision/src/offline_curve.py',
            'vision/tools/replay_offline.py', 'vision/tools/replay_curve_offline.py',
            'vision/tools/verify_push_capture.py', 'vision/src/capture_full_lap_canmv.py']
    code_hashes = {}
    for name in code:
        path = Path(name)
        shutil.copy2(path, snapshots/path.name)
        code_hashes[name] = digest(path)
    assert all(digest(Path(path)) == record['sha256'] for path, record in manifest.items())
    protected = json.loads(Path('testing/2026-11-08_vision_curve_c1/protected_hashes.json').read_text(encoding='utf-8'))
    assert all(digest(Path(path)) == value for path, value in protected.items())
    result = dict(verification=verification, source_files=len(manifest), prior_protected_files=len(protected),
                  code_hashes=code_hashes, replay_summary=summary, contact_sheets=sheets,
                  contact_sample_frame_ids=[rows[i]['frame_id'] for i in indices],
                  fixed_invalid_spans=spans(records, lambda r: not r['valid']),
                  near_missing_spans=spans(records, lambda r: not r['curve_observation']['near_field']['available']),
                  fixed_invalid_reasons=dict(Counter(reason for row in records for reason in row['reasons'])),
                  software_time_video=dict(path=str(preview), frames=decoded, fps=10,
                                           note='software-time resampling with repeated frames, not 10fps exposure'),
                  operator_report=dict(hand_pushed_laps=2, finish='entire vehicle over finish then stopped'),
                  scope='file integrity and frozen algorithm outputs, not verified route truth, accuracy or autonomous laps')
    write_json(root/'analysis.json', result)
    print(json.dumps(dict(verification=verification, source_files=len(manifest), protected_files=len(protected),
                         replay_summary=summary, sheets=sheets), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
