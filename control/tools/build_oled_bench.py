"""使用现有Keil/ARMCC构建独立OLED工程，仅编译、导出BIN并保存哈希，不访问板卡。"""
import hashlib
from pathlib import Path
import subprocess
import uuid

control = Path(__file__).resolve().parents[1]
keil = Path('D:/software/Keil5')
log = control / 'build/firmware' / ('OledBench_' + uuid.uuid4().hex + '.log')
log.parent.mkdir(parents=True, exist_ok=True)
result = subprocess.run([str(keil/'UV4/uVision.com'), '-b',
    str(control/'MDK-ARM/oled_bench.uvprojx'), '-tOledBench', '-j0', '-o'+str(log)],
    capture_output=True, timeout=180)
if log.exists():
    print(log.read_text(encoding='utf-8', errors='replace'))
if result.returncode or not log.exists() or '0 Error(s), 0 Warning(s).' not in log.read_text(encoding='utf-8', errors='replace'):
    raise SystemExit('OLED build failed; inspect ' + str(log))
(log.parent/'OledBench_build.log').write_bytes(log.read_bytes())
base = log.parent/'oled_bench/oled_bench'
subprocess.run([str(keil/'ARM/ARMCC/bin/fromelf.exe'),'--bin','--output',str(base.with_suffix('.bin')),str(base.with_suffix('.axf'))],check=True,timeout=30)
print('BIN SHA256',hashlib.sha256(base.with_suffix('.bin').read_bytes()).hexdigest())
