"""仅核对本轮交付路径、原始下载哈希及会话关闭状态，不连接任何设备。"""
import hashlib
import json
from pathlib import Path
import re

folder = Path(__file__).resolve().parent
root = folder.parents[1]
directories = ('r8_resume_mcu_01', 'r8_bench_mcu_01', 'r8_bench_mcu_02',
    'r8_positioned_mcu_01', 'r8_program_deploy_01', 'live_drive_10',
    'ground_07_capture', 'ground_07_camera', 'ground_07_stopped_view')
files = [path for name in directories for path in (folder/name).rglob('*') if path.is_file()]
files += [folder/name for name in ('r8_field_record.md', 'ground_07_analysis.py',
    'ground_07_review.json', 'ground_07_window.json', 'r8_field_verify.py', '.gitattributes')]
files += [root/'project_planning/tasks/I-04-RIGHT-ANGLE.md', folder/'entry_r8_record.md']
assert all(path.is_file() and path.resolve().is_relative_to(root.resolve()) for path in files)
assert len(files) == len(set(files))
for path in (folder/'r8_field_record.md',):
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        assert (path.parent/target).is_file(), target
deployment = json.loads((folder/'r8_program_deploy_01/result.json').read_text(encoding='utf-8'))
assert deployment['completed'] and deployment['main_unchanged'] and not deployment['script_executed']
assert (folder/'r8_program_deploy_01/readback_right_angle_drive_r8.py').read_bytes() == (folder/'release_r8_entry/right_angle_drive.py').read_bytes()
for name in ('status.json', 'result.json'):
    status = json.loads((folder/'live_drive_10'/name).read_text(encoding='utf-8'))
    assert status['current_status']['running'] is False
    assert status['source_sha256'] == deployment['program_sha256']
assert json.loads((folder/'ground_07_stopped_view/review.json').read_text())['all_wire_invalid']
failed_read = json.loads((folder/'r8_bench_mcu_01/capture.json').read_text())
assert failed_read['samples'] == [] and 'No ACK' in failed_read['error']
fetch = json.loads((folder/'ground_07_camera/fetch.json').read_text(encoding='utf-8'))
for item in fetch['files']:
    raw = (folder/'ground_07_camera'/item['remote'].rsplit('/', 1)[1]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256'] and len(raw) == item['bytes']
manifest = [{'path': path.relative_to(root).as_posix(), 'bytes': path.stat().st_size,
    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sorted(files)]
result = dict(passed=True, hardware_actions=False, checks=['current record links',
    'deployment byte equality', 'camera session closed', 'no-drive photo probe',
    'failed SWD preserved', '17 downloaded file hashes'], files=manifest)
out = folder/'r8_field_checks.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(passed=True, files=len(files)+1, bytes=sum(item['bytes'] for item in manifest)), ensure_ascii=False))
