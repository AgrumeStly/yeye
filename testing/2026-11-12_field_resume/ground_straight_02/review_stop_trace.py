"""复核0B冻结原始采样：明确本次停因，不将旧反向失败或主观动力感受替代读数。"""
import csv
import io
import json
from pathlib import Path

folder=Path(__file__).parent
raw=json.loads((folder/'fault_capture_01/capture.json').read_text(encoding='utf-8'))
first,second=raw['samples']
trace=first['diagnostic_trace']
samples=trace['samples']
assert raw['flash_matches_bin'] and raw['application_baseline_plausible']
assert trace==second['diagnostic_trace'] and trace['frozen']==1
assert trace['stop_reason']==7 and first['last_run']['reason']==7
assert first['last_run']['elapsed_ms']==2881
assert samples[-1]['at_ms']==trace['stop_at_ms']
last_left=max(s['at_ms'] for s in samples if s['left_delta']!=0)
last_right=max(s['at_ms'] for s in samples if s['right_delta']!=0)
assert trace['stop_at_ms']-last_left==300
assert trace['stop_at_ms']-last_right==0
tail=[s for s in samples if s['at_ms']>last_left]
assert len(tail)==15 and all(s['left_delta']==0 and s['left_target']>0 for s in tail)
assert all(s['right_raw_rpm']>0 for s in tail)
assert all(s['path_valid'] and not s['history'] for s in tail)
assert all(s['at_ms']-s['path_at']<200 for s in tail)
assert first['g_lap_uart_errors']==0 and first['g_speed_fault']==0
assert first['lap']['left_pwm']==0 and first['lap']['right_pwm']==0
csv_stream=io.StringIO(newline='')
writer=csv.DictWriter(csv_stream,fieldnames=['run_elapsed_ms',*samples[0].keys()])
writer.writeheader()
writer.writerows(dict(run_elapsed_ms=s['at_ms']-first['lap']['run_since'],**s) for s in samples)
(folder/'stop_trace.csv').write_text(csv_stream.getvalue(),encoding='utf-8-sig')
result=dict(passed=True,scope='actual second ground run; no new motion or reset',
    revision=hex(first['g_speed_revision']),stop_reason='LAP_NO_FEEDBACK',elapsed_ms=2881,
    frozen_samples_identical=True,total_recorded_samples=trace['total_samples'],retained_samples=len(samples),
    trace_run_range_ms=[samples[0]['at_ms']-first['lap']['run_since'],samples[-1]['at_ms']-first['lap']['run_since']],
    left_no_edge_ms=300,right_no_edge_ms=0,last_path_sequence=samples[-1]['path_sequence'],
    left_target_during_last_300ms=[min(s['left_target'] for s in tail),max(s['left_target'] for s in tail)],
    left_pwm_during_last_300ms=[min(s['left_pwm'] for s in tail),max(s['left_pwm'] for s in tail)],
    current_pwm=[first['lap']['left_pwm'],first['lap']['right_pwm']],uart_errors=0,hardware_fault=0,
    timing_us={key:first['timing'][key]/16 for key in ('systick_max_cycles','motion_lock_max_cycles')},
    limitations=['trace retains last 640ms, not full 2881ms',
        'no edges proves missing encoder feedback, not by itself mechanical stall versus sensor failure',
        'brief positive edges after 50 percent restart then no edges at lower PWM supports loaded low-speed/restart gap',
        'need actual visual per-frame log to explain inner-wheel low target',
        'no motor current or loaded voltage measurement; do not claim weak power source',
        'first 2044ms REVERSE remains a separate preserved failure'])
(folder/'trace_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
