"""离线核对官方CM图像载荷解析与主机保存边界，不使用板卡或电机。

这里只测试传输封装，合成标记字节不是相机JPEG，不作真实视觉证据。
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import queue
import struct
import unittest.mock

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); args=p.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('lap_preview_transport',ROOT/'vision/tools/canmv_lap_bench.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    session=module.Session.__new__(module.Session)
    session.output=output; session.messages=queue.Queue(); session.capture_preview=False
    session.preview_saved=0; session.preview_next_at=0.0; session.preview_invalid=0
    checks=[]; clock=[0.0]
    def check(name,ok):
        checks.append(dict(name=name,passed=bool(ok)))
        if not ok: raise AssertionError(name)
    jpeg=b'\xff\xd8HOST-TEST-MARKERS-ONLY\xff\xd9'
    packet=struct.pack('<I',42)+jpeg+b'wire-tail'
    with unittest.mock.patch.object(module.time,'monotonic',side_effect=lambda:clock[0]):
        session._save_preview(packet)
        check('disabled_no_files',session.preview_saved==0 and not (output/'preview').exists())
        session.capture_preview=True
        for body in (b'',b'bad-data',struct.pack('<I',1)+b'\xff\xd8no-end',b'x'*(5*1024*1024+1)):
            session._save_preview(body)
        check('invalid_payloads_rejected',session.preview_saved==0 and session.preview_invalid==4)
        session._save_preview(packet)
        event=session.messages.get_nowait(); file=output/event['params']['file']
        check('exact_jpeg_bytes_exclude_transport',file.read_bytes()==jpeg)
        check('little_endian_frame_id_and_hash',event['params']['frame_id']==42 and event['params']['sha256']==hashlib.sha256(jpeg).hexdigest())
        clock[0]=.5; session._save_preview(packet)
        check('one_second_sampling',session.preview_saved==1 and session.messages.empty())
        for i in range(1,9): clock[0]=float(i); session._save_preview(packet)
        check('five_image_cap_and_no_overwrite',session.preview_saved==5 and len(list((output/'preview').glob('*.jpg')))==5)
        # 存盘失败不能抛出并终止读取脚本状态的线程。
        session.preview_saved=0; session.preview_next_at=0.0
        with unittest.mock.patch.object(module.Path,'write_bytes',side_effect=OSError('host test write failure')):
            session._save_preview(packet)
        check('io_failure_disables_capture',not session.capture_preview)
        events=[]
        while not session.messages.empty(): events.append(session.messages.get_nowait())
        check('io_failure_reported',any(e.get('event')=='previewSaveError' for e in events))
    (output/'checks.json').write_text(json.dumps(dict(checks=checks,physical_board_used=False,real_camera_images=False),indent=2),encoding='utf-8')
    print(str(len(checks))+' preview transport checks PASS; no board/backend/camera/motor')


if __name__=='__main__': main()
