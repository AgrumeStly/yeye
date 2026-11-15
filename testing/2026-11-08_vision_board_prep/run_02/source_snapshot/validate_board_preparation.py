"""V-08离线验证：BP1实图回放、真实C2/F1包、生产C解析器与状态机交叉检查。"""

import argparse
import ast
import csv
import atexit
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
import tracemalloc

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from board_observer_core import detect_gray
from vision_protocol import RecognitionSender,crc16,encode_command,encode_path
from replay_recovery import load
from review_recovery_inputs import digest,save
from build_observer_bundle import build


class CProbe:
    """通过独立C进程调用原状态机，兼容32位编译器与64位Python。"""

    def __init__(self,path):
        self.process=subprocess.Popen([str(path.resolve())],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,text=True,bufsize=1)
        self.values=[0]*10
        atexit.register(self.close)

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            self.process.wait(timeout=5)

    def request(self,text):
        self.process.stdin.write(text+'\n');self.process.stdin.flush()
        line=self.process.stdout.readline()
        if not line:raise RuntimeError('C probe terminated')
        self.values=list(map(int,line.split()));assert len(self.values)==10
        return self.values[0]

    def probe_reset(self):return self.request('R')
    def probe_tick(self,now):return self.request('T '+str(now))
    def probe_transport_fault(self):return self.request('X')
    def probe_feed(self,data,count,now):return self.request('F %d %d %s'%(count,now,data.hex()))
    def probe_state(self):return self.values[1]
    def probe_reason(self):return self.values[2]
    def probe_error(self):return self.values[3]
    def probe_flags(self):return self.values[4]
    def probe_sequence(self):return self.values[5]
    def probe_left(self):return self.values[6]
    def probe_right(self):return self.values[7]
    def probe_duplicates(self):return self.values[8]
    def probe_path_time(self):return self.values[9]


