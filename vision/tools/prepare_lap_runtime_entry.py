"""准备车载持续相机main候选和人工部署说明；只写本地，不覆盖板上入口。

默认禁止驱动，显式--allow-real-camera才生成有效PATH候选；均不发送START。
STM32独立KEY／校准、3000ms或Track上限及故障监督不由此脚本修改。
"""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_lap_visual_link import BUNDLES


WRAPPER = '''
# 车载持续相机入口：上电只建立实时路径，电机仍由STM32校准和KEY人工启动。
# 日志编号与旧10秒自检分离，不覆盖旧证据；写盘失败退出，不自动重启。
RUNTIME_SD_ROOT='/sdcard'
RUNTIME_LOG_LIMIT=1000
_runtime_stream=None

def _runtime_record(record):
    """按原入口抽样规则写日志；index是算法帧号，单位ms。

    原主循环所有无效帧及每10个有效帧才调用本函数。flush时间会进入下一帧
    周期，STM32路径年龄／处理耗时保护保留；不把日志刷盘成功当接收端证据。
    """
    if _runtime_stream is None:
        raise RuntimeError('runtime log not open')
    _runtime_stream.write(json.dumps(record)+'\\n')
    if record['index']%10==0:
        _runtime_stream.flush()

def _runtime_boot():
    """一次有界持续运行，不自动START／重试，不修改boot.py或采集许可。

    相机输入窗口为600000ms，留出悬空校准与人工准备时间；STM32单次运动
    时限独立存在（当前09仅3000ms，Track候选最长300000ms）。本脚本不判圈。
    必须有真实SD日志目录；配置不符或日志槽耗尽即退出，不悄悄覆盖旧文件。
    """
    global _runtime_stream
    if MODE!='live' or not UART_ENABLED or DURATION_MS!=600000 or SHOW_PREVIEW:
        raise RuntimeError('runtime requires bounded live camera/UART/no IDE preview')
    if not (os.stat(RUNTIME_SD_ROOT)[0]&0x4000):
        raise RuntimeError('real SD mount required')
    folder=RUNTIME_SD_ROOT+'/lap_runtime_logs'
    try:
        info=os.stat(folder)
    except OSError as exc:
        if not exc.args or exc.args[0]!=2:
            raise
        os.mkdir(folder)
    else:
        if not (info[0]&0x4000):
            raise RuntimeError('runtime log path is not directory')
    target=None
    for number in range(1,RUNTIME_LOG_LIMIT+1):
        candidate=folder+'/run_%04d.jsonl'%number
        try:
            os.stat(candidate)
        except OSError as exc:
            if not exc.args or exc.args[0]!=2:
                raise
            target=candidate
            break
    if target is None:
        raise RuntimeError('runtime log slots exhausted; existing evidence retained')
    with open(target,'w') as stream:
        _runtime_stream=stream
        try:
            stream.write(json.dumps(dict(event='begin',revision='L1-R6-RUNTIME-1',
                duration_ms=DURATION_MS,drive_allowed=ALLOW_DRIVE,input_kind='real_camera',
                automatic_motor_start=False,log=target))+'\\n')
            stream.flush()
            if hasattr(os,'sync'): os.sync()
            print('[LAP RUNTIME LOG]',target)
            main()
            stream.write(json.dumps(dict(event='completed',lap_acceptance=False))+'\\n')
        except BaseException as exc:
            stream.write(json.dumps(dict(event='failed',error=repr(exc),lap_acceptance=False))+'\\n')
            raise
        finally:
            try:
                stream.flush()
                if hasattr(os,'sync'): os.sync()
            finally:
                _runtime_stream=None
    return target

if __name__=='__main__':
    _runtime_boot()
'''


