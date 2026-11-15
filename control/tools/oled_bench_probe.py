"""OLED诊断的SWD证据工具：不复位、不下载、不恢复旧程序。

使用项目环境已安装的pyOCD，指定CMSIS-DAP唯一ID，避免操作其它设备。
--backup-before首次保存完整512KiB原程序；--capture读取新AXF符号及运行变量。
Flash下载另由当前Keil链路执行，本工具不使用其它芯片型号的Flash算法。
运行中WFI睡眠时本机链路读RAM可能返回零；capture短暂停核读取两个小块后立即恢复。
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from elftools.elf.elffile import ELFFile
from pyocd.core.helpers import ConnectHelper

parser=argparse.ArgumentParser()
parser.add_argument('--backup-before',action='store_true')
parser.add_argument('--capture',action='store_true')
args=parser.parse_args()
if args.backup_before==args.capture:
    parser.error('choose exactly one of --backup-before / --capture')
control=Path(__file__).resolve().parents[1]
evidence=control.parent/'testing/2026-11-10_oled_bench'
evidence.mkdir(parents=True,exist_ok=True)
probe_id='00010001066cff554954657287234218a5a5a5a597969908'
session=ConnectHelper.session_with_chosen_probe(blocking=False,unique_id=probe_id,
    options={'target_override':'cortex_m','connect_mode':'attach','frequency':1000000,
             'auto_unlock':False,'resume_on_disconnect':False})
if session is None:
    raise SystemExit('Expected CMSIS-DAP probe not available; no other probe selected')
with session:
    target=session.target
    if args.backup_before:
        dest=evidence/'flash_before_oled.bin'
        if dest.exists():
            raise FileExistsError('Original backup already exists; refusing overwrite')
        payload=bytes(target.read_memory_block8(0x08000000,0x80000))
        dest.write_bytes(payload)
        result={'source':'SWD attach read only','probe':probe_id,'bytes':len(payload),
                'sha256':hashlib.sha256(payload).hexdigest(),'vector':payload[:8].hex()}
        (evidence/'flash_before_oled.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    else:
        axf=control/'build/firmware/oled_bench/oled_bench.axf'
        with axf.open('rb') as stream:
            elf=ELFFile(stream)
            table=elf.get_section_by_name('.symtab')
            symbols={s.name:int(s['st_value']) for s in table.iter_symbols() if s.name.startswith('g_oled')}
        names=['g_oled_revision','g_oled_fault','g_oled_stage','g_oled_ms','g_oled_address',
               'g_oled_ack_mask','g_oled_frames','g_oled_phase','g_oled_seconds','g_oled_motor_odr',
               'g_oled_watchdog_started','g_oled_watchdog_stage']
        samples=[]
        for _ in range(3):
            # 无动力诊断中短暂停核读两个小块，避免睡眠态调试访问返回无效零。
            # finally确保正常/读取异常均恢复，不执行复位、Flash操作或新运动命令。
            state_before=str(target.get_state())
            started=time.monotonic()
            target.halt()
            try:
                start=min(symbols[name] for name in names)
                count=(max(symbols[name] for name in names)-start)//4+1
                words=target.read_memory_block32(start,count)
                sample={name:words[(symbols[name]-start)//4] for name in names}
                values=target.read_memory_block32(symbols['g_oled_bus'],5)
            finally:
                target.resume()
            sample['state_before']=state_before
            sample['halt_seconds']=time.monotonic()-started
            sample['bus']=dict(zip(['error','ack_bytes','nack_bytes','recoveries','idle_pins'],values))
            samples.append(sample)
            if len(samples)<3: time.sleep(2)
        binary=axf.with_suffix('.bin').read_bytes()
        actual=bytes(target.read_memory_block8(0x08000000,len(binary)))
        result={'probe':probe_id,'samples':samples,'symbols':symbols,
                'firmware_bytes':len(binary),'flash_matches_bin':actual==binary,
                'bin_sha256':hashlib.sha256(binary).hexdigest()}
        passed=actual==binary and all(s['g_oled_revision']==0x02120001 and s['g_oled_fault']==0
            and s['g_oled_stage'] in (5,6) and s['g_oled_address'] in (0x3c,0x3d)
            and s['g_oled_phase']==4 and s['g_oled_motor_odr']==0 and s['bus']['error']==0
            for s in samples)
        passed=passed and samples[-1]['g_oled_ms']>samples[0]['g_oled_ms'] \
            and samples[-1]['g_oled_frames']>samples[0]['g_oled_frames']
        result['runtime_checks_passed']=passed
        suffix=time.strftime('%H%M%S')
        (evidence/('runtime_'+suffix+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if args.capture and not result['runtime_checks_passed']:
        raise SystemExit('Runtime checks not passed; inspect evidence before further action')
