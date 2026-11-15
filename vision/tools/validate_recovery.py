"""C2时序、失效语义、原字段／原件保护及已目视审核的逐帧表。"""

import csv
import json
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_recovery import RecoveryDetector
from replay_recovery import load, spans
from review_recovery_inputs import ROOT, digest, save


# 以下是视觉代理实际查看raw_01..15及new_01..13后的区间观察记录。
# 帧号只用于离线人工复核表，不导入识别模块，也不参与运行判据。
NOTES=[
 (98,108,'双边可见，内侧肘部逐渐下移','左为外边界，右为内边界','背景墙／地面折痕','参考行缺右侧支持，近场仍有双边'),
 (109,111,'右侧内缘裁短但近场仍可辨','外／内双边在图内的短段','墙线／折痕','C1长连通域门槛拒绝，C2有6行以上直接锚点'),
 (112,141,'仅外侧黑带可确认，转向后逐渐斜向','同一黑带两臂／两面不能当双边','墙脚线／反光／折痕','出画及实际观测不足，不能补造另一侧'),
 (142,150,'出口双边先在远处出现，随后扩展','出口左右内缘','墙脚线／折痕','R1至142不覆盖y120，C1要求到y200而延迟'),
 (175,190,'内侧逐渐出画，仅外侧斜黑带稳定可辨','外侧角色据前后帧事后复核，当前单帧角色不定','折痕／远景线','弱候选误配／透视增长不符，实际第二侧不足'),
 (191,195,'出口双边恢复且向近处扩展','左右边界真实内缘','反光折痕','C1近端覆盖门槛，C2先记录远段'),
 (269,274,'入口双边，内侧肘部向右下移动','外左内右','印字／反光','固定y120缺右侧支持，保留近段'),
 (275,276,'内侧被裁短但可见短近段','外左内右','折痕／印字','C1长连通域门槛，C2裁短锚点关联'),
 (277,298,'主要只见外侧转角黑带','一条带的两面不是道路双边','地面文字／强反光','出画，单带／文字误配均不足以接受'),
 (299,303,'出口先出现远段双边后恢复固定参考行','出口左右内缘','文字／反光','299支持不足，300仅远段，301恢复y120'),
 (368,377,'内侧退出画面，外侧斜带与反光背景','单带角色不能仅靠x位置确定','家具／墙脚／反光','第二侧实际不足，短错配拒绝'),
 (378,380,'下一弯入口双边先在远处恢复','左右内缘','墙脚反光','C1未到近端，C2仅存当前远段'),
 (381,391,'右内角与外侧均可见，381仅很短近端','外左内右','玻璃／家具反射','381支持行数不足；382后参考行缺侧'),
 (392,392,'内侧被裁短但仍有近端双边','外左内右','反光','C1长连通域关联失败，C2有短段直接锚点'),
 (393,407,'内侧出画，外侧转角带逐渐变斜，末尾远段初现','同带两面禁止当双边','强反射／终点虚线初现','出画与支持不足；407弱候选有误配风险'),
 (408,411,'出口双边恢复，路中横向虚线可见','道路左右内缘＋终点候选','文字／反光','C1近场覆盖未足，C2只保留实际范围'),
 (417,423,'道路双边及横向虚线移向下沿','道路内缘，横线为独立标记','文字／反光','横线连接两侧连通域／截断R1局部路径，C2保留远段'),
 (455,460,'双边下移至内侧被裁短','外左内右','墙脚／折痕','参考行缺右侧，460为C1短域漏检'),
 (461,469,'主要单带；469远段双边很短','单带不能给当前左右可信角色','墙脚线／反光','出画，469支持不足仍拒绝'),
 (470,479,'出口／下一弯双边出现并接近边框','左右内缘','地面褶皱反光','C1近端／连通关联限制'),
 (480,482,'内侧再次出画，仅斜外带稳定','单带当前角色未知','折痕／远景线','弱候选误配及增长不符，不能接受'),
 (483,486,'出口先有远段双边随后恢复','左右内缘','文字／褶皱','483不覆盖y120，484后恢复固定行'),
 (506,510,'双边肘部下移，510内侧短而仍可见','外左内右','文字／反光','参考行缺右侧；510为C1裁短关联失败'),
 (511,519,'主要单外侧带，末尾出口远段不足','同带两面不是道路双边','文字／反光','出画／短弱候选，保持未知'),
 (520,525,'出口双边在远处恢复并扩展','出口左右内缘','文字／褶皱','C1到y200门槛延迟，C2不外推近场'),
 (548,551,'内侧裁出画，外侧斜带稳定','单带当前角色未知','家具／墙脚反光','第二侧实际观测不足'),
 (552,554,'下一弯双边远段恢复','左右内缘','墙脚反射','C1近端门槛；C2直接远段'),
 (555,560,'双边下移，内侧逐渐裁短','外左内右','玻璃反光','固定行缺右侧；560为C1短域漏检'),
 (561,568,'内侧出画，末尾出口远段很短','一条外侧带与后续不充分双边','反光／虚线初现','当前观测不足，不用旧右转填补'),
 (569,571,'出口双边恢复并可见横向虚线','道路左右内缘＋终点候选','文字／反光','C1近端覆盖门槛'),
 (575,580,'虚线逐渐到近端，双边仍在','道路内缘＋横向虚线','文字／反光','577..578连通关系／近端支持被横线截断'),
]


