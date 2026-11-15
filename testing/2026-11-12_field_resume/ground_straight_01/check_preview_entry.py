"""仅假会话核对本次R6禁驱动预览配置；不连接设备，不模拟实物通过。"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'vision/tools'))
spec = importlib.util.spec_from_file_location('bench_check', ROOT/'vision/tools/canmv_lap_bench.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
sessions = []

class Fake:
    def __init__(self, output):
        self.running = False
        self.script_error = False
        self.tail = '[L1 DONE] HOST ONLY'
        self.requests = []
        self.closed = False
        sessions.append(self)
    def request(self, method, params=None, timeout=None):
        self.requests.append((method, params))
        if method == 'connectBoard':
            return {'host_fake': True}
        if method == 'scriptRunning':
            return {'running': False}
        if method == 'runScript':
            self.running = False
            return {'host_fake': True}
        raise AssertionError(method)
    def close(self):
        self.closed = True

bench.Session = Fake
output = Path(__file__).parent/'preview_entry_check_01'
sys.argv = ['bench', 'live_no_drive', '--visual-bundle', 'r6', '--output', str(output)]
with contextlib.redirect_stdout(io.StringIO()):
    bench.main()
session = sessions[0]
submitted = [p['script'] for m,p in session.requests if m == 'runScript']
assert len(submitted) == 1
source = submitted[0]
assert '\nALLOW_DRIVE=False\n' in source and '\nDURATION_MS=10000\n' in source
assert "MODE='live'" in source and 'SHOW_PREVIEW=True' in source
assert session.capture_preview and session.closed
assert not any(m in ('io.writeFile','replInput') for m,_ in session.requests)
compile(source, '<no-drive-preview>', 'exec')
info = json.loads((output/'run.json').read_text(encoding='utf-8'))
assert info['real_camera_link']['base_bundle'] == 'r6'
assert not info['main_py_written'] and not info['automatic_motor_start_permitted']
(output/'checks.json').write_text(json.dumps(dict(passed=True, host_fake_only=True,
    drive_gate=False, duration_ms=10000, preview=True, main_py_written=False,
    automatic_start=False),indent=2),encoding='utf-8')
print('R6 no-drive preview entry checks passed; no board accessed.')
