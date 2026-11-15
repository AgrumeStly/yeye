"""复核本次原编号日志；只统计已保存样本，不凭缺失时间戳定位地面窗口。"""
from collections import Counter
import hashlib
import json
from pathlib import Path

folder=Path(__file__).parent
raw=(folder/'board_readback_01/runtime_log.jsonl').read_bytes()
rows=[json.loads(x) for x in raw.decode('utf-8').splitlines()]
samples=[r for r in rows if 'index' in r]
valid=[r for r in samples if r['wire_valid']]
jumps=[dict(before=a,after=b) for a,b in zip(valid,valid[1:])
    if b['index']-a['index']==10 and a['steering']*b['steering']<0
    and abs(a['steering']-b['steering'])>600]
result=dict(original_log='run_0009.jsonl',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
    logged_samples=len(samples),highest_logged_frame=max(r['index'] for r in samples),
    sources=dict(Counter(r['source'] for r in samples)),wire_valid_logged_samples=len(valid),
    processing_ms=[min(r['processing_ms'] for r in samples),max(r['processing_ms'] for r in samples)],
    events=[r for r in rows if 'event' in r],large_adjacent_sampled_sign_changes=jumps,
    limitations=['all invalid and each tenth valid frame logged; counts are not accuracy rates',
        'no elapsed clock or original frames; exact 2044ms trial cannot be isolated',
        'large sign changes elsewhere in long session do not prove the ground-trial cause',
        'power cut ended session; absent completed does not imply camera exception',
        'later run_0010 is USB boot and stored separately'])
(folder/'log_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Original run_0009 reviewed:',len(samples),'logged samples;',len(jumps),'sampled large sign changes; ground cause unassigned.')