def run(output):
    """所有写入仅新证据目录。C模块按原源码编译DLL，不编译／修改板级工程。"""
    output.mkdir(parents=True,exist_ok=False)
    protected=json.loads(Path('testing/2026-11-08_vision_recovery_c2/protected_before.json').read_text(encoding='utf-8'))
    control_paths=[Path(p) for p in subprocess.check_output(['git','ls-files','control'],text=True,encoding='utf-8').splitlines()
                   if Path(p).is_file()]
    save(output/'control_before.json',{p.as_posix():digest(p) for p in control_paths})
    build(output/'board_bundle')
    idle=subprocess.run([sys.executable,str(output/'board_bundle/observer_bench_canmv.py')],capture_output=True,text=True)
    assert idle.returncode==0 and '[IDLE]' in idle.stdout
    (output/'bundle_idle.txt').write_text(idle.stdout,encoding='utf-8')
    checks=[]
    def check(name,value):
        assert value,name
        checks.append(name)
    check('CRC_123456789',crc16(b'123456789')==0x29b1)
    check('golden_path',encode_path(1,valid=True,confidence=80,processing_ms=20).hex()=='a55a01010c010150000000000000140000009201')
    check('golden_start',encode_command(1,1).hex()=='a55a01020c010000000000000000000001004d12')
    check('golden_stop',encode_command(2,2).hex()=='a55a01020c02000000000000000000000200bb88')
    spec=importlib.util.spec_from_file_location('reference_protocol','control/tools/protocol_example.py')
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    rng=random.Random(20261108)
    for _ in range(1000):
        fields=dict(sequence=rng.randrange(256),error=rng.randint(-1000,1000),valid=bool(rng.randrange(2)),
                    confidence=rng.randrange(101),heading=rng.randint(-9000,9000),bend=rng.randrange(1001),
                    processing_ms=rng.randrange(1001),finish=bool(rng.randrange(2)))
        assert encode_path(**fields)==reference.encode_path(**fields)
    check('1000_packets_match_control_reference',True)
    captured=[]
    def short_write(data):
        captured.append(data[:3]);return min(3,len(data))
    sender=RecognitionSender(short_write);data=sender.command(3)
    check('short_writes_send_remaining_bytes',b''.join(captured)==data)
    for result in (None,0,21):
        try:RecognitionSender(lambda _:result).command(3)
        except OSError:pass
        else:raise AssertionError('invalid write must raise')
    check('zero_none_or_oversize_write_fails',True)
    rows=[r for r in load(Path('testing/2026-11-08_vision_recovery_c2/replay_accepted/frames.jsonl'))
          if r['evaluation_group']=='development']
    finishes={(r['session'],r['frame_id']):r['finish'] for r in load(Path('testing/2026-11-08_vision_finish_f1/release/frames.jsonl'))}
    valid_row=next(r for r in rows if r['recovery_observation']['fixed_reference_observed'] and
                   r['recovery_observation']['temporal_state']=='stable_observation')
    sender=RecognitionSender(allow_valid_path=True)
    check('source_age_199_valid',bool(sender.path(valid_row,processing_ms=20,source_age_ms=199)[6]&1))
    check('source_age_200_invalid',not sender.path(valid_row,processing_ms=20,source_age_ms=200)[6]&1)
    check('processing_100_valid',bool(sender.path(valid_row,processing_ms=100)[6]&1))
    check('processing_101_invalid',not sender.path(valid_row,processing_ms=101)[6]&1)
    check('diagnostic_default_invalid',not RecognitionSender().path(valid_row)[6]&1)
    for bad in (None,-1,float('nan'),float('inf')):
        try:sender.path(valid_row,processing_ms=bad)
        except ValueError:pass
        else:raise AssertionError('bad processing time')
    check('bad_timing_rejected',True)
    check('independent_sequences',sender.command_sequence==0 and sender.path_sequence==4)
    sender.path_sequence=255
    check('path_wrap_255_to_0',sender.path(valid_row)[5]==255 and sender.path(valid_row)[5]==0)
    # 编译原生产解析器／状态机；本适配器没有硬件或电机调用。
    includes=['control/Drivers_Custom/Communication','control/App/Car']
    command=['gcc','-std=c99','-Wall','-Wextra','-Werror',
             'vision/tools/protocol_cross_harness.c','control/Drivers_Custom/Communication/protocol.c',
             'control/App/Car/car.c']+['-I'+p for p in includes]+['-o',str(output/'protocol_cross.exe')]
    compiled=subprocess.run(command,capture_output=True,text=True)
    (output/'c_build.txt').write_text(' '.join(command)+'\n'+compiled.stdout+compiled.stderr,encoding='utf-8')
    assert compiled.returncode==0
    dll=CProbe(output/'protocol_cross.exe')
    def feed(data,now):return dll.probe_feed(data,len(data),now)
    dll.probe_reset();feed(encode_command(1,1),0)
    check('C_START_requires_path',dll.probe_state()==0)
    straight=encode_path(1,valid=True,confidence=80,processing_ms=20)
    check('C_split_first_half_incomplete',feed(straight[:7],10)==0)
    check('C_split_completes',feed(straight[7:],10)==1)
    feed(encode_command(2,1),11);check('C_START_fresh_valid',dll.probe_state()==1)
    feed(encode_path(2,error=600,valid=True,confidence=80,processing_ms=20),20)
    check('C_right_positive_left_request_higher',dll.probe_error()==600 and dll.probe_left()>dll.probe_right())
    feed(encode_path(3,error=-600,valid=True,confidence=80,processing_ms=20),30)
    check('C_left_negative_right_request_higher',dll.probe_error()==-600 and dll.probe_right()>dll.probe_left())
    duplicate=encode_path(3,error=-600,valid=True,confidence=80,processing_ms=20)
    feed(duplicate,180);check('C_duplicate_does_not_refresh',dll.probe_path_time()==30 and dll.probe_duplicates()==1)
    dll.probe_tick(230);check('C_200ms_stream_timeout_fault_zero',dll.probe_state()==3 and dll.probe_left()==0 and dll.probe_right()==0)
    feed(encode_path(4,valid=True,confidence=80,processing_ms=20),231)
    check('C_recovery_does_not_restart',dll.probe_state()==3)
    feed(encode_command(3,1),232);feed(encode_path(5,valid=False),233)
    check('C_invalid_path_fault_immediate',dll.probe_state()==3)
    feed(encode_path(6,valid=True,confidence=80,processing_ms=20),234);feed(encode_command(4,1),235)
    bad=bytearray(encode_path(7,valid=True,confidence=80,processing_ms=20));bad[8]^=1
    check('C_bad_CRC_rejected',feed(bytes(bad),236)==0 and dll.probe_path_time()==234)
    feed(encode_command(5,2),237);feed(encode_command(4,1),238)
    check('C_delayed_START_after_STOP_rejected',dll.probe_state()==2)
    feed(encode_command(1,2),239);check('C_old_STOP_always_effective',dll.probe_state()==2)
    dll.probe_reset();feed(encode_path(255,valid=True,confidence=80,processing_ms=20),0)
    feed(encode_path(0,valid=True,confidence=80,processing_ms=20),1)
    check('C_sequence_wrap',dll.probe_sequence()==0)
    feed(encode_path(255,valid=True,confidence=80,processing_ms=20),2)
    check('C_old_path_rejected',dll.probe_sequence()==0)
    feed(encode_path(180,valid=True,confidence=80,processing_ms=20),202)
    check('C_reboot_baseline_after_200ms',dll.probe_sequence()==180)
    feed(encode_command(1,1),203);dll.probe_transport_fault()
    check('C_transport_fault_zero',dll.probe_state()==3 and dll.probe_left()==0)
    dll.probe_reset();check('C_noise_concatenated_recovery',feed(b'\xa5\x00\x5a'+straight+encode_command(1,3),0)==2)
    # 对真实C2/F1结果逐帧生成字节；时间年龄0是离线模拟，绝不当实时结果。
    packets=[];sender=RecognitionSender(allow_valid_path=True);dll.probe_reset()
    for row in rows:
        packet=sender.path(row,finishes[(row['session'],row['frame_id'])],processing_ms=row['processing_ms'],source_age_ms=0)
        check_key=(packet[6]&1)!=0
        if check_key:
            assert row['valid'] and row['recovery_observation']['fixed_reference_observed']
            assert row['recovery_observation']['temporal_state']=='stable_observation'
        assert feed(packet,len(packets)*20)==1
        packets.append(dict(session=row['session'],frame=row['frame_id'],source_sha256=row['source_sha256'],
              wire_hex=packet.hex(),valid=check_key,finish_candidate=bool(packet[6]&2),source_age_simulated=0))
    (output/'recognition_packets.bin').write_bytes(b''.join(bytes.fromhex(p['wire_hex']) for p in packets))
    save(output/'recognition_packets.json',packets)
    check('1394_real_recognition_packets_C_parser_accepts',len(packets)==1394)
    # 带原采集时间回放生产状态机，只在首个有效包后模拟一次START，验证
    # 稀疏录像会超时且后续有效图不会自动重启；不代表板上运行速度。
    dll.probe_reset();sender=RecognitionSender(allow_valid_path=True);trace=[];started=False
    for row in (r for r in rows if r['session']=='push_full_lap_0001'):
        now=row['timestamp_ms'];packet=sender.path(row,processing_ms=row['processing_ms'])
        feed(packet,now)
        if not started and packet[6]&1:
            feed(encode_command(1,1),now);started=True
        trace.append(dict(frame=row['frame_id'],capture_ms=now,state=dll.probe_state(),reason=dll.probe_reason()))
    save(output/'sparse_capture_C_state_trace.json',trace)
    check('sparse_capture_not_real_time_control',any(r['state']==3 for r in trace))
    dll.close()
    # BP1逐张真正运行；输出与C2分开，不拿诊断有效补协议有效。
    probes=[];timings=[]
    for row in rows:
        gray=cv2.imread(row['source'],cv2.IMREAD_GRAYSCALE);pixels=gray.tobytes()
        start=time.perf_counter_ns();result=detect_gray(pixels);elapsed=(time.perf_counter_ns()-start)/1e6
        timings.append(elapsed)
        assert not result['valid'] and not RecognitionSender().path(result,processing_ms=elapsed)[6]&1
        probes.append(dict(session=row['session'],frame=row['frame_id'],source_sha256=row['source_sha256'],
                r1_valid=row['valid'],c2_fixed=row['recovery_observation']['fixed_reference_observed'],
                bp1_diagnostic_valid=result['diagnostic_valid'],deviation_px=result['deviation_px'],
                r1_deviation_px=row['deviation_px'],processing_ms=elapsed,wire_valid=False))
    save(output/'bp1_frames.json',probes)
    tracemalloc.start();detect_gray(cv2.imread(valid_row['source'],0).tobytes())
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    check('BP1_all_wire_paths_invalid',all(not p['wire_valid'] for p in probes))
    blank=bytes([230])*76800
    for pixels in (None,b'',blank,bytes(76800)):
        check('BP1_bad_or_no_contrast_'+str(0 if pixels is None else len(pixels))+str(pixels is blank),not detect_gray(pixels)['diagnostic_valid'])
    original=bytearray(cv2.imread(valid_row['source'],0).tobytes());before=bytes(original);detect_gray(original)
    check('BP1_input_unmodified',bytes(original)==before)
    groups=[]
    for session in dict.fromkeys(p['session'] for p in probes):
        group=[p for p in probes if p['session']==session]
        groups.append(dict(session=session,frames=len(group),diagnostic_valid=sum(p['bp1_diagnostic_valid'] for p in group),
              R1_invalid_BP1_diagnostic=sum(p['bp1_diagnostic_valid'] and not p['r1_valid'] for p in group)))
    originals_ok=all(digest(Path(p))==h for p,h in protected.items())
    control_before=json.loads((output/'control_before.json').read_text(encoding='utf-8'))
    check('3616_original_files_preserved',originals_ok)
    check('control_tracked_bytes_unchanged',all(digest(Path(p))==h for p,h in control_before.items()))
    sources=[Path('vision/src/board_observer_core.py'),Path('vision/src/vision_protocol.py'),Path('vision/src/observer_bench_canmv.py'),
             Path(__file__),Path('vision/tools/protocol_cross_harness.c'),Path('vision/tools/build_observer_bundle.py')]
    (output/'source_snapshot').mkdir()
    for path in sources:shutil.copy2(path,output/'source_snapshot'/path.name)
    save(output/'source_hashes.json',{p.as_posix():digest(p) for p in sources})
    save(output/'validation.json',dict(passed=True,checks=checks,real_recognition_packets=len(packets),
         recognition_valid=sum(p['valid'] for p in packets),finish_candidate_packets=sum(p['finish_candidate'] for p in packets),
         bp1_groups=groups,bp1_algorithm_ms=dict(mean=float(np.mean(timings)),p95=float(np.percentile(timings,95))),
         PC_tracemalloc_bytes=dict(current=current,peak=peak,scope='CPython allocations only; not MicroPython or media memory'),
         originals_protected=len(protected),control_tracked_protected=len(control_before),
         first_sparse_fault=next((r for r in trace if r['state']==3),None),
         scope='Offline PC byte/model/diagnostic checks. No board, UART port, camera or motors opened. BP1 is not C2/F1 equivalent.'))
    print(json.dumps(dict(checks=len(checks),groups=groups,packets=len(packets),peak=peak),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
