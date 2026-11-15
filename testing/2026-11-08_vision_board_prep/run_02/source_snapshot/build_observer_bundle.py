"""将诊断核、协议和入口打包成独立CanMV脚本，不部署、不改main.py。"""

import argparse
import ast
from pathlib import Path

from review_recovery_inputs import digest,save


def build(output):
    """保留中文注释／默认idle；只去掉已内嵌的两个本地导入，拒绝覆盖。"""
    output.mkdir(parents=True,exist_ok=False)
    paths=[Path('vision/src/board_observer_core.py'),Path('vision/src/vision_protocol.py'),
           Path('vision/src/observer_bench_canmv.py')]
    contents=[]
    for path in paths:
        source=path.read_text(encoding='utf-8')
        source=source.replace('from board_observer_core import detect_gray\n','')
        source=source.replace('from vision_protocol import RecognitionSender\n','')
        contents.append('# SOURCE: '+path.as_posix()+'\n'+source)
    target=output/'observer_bench_canmv.py'
    target.write_text('\n\n'.join(contents),encoding='utf-8')
    ast.parse(target.read_text(encoding='utf-8'))
    save(output/'manifest.json',dict(sources={p.as_posix():digest(p) for p in paths},
         bundle=target.as_posix(),sha256=digest(target),mode='idle',UART_ENABLED=False,
         board_run=False,main_py_changed=False,control_ready=False))
    print(target.as_posix())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output)
