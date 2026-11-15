"""终点状态机、真实负例、全序列事件及因果性检查；不会连接设备。"""

import json
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_finish import FinishDetector
from offline_boundary import BoundaryDetector
from replay_recovery import load
from review_recovery_inputs import digest, save


def run(output):
    """合成时序只验证状态逻辑，不作为实拍终点性能。"""
    results=load(output/'frames.jsonl')
    checks=[]
    def check(name,value):
        assert value,name
        checks.append(name)
    def observation(y=None):
        return dict(visible=y is not None,y=y,dashes=[],corridor=None,reason=None)
    f=FinishDetector()
    start=[f.update(observation(100),t,'synthetic') for t in (0,500,1000,1500,2000)]
    check('visible_start_line_never_triggers',all(r['state']=='start_line_suppressed' and not r['event'] for r in start))
    for t in (2500,3000,3500,4000):f.update(observation(),t,'synthetic')
    check('arm_only_after_real_clear_time',f.armed)
    a=f.update(observation(90),4100,'synthetic')
    b=f.update(observation(92),4200,'synthetic')
    c=f.update(observation(96),4300,'synthetic')
    check('two_frames_not_enough_without_150ms',not a['event'] and not b['event'] and c['event']=='finish_line_seen')
    d=f.update(observation(120),4400,'synthetic')
    check('same_event_no_duplicate',not d['event'] and d['event_id']==c['event_id'])
    f.update(observation(),4500,'synthetic')
    d=f.update(observation(130),4600,'synthetic')
    check('short_occlusion_merges_event',not d['event'] and d['event_id']==1)
    d=f.update(observation(190),4900,'synthetic')
    check('direct_image_gate_only_once',d['gate_event']=='passed_image_y180_gate')
    d=f.update(observation(195),5000,'synthetic')
    check('image_gate_no_repeat',not d['gate_event'])
    f.update(observation(),5200,'synthetic')
    d=f.update(observation(),5600,'synthetic')
    check('absence_requires_600ms',not d['passage_event'])
    d=f.update(observation(),5800,'synthetic')
    check('absence_is_not_whole_vehicle_crossing',d['passage_event']=='near_marker_then_unobserved' and d['whole_vehicle_crossed'] is None and not d['automatic_stop'])
    f.update(observation(),6300,'synthetic');f.update(observation(),6800,'synthetic')
    f.update(observation(80),6900,'synthetic')
    d=f.update(observation(100),7100,'synthetic')
    check('rearm_after_clear_second_id',d['event']=='finish_line_seen' and d['event_id']==2)
    f.update(observation(190),7600,'synthetic')
    d=f.update(observation(),8100,'synthetic',False)
    d=f.update(observation(),8600,'synthetic',False)
    check('road_loss_does_not_imply_passage',not d['passage_event'] and not d['armed'])
    d=f.update(observation(100),10000,'synthetic')
    check('gap_timeout_returns_start_guard',d['reset_reason']=='capture_gap_timeout' and d['state']=='start_line_suppressed')
    d=f.update(observation(100),9999,'synthetic')
    check('time_reverse_clears',d['reset_reason']=='clock_not_increasing' and not d['event'])
    d=f.update(observation(100),9999,'synthetic')
    check('duplicate_time_clears',d['reset_reason']=='clock_not_increasing')
    d=f.update(observation(100),10001,'new_session')
    check('session_clears',d['reset_reason']=='session_changed' and not d['event'])
    for t in (None,float('nan'),True,-1):
        check('bad_time_'+str(t),f.update(observation(100),t,'bad')['state']=='unknown')
    blank=np.full((240,320),230,np.uint8)
    road=BoundaryDetector()
    for name,g in [('white',blank),('black',np.zeros_like(blank)),('missing',None)]:
        check('spatial_negative_'+name,not f.observe(g,road.detect(g))['visible'])
    two=[r for r in results if r['session']=='push_full_lap_0001']
    check('both_real_passes_seen_once',[r['frame_id'] for r in two if r['finish']['event']]==[409,571])
    check('only_reviewed_finish_windows_have_spatial_detections',all(408<=r['frame_id']<=422 or 570<=r['frame_id']<=581
          for r in two if r['finish']['observation']['visible']))
    check('real_curve_and_static_no_finish_false_positive',all(not r['finish']['observation']['visible']
          for r in results if r['session'] not in ('d01_straight_run01','push_full_lap_0001')))
    check('all_frames_whole_vehicle_unknown',all(r['finish']['whole_vehicle_crossed'] is None for r in results))
    prior=FinishDetector();short=FinishDetector()
    observations=[(observation(),t) for t in (0,500,1000,1500)]+[(observation(100),1700),(observation(110),1900)]
    prefix=[short.update(o,t,'prefix') for o,t in observations]
    full=[prior.update(o,t,'prefix') for o,t in observations+[(observation(200),2400)]]
    check('causal_prefix_no_future',prefix==full[:len(prefix)])
    protected=json.loads(Path('testing/2026-11-08_vision_recovery_c2/protected_before.json').read_text(encoding='utf-8'))
    check('originals_frozen_sources_old_evidence_unchanged',all(digest(Path(p))==h for p,h in protected.items()))
    save(output.parent/'validation.json',dict(passed=True,checks=checks,formal_frames=len(results),
        original_protected_files=len(protected),manual_review=dict(
            reviewed_raw='recovery_c2/finish_raw_01..04: initial1..9,405..426,569..586',
            reviewed_all_positive_overlays='accepted/detections_01..02 and identical release, including old234',
            false_events_on_two_lap=0,duplicate_events=0,
            missed_visible_frames=['407/568/569: insufficient road/ROI/shape support','579..581: near-bottom support insufficient'],
            scope='visual agent review, same-session development; not independent reliability or automatic parking')))
    print(json.dumps(dict(checks=len(checks),frames=len(results))))


if __name__=='__main__':
    run(Path('testing/2026-11-08_vision_finish_f1/release'))
