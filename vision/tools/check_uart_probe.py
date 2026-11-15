"""验证真实探针入口的默认空闲、180路径＋STOP及UART释放时序。

UART／时间为主机模型，不打开串口；针对实测末尾STOP缺解析证据，检查
deinit之前确实留出发送余量。最终到线／接收以实板计数关系为准。
"""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'vision/src'))
from vision_protocol import crc16


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True); args=parser.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('probe_under_test',ROOT/'vision/src/lap_uart_probe_canmv.py')
    probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
    checks=[]; packets=[]; state={'now':0,'last_write':0,'deinit_at':None,'created':0}
    def check(name,value):
        checks.append({'name':name,'passed':bool(value)})
        if not value: raise AssertionError(name)
    class UART:
        UART2=2; EIGHTBITS=8; PARITY_NONE=None; STOPBITS_ONE=1
        def __init__(self,*a,**kw): state['created']+=1
        def write(self,data): packets.append(bytes(data)); state['last_write']=state['now']; return len(data)
        def deinit(self): state['deinit_at']=state['now']
    class FPIOA:
        UART2_TXD=1; UART2_RXD=2
        def set_function(self,*a): pass
    clock=types.SimpleNamespace(sleep_ms=lambda ms:state.update(now=state['now']+ms))
    machine=types.SimpleNamespace(UART=UART,FPIOA=FPIOA)
    old=sys.modules.get('machine'); sys.modules['machine']=machine
    import os
    old_exitpoint=getattr(os,'exitpoint',None); os.exitpoint=lambda:None
    log=io.StringIO()
    try:
        with contextlib.redirect_stdout(log): probe.main()
        check('default_idle_never_opens_UART',state['created']==0 and not packets)
        probe.ENABLED=True; probe.time=clock
        with contextlib.redirect_stdout(log): probe.main()
    finally:
        if old is None: sys.modules.pop('machine',None)
        else: sys.modules['machine']=old
        if old_exitpoint is None: delattr(os,'exitpoint')
        else: os.exitpoint=old_exitpoint
    check('exactly_180_paths_plus_STOP',len(packets)==181 and all(p[3]==1 for p in packets[:180]) and packets[-1][3]==2 and packets[-1][16]==2)
    check('all_paths_explicitly_invalid',all(p[6]==0 and p[7]==0 and p[16]==0 for p in packets[:180]))
    check('no_START',not any(p[3]==2 and p[16]==1 for p in packets))
    check('all_frames_20bytes_and_valid_CRC',all(len(p)==20 and crc16(p[:18])==int.from_bytes(p[18:],'little') for p in packets))
    check('steering_three_signed_blocks',[int.from_bytes(packets[i][8:10],'little',signed=True) for i in (0,60,120)]==[0,600,-600])
    check('STOP_wait_before_deinit',state['deinit_at']-state['last_write']>=10)
    (output/'checks.json').write_text(json.dumps({'checks':checks,'deinit_margin_ms':state['deinit_at']-state['last_write'],'physical_TX_completion_proved':False},indent=2),encoding='utf-8')
    (output/'entry_model_terminal.txt').write_text(log.getvalue(),encoding='utf-8')
    print(str(len(checks))+' UART probe entry-model checks PASS; physical confirmation separate')


if __name__=='__main__': main()
