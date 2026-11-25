"""生成首弯CanMV独立单文件及来源哈希；不访问板卡、不覆盖main.py。"""
import argparse
import hashlib
import json
import wave
from pathlib import Path


def build(allow_drive=False, *, voice=False, joint=False):
    root = Path(__file__).resolve().parents[2]
    voice = voice or joint
    names = ('vision_protocol.py', 'lite_lap_route.py', 'lap_protocol.py', 'right_angle_racing.py', 'right_angle_grid.py',
             'right_angle_route.py', 'right_angle_protocol.py')
    if voice:
        names = (*names[:5], 'right_angle_prediction.py', *names[5:], 'voice_keywords.py')
        if joint:
            names = (*names[:6], 'straight_route.py', *names[6:])
        if not joint:
            names += ('right_angle_phone.py',)
        names += ('right_angle_voice_canmv.py',)
    else:
        names += ('right_angle_canmv.py',)
    parts = ['# 语音首弯 v9。等待本地 Go。\n' if voice else
             '# RightAngle v5 current L corner + racing arc; KEY start only.\n']
    manifest = {}
    if joint:
        parts[0] = '# 直角＋钝角联合弯 v12，等待本地 Go。\n'
        asset = root / 'vision/assets/go_received.wav'
        with wave.open(str(asset), 'rb') as reply:
            pcm = reply.readframes(reply.getnframes())
        # 把“收到”的PCM嵌入同一个main.py，视觉板无需另传声音文件或修改热点设置。
        parts.append('GO_RECEIVED_PCM = (\n' + ''.join('    %r\n' % pcm[i:i + 80]
                     for i in range(0, len(pcm), 80)) + ')\n')
        manifest['go_received.wav'] = hashlib.sha256(asset.read_bytes()).hexdigest()
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
             'from right_angle_route import ', 'from right_angle_protocol import ', 'from voice_keywords import ',
             'from right_angle_prediction import ', 'from right_angle_phone import ', 'from straight_route import ')))
        source = '\n'.join(line for line in source.splitlines() if not line.startswith(
            ('from right_angle_racing import ', 'from right_angle_grid import ',
             'from lite_lap_route import ')))
        if name == 'right_angle_canmv.py' and allow_drive:
            source = source.replace('ALLOW_DRIVE = False', 'ALLOW_DRIVE = True').replace('SHOW_PREVIEW = True', 'SHOW_PREVIEW = False')
            # 正式视觉必须覆盖摆车、双轮测试和等待；不因10分钟窗口在KEY前悄悄退出。
            # 仅延长视觉寿命，不发送START，不改变主板动作时限或许可失效条件。
            source = source.replace('DURATION_MS = 600000', 'DURATION_MS = 0')
        if name == 'right_angle_voice_canmv.py' and joint:
            source = source.replace("if __name__ == '__main__':\n    main()",
                                    "if __name__ == '__main__':\n    main(joint=True, go_pcm=GO_RECEIVED_PCM)")
        parts.append('\n# BEGIN '+name+'\n'+source+'\n')
    source = ''.join(parts)
    compile(source, 'right_angle_bundle', 'exec')
    manifest.update(bundle_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
                    wire_version=12 if joint else (9 if voice else 5), grid_step=6, allow_drive=allow_drive or voice,
                    automatic_motor_start=False, duration_ms=0 if voice or allow_drive else 600000)
    if voice:
        manifest['voice_motor_start'] = True
    if joint:
        manifest['phone_preview'] = False
    return source, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument('--voice', action='store_true', help='生成语音首弯 v9 的车载 main.py')
    targets.add_argument('--joint', action='store_true', help='生成直角和钝角联合弯的车载 main.py')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    outputs = ((True, 'main.py'),) if args.voice or args.joint else (
        (False, 'right_angle_preview.py'), (True, 'right_angle_drive.py'))
    for drive, name in outputs:
        source, manifest = build(drive, voice=args.voice, joint=args.joint)
        # Windows文本模式会把LF改为CRLF；按UTF-8字节写入以保持manifest哈希一致。
        (args.output/name).write_bytes(source.encode('utf-8'))
        (args.output/(name+'.manifest.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
