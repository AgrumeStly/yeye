"""本任务资料检查：路径、快照和RPC范围；不导入板上应用或连接设备。"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DOCS = [ROOT/'AI_HANDOFF.md', ROOT/'project_planning/project_status.md',
        ROOT/'project_planning/voice_handoff.md', ROOT/'vision/README.md',
        ROOT/'project_planning/tasks/TASK-20261124-01-vision-board-review.md', OUT/'review.md']
errors = []
links = 0
for doc in DOCS:
    source = doc.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)', source):
        if target.startswith(('http:', 'https:', '#', 'mailto:')):
            continue
        path = unquote(target.split('#', 1)[0].strip('<>'))
        links += 1
        if not (doc.parent/path).exists() and (doc.parent/path).resolve() != OUT/'checks.json':
            errors.append({'document': str(doc.relative_to(ROOT)), 'missing_link': target})
manifest_count = 0
for name in ('review', 'resources', 'collection', 'motionlog'):
    meta = json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))
    for entry in meta.get('files', []):
        raw = (OUT/entry['local']).read_bytes()
        manifest_count += 1
        if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
            errors.append({'snapshot_mismatch': entry['remote']})
summary = json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
if not all(row['byte_identical'] for row in summary['source_matches']):
    errors.append({'old_source_comparison': 'mismatch'})
if not all(row['only_read_and_connection_methods'] for row in summary['rpc']):
    errors.append({'rpc': 'unexpected board request'})
raw_wifi = OUT/'board_snapshot/sdcard/qoder_scripts/wifi_debug_track.py'
redacted_wifi = raw_wifi.with_name('wifi_debug_track.redacted.py')
if re.sub(r"(?m)^PASSWORD\s*=.*$", "PASSWORD = '<REDACTED_LOCAL_HOTSPOT_PASSWORD>'",
          raw_wifi.read_text(encoding='utf-8')) != redacted_wifi.read_text(encoding='utf-8'):
    errors.append({'redaction': 'unexpected source modification'})
tracked_docs = [str(path.relative_to(ROOT)) for path in DOCS if path.name != 'review.md' and '/tasks/' not in str(path).replace('\\', '/')]
diff_check = subprocess.run(['git', 'diff', '--check', '--', *tracked_docs], cwd=ROOT, capture_output=True, text=True)
if diff_check.returncode:
    errors.append({'git_diff_check': diff_check.stdout+diff_check.stderr})
result = {'scope': 'documentation and local evidence only; no application test, build, device run or flash',
          'documents': [str(path.relative_to(ROOT)) for path in DOCS],
          'local_links_checked': links, 'snapshot_files_verified_against_read_manifest': manifest_count,
          'old_source_byte_matches': summary['source_matches'],
          'rpc_attempts_audited': len(summary['rpc']),
          'board_read_limitations_retained': ['io.listDir timeout for d01_straight_run01',
               'motion CSV malformed and non-UTF8', 'connection/disconnection soft reboots',
               'old voice logs not bound to current source hash', 'original recording empty'],
          'passed': not errors, 'errors': errors}
(OUT/'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['passed'] else 1)
