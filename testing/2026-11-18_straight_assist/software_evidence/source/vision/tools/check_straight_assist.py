"""直道真实静态图／负例／失效与Python到生产C解析器交叉检查，无设备访问。"""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import types
import cv2
import numpy as np
from prepare_straight_bundle import build

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'vision/src'))
from straight_route import StraightRoute as ModularStraightRoute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checks = []
    examples = []

    def check(name, condition, detail=None):
        checks.append(dict(name=name, passed=bool(condition), detail=detail))
        if not condition:
            raise AssertionError(name + ': ' + str(detail))

    namespace = {'__name__': 'straight_test_host'}
    candidate, manifest = build(True)
    exec(compile(candidate, 'straight_drive.py', 'exec'), namespace)
    check('drive_variant_explicit_and_no_preview', namespace['ALLOW_DRIVE'] and not namespace['SHOW_PREVIEW'])
    check('no_entire_lap_templates', 'LiteLapRoute' not in namespace)
    preview = {'__name__': 'straight_preview_host'}
    exec(compile(build(False)[0], 'straight_preview.py', 'exec'), preview)
    check('preview_has_no_drive_permission', not preview['ALLOW_DRIVE'] and preview['SHOW_PREVIEW'])
    source = ROOT / 'vision/data/captures/final_mount_20261108'
    # 15张五姿态原图均独立输入；重复一张只验证时间稳定门，不伪称动态录像。
    for name, expected in (('v03_center_0002', 0), ('v03_offset_left_0001', 1),
                           ('v03_offset_right_0001', -1), ('v03_heading_left_0001', 1),
                           ('v03_heading_right_0001', -1)):
        for number in range(1, 4):
            path = source / name / ('data_%04d.jpg' % number)
            pixels = cv2.imread(str(path), 0).tobytes()
            before = hashlib.sha256(pixels).hexdigest()
            detector = namespace['StraightRoute']()
            first = detector.update(pixels, 0)
            second = detector.update(pixels, 40)
            result = detector.update(pixels, 80)
            check(name + str(number) + '_three_frame_gate', not first['valid'] and not second['valid'] and result['valid'], result)
            check(name + str(number) + '_sign', abs(result['steering']) < 80 if expected == 0 else result['steering'] * expected > 0, result['steering'])
            check(name + str(number) + '_input_read_only', before == hashlib.sha256(pixels).hexdigest())
            modular = ModularStraightRoute()
            for tick in (0, 40, 80):
                original = modular.update(pixels, tick)
            check(name + str(number) + '_4px_module_also_valid', original['valid'] and
                  (abs(original['steering']) < 80 if expected == 0 else original['steering'] * expected > 0), original)
            examples.append(dict(file=str(path.relative_to(ROOT)), sha256=before, observation=result))
    center = cv2.imread(str(source / 'v03_center_0002/data_0001.jpg'), 0).tobytes()
    for folder in ('v03_center_0009', 'v03_center_0012'):
        detector = namespace['StraightRoute']()
        pixels = cv2.imread(str(source / folder / 'data_0001.jpg'), 0).tobytes()
        for tick in (0, 40, 80):
            result = detector.update(pixels, tick)
        check(folder + '_negative_rejected', not result['valid'], result)
    for shade in (0, 80, 255):
        detector = namespace['StraightRoute']()
        for tick in (0, 40, 80):
            result = detector.update(bytes((shade,)) * 76800, tick)
        check('uniform_' + str(shade) + '_rejected', not result['valid'])
    # 合成折角与直道共用近似投影，用于检查折角拒绝；不代表真实转角识别率。
    def synthetic(corner):
        frame = np.full((240, 320), 220, dtype=np.uint8)
        for side in (-25, 25):
            points = []
            for y in range(65, 222):
                z = (7802.22222222222 - 15.555555555555546 * y) / (y + 38.11111111111108)
                center_x = 0 if not corner else max(0, z - 32) * 0.7
                x = round(159.5 + (side + center_x) * (y + 38.11111111111108) / 48)
                points.append((x, y))
            cv2.polylines(frame, [np.array(points, dtype=np.int32)], False, 10, 7)
        return frame.tobytes()
    for corner in (False, True):
        detector = namespace['StraightRoute']()
        for tick in (0, 40, 80):
            result = detector.update(synthetic(corner), tick)
        check('synthetic_corner_' + str(corner), result['valid'] != corner, result)
    detector = namespace['StraightRoute']()
    for tick in (0, 40, 80):
        detector.update(center, tick)
    check('loss_has_no_history', not detector.update(bytes((255,)) * 76800, 120)['valid'])
    check('loss_requires_new_stabilization', not detector.update(center, 160)['valid'])
    check('clock_reverse_revokes', not detector.update(center, 150)['valid'])
    check('clock_gap_revokes', not detector.update(center, 400)['valid'])
    check('bad_buffer_revokes', not detector.update(bytes(10), 440)['valid'])
    good = dict(valid=True, source='current_pair', steering=200, bend=0, confidence=80)
    sender = namespace['StraightSender'](allow_drive=True)
    packets = [sender.path(good, 10, 20), sender.path(dict(good, steering=-200), 10, 20), sender.stop()]
    for index, packet in enumerate(packets):
        check('v3_crc_' + str(index), len(packet) == 20 and packet[2] == 3 and namespace['crc16'](packet[:18]) == int.from_bytes(packet[18:], 'little'))
    for name, changed, process, age in (('single', dict(good, source='current_single_associated'), 10, 20),
                                       ('history', dict(good, source='history'), 10, 20),
                                       ('bend', dict(good, bend=1), 10, 20),
                                       ('old', good, 10, 150), ('slow', good, 101, 110)):
        check(name + '_cannot_drive', not sender.path(changed, process, age)[6] & 1)
    check('preview_wire_invalid', not preview['StraightSender'](allow_drive=False).path(good, 10, 20)[6] & 1)
    pieces = []
    def short_write(data):
        pieces.append(data[:3])
        return min(3, len(data))
    packet = namespace['StraightSender'](short_write, True).path(good, 10, 20)
    check('short_write_reassembles_exact_frame', b''.join(pieces) == packet)
    try:
        namespace['StraightSender'](lambda data: 0, True).path(good, 10, 20)
    except OSError:
        check('zero_write_raises', True)
    else:
        check('zero_write_raises', False)
    # 将Python真封包交给v3生产C滑窗解析器，验证版本隔离及有符号字段。
    probe = args.output / 'packet_probe.exe'
    subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-DSTRAIGHT_ASSIST_TARGET=1',
                    '-I' + str(ROOT / 'control/Drivers_Custom/Communication'),
                    str(ROOT / 'control/Drivers_Custom/Communication/lap_link.c'),
                    str(ROOT / 'control/Drivers_Custom/Communication/protocol.c'),
                    str(ROOT / 'control/Tests/Host/lap_packet_probe.c'), '-o', str(probe)], check=True)
    old = bytearray(packets[0])
    old[2] = 2
    old[18:] = namespace['crc16'](old[:18]).to_bytes(2, 'little')
    output = subprocess.run([str(probe)], input=b'noise' + bytes(old) + b''.join(packets), capture_output=True, check=True).stdout.decode().splitlines()
    check('production_C_accepts_only_v3_frames', len(output) == 3, output)
    check('signed_positive_negative_exact', output[:2] == ['1 0 1 200 0', '1 1 1 56 255'], output)
    # 执行真实主循环，设备替身只验证资源清理／异常STOP，不代表板上时序。
    saved = {name: sys.modules.get(name) for name in ('machine', 'media', 'media.sensor', 'media.display', 'media.media', 'image')}
    writes = []
    cleanups = []
    class Clock:
        current = 0
        @classmethod
        def ticks_ms(cls):
            cls.current += 1
            return cls.current
        @staticmethod
        def ticks_diff(a, b):
            return a - b
        @staticmethod
        def sleep_ms(ms):
            pass
    class Sensor:
        GRAYSCALE = 1
        def __init__(self, **kw):
            self.count = 0
        def snapshot(self, **kw):
            self.count += 1
            Clock.current += 40
            if self.count > 6:
                raise RuntimeError('injected camera failure')
            return types.SimpleNamespace(width=lambda: 320, height=lambda: 240, format=lambda: 1, bytearray=lambda: center)
        def stop(self):
            cleanups.append('sensor')
        def __getattr__(self, name):
            return lambda *a, **kw: None
    class UART:
        UART2 = 2
        EIGHTBITS = 8
        PARITY_NONE = 0
        STOPBITS_ONE = 1
        def __init__(self, *a, **kw):
            pass
        def write(self, data):
            writes.append(bytes(data))
            return len(data)
        def deinit(self):
            cleanups.append('uart')
    class Mapping:
        UART2_TXD = 11
        UART2_RXD = 12
        def set_function(self, *a):
            pass
    stream = io.StringIO()
    try:
        sys.modules['machine'] = types.SimpleNamespace(UART=UART, FPIOA=Mapping)
        sys.modules['media'] = types.ModuleType('media')
        sys.modules['media.sensor'] = types.SimpleNamespace(Sensor=Sensor, CAM_CHN_ID_0=0)
        sys.modules['media.display'] = types.SimpleNamespace(Display=types.SimpleNamespace(VIRT=1, init=lambda *a, **k: None, deinit=lambda: cleanups.append('display')))
        sys.modules['media.media'] = types.SimpleNamespace(MediaManager=types.SimpleNamespace(init=lambda: None, deinit=lambda: cleanups.append('media')))
        sys.modules['image'] = types.SimpleNamespace(GRAYSCALE=1)
        namespace['time'] = Clock
        namespace['os'] = types.SimpleNamespace(exitpoint=lambda: None)
        namespace['_open_log'] = lambda: ('host_fake_log', types.SimpleNamespace(write=stream.write, flush=lambda: None, close=lambda: cleanups.append('log')))
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                namespace['main']()
            except RuntimeError as exc:
                check('camera_exception_propagates', str(exc) == 'injected camera failure')
            else:
                check('camera_exception_propagates', False)
        check('runtime_never_sends_START', all(p[3] != 2 or p[16] == 2 for p in writes))
        check('runtime_exception_sends_STOP', writes[0][16] == 2 and writes[-1][3] == 2 and writes[-1][16] == 2)
        check('runtime_cleans_resources', set(cleanups) == {'sensor', 'display', 'media', 'uart', 'log'}, cleanups)
        records = [json.loads(line) for line in stream.getvalue().splitlines()][1:]
        check('runtime_has_stable_real_camera_permission', len(records) == 6 and any(r['wire_valid'] for r in records))
        check('runtime_logs_true_path_sequences', [r['path_sequence'] for r in records] == list(range(6)))
    finally:
        for name, value in saved.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    evidence = dict(checks=checks, examples=examples, candidate=manifest,
                    limitations=['stored static images repeated only for stability tests',
                                 'synthetic corner and device substitutes are models',
                                 'real board timing and loaded ground behavior remain untested'])
    (args.output / 'review.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Straight vision:', len(checks), 'checks PASS; static images and host models only')


if __name__ == '__main__':
    main()
