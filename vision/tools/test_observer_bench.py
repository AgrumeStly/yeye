"""在电脑模拟CanMV接口检查独立入口；不访问实体相机／UART或SD卡。"""

from contextlib import contextmanager,redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import types

from review_recovery_inputs import save


@contextmanager
def environment(bundle):
    """导入打包文件并注入内存接口，结束恢复sys.modules，避免伪造板上验收。"""
    events=[];clock=[0]
    pixels=bytes([230])*76800
    class Frame:
        def width(self):return 320
        def height(self):return 240
        def format(self):return 1
        def bytearray(self):return bytearray(pixels)
        def to_grayscale(self):return self
    class Sensor:
        GRAYSCALE=1
        def __init__(self,**kwargs):events.append('sensor_init')
        def reset(self):events.append('sensor_reset')
        def set_framesize(self,**kwargs):pass
        def set_pixformat(self,*args,**kwargs):pass
        def set_hmirror(self,value):pass
        def set_vflip(self,value):pass
        def run(self):events.append('sensor_run')
        def snapshot(self,**kwargs):events.append('snapshot');return Frame()
        def stop(self):events.append('sensor_stop')
    class Display:
        VIRT=0
        @staticmethod
        def init(*args,**kwargs):events.append('display_init')
        @staticmethod
        def deinit():events.append('display_deinit')
    class Media:
        fail=False
        @classmethod
        def init(cls):
            events.append('media_init')
            if cls.fail:raise RuntimeError('injected_media_failure')
        @staticmethod
        def deinit():events.append('media_deinit')
    def module(name,**attrs):
        m=types.ModuleType(name);m.__dict__.update(attrs);return m
    fake={'image':module('image',GRAYSCALE=1,Image=lambda _:Frame()),
          'media':module('media'),'media.sensor':module('media.sensor',Sensor=Sensor,CAM_CHN_ID_0=0),
          'media.display':module('media.display',Display=Display),'media.media':module('media.media',MediaManager=Media)}
    old={k:sys.modules.get(k) for k in fake}
    sys.modules.update(fake)
    spec=importlib.util.spec_from_file_location('observer_bench_test',bundle)
    script=importlib.util.module_from_spec(spec);spec.loader.exec_module(script)
    def ticks():clock[0]+=10;return clock[0]
    script.time=types.SimpleNamespace(ticks_ms=ticks,ticks_diff=lambda a,b:a-b,sleep_ms=lambda n:events.append('sleep'))
    script.os=types.SimpleNamespace(exitpoint=lambda:None)
    script.gc=types.SimpleNamespace(collect=lambda:None,mem_free=lambda:1000000)
    try:yield script,events,Media,Frame
    finally:
        for k,value in old.items():
            if value is None:sys.modules.pop(k,None)
            else:sys.modules[k]=value


def run(output,bundle):
    """idle、SD回放、live清理、初始化失败及UART未配置拒绝均实际执行。"""
    checks=[];logs={}
    def check(name,value):
        assert value,name
        checks.append(name)
    with environment(bundle) as (script,events,media,frame):
        stream=io.StringIO()
        with redirect_stdout(stream):script.main()
        check('default_idle_no_camera_or_uart',not events and '[IDLE]' in stream.getvalue())
        script.MODE='sd_replay';script.SD_FRAME_IDS=(1,2)
        stream=io.StringIO()
        with redirect_stdout(stream):script.main()
        lines=[json.loads(s) for s in stream.getvalue().splitlines()]
        check('SD_reads_two_frames_without_camera',len(lines)==2 and not events)
        check('SD_packets_all_invalid',all(not r['wire_valid'] for r in lines))
        check('SD_timing_label_not_camera',all(r['source_kind']=='sd_decode_not_camera' for r in lines))
        check('diagnostic_not_fake_finish',all(r['finish_state']=='not_ported' and not r['control_ready'] for r in lines))
        logs['sd_model']=lines
    with environment(bundle) as (script,events,media,frame):
        script.MODE='live';script.LIVE_DURATION_MS=120
        stream=io.StringIO()
        with redirect_stdout(stream):script.main()
        lines=[json.loads(s) for s in stream.getvalue().splitlines() if s.startswith('{')]
        check('live_model_takes_new_frame',bool(lines) and 'snapshot' in events)
        check('live_cleanup_order',events[-4:]==['sensor_stop','display_deinit','sleep','media_deinit'])
        check('live_never_enables_valid_path',all(not r['wire_valid'] for r in lines))
        logs['live_model']=dict(events=events,diagnostics=lines)
    with environment(bundle) as (script,events,media,frame):
        script.MODE='live';media.fail=True
        try:
            with redirect_stdout(io.StringIO()):script.main()
        except RuntimeError as exc:check('original_init_error_preserved',str(exc)=='injected_media_failure')
        else:raise AssertionError('expected injected error')
        check('partial_init_attempts_all_cleanup',all(s in events for s in ('sensor_stop','display_deinit','media_deinit')))
        logs['failed_init_cleanup']=events
    with environment(bundle) as (script,events,media,frame):
        script.MODE='live';script.UART_ENABLED=True
        try:script.main()
        except ValueError:pass
        else:raise AssertionError('missing verified UART config must fail')
        check('unverified_UART_refused_before_camera',not events)
    save(output,dict(passed=True,checks=checks,logs=logs,scope='PC fake API model only; no real board or end-to-end performance'))
    print(json.dumps(dict(checks=len(checks))))


if __name__=='__main__':
    run(Path('testing/2026-11-08_vision_board_prep/entry_model_tests.json'),
        Path('testing/2026-11-08_vision_board_prep/release/board_bundle/observer_bench_canmv.py'))
