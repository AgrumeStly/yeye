"""P1单边预测实际回放及隐藏已知一侧的对照，不读未来帧或操作硬件。"""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_prediction import PredictionConfig,SingleBoundaryPredictor,extract_candidates
from replay_recovery import load,spans
from review_recovery_inputs import digest,save


def component_for_side(gray,row,side):
    """仅评估器确定要隐藏的已知组件；这些真值不传给预测器。"""
    mask=(gray<=row['threshold']).astype(np.uint8);mask[:30]=0;mask[216:]=0
    _,labels=cv2.connectedComponents(mask,connectivity=8)
    inset=-1 if side=='left' else 1
    votes=[int(labels[p['y'],p[side]+inset]) for p in row['recovery_observation']['pair_samples']]
    return max(set(votes),key=votes.count)


def metrics(errors):
    """像素误差是隐藏已知边的模型检验，不是实际画外边界真值。"""
    if not errors:return dict(points=0)
    edge=[e['edge_error_px'] for e in errors];center=[e['center_error_px'] for e in errors]
    return dict(points=len(errors),frames=len({(e['session'],e['frame']) for e in errors}),
        edge_px=dict(mean=float(np.mean(edge)),median=float(np.median(edge)),p95=float(np.percentile(edge,95)),max=float(np.max(edge))),
        center_px=dict(mean=float(np.mean(center)),median=float(np.median(center)),p95=float(np.percentile(center,95)),max=float(np.max(center))),
        age_ms=dict(max=max(e['age_ms'] for e in errors)),
        inferred_role_errors=sum(not e['role_correct'] for e in errors))


