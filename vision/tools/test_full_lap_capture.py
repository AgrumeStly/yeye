"""整圈入口的一次性许可检查：模拟上电、写卡异常与重连，不访问实体板。"""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_push_capture as model

spec = importlib.util.spec_from_file_location(
    "full_lap_capture", Path(__file__).resolve().parents[1]/"src/capture_full_lap_canmv.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class StartupTests(unittest.TestCase):
    """仅允许有效许可消费后进入采集；失败不自动重建许可。"""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.arm = self.root/"full_lap_capture.arm"
        self.original = self.root/"existing.jpg"
        self.original.write_bytes(b"previous capture untouched")
        for name, value in (("ARM_FILE", str(self.arm)),):
            patcher = patch.object(capture, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.sync = patch.object(capture, "_sync")
        self.sync_mock = self.sync.start()
        self.addCleanup(self.sync.stop)
        self.main_patch = patch.object(capture, "main")
        self.main_mock = self.main_patch.start()
        self.addCleanup(self.main_patch.stop)

    def run_startup(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return capture.run_once_if_armed()

    def arm_once(self):
        self.arm.write_bytes(capture.ARM_TOKEN.encode("ascii"))

    def test_missing_marker_leaves_old_files_untouched(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        self.assertIsNone(self.run_startup())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        self.main_mock.assert_not_called()
        self.sync_mock.assert_not_called()

    def test_valid_token_is_deleted_and_synced_before_capture(self):
        self.arm_once()
        def inspect_before_capture():
            self.assertFalse(self.arm.exists())
            self.sync_mock.assert_called_once_with()
            return "session"
        self.main_mock.side_effect = inspect_before_capture
        self.assertEqual(self.run_startup(), "session")
        self.assertIsNone(self.run_startup())
        self.main_mock.assert_called_once_with()

    def test_empty_partial_or_overlong_marker_does_not_capture(self):
        for data in (b"", b"full_lap_once_v1", b"wrong\n", b"x"*100):
            self.arm.write_bytes(data)
            self.assertIsNone(self.run_startup())
            self.assertEqual(self.arm.read_bytes(), data)
        self.main_mock.assert_not_called()

    def test_capture_failure_still_disarms_reconnect(self):
        self.arm_once()
        self.main_mock.side_effect = RuntimeError("camera model failed")
        with self.assertRaises(RuntimeError):
            self.run_startup()
        self.assertFalse(self.arm.exists())
        self.assertIsNone(self.run_startup())
        self.main_mock.assert_called_once_with()

    def test_read_error_is_not_treated_as_missing(self):
        with patch("builtins.open", side_effect=OSError(5, "read error model")):
            with self.assertRaises(OSError):
                self.run_startup()
        self.main_mock.assert_not_called()

    def test_delete_error_never_starts_camera(self):
        self.arm_once()
        with patch.object(capture.os, "remove", side_effect=OSError(5, "delete model")):
            with self.assertRaises(OSError):
                self.run_startup()
        self.assertTrue(self.arm.exists())
        self.main_mock.assert_not_called()

    def test_sync_error_never_starts_camera(self):
        self.arm_once()
        self.sync_mock.side_effect = OSError(5, "sync model")
        with self.assertRaises(OSError):
            self.run_startup()
        self.assertFalse(self.arm.exists())
        self.main_mock.assert_not_called()


class FullWindow(model.PushTests):
    """复用相机／时钟故障模型，检查180秒后再次上电不增删原件。"""

    def test_armed_full_window_and_idle_reconnect(self):
        arm = self.root/"full_lap_capture.arm"
        arm.write_bytes(capture.ARM_TOKEN.encode("ascii"))
        with patch.multiple(capture, ARM_FILE=str(arm), SCENE="full_lap", PREPARE_MS=15000,
                            CAPTURE_MS=180000, INTERVAL_MS=100, MAX_FRAMES=2400, WARMUP_FRAMES=30):
            with contextlib.redirect_stdout(io.StringIO()):
                folder = capture.run_once_if_armed()
            result = model.verify(folder)
            self.assertEqual(result["frames"], 1800)
            self.assertEqual(result["scene"], "full_lap")
            self.assertGreaterEqual(result["capture_elapsed_ms"], 180000)
            self.assertEqual(self.metadata()["prepare_ms"], 15000)
            self.assertEqual(self.signals, [(1, 600), (2, 450)])
            self.assertFalse(arm.exists())
            before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in self.root.rglob("*") if p.is_file()}
            snapshots = self.snapshot_count
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNone(capture.run_once_if_armed())
            after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in self.root.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(self.snapshot_count, snapshots)


if __name__ == "__main__":
    # 原13项检查绑定整圈模块；只额外跑一次完整时间窗，避免重复继承的用例。
    capture._validate_config()
    model.capture = capture
    suite = unittest.TestLoader().loadTestsFromTestCase(model.PushTests)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(StartupTests))
    suite.addTest(FullWindow("test_armed_full_window_and_idle_reconnect"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    output = dict(tests_run=result.testsRun, passed=result.wasSuccessful(),
                  source_sha256=hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest(),
                  scope="PC models, 180-second virtual window and read-only reconnect; not actual board full lap")
    destination = Path(__file__).resolve().parents[2]/"testing/2026-11-08_full_lap_capture/startup_verification.json"
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
