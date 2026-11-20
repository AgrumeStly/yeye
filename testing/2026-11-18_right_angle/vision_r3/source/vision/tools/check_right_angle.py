"""首弯离线检查：真实静态方向、当前单边过渡、空白拒绝、v4生产解析互通。

静态重复和40ms重定时仅验证算法分支，不作为真实帧率或自主过弯证据。
同时保存原时间轴回放，原图间隔超150ms必须撤销稳定许可。
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import cv2
from prepare_right_angle_bundle import build

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    ns = {'__name__': 'right_angle_host'}
    source, manifest = build(True)
    exec(compile(source, 'right_angle_drive.py', 'exec'), ns)
    checks = []
    def check(name, condition, detail=None):
        checks.append(dict(name=name, passed=bool(condition), detail=detail))
        if not condition: raise AssertionError(name+': '+str(detail))
    check('drive_explicit_no_preview', ns['ALLOW_DRIVE'] and not ns['SHOW_PREVIEW'])
    preview = {'__name__': 'preview_host'}
    exec(build(False)[0], preview)
    check('preview_no_permission', not preview['ALLOW_DRIVE'])
    folder = ROOT/'vision/data/captures/final_mount_20261108'
    def pixels(path):
        frame = cv2.imread(str(path), 0)
        if frame is None: raise FileNotFoundError(path)
        return frame.tobytes()
    observations = []
    for name, sign in (('v03_center_0002',0),('v03_offset_left_0001',1),
                       ('v03_offset_right_0001',-1),('v03_heading_left_0001',1),
                       ('v03_heading_right_0001',-1)):
        for index in (1,2,3):
            path = folder/name/('data_%04d.jpg'%index)
            data = pixels(path); before = hashlib.sha256(data).hexdigest()
            detector = ns['RightAngleRoute']()
            results = [detector.update(data,t) for t in (0,40,80)]
            r = results[-1]
            check(name+str(index)+'_stable_gate', not results[0]['valid'] and not results[1]['valid'] and r['valid'], r)
            check(name+str(index)+'_direction', abs(r['steering']) < 100 if sign == 0 else r['steering']*sign > 0, r)
            check(name+str(index)+'_read_only', hashlib.sha256(data).hexdigest() == before)
            observations.append(dict(file=str(path.relative_to(ROOT)), sha256=before, result=r))
    for name in ('v03_center_0009','v03_center_0012'):
        detector = ns['RightAngleRoute']()
        for t in (0,40,80): r = detector.update(pixels(folder/name/'data_0001.jpg'), t)
        check(name+'_rejected', not r['valid'])
    center = pixels(folder/'v03_center_0002/data_0001.jpg')
    # 优化只缓存几何，不缓存当前像素评分；验证距离数学等价与固定内存边界。
    detector = ns['RightAngleRoute']()
    black, _, _ = ns['_grid'](center, ns['_threshold'](center))
    anchors = ns['_pair_anchors'](black)
    worst = max(abs(ns['_current_anchor_distance'](t,anchors)-ns['_anchor_distance'](t,anchors))
                for t in detector.templates)
    check('anchor_distance_equivalent', worst < 1e-7, worst)
    near = pixels(folder/'push_full_lap_0001/data_0101.jpg')
    for tick in range(0,800,40):
        r = detector.update(near,tick)
        if tick >= 80:
            check('cached_geometry_current_support_'+str(tick), r['valid'] and r['source']=='current_pair', r)
            check('tracking_candidate_budget_'+str(tick), r['search_mode']=='tracking' and r['searched_candidates']<=52, r['searched_candidates'])
        check('bounded_geometry_cache_'+str(tick), len(detector.neighbors)<=6 and len(detector.refinements)<=27)
    r = detector.update(bytes((255,))*76800,800)
    check('cache_does_not_preserve_permission', not r['valid'] and not detector.neighbors and not detector.refinements)
    for shade in (0,80,255):
        detector = ns['RightAngleRoute']()
        for t in (0,40,80): detector.update(center,t)
        check('uniform_'+str(shade)+'_no_hold', not detector.update(bytes((shade,))*76800,120)['valid'])
        check('reacquire_needs_stability_'+str(shade), not detector.update(center,160)['valid'])
    detector = ns['RightAngleRoute']()
    for t in (0,40,80): detector.update(center,t)
    check('gap_revokes', not detector.update(center,300)['valid'])
    check('clock_reverse_revokes', not detector.update(center,280)['valid'])
    check('bad_buffer_revokes', not detector.update(bytes(5),320)['valid'])
    sequence = []
    detector = ns['RightAngleRoute']()
    lap_folder = folder/'push_full_lap_0001'
    # 原真实首弯图81..125重定时，检验当前单侧与右转符号；不当作闭环仿真。
    for index in range(81,126):
        r = detector.update(pixels(lap_folder/('data_%04d.jpg'%index)),(index-81)*40)
        sequence.append(dict(frame=index, result=r))
    check('approach_detected', any(row['result']['valid'] and row['result']['stage']=='approach' for row in sequence))
    singles = [row['result'] for row in sequence if row['result']['valid'] and row['result']['source']=='current_single_associated']
    check('current_corner_single_transition', bool(singles) and all(r['bend']==1000 for r in singles))
    check('right_turn_command_seen', any(r['steering']>500 for r in singles))
    check('blank_after_corner_revokes', not detector.update(bytes((255,))*76800,1800)['valid'])
    # 同一近弯单侧图不能冷启动获得运动许可。
    detector = ns['RightAngleRoute']()
    for t in (0,40,80): r = detector.update(pixels(lap_folder/'data_0116.jpg'),t)
    check('single_cannot_initialize', not r['valid'])
    actual = []
    detector = ns['RightAngleRoute']()
    for line in (lap_folder/'frames.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        if not 81 <= row['frame_id'] <= 150: continue
        r = detector.update(pixels(lap_folder/row['file']),row['elapsed_ms'])
        actual.append(dict(frame=row['frame_id'], elapsed_ms=row['elapsed_ms'], result=r))
    good = dict(valid=True, source='current_pair', steering=700,bend=1000,confidence=75)
    sender = ns['RightAngleSender'](allow_drive=True)
    packets = [sender.path(good,30,40),sender.path(dict(good,source='current_single_associated'),30,40),sender.stop()]
    for index,p in enumerate(packets):
        check('v4_crc_'+str(index),p[2]==4 and len(p)==20 and ns['crc16'](p[:18])==int.from_bytes(p[18:],'little'))
    for source_kind in ('history','unknown'):
        check(source_kind+'_rejected',not sender.path(dict(good,source=source_kind),30,40)[6]&1)
    check('processing_deadline',not sender.path(good,101,110)[6]&1)
    check('image_age_deadline',not sender.path(good,30,150)[6]&1)
    check('single_image_age_deadline',not sender.path(dict(good,source='current_single_associated'),30,120)[6]&1)
    check('preview_packet_invalid',not preview['RightAngleSender'](allow_drive=False).path(good,30,40)[6]&1)
    probe = args.output/'packet_probe.exe'
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-DRIGHT_ANGLE_TARGET=1',
                    '-I'+str(ROOT/'control/Drivers_Custom/Communication'),
                    str(ROOT/'control/Drivers_Custom/Communication/lap_link.c'),
                    str(ROOT/'control/Drivers_Custom/Communication/protocol.c'),
                    str(ROOT/'control/Tests/Host/lap_packet_probe.c'),'-o',str(probe)],check=True)
    old = []
    for version in (2,3):
        p = bytearray(packets[0]); p[2]=version; p[18:]=ns['crc16'](p[:18]).to_bytes(2,'little'); old.append(p)
    returned = subprocess.run([str(probe)],input=b'noise'+b''.join(old+packets),capture_output=True,check=True).stdout.decode().splitlines()
    check('production_v4_isolation', len(returned)==3,returned)
    result = dict(checks=checks, manifest=manifest, static_observations=observations,
                  retimed_branch_checks=sequence, original_timestamps=actual,
                  limitations=['static repeats and retimed sequence are branch checks only',
                               'original hand-push timestamps and all invalid frames retained',
                               'no board timing or autonomous corner validation performed'])
    (args.output/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RightAngle vision:',len(checks),'checks PASS; board and ground untested')


if __name__ == '__main__':
    main()
