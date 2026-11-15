"""归档当前低速试跑候选的源码／实际构建／主机证据，不操作设备或远端。

固定输出首次创建，拒绝覆盖；原件只读。BIN来自刚完成的两目标实际构建，
记录哈希；不把保存产物称烧录成功、实体运行或比赛一圈验收。
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime
import cv2

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'vision/src'))
from lite_lap_route import LiteLapRoute


def main():
    destination=ROOT/'testing/2026-11-09_low_speed_lap/release_evidence'
    destination.mkdir(parents=True,exist_ok=False)
    files=('control/App/Motion/lap_motion.c','control/App/Motion/lap_motion.h',
        'control/Drivers_Custom/Communication/lap_link.c','control/Drivers_Custom/Communication/lap_link.h',
        'control/Drivers_Custom/Communication/lap_uart.c','control/Drivers_Custom/Communication/lap_uart.h',
        'control/Core/Src/low_speed_lap_main.c','control/MDK-ARM/low_speed_lap.uvprojx',
        'control/Tests/Host/test_lap_motion.c','control/Tests/Host/lap_packet_probe.c',
        'vision/src/lite_lap_route.py','vision/src/lap_protocol.py','vision/src/low_speed_lap_canmv.py',
        'vision/src/lap_uart_probe_canmv.py','vision/src/vision_protocol.py',
        'control/App/Motion/speed_match.c','control/Algorithms/Speed/speed_pi.c',
        'control/Drivers_Custom/Motor/straight_pwm.c','control/Drivers_Custom/Encoder/encoder_hw.c')
    hashes={}
    for name in files:
        source=ROOT/name; target=destination/'source'/name; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target); hashes[name]=hashlib.sha256(source.read_bytes()).hexdigest()
    logs=('control/build/low_speed_lap_tests.log','control/build/speed_match_tests.log',
        'control/build/speed_match_integration_tests.log','control/build/firmware/LowSpeedLap_build.log',
        'control/build/firmware/LowSpeedLapTrack_build.log','control/build/firmware/SpeedMatch_lap_regression.log')
    for name in logs:
        shutil.copy2(ROOT/name,destination/Path(name).name)
    firmware={}
    for name in ('low_speed_lap','low_speed_lap_track','speed_match'):
        binpath=ROOT/'control/build/firmware'/name/(name+'.bin')
        firmware[name]=dict(bytes=binpath.stat().st_size,sha256=hashlib.sha256(binpath.read_bytes()).hexdigest())
    # 与实板SD同一非连续30张选片，各图明确重置，valid始终不能作为实时许可。
    namespace={}; entry=(ROOT/'vision/src/low_speed_lap_canmv.py').read_text(encoding='utf-8')
    import ast
    parsed=ast.parse(entry)
    for node in parsed.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SD_FRAME_IDS' for t in node.targets):
            namespace['ids']=ast.literal_eval(node.value)
    detector=LiteLapRoute(); expected=[]
    for index in namespace['ids']:
        path=ROOT/'vision/data/captures/final_mount_20261108/push_full_lap_0001'/('data_%04d.jpg'%index)
        detector.reset(); result=detector.update(cv2.imread(str(path),0).tobytes(),0)
        expected.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),result=result,
            wire_valid=False,note='PC JPEG decode; compare board differences, not board/realtime acceptance'))
    (destination/'sd_expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=dict(date=datetime.now().astimezone().isoformat(),head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_hashes=hashes,firmware=firmware,board_tested=False,uart_tested=False,powered_tested=False,
        autonomous_lap_passed=False,drive_permission_default=False,
        formal_rule='competition/比赛文档.pdf section III, figure1/table1; goal basic60, evidence supports report20; no score claim')
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for name,digest in hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest: raise RuntimeError('source changed: '+name)
    print('archived local candidate evidence; all physical acceptance false')


if __name__=='__main__': main()