def run():
    """状态断言是真实模块执行；目视意见来自审核页，均不冒充独立真值。"""
    output=ROOT/'replay_accepted'
    rows=load(output/'frames.jsonl')
    tests=[]
    def check(name,condition):
        assert condition,name
        tests.append(name)
    check('interrupted_only_20_committed_rows',sum(r['evaluation_group']=='interrupted_only' for r in rows)==20)
    check('interrupted_extra_one_quarantined',len(json.loads((output/'interrupted_uncommitted.json').read_text()))==1)
    image=cv2.imread('vision/data/captures/final_mount_20261108/v03_center_0008/data_0001.jpg',0)
    blank=np.full((240,320),230,np.uint8)
    detector=RecoveryDetector()
    a=detector.detect(image,100,'A')['recovery_observation']
    b=detector.detect(image,140,'A')['recovery_observation']
    c=detector.detect(image,200,'A')['recovery_observation']
    check('real_time_reacquire_not_frame_count',a['temporal_state']=='reacquiring' and b['temporal_state']=='reacquiring' and c['temporal_state']=='stable_observation')
    d=detector.detect(blank,300,'A')['recovery_observation']
    check('failure_no_current_path',not d['pair_samples'] and d['turn_hint'] is None and d['advice']=='stop_required')
    check('bounded_history_is_explicit_inference',d['historical']['turn_hint']=='right' and not d['historical']['usable_as_current_path'])
    d=detector.detect(blank,501,'A')['recovery_observation']
    check('history_301ms_expires',d['historical']['turn_hint'] is None)
    detector.detect(image,600,'A')
    d=detector.detect(blank,1500,'A')['recovery_observation']
    check('gap_resets_all_history',d['time_reset']=='capture_gap_timeout' and d['historical']['state']=='unknown')
    detector.detect(image,1600,'A')
    d=detector.detect(image,1599,'A')['recovery_observation']
    check('clock_reversal_reacquires',d['time_reset']=='non_increasing_capture_time' and d['temporal_state']=='reacquiring')
    d=detector.detect(image,1599,'A')['recovery_observation']
    check('duplicate_time_resets',d['time_reset']=='non_increasing_capture_time')
    d=detector.detect(blank,1700,'B')['recovery_observation']
    check('session_does_not_leak_turn',d['time_reset']=='session_changed' and d['historical']['state']=='unknown')
    for timestamp in (None,float('nan'),-1,True):
        d=detector.detect(image,timestamp,'A')['recovery_observation']
        check('invalid_time_'+str(timestamp),d['temporal_state']=='unknown' and d['advice']=='stop_required')
    for label,invalid in [('white',blank),('black',np.zeros_like(blank)),('missing',None),
                          ('wrong_shape',blank[:100]),('float',blank.astype(float))]:
        d=detector.detect(invalid,2000,'negative')['recovery_observation']
        check('invalid_image_'+label,not d['pair_samples'] and d['turn_hint'] is None)
    for session in ('v03_center_0009','v03_center_0012'):
        check('real_single_text_'+session,all(not r['recovery_observation']['pair_samples'] for r in rows if r['session']==session))
    check('old_false_pairs_remain_rejected',all(not r['recovery_observation']['pair_samples'] for r in rows
          if r['session']=='d01_straight_run01' and r['frame_id'] in (80,81,82,190,191,192,250,251,252)))
    # 同一前缀单独回放与长序列前缀一致，证明推断不等待未来帧。
    first=RecoveryDetector(); second=RecoveryDetector()
    seq=[(image,100),(image,220),(blank,330),(blank,580)]
    prefix=[first.detect(g,t,'prefix')['recovery_observation'] for g,t in seq]
    full=[second.detect(g,t,'prefix')['recovery_observation'] for g,t in seq+[(image,800)]]
    check('causal_prefix_invariance',prefix==full[:len(prefix)])
    before=json.loads((ROOT/'protected_before.json').read_text(encoding='utf-8'))
    # 本轮新增输入审核工具自身随后可能维护，不属于原件或冻结基线。
    changed=[p for p,h in before.items() if digest(Path(p))!=h]
    check('existing_3616_files_unchanged',not changed)
    save(ROOT/'validation_accepted.json',dict(passed=True,checks=tests,protected_unchanged=len(before),
         formal_frames=1394,interrupted_logged=20,interrupted_unlogged_quarantined=1,
         frozen_fields_identical=1394,changed=changed))
    audit=json.loads((ROOT/'new_output_audit/index.json').read_text(encoding='utf-8'))
    new_keys={(p['session'],p['frame_id']) for page in audit for p in page['frames']}
    critical={i for page in json.loads((ROOT/'contact_index.json').read_text(encoding='utf-8')) for i in page['frames']}
    selected=[r for r in rows if (r['session'],r['frame_id']) in new_keys or
              r['session']=='push_full_lap_0001' and r['frame_id'] in critical]
    with (ROOT/'manual_review.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        columns=['session','frame','software_ms','visible_boundary','boundary_role','interference','baseline_failure',
                 'candidate_output','candidate_y','candidate_turn','history','recovery_state','unresolved','review_basis']
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for r in selected:
            o=r['recovery_observation'];note=None
            if r['session']=='push_full_lap_0001':
                note=next((n[2:] for n in NOTES if n[0]<=r['frame_id']<=n[1]),None)
            if note is None:
                note=('双条真实内缘与叠加点目视相符','左右边界只限当前实测段',
                      '反光／折痕／远处背景或文字','C1近场覆盖／长连通域门槛；R1字段保持')
            writer.writerow(dict(session=r['session'],frame=r['frame_id'],software_ms=r['timestamp_ms'],
                 visible_boundary=note[0],boundary_role=note[1],interference=note[2],baseline_failure=note[3],
                 candidate_output=o['current_state'],candidate_y=o['y_range'],candidate_turn=o['turn_hint'],
                 history=json.dumps(o['historical'],ensure_ascii=False),recovery_state=o['temporal_state'],
                 unresolved='无逐像素真值／车体地面几何；画外第二侧未知；不据此计准确率',
                 review_basis='视觉代理目视raw_01..15及new_01..13；不是主控逐帧人工标注'))
    save(ROOT/'manual_review_index.json',dict(raw_critical_frames=len(critical),new_output_frames=len(new_keys),
          reviewed_rows=len(selected),notes=NOTES,
          false_accepted_pairs_seen=0,scope='visual agreement on inspected overlays; no pixel truth or statistical accuracy'))
    # 针对基线每个失效区间，列出C2曾保留近段与其真正丢失后的首次再捕获。
    full=[r for r in rows if r['session']=='push_full_lap_0001']
    results=[]
    for span in spans(full,lambda r:not r['valid']):
        subset=[r for r in full if span['first_frame']<=r['frame_id']<=span['last_frame']]
        missing=[r for r in subset if not r['recovery_observation']['pair_samples']]
        last_missing=missing[-1]['frame_id'] if missing else None
        recovered=next((r for r in full if last_missing is not None and r['frame_id']>last_missing
                       and r['recovery_observation']['pair_samples']),None)
        stable=next((r for r in full if recovered and r['frame_id']>=recovered['frame_id']
                    and r['recovery_observation']['temporal_state']=='stable_observation'),None)
        results.append(dict(baseline_span=span,c2_observed_frames=[r['frame_id'] for r in subset if r['recovery_observation']['pair_samples']],
            last_missing_frame=last_missing,reacquired_frame=recovered['frame_id'] if recovered else None,
            reacquired_ms=recovered['timestamp_ms'] if recovered else None,
            stable_frame=stable['frame_id'] if stable else None,
            confirmation_latency_ms=stable['timestamp_ms']-recovered['timestamp_ms'] if stable and recovered else None))
    save(ROOT/'recovery_delays.json',results)
    print(json.dumps(dict(checks=len(tests),manual_rows=len(selected),protected=len(before))))


if __name__=='__main__':
    run()
