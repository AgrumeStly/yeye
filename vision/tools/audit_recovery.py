"""生成C2新增输出审核页及关键段逐帧复核表，目视结论另存review_notes。"""

import csv
import json
from pathlib import Path

import cv2
import numpy as np

from replay_recovery import load, paint
from review_recovery_inputs import ROOT, save


def main():
    """原图、实测边缘和输出逐帧并列；不把自动几何检查称人工真值。"""
    replay=ROOT/'replay'
    rows=load(replay/'frames.jsonl')
    chosen=[r for r in rows if r['recovery_observation']['pair_samples'] and
            not r['curve_observation']['near_field']['available']]
    target=ROOT/'new_output_audit'
    target.mkdir(exist_ok=False)
    index=[]
    for offset in range(0,len(chosen),16):
        cards=[]
        for row in chosen[offset:offset+16]:
            gray=cv2.imread(row['source'],cv2.IMREAD_GRAYSCALE)
            image=paint(row,gray)
            cv2.putText(image,row['session'],(3,15),cv2.FONT_HERSHEY_SIMPLEX,.34,(0,255,255),1)
            cards.append(image)
        while len(cards)%4:
            cards.append(np.zeros_like(cards[0]))
        path=target/f'new_{offset//16+1:02d}.jpg'
        assert cv2.imwrite(str(path),np.vstack([np.hstack(cards[i:i+4]) for i in range(0,len(cards),4)]))
        index.append(dict(path=path.as_posix(),frames=[dict(session=r['session'],frame_id=r['frame_id'])
                     for r in chosen[offset:offset+16]]))
    save(target/'index.json',index)
    print(json.dumps(dict(pages=len(index),frames=len(chosen))))


if __name__=='__main__':
    main()