def build(allow_drive=False, continuous=False, trace=False):
    """仅从已校验R6构建；返回源码和精确字节清单，不访问设备。"""
    if trace and not continuous:
        raise ValueError('per-frame trace requires reviewed continuous runtime')
    base, expected_hash = BUNDLES['r6']
    raw = base.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise RuntimeError('checked R6 bytes changed')
    source = raw.decode('utf-8').replace('\r\n', '\n')
    replacements = {
        "MODE='idle'": "MODE='live'", 'UART_ENABLED=False': 'UART_ENABLED=True',
        'DURATION_MS=300000': 'DURATION_MS=600000', 'SHOW_PREVIEW=True': 'SHOW_PREVIEW=False',
        'to_ide=True': 'to_ide=False',
        '                print(json.dumps(record))': '                _runtime_record(record)',
        "if __name__=='__main__':\n    main()": WRAPPER,
    }
    if allow_drive:
        replacements['ALLOW_DRIVE=False'] = 'ALLOW_DRIVE=True'
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise RuntimeError('unexpected checked source: ' + old)
        source = source.replace(old, new)
    if continuous:
        # 车载相机应覆盖人工校准、摆车和整圈过程。旧600000ms到期会发STOP，
        # 造成已校准但路径许可消失；不应以频繁重启相机来维持比赛输入。
        # 这里只取消相机输入的会话期限：STM32 3000/300000ms、人工KEY、
        # 路径质量/年龄、200ms断流、无反馈/反向/超速/UART保护均不修改。
        # 默认仍不许可驱动；相机、UART或日志异常仍由原finally发STOP并退出，
        # 不自动重试，也不依据恢复的路径自动启动电机。
        continuous_changes = {
            '\nDURATION_MS=600000\n': '\nDURATION_MS=0  # 0仅表示持续相机输入，绝不延长STM32单次运动期限。\n',
            'DURATION_MS!=600000': 'DURATION_MS!=0',
            "if MODE=='live' and time.ticks_diff(started,origin)>=DURATION_MS:": "if MODE=='live' and _runtime_duration_elapsed(time.ticks_diff(started,origin)):",
            "RUNTIME_SD_ROOT='/sdcard'": """RUNTIME_SD_ROOT='/sdcard'

def _runtime_duration_elapsed(elapsed_ms):
    \"\"\"相机输入期限判据；0为持续输入，运动上限由STM32独立监督。\"\"\"
    return DURATION_MS>0 and elapsed_ms>=DURATION_MS
""",
            '一次有界持续运行，不自动START／重试': '一次持续相机运行，不自动START／重试',
            '相机输入窗口为600000ms，留出悬空校准与人工准备时间；STM32单次运动': '相机输入持续至断电或显式终止；异常仍退出，不自动重试。STM32单次运动',
            'runtime requires bounded live camera/UART/no IDE preview': 'runtime requires continuous live camera/UART/no IDE preview',
            "revision='L1-R6-RUNTIME-1'": "revision='L1-R6-RUNTIME-2-CONTINUOUS'",
        }
        for old, new in continuous_changes.items():
            if source.count(old) != 1:
                raise RuntimeError('unexpected continuous runtime source: ' + old)
            source = source.replace(old, new)
    if trace:
        # 首次地面2044ms反向保护只有抽样视觉日志，不能定位到同一输入帧。
        # 此版本只补取证：每帧记录相机会话ms／实际发送序号与年龄及候选参数，
        # 不重算转向、不平滑／补造路线、不改识别器或PATH有效许可。
        # 仍每10帧flush；写盘时间计入下一周期，异常沿原finally发STOP退出。
        changes = {
            "revision='L1-R6-RUNTIME-2-CONTINUOUS'": "revision='L1-R6-RUNTIME-3-TRACE'",
            "if MODE=='sd_replay' or index%10==0 or not result['valid']:": "if MODE=='sd_replay' or TRACE_ALL_FRAMES or index%10==0 or not result['valid']:",
            'RUNTIME_LOG_LIMIT=1000': 'TRACE_ALL_FRAMES=True\nRUNTIME_LOG_LIMIT=1000',
            "record=dict(index=index,source=result['source']": "record=dict(elapsed_ms=time.ticks_diff(started,origin),wire_sequence=packet[5],\n                wire_age_ms=packet[10]|(packet[11]<<8),parameters=result.get('parameters'),\n                score=result.get('score'),threshold=result.get('threshold'),\n                index=index,source=result['source']",
            '按原入口抽样规则写日志；index是算法帧号，单位ms。': '逐帧写真实相机日志；index是帧号，elapsed_ms是会话毫秒。',
            '原主循环所有无效帧及每10个有效帧才调用本函数。flush时间会进入下一帧': '本诊断入口每帧调用，每10帧flush；源年龄／发送序号均来自本次真包。flush时间进入下一帧',
        }
        for old, new in changes.items():
            if source.count(old) != 1:
                raise RuntimeError('unexpected trace runtime source: ' + old)
            source = source.replace(old, new)
    compile(source, 'main.py', 'exec')
    return source, dict(base_bundle_sha256=expected_hash,
        candidate_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
        allow_drive=allow_drive, input_kind='real_camera', input_window_ms=None if continuous else 600000,
        continuous_camera=continuous, per_frame_trace=trace, motor_run_limit_changed=False,
        automatic_motor_start=False, main_py_deployed=False, board_tested=False,
        preserves=['all camera validity and age gates', 'startup and cleanup STOP', 'no automatic retry'],
        logs='/sdcard/lap_runtime_logs/run_NNNN.jsonl')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-real-camera', action='store_true')
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--trace', action='store_true')
    args = parser.parse_args()
    source, info = build(args.allow_real_camera, args.continuous, args.trace)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'main.py').write_bytes(source.encode('utf-8'))
    (args.output / 'manifest.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False))


if __name__ == '__main__':
    main()
