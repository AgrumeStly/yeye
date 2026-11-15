"""将已回放、已目视审核的T2证据汇总为逐帧复核表和可追溯报告。

本工具不替代人工审核：必须先存在记录已查看页的manual_observations.json。
自动列只提取冻结输出，人工可见性／未决问题单独来自该文件，不冒称真值。
"""

import argparse
import csv
import json
from pathlib import Path
import shutil

import numpy as np

from replay_recovery import load,spans
from review_recovery_inputs import digest,save


def run(root):
    """新建汇总文件，拒绝重复覆盖；报告只追加本次最终统计一次。"""
    assert not (root/'result_metrics.json').exists()
    rows=load(root/'delivery/frames.jsonl');full=[r for r in rows if r['session']=='push_full_lap_0001']
    summary=json.loads((root/'delivery/summary.json').read_text(encoding='utf-8'))
    checks=json.loads((root/'delivery_checks/checks.json').read_text(encoding='utf-8'))
    video=json.loads((root/'delivery_video/video_validation.json').read_text(encoding='utf-8'))
    audit=json.loads((root/'delivery_audit/delivery_checks.json').read_text(encoding='utf-8'))
    bench=json.loads((root/'delivery_benchmark/benchmark.json').read_text(encoding='utf-8'))
    manual=json.loads((root/'manual_observations.json').read_text(encoding='utf-8'))
    pages=json.loads((root/'delivery_video/audit_index.json').read_text(encoding='utf-8'))
    assert manual['all_listed_pages_visually_reviewed'] and len(pages)==len(manual['reviewed_pages'])
    assert set(Path(p['file']).name for p in pages)==set(manual['reviewed_pages'])
    assert checks['all_checks_passed'] and audit['passed'] and video['source_frames']==732
    core=digest(Path('vision/src/offline_temporal_route.py'))
    assert core==checks['code_sha256']==bench['code_sha256']
    selected=set(f for p in pages for f in p['frames']);review_rows=[]
    unknown=spans(full,lambda r:r['temporal_route']['state']=='map_prior_only')
    for row in full:
        if row['frame_id'] not in selected:continue
        notes=[n for n in manual['ranges'] if n['first']<=row['frame_id']<=n['last']]
        assert notes,row['frame_id']
        note=notes[-1];t=row['temporal_route']
        interval=next((s for s in unknown if s['first_frame']<=row['frame_id']<=s['last_frame']),None)
        review_rows.append(dict(frame=row['frame_id'],software_ms=row['timestamp_ms'],
            visible_boundary=note['visible'],boundary_role=note['roles'],image_interference=note['interference'],
            baseline_failure=';'.join(row['reasons']) or 'R1当前有效；另看近场覆盖',
            C1_near_available=row['curve_observation']['near_field']['available'],
            candidate_output=t['state'],path_basis=t['path_basis'],map_hypothesis=t['map']['node'],
            recovered_frame=interval['recovered_frame'] if interval else '',
            recovered_ms=interval['recovered_ms'] if interval else '',
            assessment=note['assessment'],unresolved=note['unresolved'],
            review_basis='视觉代理逐页目视；非主控逐像素标注／隐藏边真值'))
    with (root/'manual_review.csv').open('x',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(review_rows[0]));writer.writeheader();writer.writerows(review_rows)
    baseline=dict(R1=spans(full,lambda r:not r['valid']),
          C1_near=spans(full,lambda r:not r['curve_observation']['near_field']['available']),
          C2_pair=spans(full,lambda r:not r['recovery_observation']['pair_samples']))
    ablations={name:json.loads((root/f'delivery_{name}'/'summary.json').read_text(encoding='utf-8'))['groups'][0]
               for name in ['no_motion','no_map']}
    mask=json.loads((root/'delivery_checks/mask_errors.json').read_text(encoding='utf-8'))
    mask_groups={state:dict(points=len([e for e in mask if e['state']==state]),
            frames=len({e['frame'] for e in mask if e['state']==state}),
            p95=float(np.percentile([e['center_distance_px'] for e in mask if e['state']==state],95)),
            max=max(e['center_distance_px'] for e in mask if e['state']==state)) for state in {e['state'] for e in mask}}
    metrics=dict(source_core_sha256=core,summary=summary,baseline_failure_spans=baseline,
        T2_nominal_only_spans=unknown,ablation=ablations,mask_by_state=mask_groups,
        all_mask_including_unknown=checks['center_distance_px'],benchmark=bench,
        manually_reviewed_frames=len(review_rows),manually_reviewed_pages=len(pages),video=video,audit=audit)
    save(root/'result_metrics.json',metrics)
    snap=root/'tool_snapshot';snap.mkdir()
    paths=[Path('vision/src/offline_temporal_route.py'),*Path('vision/tools').glob('*temporal_route*.py')]
    for p in paths:shutil.copy2(p,snap/p.name)
    save(root/'source_hashes.json',{p.as_posix():digest(p) for p in paths})
    g=summary['groups'][-1]
    text='\n## 最终统计（delivery，完整开发数据）\n\n'
    text+='下列数量只说明模型／参考输出，不能当识别准确率或可控帧率。\n\n| 输出 | 帧数 |\n| --- | ---: |\n'
    for k,v in g['states'].items():text+=f'| T2 {k} | {v} |\n'
    text+=f"\n固定y120仍为565／732；C2当前双边606／732；P1估计94／732。T2当前模型但无C2双边为{g['current_supported_without_C2']}帧，隐藏边界无真值，不能据此宣布正确。\n\n"
    text+='| 定义 | 最长首末采样跨度ms | 到下一恢复采样ms |\n| --- | ---: | ---: |\n'
    for name,intervals in [*baseline.items(),('T2仅名义先验',unknown)]:
        s=max(intervals,key=lambda x:x['until_recovery_ms'] or 0)
        text+=f"| {name}（{s['first_frame']}–{s['last_frame']}） | {s['sample_span_ms']} | {s['until_recovery_ms']} |\n"
    text+='\n定义不同，不能把上述缺口时长的差当成控制有效性或完赛能力提升。完整区间、恢复时刻及逐帧比较见result_metrics.json与delivery_audit/frame_comparison.csv。\n\n'
    text+='| 已知边隐藏代理状态 | 帧数 | 参考点数 | 二维中点距离P95／最大px |\n| --- | ---: | ---: | ---: |\n'
    for k,v in mask_groups.items():text+=f"| {k} | {v['frames']} | {v['points']} | {v['p95']:.2f}／{v['max']:.2f} |\n"
    text+=f"\n全部状态合计121帧／2548点，含未知的总体P95={checks['center_distance_px']['p95']:.2f}px，不能省略未知部分。32px（输入宽度10%）只作为开发级严重跳移门槛，当前／历史部分通过；不是比赛门槛或准确性保证。自然回放同时检查当前C2与路线矛盾，全部比较含C2输入约束和中点回退，不能当独立准确率。\n\n"
    text+='| 消融设置 | 当前模型 | 当前双边回退 | 有限历史 | 仅名义先验 |\n| --- | ---: | ---: | ---: | ---: |\n'
    for name,data in [('完整T2',g),('禁用运动补偿／像素融合',ablations['no_motion']),('固定90°、禁用节点先验',ablations['no_map'])]:
        s=data['states'];text+=f"| {name} | {s.get('current_supported_model',0)} | {s.get('current_pair_fallback',0)} | {s.get('history_prediction',0)} | {s.get('map_prior_only',0)} |\n"
    text+='\nno_motion保留几何搜索记忆与拓扑状态，并非删除全部历史；no_map固定90°，并非最优自由角度检测器。消融只说明这两个实现开关的影响，数量仍不证明正确性。\n\n'
    text+='| 地图目标阶段 | 第一圈首次采样帧／ms | 第二圈首次采样帧／ms |\n| --- | --- | --- |\n'
    for node in ['bottom_left','left_shoulder','apex_77','right_shoulder','bottom_right','finish_straight']:
        cells=[]
        for lo,hi in [(0,70436),(70436,120537)]:
            rr=next((r for r in full if lo<=r['timestamp_ms']<hi and r['temporal_route']['map']['node']==node),None)
            cells.append(f"{rr['frame_id']}／{rr['timestamp_ms']}" if rr else '未单独进入；检查终点锚点复位')
        text+=f"| {node} | {' | '.join(cells)} |\n"
    text+='\n此表为目标阶段推断，不能解释为整车已通过角点；提前推进、漏计、等待终点均需结合审核页。F1在70.436s和120.537s看到终点；不重复触发，不据此自动停车。\n\n'
    text+=f"人工逐页复核{len(pages)}页／{len(review_rows)}帧，包含全部10段R1失效及恢复、C1近场缺口和所有新增无C2模型区间；人工定性说明见manual_observations.json，逐帧表见manual_review.csv。隐边与车体包络仍无真值。\n\n"
    text+=f"单进程电脑61张弯道窗口算法计时：中位{bench['median_ms']:.2f}ms、P95 {bench['p95_ms']:.2f}ms、最大{bench['max_ms']:.2f}ms；进程峰值工作集{bench['windows_process_memory']['peak_working_set_bytes']}B（含运行时／数据）。这比原R1/C2电脑链路开销高，不能称已实现快速完赛或满足板上实时协议时限。\n\n"
    text+=f"视频1600×900、10Hz显示、{video['decoded_frames']}显示帧、{video['duration_s']}s，全部732来源帧均展示并完整解码；有{audit['route_visible_frames']}帧在相机图内有至少2个路线／参考点，全部732帧有局部模型／参考及全局名义路线。部分路线仅在盲区模型可见，不能伪装为相机观测。\n\n视频SHA-256：`{video['sha256']}`。算法SHA-256：`{core}`。\n"
    review=root/'review.md';old=review.read_text(encoding='utf-8');assert '## 最终统计' not in old
    review.write_text(old+text,encoding='utf-8')
    print(dict(reviewed_frames=len(review_rows),pages=len(pages),video_sha256=video['sha256'],core_sha256=core))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    run(p.parse_args().root)
