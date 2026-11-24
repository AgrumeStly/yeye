import gc
import os
print('ALIVE', gc.mem_free())
try:
    st = os.stat('/sdcard/vision_classify.py')
    print('SCRIPT-ON-CARD size=', st[6])
except Exception as e:
    print('stat err', e)
