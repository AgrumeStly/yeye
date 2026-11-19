import os, json
def walk(path, depth=0):
    if depth>8:
        raise RuntimeError('depth bound')
    total=0
    count=0
    errors=[]
    try:
        entries=list(os.ilistdir(path.encode()))
    except Exception as exc:
        return 0,0,[[path,repr(exc)]]
    for entry in entries:
        try:
            name=entry[0].decode('utf-8')
            if name in ('.','..') or '/' in name:
                raise ValueError('unsafe name')
            target=path+'/'+name
            if entry[1] & 0x4000:
                c,s,e=walk(target,depth+1)
                count+=c;total+=s;errors+=e
            else:
                size=os.stat(target)[6]
                count+=1;total+=size
        except Exception as exc:
            errors.append([path,repr(entry),repr(exc)])
    return count,total,errors
for folder in ('captures','lap_boot_checks','lap_runtime_logs','straight_logs','right_angle_logs'):
    print('RESUME_INVENTORY',folder,json.dumps(walk('/sdcard/'+folder)))
print('RESUME_READ_ONLY_DONE')
