"""C2全批回放、逐字段冻结对照、采集时序及连续失效统计；无硬件操作。"""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from offline_recovery import RecoveryDetector
from review_recovery_inputs import ROOT, digest, save


def load(path):
    """JSONL逐行读取，读取错误立即失败，不隐去坏记录。"""
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def spans(rows, predicate):
    """报告首末采样跨度及到下一恢复观测的时长，均使用原软件毫秒。

    不把首末帧间隔称为实际曝光或精确失效起止；两者边界在相邻采样间。
    无真实时间的旧325张只报帧区间，不人为填入固定帧率。
    """
    result, current = [], []
    for row in rows+[None]:
        if row is not None and predicate(row):
            current.append(row)
        elif current:
            first, last = current[0], current[-1]
            a, b = first['timestamp_ms'], last['timestamp_ms']
            result.append(dict(first_frame=first['frame_id'], last_frame=last['frame_id'], frames=len(current),
                 first_ms=a, last_ms=b, sample_span_ms=b-a if a is not None and b is not None else None,
                 recovered_frame=row['frame_id'] if row else None,
                 recovered_ms=row['timestamp_ms'] if row else None,
                 until_recovery_ms=row['timestamp_ms']-a if row and a is not None else None))
            current = []
    return result


def paint(row, image):
    """只在副本绘制C2实测内缘／中点；历史不画成路径。"""
    obs = row['recovery_observation']
    canvas = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    for p in obs['pair_samples']:
        for side, color in [('left', (0, 200, 0)), ('right', (0, 100, 255))]:
            cv2.circle(canvas, (p[side], p['y']), 2, color, -1)
        cv2.circle(canvas, (round((p['left']+p['right'])/2), p['y']), 1, (255, 255, 0), -1)
    canvas = cv2.copyMakeBorder(canvas, 0, 96, 0, 0, cv2.BORDER_CONSTANT)
    lines = [f"{row['frame_id']} t={row['timestamp_ms']}ms R1={row['valid']}",
             f"C2 y={obs['y_range']} turn={obs['turn_hint']}",
             f"{obs['temporal_state']} / {obs['advice']}",
             f"history={obs['historical']['turn_hint']} (not path)", 'full turn / control ready: NO']
    for i, line in enumerate(lines):
        cv2.putText(canvas, line, (3, 257+i*18), cv2.FONT_HERSHEY_SIMPLEX, .34, (255,255,255), 1)
    return canvas


