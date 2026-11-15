"""生成无动力UART联调字节夹具；仅写新目录，不打开任何串口。"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from vision_protocol import encode_command,encode_path
from review_recovery_inputs import save


def run(output):
    """有效固定包仅供明确无动力台架；不能把夹具发送当真实识别或运动验收。"""
    output.mkdir(parents=True,exist_ok=False)
    samples=dict(path_center=encode_path(1,valid=True,confidence=80,processing_ms=20),
       path_right=encode_path(2,error=600,valid=True,confidence=80,processing_ms=20),
       path_left=encode_path(3,error=-600,valid=True,confidence=80,processing_ms=20),
       path_invalid=encode_path(4),
       path_slow_101=encode_path(5,valid=True,confidence=80,processing_ms=101),
       path_low_quality_39=encode_path(6,valid=True,confidence=39,processing_ms=20),
       path_finish_candidate=encode_path(7,valid=True,confidence=80,processing_ms=20,finish=True),
       start=encode_command(1,1),stop=encode_command(2,2),status=encode_command(3,3),
       path_sequence_255=encode_path(255,valid=True,confidence=80,processing_ms=20),
       path_sequence_0=encode_path(0,valid=True,confidence=80,processing_ms=20))
    corrupted=bytearray(samples['path_right']);corrupted[8]^=1
    samples['bad_crc']=bytes(corrupted)
    for name,data in samples.items():(output/(name+'.bin')).write_bytes(data)
    save(output/'fixtures.json',dict(scope='offline bytes only; no serial port or motion',
         samples={name:dict(bytes=len(data),hex=data.hex(' ').upper()) for name,data in samples.items()},
         order_notes='Reset software state between independent scenarios. Do not blindly transmit all fixtures as one script.'))
    print(output.as_posix())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
