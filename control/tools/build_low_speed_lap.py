"""调用同安装Keil官方控制台包装器，保存本次独立构建证据，不烧录。

Python子进程明确等待返回，避免本机PowerShell对GUI包装器的空返回码。
参数使用列表传递，不经过shell；不改原工程／编译器／下载器。
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import uuid

p=argparse.ArgumentParser(); p.add_argument('--keil-root',default='D:/software/Keil5')
p.add_argument('--target',choices=('LowSpeedLap','LowSpeedLapTrack'),default='LowSpeedLap')
args=p.parse_args(); control=Path(__file__).resolve().parents[1]; keil=Path(args.keil_root)
log=control/'build/firmware'/(args.target+'_'+uuid.uuid4().hex+'.log')
log.parent.mkdir(parents=True,exist_ok=True)
command=[str(keil/'UV4/uVision.com'),'-b',str(control/'MDK-ARM/low_speed_lap.uvprojx'),'-t'+args.target,'-j0','-o'+str(log)]
result=subprocess.run(command,capture_output=True,timeout=180)
sys.stdout.buffer.write(result.stdout); sys.stderr.buffer.write(result.stderr)
if result.returncode or not log.exists():
    raise SystemExit('Keil failed or no fresh log: '+str(result.returncode))
text=log.read_text(encoding='utf-8',errors='replace')
if '0 Error(s), 0 Warning(s).' not in text:
    raise SystemExit('Keil reported errors/warnings: '+str(log))
(log.parent/(args.target+'_build.log')).write_bytes(log.read_bytes())
base='low_speed_lap_track' if args.target=='LowSpeedLapTrack' else 'low_speed_lap'
output=log.parent/base/base
subprocess.run([str(keil/'ARM/ARMCC/bin/fromelf.exe'),'--bin','--output',str(output.with_suffix('.bin')),str(output.with_suffix('.axf'))],check=True,timeout=30)
print('BIN SHA256',hashlib.sha256(output.with_suffix('.bin').read_bytes()).hexdigest())
