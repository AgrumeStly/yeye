"""生成自包含CanMV预览／驱动许可副本与哈希；不写设备main.py。

仅提取已用网格函数，省去整圈模板类。6像素网格沿用既有实板R6配置；
模块开发默认4，两个配置都须在检查工具中验证真实图像。
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def build(allow_drive=False, *, voice=False):
    root = Path(__file__).resolve().parents[2]
    entry = 'straight_voice_canmv.py' if voice else 'straight_assist_canmv.py'
    names = ('vision_protocol.py', 'lite_lap_route.py', 'lap_protocol.py',
             'straight_route.py', 'straight_protocol.py', entry)
    version = 6 if voice else 3
    pieces = ['# 生成的语音直道 v6 入口，上电零驱动。\n' if voice else
              '# StraightAssist v3 generated file; no automatic motor START.\n']
    manifest = {}
    for name in names:
        raw = (root / 'vision/src' / name).read_bytes()
        manifest[name] = hashlib.sha256(raw).hexdigest()
        source = raw.decode('utf-8')
        if name == 'vision_protocol.py':
            # 原模块无设备操作，可整段合入；不修改原v1封包函数。
            pass
        if name == 'lite_lap_route.py':
            nodes = ast.parse(source).body
            helpers = ['from array import array', 'WIDTH=320', 'HEIGHT=240', 'GRID_STEP=6',
                       'GW=WIDTH//GRID_STEP', 'GH=HEIGHT//GRID_STEP',
                       'GY0=(40+GRID_STEP-1)//GRID_STEP', 'GY1=(228-3)//GRID_STEP+1']
            for node in nodes:
                if isinstance(node, ast.FunctionDef) and node.name in ('_threshold', '_grid', '_pair_anchors'):
                    helpers.append(ast.get_source_segment(source, node))
            source = '\n\n'.join(helpers)
        source = '\n'.join(line for line in source.splitlines() if not line.startswith(
            ('from lite_lap_route import ', 'from lap_protocol import ', 'from vision_protocol import ',
             'from straight_route import ', 'from straight_protocol import ')))
        if name == 'straight_assist_canmv.py' and allow_drive:
            source = source.replace('ALLOW_DRIVE = False', 'ALLOW_DRIVE = True').replace('SHOW_PREVIEW = True', 'SHOW_PREVIEW = False')
        pieces.append('\n# BEGIN ' + name + '\n' + source + '\n')
    text = ''.join(pieces)
    compile(text, 'straight_assist_bundle', 'exec')
    manifest.update(bundle_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                    allow_drive=allow_drive or voice, wire_version=version, grid_step=6,
                    automatic_motor_start=False, voice_motor_start=voice)
    return text, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--voice', action='store_true', help='生成语音直道 v6 的车载 main.py')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    outputs = ((True, 'main.py'),) if args.voice else ((False, 'straight_preview.py'), (True, 'straight_drive.py'))
    for allow, name in outputs:
        text, info = build(allow, voice=args.voice)
        (args.output / name).write_bytes(text.encode('utf-8'))
        (args.output / (name + '.manifest.json')).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
