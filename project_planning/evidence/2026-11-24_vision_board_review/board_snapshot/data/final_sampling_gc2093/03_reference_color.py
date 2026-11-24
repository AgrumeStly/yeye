import time, os
from media.sensor import *
from media.display import *
from media.media import *

SCENE_ID = "c02_d020_center_hd"
OUT_DIR = "/data/captures/reference_color"
DISTANCE_CM = 20        # 无距离标定时填 -1
MOUNT_HEIGHT_MM = 0     # 安装参考照可填实测值
PITCH_DEG = 0.0
AWB_NOTE = "default_auto"
HOLD_S = 6
SHOW = True

W, H = 1280, 960


def mkdirs():
    for path in ("/data/captures", OUT_DIR):
        try:
            os.mkdir(path)
        except OSError:
            pass


sensor = None
log = None
try:
    mkdirs()
    start = 1
    for name in os.listdir(OUT_DIR):
        if name.startswith("ref_") and name.endswith(".jpg"):
            idx = int(name[4:-4])
            if idx >= start:
                start = idx + 1

    sensor = Sensor(width=1280, height=960, fps=90)
    sensor.reset()
    sensor.set_framesize(width=W, height=H)
    sensor.set_pixformat(Sensor.RGB565)
    sensor.run()
    if SHOW:
        Display.init(Display.VIRT, width=W, height=H, fps=30, to_ide=True)
    for _ in range(30):
        sensor.snapshot()

    for left in range(HOLD_S, 0, -1):
        os.exitpoint()
        img = sensor.snapshot()
        img.draw_string_advanced(8, 8, 32, "hold %ds" % left, color=(255, 0, 0))
        img.draw_string_advanced(8, 50, 24, SCENE_ID, color=(255, 0, 0))
        if SHOW:
            Display.show_image(img)
        time.sleep_ms(1000)

    img = sensor.snapshot()
    ticks = time.ticks_ms()
    clean = "%s/ref_%04d.jpg" % (OUT_DIR, start)
    img.save(clean, quality=95)
    clean_bytes = os.stat(clean)[6]
    st = img.get_statistics()
    exposure = sensor.exposure()

    log_path = OUT_DIR + "/reference_log.csv"
    fresh = True
    try:
        os.stat(log_path)
        fresh = False
    except OSError:
        pass
    log = open(log_path, "a")
    if fresh:
        log.write("idx,name,ticks_ms,scene_id,distance_cm,mount_height_mm,pitch_deg,Lmean,exposure,awb_note,clean_bytes\n")
    log.write("%d,ref_%04d.jpg,%d,%s,%d,%d,%.1f,%d,%s,%s,%d\n" % (
        start, start, ticks, SCENE_ID, DISTANCE_CM, MOUNT_HEIGHT_MM,
        PITCH_DEG, st.mean(), exposure, AWB_NOTE, clean_bytes))
    log.flush()
    print("REFERENCE_DONE scene=%s file=%s bytes=%d" % (SCENE_ID, clean, clean_bytes))
except BaseException as e:
    print("ERROR:", e)
    print("STOPPED scene=%s dir=%s" % (SCENE_ID, OUT_DIR))
    raise
finally:
    if log is not None:
        log.close()
    if isinstance(sensor, Sensor):
        sensor.stop()
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
