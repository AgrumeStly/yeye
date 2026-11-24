"""本次主控授权的板上资料只读归档；不执行或写入板上程序。"""
import sys
import json
import base64
import hashlib
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone

ROOT = Path('D:/projects/projectsyeye')
sys.path.insert(0, str(ROOT / 'vision/tools'))
from canmv_lap_bench import Session

OUT = ROOT / 'project_planning/evidence/2026-11-24_vision_board_review'
OUT.mkdir(parents=True, exist_ok=True)
MODE = sys.argv[1]
session = Session(OUT)
result = {'at_utc': datetime.now(timezone.utc).isoformat(), 'mode': MODE,
          'board_write_requested': False, 'run_script_requested': False,
          'connection_may_interrupt_existing_script': True}
try:
    result['board'] = session.request('connectBoard', {'port': 'COM10', 'baudRate': 12000000}, timeout=25)
    result['script_status_after_connect'] = session.request('scriptRunning')
    result['directories'] = {}
    paths = (['/', '/sdcard', '/data', '/udisk', '/flash'] if MODE == 'inventory'
             else ['/sdcard/qoder_scripts', '/data/voice_test', '/data/models'] if MODE == 'review'
             else ['/sdcard/examples/kmodel', '/sdcard/examples/utils', '/data/voice_test'] if MODE == 'resources'
             else ['/data/captures', '/data/final_sampling_gc2093', '/sdcard/examples/ai_test_kmodel', '/sdcard/examples/ai_test_utils'] if MODE == 'collection'
             else [] if MODE == 'motionlog'
             else json.loads(sys.argv[2]))
    for path in paths:
        try:
            pages = []
            offset = 0
            for _ in range(200):
                page = session.request('io.listDir', {'path': path, 'offset': offset}, timeout=30)
                pages.append(page)
                offset = page.get('nextOffset')
                if offset is None:
                    break
            else:
                raise RuntimeError('directory pagination bound')
            result['directories'][path] = pages
            if MODE in ('review', 'collection') and path != '/data/models':
                for page in pages:
                    for entry in page.get('entries', []):
                        name = entry['name']
                        if '/' in name or '\\' in name or name in ('.', '..'):
                            raise ValueError('invalid directory entry')
                        if entry['type'] == 'directory':
                            paths.append(path.rstrip('/') + '/' + name)
        except Exception as exc:
            result['directories'][path] = {'error': repr(exc)}
    if MODE in ('fetch', 'review', 'resources', 'collection', 'motionlog'):
        result['files'] = []
        sources = json.loads(sys.argv[3]) if MODE == 'fetch' else [
            path.rstrip('/') + '/' + entry['name']
            for path, pages in result['directories'].items() if isinstance(pages, list)
            for page in pages for entry in page.get('entries', [])
            if entry['type'] == 'file' and entry['name'].lower().endswith(('.py', '.md', '.txt', '.json', '.jsonl', '.csv', '.bak'))
            and entry.get('size', 0) <= 2*1024*1024
        ]
        if MODE == 'resources':
            sources = ['/data/voice_test/events.log', '/data/voice_test/uart_events.log',
                       '/data/voice_test/session.wav', '/data/models/multi_kws.kmodel',
                       '/sdcard/examples/kmodel/multi_kws.kmodel', '/sdcard/examples/kmodel/kws.kmodel']
            sources += ['/sdcard/examples/utils/' + name for name in ('wozai.wav', 'go_new.wav', 'stop_new.wav', 'wow_new.wav')]
        if MODE == 'motionlog':
            sources = ['/data/captures/d01_straight_run01/collect_log.csv']
        if MODE == 'review':
            sources += ['/sdcard/' + entry['name'] for page in json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))['directories']['/sdcard']
                        for entry in page.get('entries', []) if entry['type'] == 'file'
                        and entry['name'].lower().endswith(('.py', '.txt', '.bak')) and '\ufffd' not in entry['name']]
        for remote in sorted(set(sources)):
            parts = PurePosixPath(remote).parts
            if not remote.startswith(('/sdcard/', '/data/')) or '..' in parts:
                raise ValueError('unexpected source path')
            before = session.request('io.queryFileStat', {'path': remote})
            size = before.get('size')
            if before.get('type') != 'file' or type(size) is not int or not 0 <= size <= 2*1024*1024:
                raise ValueError('unexpected source metadata')
            raw = bytearray()
            while len(raw) < size:
                count = min(32768, size-len(raw))
                payload = session.request('io.readFile', {'path': remote, 'offset': len(raw), 'size': count})
                chunk = base64.b64decode(payload['dataBase64'], validate=True) if isinstance(payload.get('dataBase64'), str) else bytes(payload.get('data', []))
                if len(chunk) != count:
                    raise ValueError('short read')
                raw.extend(chunk)
            after = session.request('io.queryFileStat', {'path': remote})
            if before != after:
                raise RuntimeError('file metadata changed during snapshot')
            local = OUT / 'board_snapshot' / remote.lstrip('/')
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(raw)
            result['files'].append({'remote': remote, 'local': str(local.relative_to(OUT)), 'bytes': len(raw),
                                    'sha256': hashlib.sha256(raw).hexdigest(), 'stat_before': before, 'stat_after': after})
    result['completed'] = True
except BaseException as exc:
    result['error'] = repr(exc)
    raise
finally:
    session.close()
    (OUT / (MODE + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    for name in ('backend.jsonl', 'terminal.txt'):
        (OUT/name).rename(OUT/(MODE+'_'+name))
print(json.dumps(result if MODE == 'inventory' else {'completed': result.get('completed'), 'error': result.get('error'), 'directories': list(result.get('directories', {})), 'files': [{k: row[k] for k in ('remote', 'bytes', 'sha256')} for row in result.get('files', [])]}, ensure_ascii=False))
