"""离线执行真实助手入口，用假Session核对三个悬空场景和实物条件门槛。

不会启动CanMV后端、连接端口或驱动电机；生成的执行文本也不在设备运行。
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); args=p.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('lap_bench_helper',ROOT/'vision/tools/canmv_lap_bench.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    sessions=[]; checks=[]
    def check(name,ok):
        checks.append(dict(name=name,passed=bool(ok)))
        if not ok: raise AssertionError(name)
    class FakeSession:
        def __init__(self,folder):
            self.folder=folder; self.requests=[]; self.running=False; self.script_error=False
            self.tail='[MOTOR BENCH DONE] HOST FAKE ONLY'; self.closed=False; sessions.append(self)
        def request(self,method,params=None,timeout=None):
            self.requests.append((method,params))
            if method=='connectBoard': return {'simulated':True,'purpose':'host helper checks only'}
            if method=='scriptRunning': return {'running':False}
            if method=='runScript': self.running=False; return {'simulated':True}
            raise AssertionError('unexpected method '+method)
        def close(self): self.closed=True
    module.Session=FakeSession
    old_argv=sys.argv
    try:
        for mode,scenario in module.MOTOR_SCENARIOS.items():
            folder=output/mode
            sys.argv=['helper',mode,'--output',str(folder),'--confirmed-suspended','--confirmed-mcu-run-ms','3000']
            with contextlib.redirect_stdout(io.StringIO()): module.main()
            source=(folder/'executed_source.py').read_bytes(); compile(source,str(folder/'executed_source.py'),'exec')
            session=sessions[-1]; submitted=[params['script'] for method,params in session.requests if method=='runScript']
            check(mode+'_exact_checked_scenario',len(submitted)==1 and ('SCENARIO='+repr(scenario)) in submitted[0] and 'DURATION_MS=600000' in submitted[0])
            check(mode+'_exact_recorded_source',source==submitted[0].encode('utf-8'))
            info=json.loads((folder/'run.json').read_text(encoding='utf-8'))
            check(mode+'_hash_and_no_automatic_start',hashlib.sha256(source).hexdigest()==info['source_sha256'] and info['operator_KEY_fixture_test'] and not info['automatic_motor_start_permitted'] and not info['main_py_written'])
            check(mode+'_closed',session.closed)
        # 单次任务可用短窗口，基础包仍为同一哈希核对后的R3，仅改RAM配置。
        for mode,scenario in module.MOTOR_SCENARIOS.items():
            folder=output/(mode+'_short')
            sys.argv=['helper',mode,'--output',str(folder),'--confirmed-suspended','--confirmed-mcu-run-ms','3000','--motor-window-ms','120000']
            with contextlib.redirect_stdout(io.StringIO()): module.main()
            source=(folder/'executed_source.py').read_bytes(); compile(source,str(folder/'executed_source.py'),'exec')
            info=json.loads((folder/'run.json').read_text(encoding='utf-8'))
            check(mode+'_short_window',b'DURATION_MS=120000' in source and b'120s input window' in source and info['input_window_ms']==120000)
            check(mode+'_short_gate_retained',info['confirmed_suspended'] and info['confirmed_mcu_run_ms']==3000 and not info['automatic_motor_start_permitted'])
            check(mode+'_short_hash',hashlib.sha256(source).hexdigest()==info['source_sha256'])
        # 三种场景都须拒绝缺少悬空确认或错误运行上限，且拒绝发生在连接之前。
        for mode in module.MOTOR_SCENARIOS:
            for suffix,flags in (('not_suspended',['--confirmed-mcu-run-ms','3000']),('wrong_limit',['--confirmed-suspended','--confirmed-mcu-run-ms','300000'])):
                before=len(sessions); sys.argv=['helper',mode,'--output',str(output/(mode+'_'+suffix)),*flags]
                rejected=False
                try: module.main()
                except ValueError: rejected=True
                check(mode+'_'+suffix+'_before_connection',rejected and len(sessions)==before)
            before=len(sessions); sys.argv=['helper',mode,'--output',str(output/(mode+'_bad_window')),'--confirmed-suspended','--confirmed-mcu-run-ms','3000','--motor-window-ms','999999']
            rejected=False
            with contextlib.redirect_stderr(io.StringIO()):
                try: module.main()
                except SystemExit as exc: rejected=exc.code==2
            check(mode+'_bad_window_before_connection',rejected and len(sessions)==before)
    finally: sys.argv=old_argv
    (output/'checks.json').write_text(json.dumps(dict(checks=checks,physical_board_used=False,motor_run_verified=False),indent=2),encoding='utf-8')
    print(str(len(checks))+' helper entry checks PASS; fake Session only, no board/backend/motor')


if __name__=='__main__': main()
