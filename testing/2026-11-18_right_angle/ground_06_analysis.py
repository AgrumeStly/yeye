"""只读关联第六次实跑原始MCU、视觉与图像记录，不修改控制或试跑参数。"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'vision/src'))
from right_angle_racing import racing_route

folder = Path(__file__).resolve().parent
captured = json.loads((folder/'ground_06_capture/capture.json').read_text(encoding='utf-8'))
sample = captured['samples'][0]
trace = sample['diagnostic_trace']
rows = [json.loads(line) for line in (folder/'ground_06_camera/run_0002.jsonl').read_text(encoding='utf-8').splitlines()]
frames = {r['index']: r for r in rows if 'index' in r}
events = [r for r in rows if r.get('event') == 'path_lost']
last = trace['samples'][-1]
matches = [e for e in events if e['before_sequence'] == last['path_sequence']
           and frames[e['before_index']]['steering'] == last['steering']]
assert len(matches) == 1
event = matches[0]
before, after = frames[event['before_index']], frames[event['after_index']]
window = [r for r in frames.values() if before['index']-30 <= r['index'] <= after['index']+5]
by_sequence = {r['path_sequence']: r for r in window if r['index'] <= before['index']}
offsets = sorted({r['path_at']-by_sequence[r['path_sequence']]['elapsed_ms']
                  for r in trace['samples'] if r['path_sequence'] in by_sequence})
recomputed = []
for r in window:
    if r.get('turn_floor'):
        replay = racing_route(r['parameters'])
        recomputed.append(dict(index=r['index'], elapsed_ms=r['elapsed_ms'], parameters=r['parameters'],
            desktop_route_from_serialized_parameters=replay['steering'],
            recorded_turn_floor=r['turn_floor'], actual_sent_steering=r['steering']))
images = []
for name in ('run_0002_loss_05_before.pgm', 'run_0002_loss_05_after.pgm'):
    raw = (folder/'ground_06_camera'/name).read_bytes()
    assert len(raw) == 76815 and raw[:15] == b'P5\n320 240\n255\n'
    images.append(dict(file='ground_06_camera/'+name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
assert trace['frozen'] == 1 and sample['last_run']['reason'] == 3
assert before['wire_valid'] and not after['wire_valid']
assert before['steering'] == last['steering'] == 508
# 串口接收、两个独立时钟及包内年龄有量化误差；保留实际偏移范围，
# 不为得到理想对齐而改写时间戳或收紧成虚假的毫秒一致。
result = dict(user_report='未进入拐弯，小车在距离弯道一定距离时提前拐弯，失去方向，后停下，绿灯快闪',
    actual_revision=hex(sample['g_speed_revision']), flash_matches_bin=captured['flash_matches_bin'],
    last_run=sample['last_run'], frozen_trace_summary={k:v for k,v in trace.items() if k!='samples'},
    wire_errors=sample['uart'], vision_frames=len(frames), json_lines=len(rows),
    matched_loss_event=event, last_valid=before, first_invalid=after,
    frame_to_mcu_source_offsets_ms=offsets, frozen_ring_source_age_at_stop_ms=trace['stop_at_ms']-last['path_at'],
    desktop_parameter_recomputation=recomputed, original_images=images,
    limitations=['Desktop recomputation uses rounded JSON parameters and double precision; it is not measured MCU or K230 pre-floor telemetry.',
                 'No raw exposure was saved at the first strong-turn onset; physical onset distance is not measured.',
                 'Proxy geometry units are not calibrated centimetres.',
                 'Post-stop image and post-stop valid paths do not replace the trigger frames.'])
(folder/'ground_06_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(folder/'ground_06_window.json').write_text(json.dumps(window,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(elapsed_ms=sample['last_run']['elapsed_ms'],reason=sample['last_run']['reason'],
    matched_event=event, offsets_ms=offsets,images=images),ensure_ascii=False))
