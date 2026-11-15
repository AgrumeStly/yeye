"""T2可复现离线回放：冻结基线对照、真实时间、几何诊断与来源保护。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from offline_temporal_route import TemporalRouteDetector
from replay_recovery import load, spans
from review_recovery_inputs import digest, save


def run(output, session=None, limit=None, history=True, use_map=True):
    """输出必须新建；历史按会话清空，只有主控确认的整圈会话初始化地图。"""
    output.mkdir(parents=True, exist_ok=False)
    source = Path('testing/2026-11-08_vision_prediction_p1/release/frames.jsonl')
    inputs = load(source)
    inputs = [r for r in inputs if (session is None or r['session'] == session)]
    if limit:
        inputs = inputs[:limit]
    detector = TemporalRouteDetector(use_history=history, use_map=use_map)
    finish_rows=load(Path('testing/2026-11-08_vision_finish_f1/release/frames.jsonl'))
    finish_lookup={(r['session'],r['frame_id']):r['finish'] for r in finish_rows}
    save(output/'parameters.json', detector.parameters())
    save(output/'operator_confirmation.json', dict(date='2026-11-09',
        initial='entire footprint on right of dashed start line, heading left, clockwise',
        layout='Figure 1 five-node order confirmed', recorded_laps=2, competition_laps=1,
        final='entire footprint on left of finish line; operator statement, camera cannot verify rear',
        runtime_note='lap count and frame IDs not used as image detection criteria'))
    protected = {r['source']:r['source_sha256'] for r in inputs}
    for p in [source, Path('vision/src/offline_boundary.py'), Path('vision/src/offline_curve.py'),
              Path('vision/src/offline_recovery.py'), Path('vision/src/offline_prediction.py')]:
        protected[p.as_posix()] = digest(p)
    save(output/'protected_before.json', protected)
    save(output/'workspace.json', dict(branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        status=subprocess.check_output(['git','status','--short'],encoding='utf-8',text=True)))
    rows = []
    with (output/'frames.jsonl').open('w',encoding='utf-8') as stream:
        for i, row in enumerate(inputs):
            assert digest(Path(row['source'])) == row['source_sha256']
            image = cv2.imread(row['source'],cv2.IMREAD_GRAYSCALE)
            start = time.perf_counter_ns()
            finish=finish_lookup[(row['session'],row['frame_id'])]
            finish_id=finish['event_id'] if finish['event']=='finish_line_seen' else None
            result = detector.update(image,row['timestamp_ms'],row['session'],row['threshold'],
                       map_initialized=row['session']=='push_full_lap_0001',
                       pair_samples=row['recovery_observation']['pair_samples'],finish_event=finish_id)
            record = dict(row); record['temporal_route'] = result
            record['t2_pc_algorithm_ms'] = (time.perf_counter_ns()-start)/1e6
            stream.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n'); rows.append(record)
            if (i+1)%100 == 0:
                print(f'{i+1}/{len(inputs)}',flush=True)
    groups = []
    for key in dict.fromkeys(r['session'] for r in rows):
        group = [r for r in rows if r['session']==key]
        results = [r['temporal_route'] for r in group]
        timing = [r['t2_pc_algorithm_ms'] for r in group]
        groups.append(dict(session=key,frames=len(group), R1_valid=sum(r['valid'] for r in group),
            C2_pair_frames=sum(bool(r['recovery_observation']['pair_samples']) for r in group),
            P1_estimated_frames=sum(bool(r['prediction_observation']['estimated_pairs']) for r in group),
            states=dict(Counter(r['state'] for r in results)),
            motion_available=sum(r['motion']['available'] for r in results),
            last_yaw_total_deg=results[-1]['yaw_total_deg'],
            current_supported_without_C2=sum(r['temporal_route']['state']=='current_supported_model' and not r['recovery_observation']['pair_samples'] for r in group),
            unverified_prior_spans=spans(group,lambda r:r['temporal_route']['state']=='map_prior_only'),
            map_transitions=[dict(frame=r['frame_id'],ms=r['timestamp_ms'],**r['temporal_route']['map'])
                for j,r in enumerate(group) if j==0 or
                r['temporal_route']['map']['node']!=group[j-1]['temporal_route']['map']['node'] or
                r['temporal_route']['map']['lap_observation']!=group[j-1]['temporal_route']['map']['lap_observation']],
            pc_algorithm_ms=dict(median=float(np.median(timing)),p95=float(np.percentile(timing,95)),max=max(timing)),
            limitation='model support counts are not accuracy, map correspondence or control acceptance'))
    save(output/'summary.json',dict(groups=groups, total_frames=len(rows),
          note='Both laps are development data. Metric plane outside central 20-60cm is an unvalidated model.'))
    snap=output/'source_snapshot'; snap.mkdir()
    for path in [Path('vision/src/offline_temporal_route.py'),Path(__file__)]:
        shutil.copy2(path,snap/path.name)
    save(output/'code_hashes.json',{p.name:digest(p) for p in snap.iterdir()})
    unchanged=all(digest(Path(p))==h for p,h in protected.items()); assert unchanged
    save(output/'validation.json',dict(passed=True,frames=len(rows),protected_unchanged=len(protected),
         all_protocol_invalid=all(not r['temporal_route']['protocol_valid'] for r in rows),
         fixed_reference_fields_preserved=True, source_sha256=digest(source),
         description='Structural/protection checks only, not evidence of route correctness'))
    print(json.dumps(groups,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True); parser.add_argument('--session')
    parser.add_argument('--limit',type=int);parser.add_argument('--no-history',action='store_true')
    parser.add_argument('--no-map',action='store_true');args=parser.parse_args()
    run(args.output,args.session,args.limit,not args.no_history,not args.no_map)
