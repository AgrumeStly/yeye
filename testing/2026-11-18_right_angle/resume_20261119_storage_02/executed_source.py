import os, json
print('RESUME_UNAME', os.uname())
for path in ('/', '/sdcard', '/sdcard/right_angle_logs', '/sdcard/main.py'):
    try:
        print('RESUME_FILE_STAT', path, json.dumps(os.stat(path)))
        if os.stat(path)[0] & 0x4000:
            names = os.listdir(path)
            print('RESUME_DIRECTORY', path, len(names), json.dumps(names[:50]))
            if path == '/sdcard':
                for name in names[:50]:
                    print('RESUME_ENTRY', name, json.dumps(os.stat(path+'/'+name)))
    except OSError as exc:
        print('RESUME_FILE_ERROR', path, str(exc))
print('RESUME_READ_ONLY_DONE')