def run(output):
    """1394张正式开发回归与20张IDE中断组隔离回放，输出拒绝覆盖。"""
    output.mkdir(parents=True, exist_ok=False)
    prior_paths = [Path('testing/2026-11-08_vision_curve_c1/frames.jsonl'),
                   Path('testing/2026-11-08_push_corner_review/replay_c1/frames.jsonl'),
                   Path('testing/2026-11-08_two_lap_review/replay_c1/frames.jsonl')]
    expected = [r for path in prior_paths for r in load(path)]
    assert len(expected) == 1394
    folders = list(dict.fromkeys(Path(r['source']).parent for r in expected))
    interrupted = Path('vision/data/captures/final_mount_20261108/push_corner_77_0002')
    expected_map = {(Path(r['source']).parent.name, Path(r['source']).name): r for r in expected}
    detector = RecoveryDetector()
    save(output/'parameters.json', detector.parameters())
    snap = output/'source_snapshot'
    snap.mkdir()
    for path in [Path('vision/src/offline_recovery.py'), Path(__file__),
                 Path('vision/src/offline_boundary.py'), Path('vision/src/offline_curve.py')]:
        shutil.copy2(path, snap/path.name)
    save(output/'code_hashes.json', {p.name:digest(p) for p in snap.iterdir()})
    rows, summaries, compared = [], [], 0
    for folder in folders+[interrupted]:
        detector.reset()
        metadata = {r['file']:r for r in load(folder/'frames.jsonl')} if (folder/'frames.jsonl').exists() else {}
        group = []
        video_dir = output/'overlays'/folder.name
        video_dir.mkdir(parents=True)
        video = cv2.VideoWriter(str(output/(folder.name+'.mp4')), cv2.VideoWriter_fourcc(*'mp4v'),10,(320,336))
        assert video.isOpened()
        try:
            sources=sorted(folder.glob('data_*.jpg'))
            if folder==interrupted:
                # 中断组第21张JPEG不在20条已提交日志内；即使能解码也不能
                # 当成完整采集帧。只保存哈希并隔离，不进入时序／识别统计。
                saved_count=json.loads((folder/'session.json').read_text(encoding='utf-8'))['saved_count']
                unlogged=[p for p in sources if p.name not in metadata or metadata[p.name]['frame_id']>saved_count]
                save(output/'interrupted_uncommitted.json',
                     [dict(source=p.as_posix(),sha256=digest(p),reason='beyond_session_saved_count_or_missing_log',
                           session_saved_count=saved_count,log_present=p.name in metadata) for p in unlogged])
                sources=[p for p in sources if p not in unlogged]
            for source in sources:
                gray = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
                assert gray is not None and gray.shape == (240,320)
                timestamp = metadata.get(source.name, {}).get('elapsed_ms')
                start = time.perf_counter_ns()
                row = detector.detect(gray, timestamp, folder.name)
                elapsed = (time.perf_counter_ns()-start)/1e6
                old = expected_map.get((folder.name,source.name))
                if old:
                    for key in detector.spatial.detect(None):
                        assert row[key] == old[key], (str(source),key)
                    assert digest(source) == old['source_sha256']
                    compared += 1
                row.update(frame_id=int(source.stem.split('_')[1]), session=folder.name,
                           timestamp_ms=timestamp, source=source.as_posix(), source_sha256=digest(source),
                           processing_ms=elapsed, evaluation_group='interrupted_only' if folder==interrupted else 'development')
                display = paint(row, gray)
                assert cv2.imwrite(str(video_dir/(source.stem+'.jpg')), display)
                video.write(display)
                group.append(row)
        finally:
            video.release()
        decoder=cv2.VideoCapture(str(output/(folder.name+'.mp4')))
        decoded=0
        while decoder.read()[0]:
            decoded+=1
        decoder.release()
        assert decoded == len(group)
        summaries.append(dict(session=folder.name, frames=len(group), group=group[0]['evaluation_group'],
              r1_valid=sum(r['valid'] for r in group),
              c1_near=sum(r['curve_observation']['near_field']['available'] for r in group),
              c2_direct=sum(bool(r['recovery_observation']['pair_samples']) for r in group),
              c2_near=sum(r['recovery_observation']['near_available'] for r in group),
              c2_reference=sum(r['recovery_observation']['fixed_reference_observed'] for r in group),
              c2_turns=dict(Counter(r['recovery_observation']['turn_hint'] or 'none' for r in group)),
              baseline_fixed_invalid=spans(group, lambda r:not r['valid']),
              baseline_near_invalid=spans(group, lambda r:not r['curve_observation']['near_field']['available']),
              c2_direct_missing=spans(group, lambda r:not r['recovery_observation']['pair_samples']),
              c2_near_missing=spans(group, lambda r:not r['recovery_observation']['near_available']),
              c2_new_direct=spans(group, lambda r:bool(r['recovery_observation']['pair_samples']) and not r['curve_observation']['near_field']['available']),
              algorithm_ms=dict(mean=float(np.mean([r['processing_ms'] for r in group])),
                                p95=float(np.percentile([r['processing_ms'] for r in group],95))),
              video_decoded=decoded))
        rows.extend(group)
    assert compared == 1394
    with (output/'frames.jsonl').open('w',encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
    columns=['session','frame_id','timestamp_ms','r1_valid','c1_near','c2_direct','c2_near','c2_reference',
             'turn','history_turn','temporal','advice','rejection','source_sha256']
    with (output/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns)
        writer.writeheader()
        for r in rows:
            o=r['recovery_observation']
            writer.writerow(dict(session=r['session'],frame_id=r['frame_id'],timestamp_ms=r['timestamp_ms'],
                 r1_valid=r['valid'],c1_near=r['curve_observation']['near_field']['available'],
                 c2_direct=bool(o['pair_samples']),c2_near=o['near_available'],c2_reference=o['fixed_reference_observed'],
                 turn=o['turn_hint'],history_turn=o['historical']['turn_hint'],temporal=o['temporal_state'],
                 advice=o['advice'],rejection=o['rejection'],source_sha256=r['source_sha256']))
    save(output/'summary.json',dict(frozen_fields_identical=compared,groups=summaries,
         evaluation='Both laps inspected and used as development data; no blind test',
         timing='PC algorithm only; videos artificial 10fps; original capture software time in JSONL'))
    print(json.dumps([dict(session=g['session'],frames=g['frames'],r1=g['r1_valid'],c1=g['c1_near'],
              c2=g['c2_direct'],near=g['c2_near']) for g in summaries],ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
