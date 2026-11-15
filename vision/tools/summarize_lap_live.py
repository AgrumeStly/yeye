"""汇总已有无驱动实时诊断日志和主机预览，不连接设备、不修改原件。

板上只打印每第10个有效帧与所有无效帧，统计明确是日志样本，不补造总帧数。
后端预览帧号与算法index不相同，不声称JPEG与某条算法记录严格逐帧对应。
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics


def main():
    p=argparse.ArgumentParser(); p.add_argument('folder'); args=p.parse_args()
    folder=Path(args.folder); rows=[]
    terminal=(folder/'terminal.txt').read_text(encoding='utf-8')
    for line in terminal.replace('\r','').splitlines():
        if not line.startswith('{'): continue
        try: item=json.loads(line)
        except ValueError: continue
        if isinstance(item,dict) and 'index' in item and 'processing_ms' in item: rows.append(item)
    if not rows: raise ValueError('no actual frame records')
    def stats(name,items):
        values=[r[name] for r in items if isinstance(r.get(name),(int,float))]
        return dict(min=min(values),median=statistics.median(values),max=max(values)) if values else None
    valid=[r for r in rows if r['valid']]
    result=dict(logged_samples=len(rows),highest_observed_algorithm_index=max(r['index'] for r in rows),
        actual_total_frame_count=None,logging_rule='every tenth valid frame and all invalid frames; metrics are logged samples',
        source_counts=dict(Counter(r['source'] for r in rows)),valid_logged_samples=len(valid),
        invalid_logged_indices=[r['index'] for r in rows if not r['valid']],
        all_logged_wire_valid_false=all(not r['wire_valid'] for r in rows),
        all_logged_drive_allowed_false=all(not r['drive_allowed'] for r in rows),
        valid_steering=stats('steering',valid),valid_bend=stats('bend',valid),
        processing_ms=stats('processing_ms',rows),to_send_ms=stats('to_send_ms',rows),
        interval_ms=stats('interval_ms',rows),min_logged_free_heap=min(r['free_heap'] for r in rows),
        normal_completion='[L1 DONE]' in terminal,
        preview_frame_index_is_not_algorithm_index=True,preview=[])
    for file in sorted((folder/'preview').glob('*.jpg')):
        data=file.read_bytes()
        result['preview'].append(dict(file=str(file.relative_to(folder)),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    (folder/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()
