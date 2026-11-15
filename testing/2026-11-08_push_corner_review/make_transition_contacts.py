"""补看无效区间及恢复相邻帧；不重新运行算法、不覆盖已有审核页。"""
from pathlib import Path
import json
import cv2
import numpy as np

root = Path('testing/2026-11-08_push_corner_review')
rows = [json.loads(line) for line in (root/'replay_c1/frames.jsonl').read_text(encoding='utf-8').splitlines()]
times = {r['frame_id']: r['elapsed_ms'] for r in
         (json.loads(line) for line in Path('vision/data/captures/final_mount_20261108/push_corner_77_0001/frames.jsonl').read_text(encoding='utf-8').splitlines())}
selected = [r for r in rows if 20 <= r['frame_id'] <= 60]
for start in range(0, len(selected), 16):
    group = selected[start:start+16]
    for mode in ('raw', 'overlay'):
        cards = []
        for row in group:
            source = root/'replay_c1'/row['overlay'] if mode == 'overlay' else Path(row['source'])
            im = cv2.imread(str(source))
            assert im is not None
            card = cv2.copyMakeBorder(im, 22, 0, 0, 0, cv2.BORDER_CONSTANT)
            o = row['curve_observation']
            label = 'f%d t%.3fs V%d N%d T%s' % (row['frame_id'], times[row['frame_id']]/1000,
                                               row['valid'], o['near_field']['available'], o['turn_hint'])
            cv2.putText(card, label, (4,16), cv2.FONT_HERSHEY_SIMPLEX, .35, (255,255,255), 1)
            cards.append(card)
        while len(cards) < 16:
            cards.append(np.zeros_like(cards[0]))
        path = root/('transition_%s_%02d.png' % (mode, start//16+1))
        if path.exists():
            raise FileExistsError(path)
        assert cv2.imwrite(str(path), np.vstack([np.hstack(cards[i:i+4]) for i in range(0,16,4)]))
print('Created six transition contact pages for frames 20..60.')
