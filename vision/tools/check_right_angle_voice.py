"""用真实归档赛道图和模拟口令验证 v9 续行、失效、图传和留证。"""
import math
import subprocess
from types import SimpleNamespace

import cv2
import numpy as np
from check_straight_voice import BUILD, CONTROL, ROOT
from prepare_right_angle_bundle import build


def simulate(frames, keywords, *, gap_at=0, preview=None, kws_ms=0):
    source, info = build(voice=True)
    assert info['wire_version'] == 9 and not info['automatic_motor_start']
    ns = {'__name__': 'voice_check', 'print': lambda *args: None}
    exec(source, ns)
    index = clock = 0
    trace, saves = [], []

    def snapshot(chn):
        nonlocal index, clock
        assert chn == 0
        index += 1
        clock += 211 if index == gap_at else 50
        return SimpleNamespace(width=lambda: 320, height=lambda: 240, format=lambda: 7,
                               bytearray=lambda: frames[index - 1])

    def exitpoint():
        if index == len(frames):
            raise EOFError('simulation complete')

    def write(packet):
        assert len(packet) == 20 and packet[2] == 9
        assert ns['crc16'](packet[:18]) == int.from_bytes(packet[18:], 'little')
        trace.append((clock, packet))
        return len(packet)

    def save(evidence, event, at):
        saves.append((at, event, evidence.go_at, evidence.records[:evidence.count], evidence.issue))

    ns.update(time=SimpleNamespace(ticks_ms=lambda: clock, ticks_diff=lambda a, b: a - b, ticks_add=lambda a, b: a + b),
              os=SimpleNamespace(exitpoint=exitpoint))
    ns['RunEvidence'].save = save
    evidence = ns['RunEvidence']()
    def poll():
        nonlocal clock
        clock += kws_ms
        return keywords.get(index, 0)

    voice = SimpleNamespace(poll=poll, play=lambda label: trace.append((clock, label)))
    try:
        ns['drive'](SimpleNamespace(snapshot=snapshot), 0, 7,
                    ns['RightAngleVoiceSender'](write, allow_drive=True), voice, evidence, preview)
    except EOFError:
        pass
    return trace, saves, evidence


def packets(trace):
    return [packet for _, packet in trace if isinstance(packet, bytes)]


def verify_prediction():
    """本轮停车前后真实L不再退到未知；单边、短预测和重新观测分别检查。"""
    folder = ROOT / 'testing/2026-11-18_right_angle/voice_ground_01_camera'
    before = (folder / 'voice_0001_issue_10166_056.pgm').read_bytes()[15:]
    after = (folder / 'voice_0001_issue_10277_057.pgm').read_bytes()[15:]
    one_edge = b'\x96' * (115 * 320) + after[115 * 320:]
    blank = b'\x96' * len(after)
    trace, _, _ = simulate([before] * 4 + [after, one_edge, blank, after], {3: 2})
    observed = [(p[6], p[7]) for p in packets(trace) if p[3] == 1]
    assert observed[2:] == [(9, 60), (9, 60), (9, 60), (5, 55), (5, 45), (9, 60)], observed
    trace, _, _ = simulate([before] * 4 + [after] + [blank] * 6, {3: 2})
    assert [p[6] for p in packets(trace) if p[3] == 1][-6:] == [5, 5, 5, 5, 0, 0]
    trace, _, _ = simulate([before] * 4 + [after] + [one_edge] * 26, {3: 2})
    endings = [p[6] for p in packets(trace) if p[3] == 1][-26:]
    assert endings[:10] == [5] * 10 and endings[-4:] == [5, 0, 0, 0], endings
    trace, _, _ = simulate([one_edge] * 6, {3: 2})
    assert all(p[3] == 1 and p[6] == 0 for p in packets(trace))


