"""T2有意义的模型检查与遮挡对照；检查结果不等同实车正确率。"""

import argparse
import json
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_temporal_route import GroundMotion,GroundProjection,TemporalRouteConfig,TemporalRouteDetector
from replay_prediction import component_for_side
from replay_recovery import load
from review_recovery_inputs import digest,save


def point_errors(truth,path):
    """逐点到预测折线的二维像素距离；不强迫弯道路线为单值x(y)。"""
    if len(path)<2 or not truth:return []
    p=np.asarray(truth,float);a=np.asarray(path[:-1],float);b=np.asarray(path[1:],float)
    ab=b-a;den=np.maximum(1e-8,np.sum(ab*ab,axis=1))
    t=np.clip(np.sum((p[:,None]-a[None])*ab[None],axis=2)/den[None],0,1)
    projection=a[None]+t[...,None]*ab[None]
    return np.min(np.linalg.norm(p[:,None]-projection,axis=2),axis=1).tolist()


def run(output,mask=False):
    """先验证时间／空白／已知地面变换；遮挡仅在当前图像进行，不给隐藏真值。"""
    output.mkdir(parents=True,exist_ok=False);checks=[]
    def check(name,value,details=None):
        checks.append(dict(name=name,passed=bool(value),details=details))
    projection=GroundProjection();config=TemporalRouteConfig()
    samples=projection.ground([[159.5,198],[159.5,113],[159.5,73]])
    check('central_calibration_three_points',np.max(np.abs(samples[:,1]-[20,40,60]))<1e-6)
    back=projection.image(projection.ground([[50,100],[200,180],[159.5,146]]))
    check('projection_roundtrip',np.max(np.abs(back-[[50,100],[200,180],[159.5,146]]))<1e-6)
    rows=load(Path('testing/2026-11-08_vision_prediction_p1/release/frames.jsonl'))
    full=[r for r in rows if r['session']=='push_full_lap_0001']
    gray=cv2.imread(full[0]['source'],cv2.IMREAD_GRAYSCALE)
    motion=GroundMotion(projection,config);motion.update(gray);matrix,diag=motion.update(gray)
    check('same_image_motion_zero',matrix is not None and np.max(np.abs(matrix-np.eye(3)))<.01,diag)
    angle=np.deg2rad(3.);known=np.array([[np.cos(angle),-np.sin(angle),1.],
                     [np.sin(angle),np.cos(angle),-2.],[0.,0.,1.]])
    warped=cv2.warpPerspective(gray,projection.inverse@known@projection.matrix,(320,240),borderValue=160)
    motion.reset();motion.update(gray);estimated,diag=motion.update(warped)
    check('synthetic_known_ground_motion',estimated is not None and abs(diag['yaw_deg']-3)<1. and np.linalg.norm(estimated[:2,2]-known[:2,2])<2.,diag)
    d=TemporalRouteDetector();r1=d.update(gray,0,'a',96,True)
    r2=d.update(gray,200,'a',96,True)
    check('same_frame_history_used',r2['history_frames']==2 and r2['motion']['available'])
    r3=d.update(gray,1200,'a',96,True)
    check('gap_resets_and_revokes_start_map',r3['time_reset']=='clock_or_capture_gap_reset' and not r3['map']['initialized'] and r3['history_frames']==1)
    r4=d.update(gray,1100,'a',96,True)
    check('backwards_clock_resets',r4['time_reset']=='clock_or_capture_gap_reset' and not r4['map']['initialized'])
    r5=d.update(gray,None,'a',96,True)
    check('missing_clock_no_history_or_map',r5['history_frames']==0 and not r5['map']['initialized'])
    r6=d.update(gray,0,'b',96,True)
    check('new_session_resets',r6['time_reset']=='session_reset' and r6['map']['passed_node_count']==0)
    for value in [0,255]:
        result=TemporalRouteDetector().update(np.full_like(gray,value),0,'blank',96,False)
        check(f'blank_{value}_not_current_road',result['state']=='map_prior_only' and not result['protocol_valid'],result['state'])
    negative=next(r for r in rows if r['session']=='v03_center_0012')
    image=cv2.imread(negative['source'],cv2.IMREAD_GRAYSCALE)
    d=TemporalRouteDetector();d.update(gray,0,'text',96,False)
    result=d.update(image,200,'text',negative['threshold'],False)
    check('real_text_not_current_road',result['state']!='current_supported_model',result['model'])
    # 相同前缀单独重放，检验状态不依赖尾部帧或总帧数。
    def prefix():
        detector=TemporalRouteDetector();result=[]
        for row in full[:8]:
            cv2.setRNGSeed(123)
            result.append(detector.update(cv2.imread(row['source'],0),row['timestamp_ms'],'causal',row['threshold'],True,
                       pair_samples=row['recovery_observation']['pair_samples']))
        return result
    first=prefix();second=prefix()
    check('same_prefix_deterministic',first==second)
    errors=[];masked_count=0
    if mask:
        detector=TemporalRouteDetector()
        for i,row in enumerate(full):
            gray=cv2.imread(row['source'],0);pairs=row['recovery_observation']['pair_samples'];ms=row['timestamp_ms']
            hide=1200<=ms%3000<1800 and bool(pairs)
            hidden_side='left' if int(ms//3000)%2 else 'right'
            if hide:
                component=component_for_side(gray,row,hidden_side)
                dark=(gray<=row['threshold']).astype(np.uint8);dark[:30]=0;dark[216:]=0
                _,labels=cv2.connectedComponents(dark,connectivity=8)
                mask_image=cv2.dilate((labels==component).astype(np.uint8),np.ones((3,3),np.uint8))>0
                gray=gray.copy();gray[mask_image]=int(np.percentile(gray,70));masked_count+=1
            result=detector.update(gray,ms,row['session'],row['threshold'],True,
                       pair_samples=[] if hide else pairs)
            if hide:
                truth=[[(p['left']+p['right'])/2,p['y']] for p in pairs if 80<=p['y']<=190]
                distances=point_errors(truth,result['recommended_path_px'])
                for p,error in zip(truth,distances):
                    errors.append(dict(frame=row['frame_id'],capture_ms=ms,hidden_side=hidden_side,
                        y=p[1],center_distance_px=error,state=result['state'],map_node=result['map']['node']))
            if (i+1)%150==0:print(f'mask {i+1}/732',flush=True)
        save(output/'mask_errors.json',errors)
    values=[e['center_distance_px'] for e in errors]
    report=dict(checks=checks,all_checks_passed=all(c['passed'] for c in checks),masked_frames=masked_count,
        masked_points=len(values),center_distance_px=dict(median=float(np.median(values)),p95=float(np.percentile(values,95)),max=max(values)) if values else None,
        mask_scope='Known C2 midpoint hiding proxy; no hidden GT sent to predictor. Not actual missing-boundary truth.',
        code_sha256=digest(Path('vision/src/offline_temporal_route.py')))
    report['mask_by_state']={state:dict(points=len([e for e in errors if e['state']==state]),
          p95_px=float(np.percentile([e['center_distance_px'] for e in errors if e['state']==state],95)))
          for state in {e['state'] for e in errors}}
    save(output/'checks.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
    if not report['all_checks_passed']:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mask',action='store_true');a=p.parse_args();run(a.output,a.mask)
