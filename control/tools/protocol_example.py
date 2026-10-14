"""PC reference encoder for 视觉; emits files only, never sends START to a port."""
from pathlib import Path
import argparse
import struct

def crc16(data):
    crc = 0xffff
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xffff if crc & 0x8000 else (crc << 1) & 0xffff
    return crc

def encode_path(sequence, error=0, valid=True, confidence=80, heading=0, bend=0, processing_ms=20, finish=False):
    if not (0 <= sequence <= 255 and -1000 <= error <= 1000 and 0 <= confidence <= 100 and
            -9000 <= heading <= 9000 and 0 <= bend <= 1000 and 0 <= processing_ms <= 1000):
        raise ValueError('Path fields out of range')
    payload = struct.pack('<BBhhHHBB', int(valid) | (int(finish) << 1), confidence, error, heading, bend, processing_ms, 0, 0)
    header = bytes((0xa5, 0x5a, 1, 1, 12, sequence))
    return header + payload + struct.pack('<H', crc16(header + payload))

def encode_command(sequence, command):
    if not 0 <= sequence <= 255 or command not in (1, 2, 3):
        raise ValueError('Command fields out of range')
    data = bytes((0xa5, 0x5a, 1, 2, 12, sequence)) + bytes(10) + bytes((command, 0))
    return data + struct.pack('<H', crc16(data))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'build/protocol_samples')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    samples = {'path_valid': encode_path(1), 'path_invalid': encode_path(2, valid=False),
               'start': encode_command(1, 1), 'stop': encode_command(2, 2), 'status': encode_command(3, 3)}
    for name, data in samples.items():
        (args.output / (name + '.bin')).write_bytes(data)
        print(name + ': ' + data.hex(' ').upper())
