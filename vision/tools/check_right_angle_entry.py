"""检查真实提前转向回归、连续入弯几何和路径失效保护，不连接板卡。

读取本次原始PGM和逐帧日志，以相同当前观测比较R7／新候选；模型输入
时间是明确的离线重放，不冒充真实闭环轨迹或K230执行耗时。
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from prepare_right_angle_bundle import build

ROOT=Path(__file__).resolve().parents[2]


def namespace(source):
    """加载单文件算法但不调用main；桌面没有相机／UART／驱动副作用。"""
    values={'__name__':'right_angle_entry_check'}
    exec(compile(source,'right_angle_entry_check','exec'),values)
    return values


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    candidate,manifest=build(True)
    new=namespace(candidate)
    old=namespace((ROOT/'testing/2026-11-18_right_angle/release_r7_storage/right_angle_drive.py').read_text(encoding='utf-8'))
    checks=[]
    def check(name,passed,detail=None):
        checks.append(dict(name=name,passed=bool(passed),detail=detail))
        if not passed:
            (args.output/'failed_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
            raise AssertionError(name+': '+str(detail))
    review=json.loads((ROOT/'testing/2026-11-18_right_angle/ground_06_review.json').read_text(encoding='utf-8'))
    corrections=[]
    for row in review['desktop_parameter_recomputation']:
        path=new['racing_route'](row['parameters'])
        # 这些是实际日志确认仍在圆弧入口之前的模型。只作同输入反事实，
        # 不声称新版本驾驶后仍会经历完全相同的帧或同样停止位置。
        check('actual_entry_phase_'+str(row['index']),path['phase']=='entry',path)
        check('actual_entry_no_forced_right_'+str(row['index']),path['steering']<=100,path['steering'])
        corrections.append(dict(index=row['index'],parameters=row['parameters'],
            old_actual=row['actual_sent_steering'],new_signed_route=path['steering'],
            entry_distance=path['entry_distance']))
    before=review['last_valid']; after=review['first_invalid']
    image_folder=ROOT/'testing/2026-11-18_right_angle/ground_06_camera'
    before_raw=(image_folder/'run_0002_loss_05_before.pgm').read_bytes()
    after_raw=(image_folder/'run_0002_loss_05_after.pgm').read_bytes()
    for raw in (before_raw,after_raw):
        check('original_PGM_layout_'+hashlib.sha256(raw).hexdigest()[:8],
              len(raw)==76815 and raw[:15]==b'P5\n320 240\n255\n')
    results={}
    for label,ns in (('R7',old),('candidate',new)):
        detector=ns['RightAngleRoute']()
        cx,cz,yaw,angle=before['parameters']
        c=cx*math.cos(yaw)-cz*math.sin(yaw)
        d=cx*math.sin(yaw)+cz*math.cos(yaw)
        detector.previous=ns['_corner_template'](c,d,yaw,angle)
        detector.stable=40; detector.stable_at=0
        detector.corner_at=1000-before['corner_age_ms']; detector.last_at=900
        first=detector.update(before_raw[15:],1000)
        second=detector.update(after_raw[15:],1000+after['elapsed_ms']-before['elapsed_ms'])
        results[label]=dict(before=first,after=second)
        check(label+'_real_before_supported',first['valid'],first)
        check(label+'_real_loss_still_rejected',not second['valid'],second)
    check('before_current_pair_can_correct_left',results['candidate']['before']['source']=='current_pair'
          and results['candidate']['before']['steering']<0,results['candidate']['before'])
    sender=new['RightAngleSender'](allow_drive=True)
    packet=sender.path(results['candidate']['before'],80,82)
    check('signed_pair_survives_v5_packet',packet[6]&1 and struct.unpack_from('<h',packet,8)[0]<0)
    check('failed_frame_still_withdraws_permission',not sender.path(results['candidate']['after'],71,74)[6]&1)
    check('no_forced_floor_in_actual_before',results['candidate']['before']['turn_floor']==0)
    # 无人工“最小右转”不等于取消弯道。车辆正好在半径30的圆弧上并与
    # 切线同向时，纯追踪的差速应为轮距/(2R)=14/60，独立验证几何方向。
    theta=math.radians(15); yaw=-theta
    qx=25-30*math.cos(theta); qz=-25+30*math.sin(theta)
    u=(math.sin(yaw),math.cos(yaw)); n=(u[1],-u[0])
    parameters=(-qx*n[0]-qz*u[0],-qx*n[1]-qz*u[1],yaw,math.pi/2)
    arc=new['racing_route'](parameters)
    check('true_arc_still_turns',arc['phase']=='arc' and abs(arc['steering']-1000*14/60)<2,arc)
    # 跨越旧cz=55阈值及实际切点时都不能出现几十个百分点的请求跳变。
    for label,a,b in (('old_distance_threshold',(0,55.001,0,math.pi/2),(0,54.999,0,math.pi/2)),
                      ('arc_entry_tangent',(5,25.001,0,math.pi/2),(5,24.999,0,math.pi/2))):
        left=new['racing_route'](a); right=new['racing_route'](b)
        check(label+'_continuous',abs(left['steering']-right['steering'])<=2,dict(before=left,after=right))
    # 失效没有变为许可、发送门槛不放宽；不需要重跑未改动的主板构建。
    good=dict(valid=True,source='current_pair',steering=100,bend=1000,confidence=75)
    check('processing_101_rejected',not sender.path(good,101,110)[6]&1)
    check('age_150_rejected',not sender.path(good,30,150)[6]&1)
    report=dict(checks=checks,manifest=manifest,actual_log_parameter_cases=corrections,
                actual_trigger_replay=results,
                limitations=['Desktop deterministic tests only; no K230 timing or new vehicle trajectory measured.',
                             'Original PATH rejection is retained rather than hidden by a relaxed geometry gate.',
                             'Model geometry and wheel track remain uncalibrated proxy units.'])
    (args.output/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(checks=len(checks),passed=all(r['passed'] for r in checks))))


if __name__=='__main__':
    main()
