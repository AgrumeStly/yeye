"""上电手推采集故障模型：真实临时JPEG／文件系统，模拟相机、PWM与时钟。"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_push_capture import verify

spec = importlib.util.spec_from_file_location('push_capture', Path(__file__).resolve().parents[1]/'src/capture_push_canmv.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class Clock:
    """故意靠近回绕边界启动，验证ticks_diff而非直接相减。"""

    def __init__(self): self.now = (1 << 20)-400
    def ticks_ms(self): return self.now % (1 << 20)
    def ticks_diff(self, a, b): return (a-b+(1 << 19)) % (1 << 20)-(1 << 19)
    def sleep_ms(self, value): self.now += value


class PushTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.events, self.signals = [], []
        self.clock = Clock()
        self.save_count = self.snapshot_count = 0
        self.fail_save_at = self.interrupt_at = None
        self.bad_format = self.fail_cleanup = False
        owner = self

        class Frame:
            def width(self): return 320
            def height(self): return 240
            def format(self): return 'bad' if owner.bad_format else 'image_gray'
            def save(self, path, quality):
                owner.save_count += 1
                if owner.save_count == owner.fail_save_at:
                    raise OSError(28, 'disk full model')
                ok, data = cv2.imencode('.jpg', np.full((240, 320), 120, np.uint8))
                assert ok
                Path(path).write_bytes(data.tobytes())

        class Sensor:
            GRAYSCALE = 'sensor_gray'
            def __init__(self, **kwargs): owner.events.append('camera_created')
            def reset(self): pass
            def set_framesize(self, **kwargs): pass
            def set_pixformat(self, *args, **kwargs): pass
            def set_hmirror(self, value): pass
            def set_vflip(self, value): pass
            def run(self): owner.events.append('camera_run')
            def snapshot(self, **kwargs):
                owner.snapshot_count += 1
                if owner.snapshot_count == owner.interrupt_at:
                    raise KeyboardInterrupt()
                owner.clock.now += 10
                return Frame()
            def stop(self): owner.events.append('camera_stop')

        class Media:
            @staticmethod
            def init(): owner.events.append('media_init')
            @staticmethod
            def deinit():
                owner.events.append('media_deinit')
                if owner.fail_cleanup:
                    raise OSError('media cleanup model')

        class Beeper:
            def __init__(self): owner.events.append('beeper_init')
            def signal(self, count, duration_ms, gap_ms=200):
                owner.signals.append((count, duration_ms))
                if count == 2:
                    # 成功提示必须晚于相机／媒体释放及最终JSON写入。
                    owner.assertEqual(owner.events[-2:], ['camera_stop', 'media_deinit'])
                    owner.assertEqual(owner.metadata()['state'], 'complete')
                owner.clock.now += count*duration_ms+(count-1)*gap_ms
            def close(self): owner.events.append('beeper_close')

        modules = {}
        for name, fields in {'image': {'GRAYSCALE': 'image_gray'}, 'media': {},
                             'media.sensor': {'Sensor': Sensor, 'CAM_CHN_ID_0': 0},
                             'media.media': {'MediaManager': Media}}.items():
            module = types.ModuleType(name)
            module.__dict__.update(fields)
            modules[name] = module
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, modules).start()
        for name, value in dict(SD_ROOT=str(self.root), PREPARE_MS=20, CAPTURE_MS=120,
                                INTERVAL_MS=20, WARMUP_FRAMES=1, MAX_FRAMES=20,
                                SCENE='board_smoke', Beeper=Beeper, time=self.clock).items():
            patch.object(capture, name, value).start()
        patch.object(os, 'exitpoint', lambda: None, create=True).start()
        patch.object(capture, '_sync', lambda: None).start()
        patch.object(capture, '_free_bytes', lambda: 100*1024*1024).start()

    def folders(self): return sorted((self.root/'captures').glob('push_*'))
    def metadata(self): return json.loads((self.folders()[-1]/'session.json').read_text())
    def run_capture(self):
        with contextlib.redirect_stdout(io.StringIO()): return capture.main()
    def assert_no_done(self): self.assertNotIn((2, capture.DONE_BEEP_MS), self.signals)

    def test_timed_capture_wraparound_and_done_after_sync(self):
        result = verify(self.run_capture())
        self.assertEqual(result['frames'], 6)
        self.assertEqual(self.signals, [(1, 600), (2, 450)])
        self.assertLess(self.events.index('media_init'), self.events.index('camera_run'))
        self.assertEqual(self.events[-1], 'beeper_close')

    def test_repeat_does_not_overwrite(self):
        first = Path(self.run_capture())
        original = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        self.run_capture()
        self.assertEqual(len(self.folders()), 2)
        self.assertEqual(original, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()})

    def test_preflight_full_card_no_start_or_done(self):
        self.fail_save_at = 1
        with self.assertRaises(OSError): self.run_capture()
        self.assertEqual(self.metadata()['state'], 'failed')
        self.assertNotIn((1, 600), self.signals)
        self.assert_no_done()

    def test_mid_recording_full_card_keeps_partial(self):
        self.fail_save_at = 3  # 预检、首张成功，第二张保存失败。
        with self.assertRaises(OSError): self.run_capture()
        self.assertEqual(self.metadata()['saved_count'], 1)
        self.assertEqual(self.metadata()['state'], 'failed')
        self.assert_no_done()
        with self.assertRaises(ValueError): verify(self.folders()[0])

    def test_interrupt_has_no_done(self):
        self.interrupt_at = 5  # 1预热+2准备+1保存后中断。
        with self.assertRaises(KeyboardInterrupt): self.run_capture()
        self.assertEqual(self.metadata()['state'], 'interrupted')
        self.assert_no_done()

    def test_no_card_never_initializes_camera(self):
        with patch.object(capture, 'SD_ROOT', str(self.root/'missing')):
            with self.assertRaises(RuntimeError): self.run_capture()
        self.assertNotIn('camera_created', self.events)
        self.assert_no_done()

    def test_low_space_never_initializes_camera(self):
        with patch.object(capture, '_free_bytes', lambda: 100):
            with self.assertRaises(RuntimeError): self.run_capture()
        self.assertFalse(self.folders())
        self.assertNotIn('camera_created', self.events)

    def test_cleanup_failure_rejects_complete(self):
        self.fail_cleanup = True
        with self.assertRaises(RuntimeError): self.run_capture()
        self.assertEqual(self.metadata()['state'], 'failed')
        self.assertTrue(self.metadata()['cleanup_errors'])
        self.assert_no_done()

    def test_manifest_failure_cannot_beep_success(self):
        original = capture._json_file
        def fail_final(path, meta):
            if meta['state'] == 'complete': raise OSError('final write model')
            return original(path, meta)
        with patch.object(capture, '_json_file', fail_final):
            with self.assertRaises(OSError): self.run_capture()
        self.assert_no_done()
        with self.assertRaises(ValueError): verify(self.folders()[0])

    def test_wrong_actual_image_format_rejected(self):
        self.bad_format = True
        with self.assertRaises(RuntimeError): self.run_capture()
        self.assertEqual(self.metadata()['saved_count'], 0)
        self.assert_no_done()

    def test_bad_scene_and_frame_guard_rejected_before_io(self):
        for values in (dict(SCENE='../bad'), dict(MAX_FRAMES=1)):
            with patch.multiple(capture, **values):
                with self.assertRaises(ValueError): self.run_capture()
        self.assertEqual(self.events, [])

    def test_copy_corruption_rejected(self):
        folder = Path(self.run_capture())
        path = folder/'data_0001.jpg'
        data = bytearray(path.read_bytes()); data[40] ^= 1; path.write_bytes(data)
        with self.assertRaises(ValueError): verify(folder)

    def test_rename_eexist_only_replaces_own_metadata(self):
        original = os.rename
        def card_rename(source, target):
            if Path(target).exists(): raise OSError(17, 'EEXIST')
            return original(source, target)
        with patch.object(os, 'rename', card_rename):
            self.assertTrue(verify(self.run_capture())['passed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
