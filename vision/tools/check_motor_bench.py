"""验证固定输入台架的真实入口／共享封包，无任何设备或电机操作。

检查默认不打开UART、各场景固定转向与有效测试输入、只有STOP命令、
发送期限／短写边界，以及最后STOP到deinit的余量；不当作实测转速。
"""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'vision/src'))
from vision_protocol import crc16


def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); args=p.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('motor_fixture_under_test',ROOT/'vision/src/lap_motor_bench_canmv.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    default_duration=module.DURATION_MS
    checks=[]; traces={}
    def check(name,ok):
        checks.append(dict(name=name,passed=bool(ok)))
        if not ok: raise AssertionError(name)
    class FPIOA:
        UART2_TXD=1; UART2_RXD=2
        def set_function(self,*args): pass
    import os
    old_machine=sys.modules.get('machine'); old_exitpoint=getattr(os,'exitpoint',None)
    os.exitpoint=lambda:None
    try:
        for scenario,steer in (('straight',0),('right',500),('left',-500)):
            state=dict(now=0,created=0,last_write=0,deinit=None); packets=[]
            class UART:
                UART2=2; EIGHTBITS=8; PARITY_NONE=None; STOPBITS_ONE=1
                def __init__(self,*args,**kwargs): state['created']+=1
                def write(self,data): packets.append(bytes(data)); state['last_write']=state['now']; return len(data)
                def deinit(self): state['deinit']=state['now']
            module.time=types.SimpleNamespace(ticks_ms=lambda:state['now'],ticks_diff=lambda a,b:a-b,
                sleep_ms=lambda ms:state.update(now=state['now']+ms))
            sys.modules['machine']=types.SimpleNamespace(UART=UART,FPIOA=FPIOA)
            module.ENABLED=False
            with contextlib.redirect_stdout(io.StringIO()): module.main()
            check(scenario+'_default_idle',state['created']==0 and not packets)
            module.ENABLED=True; module.SCENARIO=scenario; module.DURATION_MS=default_duration if scenario=='straight' else 10000
            with contextlib.redirect_stdout(io.StringIO()): module.main()
            paths=[f for f in packets if f[3]==1]; commands=[f for f in packets if f[3]==2]
            check(scenario+'_bounded_paths',len(paths)==module.DURATION_MS//50)
            if scenario=='straight':
                check('default_600s_window_STOP_and_no_START',default_duration==600000 and state['now']==600020)
            check(scenario+'_fixed_input',all(f[6]==1 and int.from_bytes(f[8:10],'little',signed=True)==steer for f in paths))
            check(scenario+'_STOP_only',len(commands)==2 and all(f[16]==2 for f in commands))
            check(scenario+'_CRC',all(len(f)==20 and crc16(f[:18])==int.from_bytes(f[18:],'little') for f in packets))
            check(scenario+'_drain_before_deinit',state['deinit']-state['last_write']>=10)
            traces[scenario]=dict(paths=len(paths),steering=steer,commands=[f[16] for f in commands],
                virtual_ms=state['now'],not_camera=True)
    finally:
        if old_machine is None: sys.modules.pop('machine',None)
        else: sys.modules['machine']=old_machine
        if old_exitpoint is None: delattr(os,'exitpoint')
        else: os.exitpoint=old_exitpoint
    (output/'checks.json').write_text(json.dumps(dict(checks=checks,traces=traces,physical_motor_tested=False),indent=2),encoding='utf-8')
    print(str(len(checks))+' suspended fixture entry-model checks PASS; no physical motor operation')


if __name__=='__main__': main()
