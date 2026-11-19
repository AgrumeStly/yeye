import os, json
print('RESUME_UNAME', os.uname())
for path in ('/sdcard', '/data', '/data/right_angle_logs', '/sdcard/right_angle_logs', '/sdcard/captures', '/sdcard/straight_logs', '/sdcard/lap_runtime_logs'):
    try:
        print('RESUME_FILE_STAT', path, json.dumps(os.stat(path)))
        print('RESUME_VFS', path, json.dumps(os.statvfs(path)))
        if os.stat(path)[0] & 0x4000:
            entries = list(os.ilistdir(path.encode()))
            print('RESUME_RAW_DIRECTORY', path, len(entries))
            for entry in entries[:12]:
                print('RESUME_RAW_ENTRY', repr(entry))
    except Exception as exc:
        print('RESUME_FILE_ERROR', path, str(exc))
print('RESUME_READ_ONLY_DONE')
