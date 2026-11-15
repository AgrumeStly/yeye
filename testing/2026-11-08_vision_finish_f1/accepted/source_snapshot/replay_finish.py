"""V-07终点完整开发回放：按原采集毫秒状态合并，保存每帧与实际解码视频。"""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import shutil
import sys
import time

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_finish import FinishDetector
from replay_recovery import load, spans
from review_recovery_inputs import digest, save


def paint(gray,row):
    """紫框只标本帧实测短划，字幕区分看到／观察区经过；不标车尾越线。"""
    canvas=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)
    result=row['finish'];obs=result['observation']
    for dash in obs['dashes']:
        cv2.rectangle(canvas,(dash['x'],dash['y']),
                      (dash['x']+dash['width'],dash['y']+dash['height']),(255,0,255),1)
    corridor=obs['corridor']
    if corridor:
        cv2.line(canvas,(corridor['left'],corridor['measured_y']),
                 (corridor['right'],corridor['measured_y']),(0,220,0),1)
    canvas=cv2.copyMakeBorder(canvas,0,72,0,0,cv2.BORDER_CONSTANT)
    for i,line in enumerate([f"{row['frame_id']} t={row['timestamp_ms']} y={obs['y']}",
                             f"{result['state']} id={result['event_id']}",
                             f"emit={result['event'] or result['passage_event']}",
                             'whole vehicle crossed: UNKNOWN']):
        cv2.putText(canvas,line,(3,255+i*17),cv2.FONT_HERSHEY_SIMPLEX,.34,(255,255,255),1)
    return canvas


def run(output,input_path):
    """复用已核对R1同帧诊断，终点算法重新实际执行，任何输入字节改变即失败。"""
    output.mkdir(parents=True,exist_ok=False)
    detector=FinishDetector()
    save(output/'parameters.json',detector.parameters())
    (output/'source_snapshot').mkdir()
    for file in [Path('vision/src/offline_finish.py'),Path(__file__)]:
        shutil.copy2(file,output/'source_snapshot'/file.name)
    save(output/'code_hashes.json',{p.name:digest(p) for p in (output/'source_snapshot').iterdir()})
    inputs=[r for r in load(input_path) if r['evaluation_group']=='development']
    records=[];summaries=[];cards=[]
    for session in dict.fromkeys(r['session'] for r in inputs):
        detector.reset();group=[]
        overlay_dir=output/'overlays'/session;overlay_dir.mkdir(parents=True)
        video=None
        if session=='push_full_lap_0001':
            video=cv2.VideoWriter(str(output/'two_lap_finish.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),10,(320,312))
            assert video.isOpened()
        try:
            for row in (r for r in inputs if r['session']==session):
                source=Path(row['source']);assert digest(source)==row['source_sha256']
                gray=cv2.imread(str(source),cv2.IMREAD_GRAYSCALE)
                start=time.perf_counter_ns()
                result=detector.detect(gray,row,row['timestamp_ms'],session)
                elapsed=(time.perf_counter_ns()-start)/1e6
                record={k:row[k] for k in ('frame_id','session','timestamp_ms','source','source_sha256')}
                record.update(finish=result,finish_processing_ms=elapsed,road_valid=row['valid'])
                display=paint(gray,record)
                assert cv2.imwrite(str(overlay_dir/(source.stem+'.jpg')),display)
                if video is not None:video.write(display)
                if result['observation']['visible'] or result['event'] or result['passage_event']:
                    cards.append((record,display))
                group.append(record)
        finally:
            if video is not None:video.release()
        summaries.append(dict(session=session,frames=len(group),
          spatial_visible_frames=[r['frame_id'] for r in group if r['finish']['observation']['visible']],
          seen_events=[dict(frame=r['frame_id'],ms=r['timestamp_ms'],id=r['finish']['event_id']) for r in group if r['finish']['event']],
          passage_events=[dict(frame=r['frame_id'],ms=r['timestamp_ms'],id=r['finish']['event_id']) for r in group if r['finish']['passage_event']],
          gate_events=[dict(frame=r['frame_id'],ms=r['timestamp_ms'],id=r['finish']['event_id']) for r in group if r['finish']['gate_event']],
          states=dict(Counter(r['finish']['state'] for r in group)),
          algorithm_ms=dict(mean=float(np.mean([r['finish_processing_ms'] for r in group])),p95=float(np.percentile([r['finish_processing_ms'] for r in group],95)))))
        records.extend(group)
    with (output/'frames.jsonl').open('w',encoding='utf-8') as stream:
        for row in records:stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    with (output/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['session','frame','software_ms','road_valid','visible','line_y','state','event','event_id','near_then_unobserved','image_gate_crossed','source_sha256'])
        for r in records:
            f=r['finish'];o=f['observation']
            writer.writerow([r['session'],r['frame_id'],r['timestamp_ms'],r['road_valid'],o['visible'],o['y'],f['state'],f['event'],f['event_id'],f['passage_event'],f['gate_event'],r['source_sha256']])
    pages=[]
    for offset in range(0,len(cards),16):
        images=[c for _,c in cards[offset:offset+16]]
        while len(images)%4:images.append(np.zeros_like(images[0]))
        path=output/f'detections_{offset//16+1:02d}.jpg'
        assert cv2.imwrite(str(path),np.vstack([np.hstack(images[i:i+4]) for i in range(0,len(images),4)]))
        pages.append(dict(path=path.as_posix(),frames=[dict(session=r['session'],frame=r['frame_id']) for r,_ in cards[offset:offset+16]]))
    save(output/'detection_contacts.json',pages)
    decoder=cv2.VideoCapture(str(output/'two_lap_finish.mp4'));decoded=0
    while decoder.read()[0]:decoded+=1
    decoder.release();assert decoded==732
    save(output/'summary.json',dict(groups=summaries,frames=len(records),video_decoded=decoded,
         baseline='No finish detector existed; frozen R1/C1 have no emitted finish events',
         evaluation='All inspected development data; previous-installation line appearances are not negative ground truth'))
    print(json.dumps(summaries,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--input',type=Path,default=Path('testing/2026-11-08_vision_recovery_c2/replay_accepted/frames.jsonl'))
    args=parser.parse_args();run(args.output,args.input)