def verify_phone():
    """慢手机每次只消耗一个定长写额度，发到一半时不编码下一帧。"""
    ns = {'__name__': 'phone_host_check'}
    exec(build(voice=True)[0], ns)
    clock, writes, overlays = 0, [], []
    accepting = True

    def accept():
        nonlocal accepting
        if not accepting:
            raise OSError(11)
        accepting = False
        return client, None

    remaining = None
    def send(data):
        nonlocal remaining
        writes.append(len(data))
        if remaining is None:
            remaining = len(data)
            return len(data)
        raise OSError(11)

    client = SimpleNamespace(setblocking=lambda block: None, recv=lambda size: b'GET /stream HTTP/1.1\r\n\r\n',
                             send=send, close=lambda: None)
    ns['time'] = SimpleNamespace(ticks_ms=lambda: clock, ticks_diff=lambda a, b: a - b, ticks_add=lambda a, b: a + b)
    ns['annotate_preview'] = lambda *args: overlays.append(1)
    phone = ns['PhonePreview'](SimpleNamespace(accept=accept))
    frame = SimpleNamespace(to_jpeg=lambda quality: SimpleNamespace(bytearray=lambda: bytearray(12000)))
    phone.step(frame, {}, b'', False)
    assert writes == [len(ns['MJPEG_HEADER'])] and not overlays
    clock = 100
    phone.step(frame, {}, b'', False)
    assert not overlays
    clock = 150
    phone.step(frame, {}, b'', True)
    clock = 200
    phone.step(frame, {}, b'', True)
    assert len(overlays) == 1 and writes[1:] == [8192, 8192]
    clock = 1100
    phone.step(frame, {}, b'', True)
    assert phone.client is None and len(overlays) == 1


def verify_current_front():
    """真实故障图对接仅前线的位姿序列，直到两侧直线恢复。"""
    folder = ROOT / 'testing/2026-11-18_right_angle/voice_ground_02_camera'
    before = (folder / 'voice_0002_issue_31829_147.pgm').read_bytes()[15:]
    after = (folder / 'voice_0002_issue_31891_148.pgm').read_bytes()[15:]
    x, y = np.meshgrid(np.arange(320), np.arange(240))
    ground_x = (x - 159.5) * 48 / (y + 38.11111111111108)
    ground_z = (7802.22222222222 - 15.555555555555546 * y) / (y + 38.11111111111108)

    def render(degrees, distance, pair=False):
        yaw = math.radians(degrees)
        along = ground_x * math.cos(yaw) - ground_z * math.sin(yaw)
        depth = ground_x * math.sin(yaw) + ground_z * math.cos(yaw)
        black = (abs(depth - distance) < 2.5) & (along >= -35)
        if pair:
            black |= (abs(depth - (distance - 50)) < 2.5) & (along >= -35)
        return np.where(black, 40, 160).astype(np.uint8).tobytes()

    ns = {'__name__': 'front_only_check'}
    exec(build(voice=True)[0], ns)
    route = ns['RightAngleRoute'](predictive=True)
    sender = ns['RightAngleVoiceSender'](allow_drive=True)
    for at in (0, 65, 130):
        assert route.update(before, at)['source'] == 'current_corner_predicted'
    fault_point = route.update(after, 195)
    assert fault_point['valid'] and fault_point['searched_candidates'] == 0
    measured = []
    for index in range(24):
        yaw, distance = max(-90, -5 - 5 * index), max(25, 41 - 1.5 * index)
        result = route.update(render(yaw, distance), 260 + 65 * index)
        assert result['valid'] and result['source'] == 'current_front_forecast', result
        packet = sender.path(result, 40, 45)
        assert (packet[6], packet[7]) == (5, 58)
        measured.append((result['stage'], result['front_distance'], result['steering']))
    assert measured[0][0] == 'turn' and measured[0][2] > 0
    assert measured[-1][0] == 'exit' and measured[-1][1] < measured[0][1] - 10
    assert route.update(render(-90, 25, pair=True), 1820)['source'] == 'current_pair'
    unknown = ns['RightAngleRoute'](predictive=True)
    assert not any(unknown.update(render(-5, 41), time)['valid'] for time in (0, 65, 130))


