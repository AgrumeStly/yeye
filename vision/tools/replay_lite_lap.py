"""L1试跑候选回放／计时／原字段独立留证；只读原图，拒绝覆盖输出。

电脑耗时不是K230性能，输出有效张数不是准确率。原录像采样稀疏，按
真实时间运行，保留其导致的状态清空；不得偷偷改成假50Hz以增加有效帧。
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from collections import Counter
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'vision/src'))
from lite_lap_route import LiteLapRoute
from lap_protocol import LapSender


def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True)
    p.add_argument('--limit',type=int); p.add_argument('--session',default='push_full_lap_0001')
    args=p.parse_args(); output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    source=ROOT/'vision/data/captures/final_mount_20261108'/args.session
    rows=[json.loads(line) for line in (source/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    if args.limit: rows=rows[:args.limit]
    snapshots=output/'source'; snapshots.mkdir()
    hashes={}
    for name in ('lite_lap_route.py','lap_protocol.py','low_speed_lap_canmv.py','vision_protocol.py'):
        src=ROOT/'vision/src'/name; shutil.copy2(src,snapshots/name)
        hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest()
    detector=LiteLapRoute(); sender=LapSender(allow_drive=True); timings=[]; states=Counter(); results=[]
    for row in rows:
        gray=cv2.imread(str(source/row['file']),cv2.IMREAD_GRAYSCALE)
        started=time.perf_counter(); result=detector.update(gray.tobytes(),row['elapsed_ms'])
        elapsed=(time.perf_counter()-started)*1000; timings.append(elapsed); states[result['source']]+=1
        packet=sender.path(result,int(np.ceil(elapsed)),0)
        results.append(dict(file=row['file'],timestamp_ms=row['elapsed_ms'],**result,pc_ms=elapsed,
                            simulated_fresh_packet_hex=packet.hex()))
        if len(results)%50==0: print('frames',len(results),flush=True)
    (output/'frames.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results),encoding='utf-8')
    summary=dict(frames=len(rows),states=dict(states),valid=sum(r['valid'] for r in results),
        templates=len(detector.templates),pc_median_ms=float(np.median(timings)),pc_p95_ms=float(np.percentile(timings,95)),
        pc_max_ms=max(timings),source_hashes=hashes,hardware_tested=False,autonomous_lap_tested=False,
        warning='development images; counts are not accuracy; PC time is not board time; packet age=0 is simulated')
    for name,digest in hashes.items():
        if hashlib.sha256((ROOT/'vision/src'/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('source changed during replay: '+name)
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