def run(output,ttl):
    """1394张正式素材原样回归；20张中断组不混入，旧325无真实时钟不预测。"""
    output.mkdir(parents=True,exist_ok=False)
    config=PredictionConfig(max_width_age_ms=ttl)
    source=Path('testing/2026-11-08_vision_recovery_c2/replay_accepted/frames.jsonl')
    originals=load(source);rows=[r for r in originals if r['evaluation_group']=='development']
    protected={r['source']:r['source_sha256'] for r in rows}
    for p in [source,Path('vision/src/offline_boundary.py'),Path('vision/src/offline_curve.py'),Path('vision/src/offline_recovery.py')]:
        protected[p.as_posix()]=digest(p)
    save(output/'protected_before.json',protected)
    save(output/'parameters.json',dict(prediction=config.__dict__,mask_test=dict(period_ms=4000,hidden_phase_ms=[2000,3000],
        side='alternates_by_time_window',truth='current C2 accepted pair, held out of predictor',blind=False)))
    save(output/'workspace.json',dict(branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
         head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
         status=subprocess.check_output(['git','status','--short'],text=True,encoding='utf-8')))
    real=SingleBoundaryPredictor(config);masked=SingleBoundaryPredictor(config)
    results=[];errors=[];summaries=[];masked_frames=0;masked_output_frames=0
    with (output/'frames.jsonl').open('w',encoding='utf-8') as stream:
        for row in rows:
            gray=cv2.imread(row['source'],cv2.IMREAD_GRAYSCALE)
            assert gray is not None and digest(Path(row['source']))==row['source_sha256']
            candidates=extract_candidates(gray,row['threshold'])
            obs=row['recovery_observation'];timestamp=row['timestamp_ms'];session=row['session']
            prediction=real.update(timestamp,session,obs['pair_samples'],candidates,obs['edge_jump'])
            record=dict(row);record['prediction_observation']=prediction
            stream.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n');results.append(record)
            # 人工隐藏只作用于当前候选和双边输入，不向预测器传隐藏侧真值。
            hidden=timestamp is not None and 2000<=timestamp%4000<3000 and bool(obs['pair_samples'])
            mask_candidates=candidates;direct=obs['pair_samples'];side=None
            if hidden:
                side='right' if int(timestamp//4000)%2==0 else 'left'
                component=component_for_side(gray,row,side)
                mask_candidates=[c for c in candidates if c['component']!=component]
                direct=[];masked_frames+=1
            output_mask=masked.update(timestamp,session,direct,mask_candidates,False if hidden else obs['edge_jump'])
            if hidden and output_mask['estimated_pairs']:
                masked_output_frames+=1
                truth={p['y']:p for p in obs['pair_samples']}
                for point in output_mask['estimated_pairs']:
                    if point['y'] not in truth:continue
                    ground=truth[point['y']];role_correct=point['estimated_role']==side
                    edge_error=abs(point[side]-ground[side])
                    center_error=abs((point['left']+point['right'])/2-(ground['left']+ground['right'])/2)
                    errors.append(dict(session=session,frame=row['frame_id'],capture_ms=timestamp,y=point['y'],
                        hidden_side=side,role_correct=role_correct,age_ms=point['model_age_ms'],
                        edge_error_px=edge_error,center_error_px=center_error,
                        predicted=dict(left=point['left'],right=point['right']),truth=ground))
    for session in dict.fromkeys(r['session'] for r in results):
        group=[r for r in results if r['session']==session]
        summaries.append(dict(session=session,frames=len(group),
             direct_pairs=sum(bool(r['recovery_observation']['pair_samples']) for r in group),
             prediction_frames=sum(bool(r['prediction_observation']['estimated_pairs']) for r in group),
             predicted_without_any_C2_pair=sum(bool(r['prediction_observation']['estimated_pairs']) and not r['recovery_observation']['pair_samples'] for r in group),
             predicted_y120_when_R1_invalid=sum(r['prediction_observation']['estimated_y120_px'] is not None and not r['valid'] for r in group),
             prediction_spans=spans(group,lambda r:bool(r['prediction_observation']['estimated_pairs'])),
             unknown_without_prediction=spans(group,lambda r:not r['recovery_observation']['pair_samples'] and not r['prediction_observation']['estimated_pairs']),
             states=dict(Counter(r['prediction_observation']['reason'] or r['prediction_observation']['state'] for r in group))))
    save(output/'mask_errors.json',errors)
    save(output/'summary.json',dict(groups=summaries,masked_frames=masked_frames,masked_output_frames=masked_output_frames,
         mask_errors_all=metrics(errors),
         mask_errors_moving_two_lap=metrics([e for e in errors if e['session']=='push_full_lap_0001' and e['capture_ms']<=125000]),
         mask_errors_corner=metrics([e for e in errors if e['session']=='push_corner_77_0001' and e['capture_ms']<=9000]),
         scope='Development only. Known-edge hiding is a proxy; actual missing boundaries have no pixel truth. No control acceptance.'))
    save(output/'validation.json',dict(passed=True,protected_unchanged=len(protected),
          actual_frames=len(results),predictions_labelled_separately=True,
          protocol_valid_always_false=all(not r['prediction_observation']['protocol_valid'] for r in results),
          max_observed_model_age_ms=max([p['model_age_ms'] for r in results for p in r['prediction_observation']['estimated_pairs']] or [0]),
          original_hashes_unchanged=all(digest(Path(p))==h for p,h in protected.items())))
    assert all(digest(Path(p))==h for p,h in protected.items())
    (output/'source_snapshot').mkdir()
    for path in [Path('vision/src/offline_prediction.py'),Path(__file__)]:shutil.copy2(path,output/'source_snapshot'/path.name)
    save(output/'code_hashes.json',{p.name:digest(p) for p in (output/'source_snapshot').iterdir()})
    print(json.dumps(dict(groups=[{k:g[k] for k in ['session','prediction_frames','predicted_without_any_C2_pair','predicted_y120_when_R1_invalid']} for g in summaries],
          all=metrics(errors),moving=metrics([e for e in errors if e['session']=='push_full_lap_0001' and e['capture_ms']<=125000])),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ttl-ms',type=int,default=1500)
    args=parser.parse_args();run(args.output,args.ttl_ms)
