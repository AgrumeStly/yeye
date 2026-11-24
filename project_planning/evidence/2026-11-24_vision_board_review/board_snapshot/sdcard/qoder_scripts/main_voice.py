import gc
try:
    exec(open('/sdcard/qoder_scripts/voice_assistant.py').read())
except KeyboardInterrupt:
    print('voice assistant stopped by user')
except Exception as e:
    print('voice assistant crashed:', type(e).__name__, e)