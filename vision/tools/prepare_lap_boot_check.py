"""从已验证runtime_r5生成10秒脱机无动力诊断候选，仅写本地新目录。

保留原main.py和采集许可；本工具不连接板卡、不部署、不放行有效运动。
生成文件候选名main.py，实际安装前须备份板上入口并核对供电条件。
新增日志只进入/sdcard/lap_boot_checks的新编号文件，不覆盖旧记录。
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'testing/2026-11-09_low_speed_lap/board_bundle_runtime_r5'

BOOT_WRAPPER = '''
# 独立上电诊断：只发无效PATH与STOP，不发START，不读取或重建采集许可。
# 本段在合并文件的main定义之后、上电调用之前生效。
BOOT_SD_ROOT='/sdcard'
BOOT_LOG_LIMIT=1000
_boot_stream=None

def _boot_record(record):
    """保存原帧诊断，时间单位ms；日志异常向上抛出，让原main清理UART。

    每10帧flush以限制缓存，正常结束再sync；不保证突然断电时所有帧落盘。
    本函数不改变path结果、ALLOW_DRIVE或STM32的独立停止监督。
    """
    if _boot_stream is None:
        raise RuntimeError('boot log not open')
    _boot_stream.write(json.dumps(record)+'\\n')
    if record['index']%10==0:
        _boot_stream.flush()

def _boot_check():
    """一次10秒上电诊断；无TF／配置错误／日志错误均禁止进入相机主流程。

    不自动重试，不修改旧main.py／boot.py或采集许可。
    只有原主流程正常返回才记录completed；异常保留failed记录并重新抛出。
    completed表示诊断代码返回，不表示STM32接收、供电或整车已通过。
    """
    global _boot_stream
    if MODE!='live' or not UART_ENABLED or ALLOW_DRIVE or DURATION_MS!=10000 or SHOW_PREVIEW:
        raise RuntimeError('boot check must remain 10s live / UART / NO DRIVE / no preview')
    if not (os.stat(BOOT_SD_ROOT)[0]&0x4000):
        raise RuntimeError('real SD mount required')
    folder=BOOT_SD_ROOT+'/lap_boot_checks'
    try:
        info=os.stat(folder)
    except OSError as exc:
        if not exc.args or exc.args[0]!=2:
            raise
        os.mkdir(folder)
    else:
        if not (info[0]&0x4000):
            raise RuntimeError('boot log directory is not a directory')
    target=None
    for number in range(1,BOOT_LOG_LIMIT+1):
        candidate=folder+'/check_%04d.jsonl'%number
        try:
            os.stat(candidate)
        except OSError as exc:
            if not exc.args or exc.args[0]!=2:
                raise
            target=candidate
            break
    if target is None:
        raise RuntimeError('boot log slots exhausted; existing files retained')
    # 上电流程只有一个写者；编号存在则跳过，不用w打开已有证据。
    with open(target,'w') as stream:
        _boot_stream=stream
        try:
            stream.write(json.dumps(dict(event='begin',version='L1-BOOT-NODRIVE-1',
                duration_ms=DURATION_MS,drive_allowed=False,log=target))+'\\n')
            stream.flush()
            if hasattr(os,'sync'):
                os.sync()
            print('[BOOT CHECK LOG]',target)
            main()
            stream.write(json.dumps(dict(event='completed',motor_acceptance=False))+'\\n')
        except BaseException as exc:
            stream.write(json.dumps(dict(event='failed',error=repr(exc)))+'\\n')
            raise
        finally:
            try:
                stream.flush()
                if hasattr(os,'sync'):
                    os.sync()
            finally:
                _boot_stream=None
    return target

if __name__=='__main__':
    _boot_check()
'''


def main():
    """先核对输入字节，再只生成新的候选和来源清单；从不覆盖既有输出。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw = (BASE / 'low_speed_lap_canmv.py').read_bytes()
    original = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(raw).hexdigest() != original['bundle_sha256']:
        raise RuntimeError('runtime_r5 bytes differ from checked manifest')
    source = raw.decode('utf-8').replace('\r\n', '\n')
    replacements = {
        "MODE='idle'": "MODE='live'",
        'UART_ENABLED=False': 'UART_ENABLED=True',
        'DURATION_MS=300000': 'DURATION_MS=10000',
        'SHOW_PREVIEW=True': 'SHOW_PREVIEW=False',
        'to_ide=True': 'to_ide=False',
        '                print(json.dumps(record))': '                _boot_record(record)',
        "if __name__=='__main__':\n    main()": BOOT_WRAPPER,
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise RuntimeError('unexpected runtime source shape: ' + old)
        source = source.replace(old, new)
    if source.count('ALLOW_DRIVE=False') != 1:
        raise RuntimeError('expected explicit drive prohibition')
    compile(source, 'main.py', 'exec')
    args.output.mkdir(parents=True, exist_ok=False)
    target = args.output / 'main.py'
    target.write_bytes(source.encode('utf-8'))
    manifest = dict(base=str(BASE.relative_to(ROOT)), base_sha256=original['bundle_sha256'],
                    candidate_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                    mode='live', duration_ms=10000, uart=True, allow_drive=False, preview=False,
                    main_py_deployed=False, board_tested=False, motor_tested=False,
                    logs='/sdcard/lap_boot_checks/check_NNNN.jsonl',
                    purpose='Local boot diagnostic candidate only; not autonomous racing program')
    (args.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Prepared local 10s NO DRIVE boot candidate:', target)


if __name__ == '__main__':
    main()