def verify_preview_schedule(pixels):
    """慢帧待机仍能更新；Go等待帧和跑动慢帧给控制路径让路。"""
    allowances = []
    phone = SimpleNamespace(step=lambda frame, result, packet, encode: allowances.append(encode))
    simulate([pixels] * 8, {3: 2, 7: 3}, preview=phone, kws_ms=40)
    # 第4帧先发START并跳过图传。第7帧收到Stop并结束运动窗口后恢复预览。
    assert allowances == [True, True, False, False, False, True, True]


def main():
    folder = ROOT / 'vision/data/captures/final_mount_20261108'
    pair = cv2.imread(str(folder / 'v03_center_0002/data_0001.jpg'), 0).tobytes()
    corner = cv2.imread(str(folder / 'push_full_lap_0001/data_0126.jpg'), 0).tobytes()
    blank = b'\xff' * len(pair)
    trace, saves, _ = simulate([pair] * 8, {})
    assert trace[0] == (0, 1) and all(packet[3] == 1 for packet in packets(trace))
    assert not saves and packets(trace)[-1][6] == 1

    trace, saves, _ = simulate([corner] * 8, {3: 2, 5: 2, 7: 3})
    frames = packets(trace)
    commands = [packet for packet in frames if packet[3] == 2]
    assert [packet[16] for packet in commands] == [1, 2, 2, 2]
    start = frames.index(commands[0])
    assert frames[start - 1][6] == 9 and commands[0][8] == frames[start - 1][5]
    assert trace[-2] == (350, 3)
    assert len(saves) == 1 and saves[0][:3] == (350, 'stop_sent', 200)
    assert saves[0][3][0][2] == 9 and not saves[0][4]

    trace, saves, evidence = simulate([pair] * 5 + [blank] + [pair] * 4, {3: 2}, gap_at=6)
    assert not saves and sum(packet[3] == 2 for packet in packets(trace)) == 1
    before, after = evidence.issue
    assert before[2] == pair and after[2] == blank
    assert evidence.records[2][10] >= 200 and evidence.records[2][2] == 0
    assert packets(trace)[-1][6] == 1  # 图像恢复可以恢复供诊断的PATH，不能生成Go。
    trace, saves, _ = simulate([pair] * 3 + [blank] + [pair] * 4, {3: 2})
    assert not saves and all(packet[3] == 1 for packet in packets(trace))

    trace, saves, _ = simulate([pair] * 248, {3: 2, 6: 4})
    assert [item for item in trace if isinstance(item[1], int)] == [(0, 1), (12350, 2)]
    assert len(saves) == 1 and saves[0][:3] == (12350, 'go_window_elapsed', 200)

    probe_sources = ('Tests/Host/lap_packet_probe.c', 'Drivers_Custom/Communication/lap_link.c',
                     'Drivers_Custom/Communication/protocol.c')
    probe = BUILD / 'right_angle_voice_packet_probe.exe'
    subprocess.run(['gcc', '-pedantic', '-Wall', '-Wextra', '-Werror', '-DRIGHT_ANGLE_VOICE_TARGET=1',
                    '-I', str(CONTROL / 'Drivers_Custom/Communication'),
                    *(str(CONTROL / path) for path in probe_sources), '-o', str(probe)], check=True)
    decoded = subprocess.run([str(probe)], input=b''.join(frames), capture_output=True, check=True)
    assert decoded.stdout.decode().splitlines() == [
        ' '.join(str(packet[field]) for field in (3, 5, 6, 8, 9)) for packet in frames
    ]
    verify_prediction()
    verify_current_front()
    verify_phone()
    verify_preview_schedule(pair)
    print('RightAngleVoice scheduling, real corner replay, confidence expiry, phone backpressure and production v9 parser PASS')


if __name__ == '__main__':
    main()
