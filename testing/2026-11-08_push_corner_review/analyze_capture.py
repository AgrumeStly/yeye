"""核验本轮手推原件并回放；仅完整0001进入分析，保留失败0002原件。"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

import cv2
import numpy as np

sys.path.insert(0, 'vision/tools')
from verify_push_capture import verify
from replay_curve_offline import replay


def digest(path):
    """以实际字节核对原件／源码，不能用文件时间戳代替。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def spans(rows, predicate):
    """保留每一段连续帧及软件时间；不将输出可用性当作道路识别正确率。"""
    result, first = [], None
    for index, row in enumerate(rows):
        if predicate(row) and first is None:
            first = index
        if first is not None and (not predicate(row) or index == len(rows)-1):
            last = index if predicate(row) else index-1
            result.append(dict(first_frame=rows[first]['frame_id'], last_frame=rows[last]['frame_id'],
                               first_ms=rows[first]['capture_elapsed_ms'], last_ms=rows[last]['capture_elapsed_ms'],
                               frames=last-first+1))
            first = None
    return result


def main():
    """完整下载校验→冻结候选回放→逐帧来源关联→审核拼图及时间段统计。"""
    root = Path('testing/2026-11-08_push_corner_review')
    target = root/'analysis.json'
    if target.exists():
        raise FileExistsError('保留已有分析，勿覆盖')
    capture_root = Path('vision/data/captures/final_mount_20261108')
    inventory = json.loads((root/'board_inventory.json').read_text(encoding='utf-8'))
    source_manifest = []
    for group in inventory['sessions']:
        for entry in group['entries']:
            file = capture_root/group['name']/entry['name']
            assert file.stat().st_size == entry['size'], file
            source_manifest.append(dict(path=str(file), bytes=file.stat().st_size, sha256=digest(file)))
    write_json(root/'source_manifest.json', source_manifest)
    original = {s['path']: s['sha256'] for s in source_manifest}
    complete = verify(capture_root/'push_corner_77_0001')
    write_json(root/'verification.json', complete)
    try:
        verify(capture_root/'push_corner_77_0002')
    except ValueError as exc:
        failed = dict(rejected=True, reason=str(exc), used_for_replay=False)
    else:
        raise AssertionError('failed session must not pass complete verification')
    write_json(root/'failed_session_check.json', failed)
    frames = [json.loads(line) for line in (capture_root/'push_corner_77_0001/frames.jsonl').read_text(encoding='utf-8').splitlines()]
    records, replay_summary = replay([capture_root/'push_corner_77_0001'], root/'replay_c1')
    for row, frame in zip(records, frames):
        assert row['frame_id'] == frame['frame_id'] and row['source_sha256'] == frame['sha256']
        row['capture_elapsed_ms'] = frame['elapsed_ms']
    assert len(records) == len(frames) == complete['frames']
    # 以约每10帧抽样形成原图／叠加审核页，逐页查看；不声称逐张人工标注304张。
    indices = sorted(set(list(range(0, len(records), 10))+[len(records)-1]))
    sheets = []
    for page in range((len(indices)+15)//16):
        selected = indices[page*16:(page+1)*16]
        for mode in ('raw', 'overlay'):
            cards = []
            for index in selected:
                row = records[index]
                image = cv2.imread(str(root/'replay_c1'/row['overlay']) if mode == 'overlay' else row['source'])
                assert image is not None
                card = cv2.copyMakeBorder(image, 22, 0, 0, 0, cv2.BORDER_CONSTANT)
                obs = row['curve_observation']
                title = 'f%d t%.2fs V%d N%d T%s' % (row['frame_id'], row['capture_elapsed_ms']/1000,
                                                   row['valid'], obs['near_field']['available'], obs['turn_hint'])
                cv2.putText(card, title, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, .37, (255, 255, 255), 1)
                cards.append(card)
            while len(cards) < 16:
                cards.append(np.zeros_like(cards[0]))
            path = root/('%s_contact_%02d.png' % (mode, page+1))
            assert cv2.imwrite(str(path), np.vstack([np.hstack(cards[i:i+4]) for i in range(0, 16, 4)]))
            sheets.append(str(path))
    snapshot = root/'source_snapshot'
    snapshot.mkdir()
    code = ['vision/src/offline_boundary.py', 'vision/src/offline_curve.py', 'vision/tools/replay_offline.py',
            'vision/tools/replay_curve_offline.py', 'vision/tools/verify_push_capture.py',
            'vision/src/capture_push_canmv.py']
    hashes = {}
    for name in code:
        file = Path(name)
        shutil.copy2(file, snapshot/file.name)
        hashes[name] = digest(file)
    assert all(digest(Path(path)) == sha for path, sha in original.items())
    prior = json.loads(Path('testing/2026-11-08_vision_curve_c1/protected_hashes.json').read_text(encoding='utf-8'))
    assert all(digest(Path(path)) == sha for path, sha in prior.items())
    summary = dict(verification=complete, source_files_preserved=len(original), prior_files_preserved=len(prior),
                   failed_session=failed, code_hashes=hashes, manual_contact_sample_frames=[records[i]['frame_id'] for i in indices],
                   sheets=sheets, replay_summary=replay_summary,
                   fixed_invalid_reasons=dict(Counter(reason for row in records for reason in row['reasons'])),
                   fixed_valid_spans=spans(records, lambda r: r['valid']),
                   fixed_invalid_spans=spans(records, lambda r: not r['valid']),
                   near_available_spans=spans(records, lambda r: r['curve_observation']['near_field']['available']),
                   paired_bend_spans=spans(records, lambda r: r['curve_observation']['turn_hint'] is not None),
                   scope='one operator-reported hand-pushed series; validity statistics only, not accuracy or automatic turn acceptance')
    write_json(target, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
