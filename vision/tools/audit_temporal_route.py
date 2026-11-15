"""T2交付审核：冻结字段／文件保护、逐帧差异、异常路线与中断组隔离。"""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_temporal_route import TemporalRouteDetector
from replay_recovery import load,spans
from review_recovery_inputs import digest,save
from validate_temporal_route import point_errors


def run(root,release_name='delivery',audit_name='delivery_audit'):
    """只审计新输出，不覆盖旧基线；保护失败立即列出并使检查失败。"""
    output=root/audit_name;output.mkdir(exist_ok=False)
    rows=load(root/release_name/'frames.jsonl')
    old=load(Path('testing/2026-11-08_vision_prediction_p1/release/frames.jsonl'))
    assert len(rows)==len(old)==1394
    assert all(all(r[k]==b[k] for k in b) for r,b in zip(rows,old))
    full=[r for r in rows if r['session']=='push_full_lap_0001']
    columns=['frame','capture_ms','R1_valid','C2_pair','P1_predict','T2_state','T2_node',
             'current_left_support','current_right_support','route_visible_points','C2_midpoint_distance_p95_px','C2_midpoint_distance_max_px','review_needed']
    differences=[];distances=[]
    for row in full:
        t=row['temporal_route'];pairs=row['recovery_observation']['pair_samples']
        truth=[[(p['left']+p['right'])/2,p['y']] for p in pairs]
        errors=point_errors(truth,t['recommended_path_px']);distances.extend(errors)
        visible=sum(0<=p[0]<320 and 0<=p[1]<240 for p in t['recommended_path_px'])
        differences.append(dict(frame=row['frame_id'],capture_ms=row['timestamp_ms'],R1_valid=row['valid'],
             C2_pair=bool(pairs),P1_predict=bool(row['prediction_observation']['estimated_pairs']),
             T2_state=t['state'],T2_node=t['map']['node'],
             current_left_support=t['model']['current_side_support'][0],
             current_right_support=t['model']['current_side_support'][1],route_visible_points=visible,
             C2_midpoint_distance_p95_px=float(np.percentile(errors,95)) if errors else None,
             C2_midpoint_distance_max_px=max(errors) if errors else None,
             review_needed=not pairs or not row['valid'] or t['state']!='current_supported_model'))
    with (output/'frame_comparison.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(differences)
    save(output/'largest_model_midpoint_differences.json',sorted([r for r in differences if r['C2_midpoint_distance_p95_px'] is not None],
            key=lambda r:r['C2_midpoint_distance_p95_px'],reverse=True)[:30])
    # 原始中断会话只取C2已隔离的20张，禁止纳入1394正式组或假称21张完整采集。
    interrupted=[r for r in load(Path('testing/2026-11-08_vision_recovery_c2/replay_accepted/frames.jsonl')) if r['evaluation_group']!='development']
    detector=TemporalRouteDetector();interrupted_results=[]
    for row in interrupted:
        assert digest(Path(row['source']))==row['source_sha256']
        result=detector.update(cv2.imread(row['source'],0),row['timestamp_ms'],row['session'],row['threshold'],False,
                       pair_samples=row['recovery_observation']['pair_samples'])
        interrupted_results.append(dict(source=row['source'],frame=row['frame_id'],timestamp_ms=row['timestamp_ms'],
               evaluation_group='IDE_interrupted_separate_not_complete',temporal_route=result))
    save(output/'interrupted_frames.json',interrupted_results)
    manifests=[Path('testing/2026-11-08_vision_recovery_c2/protected_before.json'),
               Path('testing/2026-11-08_vision_curve_c1/protected_hashes.json'),
               Path('testing/2026-11-08_vision_prediction_p1/release/protected_before.json'),
               Path('testing/2026-11-08_vision_board_prep/release/control_before.json')]
    protected=[];changed=[]
    for manifest in manifests:
        hashes=json.loads(manifest.read_text(encoding='utf-8'))
        differences_files=[p for p,h in hashes.items() if not Path(p).exists() or digest(Path(p))!=h]
        changed.extend(differences_files)
        protected.append(dict(manifest=manifest.as_posix(),unchanged=len(hashes)-len(differences_files),changed=differences_files))
    code=json.loads((root/release_name/'code_hashes.json').read_text(encoding='utf-8'))
    assert all(digest(Path('vision/src' if name=='offline_temporal_route.py' else 'vision/tools')/name)==h for name,h in code.items())
    mask_report=json.loads((root/'delivery_checks/checks.json').read_text(encoding='utf-8'))
    assert mask_report['code_sha256']==code['offline_temporal_route.py'] and mask_report['all_checks_passed']
    masked=json.loads((root/'delivery_checks/mask_errors.json').read_text(encoding='utf-8'))
    accepted_mask=[e for e in masked if e['state']!='map_prior_only']
    # 32px=输入宽度10%的开发级严重跳移门槛；只用于已知边隐藏代理检验，
    # 不将通过这个粗门槛称为像素精确、实际隐边正确或整车安全。
    bad_mask=sorted({e['frame'] for e in accepted_mask if e['center_distance_px']>32})
    mask_gate=dict(threshold_px=32,accepted_points=len(accepted_mask),
                   largest_distance_px=max(e['center_distance_px'] for e in accepted_mask),
                   bad_frames=bad_mask,passed=not bad_mask,
                   nominal_unknown_points=sum(e['state']=='map_prior_only' for e in masked))
    natural_bad=[r['frame'] for r in differences if r['T2_state']!='map_prior_only'
                  and r['C2_midpoint_distance_max_px'] is not None and r['C2_midpoint_distance_max_px']>32]
    summary=dict(passed=not changed and not bad_mask and not natural_bad,frames=len(rows),frozen_fields_unchanged=len(rows),
        groups=dict(Counter(r['session'] for r in rows)),protected=protected,
        T2_states=dict(Counter(r['temporal_route']['state'] for r in full)),
        C2_midpoint_distance_px=dict(points=len(distances),median=float(np.median(distances)),p95=float(np.percentile(distances,95)),max=max(distances)),
        route_visible_frames=sum(r['route_visible_points']>1 for r in differences),
        full_nominal_ground_route_frames=sum(bool(r['temporal_route']['recommended_path_ground_full']) for r in full),
        unsupported_spans=spans(full,lambda r:r['temporal_route']['state']=='map_prior_only'),
        interrupted_separate_frames=len(interrupted_results),
        held_known_midpoint_jump_gate=mask_gate,
        current_pair_contradiction_gate=dict(threshold_px=32,bad_frames=natural_bad,passed=not natural_bad),
        caveat='Model-vs-C2 midpoint distance includes intentional corner smoothing; not true invisible-edge or safe-driving accuracy.',
        branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        physical_actions=False,uploaded=False,global_summary_updated=False)
    save(output/'delivery_checks.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
    assert not changed and not bad_mask and not natural_bad


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--release-name',default='delivery');p.add_argument('--audit-name',default='delivery_audit')
    a=p.parse_args();run(a.root,a.release_name,a.audit_name)
