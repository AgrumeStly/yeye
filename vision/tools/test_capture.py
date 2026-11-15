"""采集流程电脑模型检查；摄像头／时钟／显示用模型，不连接实体开发板。

使用真实临时文件、JPEG编码和校验器，验证不覆盖、日志一致性、故障收尾。
这不能证明CanMV固件兼容、相机画面或TF卡可靠性。
"""

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
from verify_capture import verify

spec = importlib.util.spec_from_file_location("capture_canmv", Path(__file__).resolve().parents[1]/"src/capture_canmv.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class Clock:
    def __init__(self):
        self.now = 250  # 故意靠近256的回绕点，每次相机取图推进10ms。

    def ticks_ms(self):
        return self.now % 256

    @staticmethod
    def ticks_diff(a, b):
        return (a-b+128) % 256-128

    def sleep_ms(self, value):
        self.now += value


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = Clock()
        self.events = []
        self.fail_save = False
        self.bad_jpeg = False
        self.interrupt_at = None
        owner = self

        class Frame:
            def width(self): return 320
            def height(self): return 240
            def format(self): return "image_gray"
            def save(self, path, quality):
                if owner.fail_save:
                    raise OSError(28, "model disk full")
                if owner.bad_jpeg:
                    Path(path).write_bytes(b"broken")
                else:
                    gray = np.tile(np.arange(320, dtype=np.uint16) % 256, (240, 1)).astype(np.uint8)
                    ok, data = cv2.imencode(".jpg", gray, [cv2.IMWRITE_JPEG_QUALITY, quality])
                    assert ok
                    Path(path).write_bytes(data.tobytes())

        class Sensor:
            GRAYSCALE = "sensor_gray"
            def __init__(self, id): self.frames = 0
            def reset(self): owner.events.append("reset")
            def set_framesize(self, **kwargs): owner.events.append("size")
            def set_pixformat(self, *args, **kwargs): pass
            def set_hmirror(self, value): pass
            def set_vflip(self, value): pass
            def run(self): owner.events.append("run")
            def snapshot(self, **kwargs):
                self.frames += 1
                if owner.interrupt_at == self.frames:
                    raise KeyboardInterrupt()
                owner.clock.now += 10
                return Frame()
            def stop(self): owner.events.append("stop")

        class Display:
            VIRT = "virtual"
            @staticmethod
            def init(*args, **kwargs): owner.events.append("display_init")
            @staticmethod
            def show_image(frame): pass
            @staticmethod
            def deinit(): owner.events.append("display_deinit")

        class Media:
            @staticmethod
            def init(): owner.events.append("media_init")
            @staticmethod
            def deinit(): owner.events.append("media_deinit")

        modules = {}
        for name, fields in {"image": {"GRAYSCALE": "image_gray"}, "media": {}, "media.sensor": {"Sensor": Sensor, "CAM_CHN_ID_0": 0},
                             "media.display": {"Display": Display}, "media.media": {"MediaManager": Media}}.items():
            mod = types.ModuleType(name)
            mod.__dict__.update(fields)
            modules[name] = mod
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, modules).start()
        for name, value in dict(SD_ROOT=str(self.root), COUNTDOWN_MS=20, INTERVAL_MS=10,
                                WARMUP_FRAMES=1, FRAME_COUNT=3, POSE="center", PREVIEW_ONLY=False).items():
            patch.object(capture, name, value).start()
        patch.object(capture, "time", self.clock).start()
        patch.object(os, "exitpoint", lambda: None, create=True).start()

    def run_capture(self):
        with contextlib.redirect_stdout(io.StringIO()):
            capture.main()

    def folders(self):
        return sorted((self.root/"captures").glob("v03_*"))

    def test_complete_session_wraparound_and_real_jpeg(self):
        self.run_capture()
        result = verify(self.folders()[0])
        self.assertEqual(result["frames"], 3)
        self.assertLess(self.events.index("media_init"), self.events.index("run"))
        self.assertEqual(self.events[-3:], ["stop", "display_deinit", "media_deinit"])

    def test_repeat_run_does_not_overwrite(self):
        self.run_capture()
        first = self.folders()[0]
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        self.run_capture()
        self.assertEqual(len(self.folders()), 2)
        self.assertEqual(hashes, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()})

    def test_card_rename_rejects_existing_target(self):
        """复现板上EEXIST：元数据反复更新及新会话均应成功，旧会话字节不得改变。"""
        original_rename = os.rename

        def card_rename(source, target):
            if Path(target).exists():
                raise OSError(17, "EEXIST")
            return original_rename(source, target)

        # 隐藏replace以复现旧脚本在CanMV上走rename分支的条件。
        card_os = types.SimpleNamespace(**{name: getattr(os, name) for name in
                                         ("stat", "mkdir", "rename", "remove", "exitpoint")})
        card_os.rename = card_rename
        if hasattr(os, "sync"):
            card_os.sync = os.sync
        with patch.object(capture, "os", card_os):
            self.run_capture()
            first = self.folders()[0]
            self.assertEqual(verify(first)["frames"], 3)
            hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
            self.run_capture()
            self.assertEqual(len(self.folders()), 2)
            self.assertEqual(verify(self.folders()[1])["frames"], 3)
            self.assertEqual(hashes, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()})

    def test_metadata_permission_error_preserves_existing_file(self):
        """非EEXIST错误不得删除原元数据；新临时文件保留，便于定位失败原因。"""
        path = self.root/"session.json"
        path.write_text('{"state":"initializing"}\n', encoding="utf-8")
        original = path.read_bytes()
        with patch.object(capture.os, "rename", side_effect=OSError(13, "EACCES")), \
                patch.object(capture.os, "remove") as remove:
            with self.assertRaises(OSError) as error:
                capture._json_file(str(path), {"state": "capturing"})
            self.assertEqual(error.exception.args[0], 13)
            remove.assert_not_called()
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(json.loads(Path(str(path)+".tmp").read_text())["state"], "capturing")

    def test_metadata_second_rename_failure_retains_temporary_file(self):
        """删除目标后的重命名若失败必须上报，并保留完整临时元数据和其他原始文件。"""
        path = self.root/"session.json"
        path.write_text('{"state":"initializing"}\n', encoding="utf-8")
        evidence = self.root/"old_photo.jpg"
        evidence.write_bytes(b"preserve evidence")
        with patch.object(capture.os, "rename", side_effect=[OSError(17, "EEXIST"), OSError(28, "ENOSPC")]):
            with self.assertRaises(OSError) as error:
                capture._json_file(str(path), {"state": "capturing"})
            self.assertEqual(error.exception.args[0], 28)
        self.assertFalse(path.exists())
        self.assertEqual(json.loads(Path(str(path)+".tmp").read_text())["state"], "capturing")
        self.assertEqual(evidence.read_bytes(), b"preserve evidence")

    def test_disk_full_stays_failed_and_releases_resources(self):
        self.fail_save = True
        with self.assertRaises(OSError): self.run_capture()
        meta = json.loads((self.folders()[0]/"session.json").read_text())
        self.assertEqual((meta["state"], meta["saved_count"]), ("failed", 0))
        self.assertIn("media_deinit", self.events)
        with self.assertRaises(ValueError): verify(self.folders()[0])

    def test_corrupt_jpeg_never_logged_as_complete(self):
        self.bad_jpeg = True
        with self.assertRaises(RuntimeError): self.run_capture()
        folder = self.folders()[0]
        self.assertEqual((folder/"frames.jsonl").read_text(), "")
        self.assertEqual(json.loads((folder/"session.json").read_text())["state"], "failed")

    def test_interrupt_retains_partial_session(self):
        self.interrupt_at = 5  # 预热1、倒计时1、保存2，下一帧中断。
        with self.assertRaises(KeyboardInterrupt): self.run_capture()
        meta = json.loads((self.folders()[0]/"session.json").read_text())
        self.assertEqual(meta["state"], "interrupted")
        self.assertGreater(meta["saved_count"], 0)
        self.assertLess(meta["saved_count"], 3)

    def test_missing_card_has_no_camera_side_effects(self):
        with patch.object(capture, "SD_ROOT", str(self.root/"missing")):
            with self.assertRaises(RuntimeError): self.run_capture()
        self.assertFalse(self.events)

    def test_path_label_rejected_before_io(self):
        with patch.object(capture, "POSE", "../bad"):
            with self.assertRaises(ValueError): self.run_capture()
        self.assertFalse(self.events)

    def test_preview_does_not_create_storage(self):
        self.interrupt_at = 4
        with patch.object(capture, "PREVIEW_ONLY", True):
            with self.assertRaises(KeyboardInterrupt): self.run_capture()
        self.assertFalse((self.root/"captures").exists())

    def test_pc_check_detects_post_copy_corruption(self):
        self.run_capture()
        folder = self.folders()[0]
        path = folder/"data_0001.jpg"
        data = bytearray(path.read_bytes()); data[len(data)//2] ^= 1; path.write_bytes(data)
        with self.assertRaises(ValueError): verify(folder)


if __name__ == "__main__":
    unittest.main(verbosity=2)
