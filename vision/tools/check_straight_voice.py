"""离线验证语音直道入口调度、两端封包及STM32运动保护。不会连接任何设备。"""
from pathlib import Path
import subprocess
from types import SimpleNamespace

import cv2
from prepare_straight_bundle import build

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / 'control'
BUILD = CONTROL / 'build'


def compile_host(name, sources):
    BUILD.mkdir(parents=True, exist_ok=True)
    output = BUILD / (name + '.exe')
    options = ['-std=c99', '-Wall', '-Wextra', '-Wconversion', '-Werror', '-pedantic',
               '-DSTRAIGHT_ASSIST_TARGET=1', '-DSTRAIGHT_VOICE_TARGET=1']
    for folder in ('App/Motion', 'Algorithms/Speed', 'Algorithms/Encoder', 'Drivers_Custom/Communication'):
        options.extend(('-I', str(CONTROL / folder)))
    sources = (*sources, 'Drivers_Custom/Communication/lap_link.c', 'Drivers_Custom/Communication/protocol.c')
    subprocess.run(['gcc', *options, *(str(CONTROL / path) for path in sources), '-lm', '-o', str(output)], check=True)
    return output


def simulate(pixels, commands, frame_count, lost_at=0):
    source, info = build(voice=True)
    assert info['wire_version'] == 6 and not info['automatic_motor_start']
    namespace = {'__name__': 'voice_host_check'}
    exec(compile(source, 'main.py', 'exec'), namespace)
    frame_index = clock = 0
    trace, logs = [], []
    blank = bytes((255,)) * len(pixels)

    def snapshot(chn):
        nonlocal frame_index, clock
        assert chn == 0
        frame_index += 1
        clock += 50
        return SimpleNamespace(width=lambda: 320, height=lambda: 240, format=lambda: 7,
                               bytearray=lambda: blank if frame_index == lost_at else pixels)

    def exitpoint():
        if frame_index == frame_count:
            raise EOFError('simulation complete')

    def write(packet):
        assert len(packet) == 20 and packet[2] == 6
        assert namespace['crc16'](packet[:18]) == int.from_bytes(packet[18:], 'little')
        trace.append((clock, packet))
        return len(packet)

    def play(label):
        trace.append((clock, label))

    def poll():
        assert trace[0] == (0, 1)  # 首次录音识别前已请求“我在”。
        return commands.get(frame_index, 0)

    namespace.update(time=SimpleNamespace(ticks_ms=lambda: clock, ticks_diff=lambda later, earlier: later - earlier,
                                          ticks_add=lambda base, delta: base + delta),
                     os=SimpleNamespace(exitpoint=exitpoint), log_event=lambda *fields: logs.append(fields))
    sender = namespace['StraightVoiceSender'](write, allow_drive=True)
    voice = SimpleNamespace(poll=poll, play=play)
    try:
        namespace['drive'](SimpleNamespace(snapshot=snapshot), 0, 7, sender, voice)
    except EOFError:
        pass
    return trace, logs


def main():
    motion = compile_host('test_straight_voice', (
        'App/Motion/lap_motion.c', 'App/Motion/speed_match.c', 'Algorithms/Speed/speed_pi.c',
        'Algorithms/Speed/straight_guide.c', 'Algorithms/Encoder/encoder_counter.c',
        'Tests/Host/test_straight_voice.c',
    ))
    subprocess.run([str(motion)], check=True)
    probe = compile_host('straight_voice_packet_probe', ('Tests/Host/lap_packet_probe.c',))
    path = ROOT / 'vision/data/captures/final_mount_20261108/v03_center_0002/data_0001.jpg'
    pixels = cv2.imread(str(path), 0).tobytes()

    idle, _ = simulate(pixels, {}, 8)
    assert idle[0] == (0, 1) and len(idle) == 9
    assert all(isinstance(packet, bytes) and packet[3] == 1 for _, packet in idle[1:])
    assert idle[-1][1][6] & 1  # 有许可但没有任何上电自动运动指令。
    trace, _ = simulate(pixels, {3: 2, 5: 2, 6: 3}, 8)
    packets = [item for _, item in trace if isinstance(item, bytes)]
    commands = [packet for packet in packets if packet[3] == 2]
    assert [packet[16] for packet in commands] == [1, 2, 2, 2]
    start_at = packets.index(commands[0])
    assert packets[start_at - 1][3] == 1 and commands[0][8] == packets[start_at - 1][5]
    spoken_stop = next(index for index, (_, item) in enumerate(trace) if item == 3)
    assert all(packet[16] == 2 for _, packet in trace[spoken_stop - 3:spoken_stop])
    decoded = subprocess.run([str(probe)], input=b''.join(packets), capture_output=True, check=True)
    assert decoded.stdout.decode().splitlines() == [
        ' '.join(str(packet[index]) for index in (3, 5, 6, 8, 9)) for packet in packets
    ]

    lost, logs = simulate(pixels, {3: 2}, 9, lost_at=4)
    assert any(event[0] == 'go_no_fresh_pair' for event in logs)
    assert all(packet[3] == 1 for _, packet in lost[1:]) and lost[-1][1][6] & 1
    full, _ = simulate(pixels, {3: 2, 6: 4}, 50)
    start_ms = next(at for at, packet in full if isinstance(packet, bytes) and packet[3] == 2)
    assert [(at, label) for at, label in full if isinstance(label, int)] == [(0, 1), (start_ms + 2150, 2)]
    print('Voice scheduling, R2 image paths and Python-to-STM32 v6 frames PASS')


if __name__ == '__main__':
    main()
