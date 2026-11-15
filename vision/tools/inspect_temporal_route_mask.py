"""复查遮挡压力测试的错误接受：仅诊断，不向算法传入隐藏真值。"""
import argparse
import json
from pathlib import Path
import sys
import cv2
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_temporal_route import TemporalRouteDetector
from replay_prediction import component_for_side
from replay_recovery import load
from validate_temporal_route import point_errors
from review_recovery_inputs import save


def run(output,limit):
    """从会话起点重放前缀，保存有较大中点差异的当前模型完整状态。"""
    output.mkdir(parents=True,exist_ok=False);d=TemporalRouteDetector();reports=[]
    rows=[r for r in load(Path('testing/2026-11-08_vision_prediction_p1/release/frames.jsonl')) if r['session']=='push_full_lap_0001']
    for r in rows[:limit]:
        g=cv2.imread(r['source'],0);pairs=r['recovery_observation']['pair_samples'];ms=r['timestamp_ms']
        hide=1200<=ms%3000<1800 and bool(pairs)
        if hide:
            side='left' if int(ms//3000)%2 else 'right';component=component_for_side(g,r,side)
            dark=(g<=r['threshold']).astype(np.uint8);dark[:30]=0;dark[216:]=0
            _,labels=cv2.connectedComponents(dark,connectivity=8)
            hidden=cv2.dilate((labels==component).astype(np.uint8),np.ones((3,3),np.uint8))>0
            g=g.copy();g[hidden]=int(np.percentile(g,70))
        out=d.update(g,ms,r['session'],r['threshold'],True,pair_samples=[] if hide else pairs)
        if hide:
            errors=point_errors([[(p['left']+p['right'])/2,p['y']] for p in pairs if 80<=p['y']<=190],out['recommended_path_px'])
            if errors and max(errors)>25 and out['state']=='current_supported_model':
                reports.append(dict(frame=r['frame_id'],max_error=max(errors),result=out))
                assert cv2.imwrite(str(output/f'masked_{r["frame_id"]:04d}.jpg'),g)
    save(output/'errors.json',reports)
    print(json.dumps([dict(frame=r['frame'],max_error=r['max_error'],model=r['result']['model']) for r in reports],ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--limit',type=int,required=True)
    a=p.parse_args();run(a.output,a.limit)
