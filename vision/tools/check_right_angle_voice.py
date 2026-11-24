"""用真实归档赛道图和模拟口令验证 v7 调度、续行、失效和延迟留证。"""
import subprocess
from types import SimpleNamespace

import cv2
from check_straight_voice import BUILD, CONTROL, ROOT
from prepare_right_angle_bundle import build


def simulate(frames, keywords, *, gap_at=0):
    source, info = build(voice=True)
    assert info['wire_version'] == 7 and not info['automatic_motor_start']
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
        assert len(packet) == 20 and packet[2] == 7
        assert ns['crc16'](packet[:18]) == int.from_bytes(packet[18:], 'little')
        trace.append((clock, packet))
        return len(packet)

    def save(evidence, event, at):
        saves.append((at, event, evidence.go_at, evidence.records[:evidence.count], evidence.issue))

    ns.update(time=SimpleNamespace(ticks_ms=lambda: clock, ticks_diff=lambda a, b: a - b, ticks_add=lambda a, b: a + b),
              os=SimpleNamespace(exitpoint=exitpoint))
    ns['RunEvidence'].save = save
    evidence = ns['RunEvidence']()
    voice = SimpleNamespace(poll=lambda: keywords.get(index, 0), play=lambda label: trace.append((clock, label)))
    try:
        ns['drive'](SimpleNamespace(snapshot=snapshot), 0, 7,
                    ns['RightAngleVoiceSender'](write, allow_drive=True), voice, evidence)
    except EOFError:
        pass
    return trace, saves, evidence


def packets(trace):
    return [packet for _, packet in trace if isinstance(packet, bytes)]


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
    print('RightAngleVoice scheduling, R8 frames, loss evidence and production v7 parser PASS')


if __name__ == '__main__':
    main()
