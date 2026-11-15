"""L1有意义的失效／因果／协议检查，保存证据；不访问设备。

相同图片两次输入仅用于测试稳定门／确定性，不伪装真实高帧率录像。
真实五姿态和文字负例验证方向／拒绝行为，不据此宣称识别准确率。
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import cv2

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'vision/src'))
from lite_lap_route import LiteLapRoute
from lap_protocol import LapSender
from vision_protocol import crc16,encode_path


def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--bundle'); args=p.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    records=[]
    def check(name,condition,details=None):
        records.append(dict(name=name,passed=bool(condition),details=details))
        if not condition: raise AssertionError(name+': '+str(details))
    source=ROOT/'vision/data/captures/final_mount_20261108'
    if args.bundle:
        namespace={'__name__':'lap_bundle_validation'}
        bundle=Path(args.bundle); exec(compile(bundle.read_text(encoding='utf-8'),str(bundle),'exec'),namespace)
        detector=namespace['LiteLapRoute'](search_budget=namespace['SEARCH_BUDGET'])
    else:
        detector=LiteLapRoute()
    examples={}
    for name in ('v03_center_0002','v03_offset_left_0001','v03_offset_right_0001',
                 'v03_heading_left_0001','v03_heading_right_0001','v03_center_0009','v03_center_0012'):
        path=source/name/'data_0001.jpg'; data=cv2.imread(str(path),0).tobytes(); before=hashlib.sha256(data).hexdigest()
        detector.reset(); first=detector.update(data,0); second=detector.update(data,50)
        check(name+'_input_read_only',before==hashlib.sha256(data).hexdigest())
        check(name+'_first_frame_cannot_start',not first['valid'])
        examples[name]=dict(file=str(path.relative_to(ROOT)),sha256=before,first=first,second=second,
            note='same stored image repeated at synthetic 0/50ms only to test stable gate, not real camera stream')
    check('center_near_zero',abs(examples['v03_center_0002']['second']['steering'])<120)
    check('left_offset_turns_right',examples['v03_offset_left_0001']['second']['steering']>0)
    check('right_offset_turns_left',examples['v03_offset_right_0001']['second']['steering']<0)
    check('text_graphics_rejected',not examples['v03_center_0012']['second']['valid'])
    check('single_band_not_promoted_to_initial_pair',not examples['v03_center_0009']['second']['valid'])
    for shade in (0,255):
        detector.reset(); result=detector.update(bytes((shade,))*76800,0)
        check('uniform_'+str(shade)+'_invalid',not result['valid'] and result['source']=='unknown')
    data=cv2.imread(str(source/'v03_center_0002/data_0001.jpg'),0).tobytes()
    detector.reset(); detector.update(data,0); check('two_frame_stable',detector.update(data,50)['valid'])
    check('clock_reverse_clears_permission',not detector.update(data,40)['valid'])
    detector.update(data,90); check('gap_clears_permission',not detector.update(data,400)['valid'])
    detector.reset(); detector.update(data,0); detector.update(data,50)
    held=detector.update(bytes((255,))*76800,100)
    check('short_history_explicit',held['source']=='history')
    check('history_expires',not detector.update(bytes((255,))*76800,180)['valid'])
    result=examples['v03_center_0002']['second']; packets=[]
    sender=LapSender(allow_drive=True)
    packets.append(sender.path(result,20,30)); check('v2_header_length_crc',len(packets[-1])==20 and packets[-1][2]==2 and crc16(packets[-1][:18])==int.from_bytes(packets[-1][18:],'little'))
    check('explicit_source_age',int.from_bytes(packets[-1][10:12],'little')==30)
    check('drive_disabled_invalid',not (LapSender().path(result,20,30)[6]&1))
    check('processing_limit_invalid',not (sender.path(result,101,120)[6]&1))
    check('source_age_limit_invalid',not (sender.path(result,20,150)[6]&1))
    for value,source_kind in ((600,'current_pair'),(-600,'current_single_associated'),(600,'history')):
        r=dict(result,steering=value,source=source_kind); packets.append(sender.path(r,20,30))
        check('signed_'+str(value)+'_'+source_kind,int.from_bytes(packets[-1][8:10],'little',signed=True)==value)
    check('single_source_explicit',packets[-2][6]==9)
    check('history_source_explicit',packets[-1][6]==5)
    old=dict(result,source='history',evidence_age_ms=100)
    check('history_expired_source_not_refreshed',not (sender.path(old,5,21)[6]&1))
    history_packet=sender.path(old,5,10)
    check('history_reports_original_support_age',int.from_bytes(history_packet[10:12],'little')==110)
    packets.append(sender.stop()); check('stop_layout',len(packets[-1])==20 and packets[-1][16]==2)
    failed=False
    try: LapSender(lambda data:0,True).path(result,20,30)
    except OSError: failed=True
    check('zero_short_write_raises',failed)
    written=bytearray()
    def writer(data): written.extend(data[:3]); return min(3,len(data))
    p=LapSender(writer,True).path(result,20,30); check('partial_write_exact',bytes(written)==p)
    exe=output/'lap_packet_probe.exe'
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-I',str(ROOT/'control/Drivers_Custom/Communication'),
        str(ROOT/'control/Drivers_Custom/Communication/lap_link.c'),str(ROOT/'control/Drivers_Custom/Communication/protocol.c'),
        str(ROOT/'control/Tests/Host/lap_packet_probe.c'),'-o',str(exe)],check=True)
    bad=bytearray(packets[0]); bad[8]^=1
    stream=b'noise'+encode_path(1,error=0,valid=True,confidence=80)+bad+b''.join(packets)
    returned=subprocess.run([str(exe)],input=stream,capture_output=True,check=True).stdout.decode().splitlines()
    check('real_C_rejects_v1_bad_CRC_resyncs',len(returned)==len(packets),returned)
    (output/'checks.json').write_text(json.dumps(dict(checks=records,examples=examples,board_tested=False),ensure_ascii=False,indent=2),encoding='utf-8')
    print(str(len(records))+' L1 checks PASS; not board/lap acceptance')


if __name__=='__main__': main()
