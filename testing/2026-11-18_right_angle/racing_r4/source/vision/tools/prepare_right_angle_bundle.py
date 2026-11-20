"""生成首弯CanMV独立单文件及来源哈希；不访问板卡、不覆盖main.py。"""
import argparse
import hashlib
import json
from pathlib import Path


def build(allow_drive=False):
    root = Path(__file__).resolve().parents[2]
    names = ('vision_protocol.py', 'lite_lap_route.py', 'lap_protocol.py', 'right_angle_racing.py',
             'right_angle_route.py', 'right_angle_protocol.py', 'right_angle_canmv.py')
    parts = ['# RightAngle v5 current L corner + racing arc; KEY start only.\n']
    manifest = {}
    for name in names:
        raw = (root/'vision/src'/name).read_bytes()
        manifest[name] = hashlib.sha256(raw).hexdigest()
        source = raw.decode('utf-8')
        if name == 'lite_lap_route.py':
            # 合入已有投影、网格、模板函数，不合入完整赛道观察器。
            source = source[:source.index('class LiteLapRoute:')].replace('GRID_STEP=4', 'GRID_STEP=6')
        if name == 'right_angle_route.py':
            source = source.replace('from lite_lap_route import (_threshold, _grid, _pair_anchors, _template,\n'
                                    '                            _anchor_distance, _hypot, _point, _pixel)\n', '')
        source = '\n'.join(line for line in source.splitlines() if not line.startswith(
            ('from lap_protocol import ', 'from vision_protocol import ',
             'from right_angle_route import ', 'from right_angle_protocol import ')))
        source = '\n'.join(line for line in source.splitlines() if not line.startswith('from right_angle_racing import '))
        if name == 'right_angle_canmv.py' and allow_drive:
            source = source.replace('ALLOW_DRIVE = False', 'ALLOW_DRIVE = True').replace('SHOW_PREVIEW = True', 'SHOW_PREVIEW = False')
        parts.append('\n# BEGIN '+name+'\n'+source+'\n')
    source = ''.join(parts)
    compile(source, 'right_angle_bundle', 'exec')
    manifest.update(bundle_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
                    wire_version=5, grid_step=6, allow_drive=allow_drive, automatic_motor_start=False)
    return source, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    for drive, name in ((False, 'right_angle_preview.py'), (True, 'right_angle_drive.py')):
        source, manifest = build(drive)
        # Windows文本模式会把LF改为CRLF；按UTF-8字节写入以保持manifest哈希一致。
        (args.output/name).write_bytes(source.encode('utf-8'))
        (args.output/(name+'.manifest.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
