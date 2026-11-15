"""合并悬空固定输入台架脚本，保留默认ENABLED=False；不写板卡。

该产物只测试动力调用链，和相机脚本／实际图像候选隔离保存。主控已确认
轮子悬空和MCU 3000ms上限后才可手动开启，协议本身不证明这些实物条件。
"""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('--output',required=True); args=p.parse_args()
root=Path(__file__).resolve().parents[2]; output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
parts=['# Suspended motor fixture only; NOT CAMERA; default IDLE; never START\n']; hashes={}
for name in ('vision_protocol.py','lap_protocol.py','lap_motor_bench_canmv.py'):
    source=root/'vision/src'/name; hashes[name]=hashlib.sha256(source.read_bytes()).hexdigest()
    lines=[line for line in source.read_text(encoding='utf-8').splitlines() if not line.startswith(('from vision_protocol import','from lap_protocol import'))]
    parts.extend(['\n# BEGIN '+name+'\n','\n'.join(lines)+'\n'])
path=output/'lap_motor_bench_canmv.py'; path.write_text(''.join(parts),encoding='utf-8')
compile(path.read_text(encoding='utf-8'),str(path),'exec')
hashes['bundle_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
hashes['purpose']='suspended 3-second motor chain fixture; NOT CAMERA; operator KEY only; no START'
(output/'manifest.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf-8')
print(path)
