"""V-06接续输入归档与原图审核页；只读原件，不接触板卡。"""

import hashlib
import json
from pathlib import Path
import subprocess

import cv2
import fitz
import numpy as np


ROOT = Path('testing/2026-11-08_vision_recovery_c2')
CAPTURE = Path('vision/data/captures/final_mount_20261108/push_full_lap_0001')


def digest(path):
    """使用实际文件字节而非Git状态，覆盖未跟踪的原件和冻结证据。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    """保存UTF-8可审查JSON，拒绝非有限浮点。"""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def contacts(ids, destination, records=None, prefix='raw', overlays=None):
    """每页16张原图／副本，字幕为原始帧号和软件毫秒；不插帧。"""
    pages = []
    for offset in range(0, len(ids), 16):
        cards = []
        for frame_id in ids[offset:offset+16]:
            file = CAPTURE/f'data_{frame_id:04d}.jpg'
            gray = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
            image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            if overlays is not None:
                image = overlays(frame_id, image)
            card = cv2.copyMakeBorder(image, 24, 0, 0, 0, cv2.BORDER_CONSTANT)
            stamp = records[frame_id]['elapsed_ms'] if records else 0
            cv2.putText(card, f'{frame_id}   t={stamp}ms', (5, 17), cv2.FONT_HERSHEY_SIMPLEX,
                        .45, (255, 255, 255), 1)
            cards.append(card)
        while len(cards) % 4:
            cards.append(np.zeros_like(cards[0]))
        sheet = np.vstack([np.hstack(cards[i:i+4]) for i in range(0, len(cards), 4)])
        target = destination/f'{prefix}_{offset//16+1:02d}.jpg'
        assert cv2.imwrite(str(target), sheet)
        pages.append(dict(path=target.as_posix(), frames=ids[offset:offset+16]))
    return pages


def main():
    """启动前快照所有既有视觉源码、原件及旧证据，随后制作完整失效审核页。"""
    ROOT.mkdir(parents=True, exist_ok=False)
    roots = [Path('vision/src'), Path('vision/tools'), Path('vision/data/captures')]
    roots.extend(p for p in Path('testing').iterdir() if p.is_dir() and p != ROOT
                 and ('vision' in p.name or 'capture' in p.name or 'review' in p.name))
    paths = {p for folder in roots for p in folder.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    paths.update([Path('competition/比赛文档.pdf'), Path('project_planning/project_status.md'),
                  Path('control/docs/protocol_v1_draft.md')])
    save(ROOT/'protected_before.json', {p.as_posix(): digest(p) for p in sorted(paths)})
    status = subprocess.check_output(['git', 'status', '--short'], text=True, encoding='utf-8')
    save(ROOT/'workspace_before.json', dict(cwd=str(Path.cwd()),
         branch=subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip(),
         head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), status=status))
    pdf = fitz.open('competition/比赛文档.pdf')
    (ROOT/'competition_pdf.txt').write_text('\n'.join(p.get_text() for p in pdf), encoding='utf-8')
    for i in (1, 2, 3):
        pdf[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(str(ROOT/f'competition_page_{i+1}.png'))
    records = {r['frame_id']: r for r in [json.loads(s) for s in
               (CAPTURE/'frames.jsonl').read_text(encoding='utf-8').splitlines()]}
    analysis = json.loads(Path('testing/2026-11-08_two_lap_review/analysis.json').read_text(encoding='utf-8'))
    ids = set()
    for key in ('fixed_invalid_spans', 'near_missing_spans'):
        for span in analysis[key]:
            ids.update(range(max(1, span['first_frame']-2), min(732, span['last_frame']+2)+1))
    pages = contacts(sorted(ids), ROOT, records)
    save(ROOT/'contact_index.json', pages)
    save(ROOT/'finish_contact_index.json', contacts(list(range(1, 10))+list(range(405, 427))+
         list(range(569, 587)), ROOT, records, 'finish_raw'))
    print(json.dumps(dict(protected=len(paths), reviewed_frame_candidates=len(ids), pages=len(pages))))


if __name__ == '__main__':
    main()
