"""P1独立预测状态、因果性、误差及冻结输入保护；不会访问设备。"""

import copy
import json
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_prediction import SingleBoundaryPredictor,extract_candidates
from offline_boundary import BoundaryDetector
from vision_protocol import RecognitionSender
from replay_recovery import load
from review_recovery_inputs import digest,save


def run(root):
    """几何合成仅验证语义；真实预测正确性仍由隐藏边评估和目视复核限定。"""
    checks=[]
    def check(name,value):
        assert value,name
        checks.append(name)
    pairs=[dict(y=y,left=80-(y-65)//3,right=180+(y-65)//3) for y in range(65,216,5)]
    def candidate(side,component=1,shift=0):
        return dict(component=component,role_hypothesis=side,
                    points=[dict(y=p['y'],x=p[side]+shift) for p in pairs])
    left=candidate('left');right=candidate('right',2)
    predictor=SingleBoundaryPredictor()
    predictor.update(0,'A',pairs,[left,right])
    result=predictor.update(100,'A',[],[left])
    check('single_current_band_produces_separate_estimate',result['state']=='historical_geometry_prediction' and result['inferred_role']=='left')
    check('hidden_edge_matches_synthetic_width',[dict(y=p['y'],left=p['left'],right=p['right']) for p in result['estimated_pairs']]==pairs)
    check('estimated_center_is_pair_midpoint',all(c['x']==(p['left']+p['right'])/2 for c,p in zip(result['estimated_centerline'],result['estimated_pairs'])))
    check('prediction_never_protocol_valid',not result['protocol_valid'] and not result['control_ready'])
    check('prediction_has_independent_y120_value',result['estimated_y120_px'] is not None)
    for t in range(200,1501,100):result=predictor.update(t,'A',[],[left])
    check('single_band_does_not_refresh_width_age',result['model_age_max_ms']==1500)
    result=predictor.update(1600,'A',[],[left])
    check('hard_expiry_at_1501_or_later',not result['estimated_pairs'] and result['reason']=='no_unexpired_width_model')
    predictor.update(1700,'A',pairs,[left,right]);result=predictor.update(1800,'B',[],[left])
    check('session_reset_clears_geometry',not result['estimated_pairs'] and result['time_reset']=='session_changed')
    predictor.update(1900,'B',pairs,[left,right]);result=predictor.update(1899,'B',[],[left])
    check('clock_reversal_clears',not result['estimated_pairs'] and result['time_reset']=='clock_not_increasing')
    predictor.update(2000,'B',pairs,[left,right]);result=predictor.update(2000,'B',[],[left])
    check('duplicate_time_clears',not result['estimated_pairs'])
    predictor.update(2100,'B',pairs,[left,right]);result=predictor.update(2900,'B',[],[left])
    check('capture_gap_clears',result['time_reset']=='capture_gap_timeout' and not result['estimated_pairs'])
    for stamp in (None,-1,True,float('nan'),float('inf')):
        result=predictor.update(stamp,'B',pairs,[left,right])
        check('bad_time_'+str(stamp),not result['estimated_pairs'] and result['time_reset']=='missing_real_capture_time')
    predictor.update(3000,'B',pairs,[left,right]);result=predictor.update(3100,'B',[],[left],True)
    check('direct_edge_jump_revokes_old_width',not result['estimated_pairs'] and result['time_reset']=='C2_direct_edge_jump')
    predictor.update(3200,'B',pairs,[left,right]);result=predictor.update(3300,'B',[],[candidate('left',1),candidate('left',3,3)])
    check('ambiguous_band_role_refused',not result['estimated_pairs'])
    predictor.update(3400,'B',pairs,[left,right]);result=predictor.update(3500,'B',[],[candidate('left',1),candidate('right',1)])
    check('one_band_two_faces_not_two_boundaries',not result['estimated_pairs'])
    predictor.update(3600,'B',pairs,[left,right]);result=predictor.update(3700,'B',[],[candidate('left',1,100)])
    check('sudden_single_band_shift_refused',not result['estimated_pairs'])
    predictor.update(3800,'B',pairs,[left,right]);result=predictor.update(3900,'B',[],[])
    check('no_current_band_no_width_only_fill',not result['estimated_pairs'])
    original=copy.deepcopy(pairs);predictor.update(4000,'B',pairs,[left,right])
    check('caller_geometry_not_modified',pairs==original)
    # 水平镜像只验证左右模型对称，不当作新采到的独立左弯。
    mirrored=[dict(y=p['y'],left=319-p['right'],right=319-p['left']) for p in pairs]
    mirror_right=dict(component=1,role_hypothesis='right',points=[dict(y=p['y'],x=p['right']) for p in mirrored])
    normal=SingleBoundaryPredictor();mirror=SingleBoundaryPredictor()
    normal.update(0,'mirror',pairs,[left,right]);mirror.update(0,'mirror',mirrored,[])
    a=normal.update(100,'mirror',[],[left]);b=mirror.update(100,'mirror',[],[mirror_right])
    check('mirror_missing_side_symmetric',all(abs(x['x']+y['x']-319)<1e-9 for x,y in zip(a['estimated_centerline'],b['estimated_centerline'])))
    short=SingleBoundaryPredictor();long=SingleBoundaryPredictor()
    sequence=[(0,pairs,[left,right]),(100,[],[left]),(200,[],[left]),(300,[],[])]
    prefix=[short.update(t,'prefix',p,c) for t,p,c in sequence]
    complete=[long.update(t,'prefix',p,c) for t,p,c in sequence+[(400,pairs,[left,right])]]
    check('causal_prefix_future_cannot_change_output',prefix==complete[:len(prefix)])
    rows=load(root/'release/frames.jsonl')
    expected={(r['session'],r['frame_id']):r for r in load(Path('testing/2026-11-08_vision_recovery_c2/replay_accepted/frames.jsonl'))}
    old_sender=RecognitionSender(allow_valid_path=True);new_sender=RecognitionSender(allow_valid_path=True)
    preserved=0
    for row in rows:
        prior=expected[(row['session'],row['frame_id'])]
        for key,value in prior.items():assert row[key]==value,(row['source'],key)
        assert old_sender.path(prior,processing_ms=20,source_age_ms=0)==new_sender.path(row,processing_ms=20,source_age_ms=0)
        for point in row['prediction_observation']['estimated_pairs']:
            assert 0<=point['model_age_ms']<=1500
            assert point['width_source_ms']<=row['timestamp_ms']
        preserved+=1
    check('1394_all_C2_original_fields_unchanged',preserved==1394)
    check('predictions_do_not_change_protocol_packets',True)
    check('old_no_timestamp_no_prediction',all(not r['prediction_observation']['estimated_pairs'] for r in rows if r['session']=='d01_straight_run01'))
    check('static_single_band_and_text_no_new_prediction',all(not r['prediction_observation']['estimated_pairs'] for r in rows if r['session'] in ('v03_center_0009','v03_center_0012')))
    seed=cv2.imread('vision/data/captures/final_mount_20261108/v03_center_0002/data_0001.jpg',0)
    seed_result=BoundaryDetector().detect(seed)
    for session in ('v03_center_0009','v03_center_0012'):
        test=SingleBoundaryPredictor();test.update(0,'negative',seed_result['pair_samples'],extract_candidates(seed,seed_result['threshold']))
        gray=cv2.imread('vision/data/captures/final_mount_20261108/'+session+'/data_0001.jpg',0)
        before=gray.copy();base=BoundaryDetector().detect(gray)
        result=test.update(100,'negative',[],extract_candidates(gray,base['threshold']))
        check('real_failure_after_seed_'+session,not result['estimated_pairs'])
        check('real_image_unmodified_'+session,np.array_equal(gray,before))
    protected=json.loads((root/'release/protected_before.json').read_text(encoding='utf-8'))
    check('1394_sources_and_frozen_C2_preserved',all(digest(Path(p))==h for p,h in protected.items()))
    save(root/'checks.json',dict(passed=True,checks=checks,formal_frames=1394,
         no_future_inputs=True,unchanged_protocol=True,
         actual_missing_edge_accuracy='not measurable without truth; see separate proxy mask_errors',
         source_hash=digest(Path('vision/src/offline_prediction.py'))))
    print(dict(checks=len(checks),formal_frames=preserved))


if __name__=='__main__':run(Path('testing/2026-11-08_vision_prediction_p1'))
