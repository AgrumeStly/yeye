import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path('D:/projects/projectsyeye')
sys.path.insert(0,str(ROOT/'vision/tools'))
from canmv_lap_bench import Session

out=ROOT/'testing/2026-11-18_right_angle/ground_07_camera'
out.mkdir(exist_ok=False)
session=Session(out)
result={'files':[],'no_start':True,'no_camera_run':True,'no_board_write':True}
def fetch(name, limit):
    remote='/data/right_angle_logs/'+name
    stat=session.request('io.queryFileStat',{'path':remote})
    size=stat['size']
    if not stat.get('exists') or not 0<size<=limit:raise ValueError('invalid file size '+name)
    data=bytearray()
    while len(data)<size:
        count=min(32768,size-len(data))
        reply=session.request('io.readFile',{'path':remote,'offset':len(data),'size':count})
        part=base64.b64decode(reply['dataBase64'],validate=True) if isinstance(reply.get('dataBase64'),str) else bytes(reply.get('data',[]))
        if len(part)!=count:raise ValueError('short read')
        data.extend(part)
    (out/name).write_bytes(data)
    result['files'].append({'remote':remote,'bytes':size,'sha256':hashlib.sha256(data).hexdigest()})
    return data
try:
    session.request('connectBoard',{'port':'COM10','baudRate':12000000},timeout=25)
    if session.request('scriptRunning').get('running') is not False:raise RuntimeError('camera active; not interrupted')
    data=fetch('run_0005.jsonl',16*1024*1024)
    rows=[json.loads(s) for s in data.decode('utf-8').splitlines()]
    events=[r for r in rows if r.get('event')=='path_lost']
    result['loss_events']=events
    for event in events:
        prefix=event['prefix']
        if not prefix.startswith('/data/right_angle_logs/run_0005_loss_') or '/' in prefix[len('/data/right_angle_logs/'):]:
            raise ValueError('unexpected event image path')
        name=prefix.rsplit('/',1)[1]
        for suffix in ('_before.pgm','_after.pgm'):
            raw=fetch(name+suffix,76900)
            if len(raw)!=76815 or raw[:15]!=b'P5\n320 240\n255\n':raise ValueError('unexpected original PGM')
    result['completed']=True
except BaseException as exc:
    result['error']=repr(exc)
    raise
finally:
    session.close()
    (out/'fetch.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':len(result['files']),'loss_events':len(result.get('loss_events',[])),'completed':result.get('completed')}))
