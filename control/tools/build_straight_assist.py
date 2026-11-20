"""串行调用现有Keil5编译StraightAssist并导出BIN，不下载或启动板卡。"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keil-root', default='D:/software/Keil5')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    keil = Path(args.keil_root)
    folder = root / 'build/firmware/straight_assist'
    folder.mkdir(parents=True, exist_ok=True)
    log = folder / ('build_' + uuid.uuid4().hex + '.log')
    result = subprocess.run([str(keil / 'UV4/uVision.com'), '-b', str(root / 'MDK-ARM/straight_assist.uvprojx'),
                             '-tStraightAssist', '-j0', '-o' + str(log)], capture_output=True, timeout=180)
    if result.returncode or not log.exists() or '0 Error(s), 0 Warning(s).' not in log.read_text(encoding='utf-8', errors='replace'):
        raise RuntimeError('Keil failed; inspect ' + str(log))
    (folder / 'build.log').write_bytes(log.read_bytes())
    binary = folder / 'straight_assist.bin'
    subprocess.run([str(keil / 'ARM/ARMCC/bin/fromelf.exe'), '--bin', '--output', str(binary),
                    str(folder / 'straight_assist.axf')], check=True, timeout=30)
    print('StraightAssist 0 errors / 0 warnings; BIN SHA256', hashlib.sha256(binary.read_bytes()).hexdigest())
    print(log)


if __name__ == '__main__':
    main()
