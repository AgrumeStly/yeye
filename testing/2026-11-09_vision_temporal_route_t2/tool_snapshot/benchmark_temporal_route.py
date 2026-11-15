"""T2单进程电脑计时与进程工作集记录；绝不等同K230端到端性能。"""
import argparse
import ctypes
import os
from pathlib import Path
import platform
import sys
import time
import cv2
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_temporal_route import TemporalRouteDetector
from replay_recovery import load
from review_recovery_inputs import save,digest


def run(output):
    """预加载连续150帧，仅计90～150帧算法，剔除文件I/O与视频渲染。"""
    output.mkdir(parents=True,exist_ok=False)
    rows=[r for r in load(Path('testing/2026-11-08_vision_prediction_p1/release/frames.jsonl')) if r['session']=='push_full_lap_0001'][:150]
    images=[cv2.imread(r['source'],0) for r in rows];d=TemporalRouteDetector();times=[]
    for index,(r,g) in enumerate(zip(rows,images)):
        start=time.perf_counter_ns();d.update(g,r['timestamp_ms'],r['session'],r['threshold'],True,
                   pair_samples=r['recovery_observation']['pair_samples'])
        elapsed=(time.perf_counter_ns()-start)/1e6
        if index>=89:times.append(elapsed)
    memory=None
    if os.name=='nt':
        # Windows进程工作集含Python、NumPy与OpenCV运行时，不能当算法工作区或板卡RAM需求。
        class Counters(ctypes.Structure):
            _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong),
                      *[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage',
                      'QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]]
        counters=Counters();counters.cb=ctypes.sizeof(counters)
        handle=ctypes.windll.kernel32.GetCurrentProcess();ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong]
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(counters),counters.cb):
            memory=dict(peak_working_set_bytes=counters.PeakWorkingSetSize,working_set_bytes=counters.WorkingSetSize)
    save(output/'benchmark.json',dict(python=platform.python_version(),opencv=cv2.__version__,numpy=np.__version__,
        algorithm_samples=len(times),frame_window=[90,150],median_ms=float(np.median(times)),p95_ms=float(np.percentile(times,95)),max_ms=max(times),
        windows_process_memory=memory,code_sha256=digest(Path('vision/src/offline_temporal_route.py')),
        scope='PC algorithm only, preloaded images; excludes capture, decode, rendering, UART. Not board performance.'))
    print((output/'benchmark.json').read_text(encoding='utf-8'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
