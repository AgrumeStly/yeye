import os, json
print('RESUME_SD_STATVFS', json.dumps(os.statvfs('/sdcard')))
for path in ('/sdcard/right_angle_logs/run_0012.jsonl', '/sdcard/right_angle_logs/run_0013.jsonl', '/sdcard/right_angle_logs/run_0013_view.pgm'):
    try:
        print('RESUME_FILE_STAT', path, json.dumps(os.stat(path)))
    except OSError as exc:
        print('RESUME_FILE_ERROR', path, str(exc))
print('RESUME_READ_ONLY_DONE')
