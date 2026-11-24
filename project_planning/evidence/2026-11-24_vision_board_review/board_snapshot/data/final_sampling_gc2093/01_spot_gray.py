import time, os
from media.sensor import *
from media.display import *
from media.media import *

SCENE_ID = "c02_d020_center"
OUT_DIR = "/data/captures/spot_gray"
MODE = "calib"          # "calib"=2帧；"static"=5帧
DISTANCE_CM = 20        # 无距离标定时填 -1
LATERAL_CM = 0
HEADING_DEG = 0
EXPECTED_PATH = "both" # both | single | none | finish
LOCK_AE = True
HOLD_S = 8
SHOW = True

W, H = 320, 240
N_SHOTS = 2 if MODE == "calib" else 5


def mkdirs():
    for path in ("/data/captures", OUT_DIR):
        try:
            os.mkdir(path)
        except OSError:
            pass


def next_index():
    start = 1
    for name in os.listdir(OUT_DIR):
        if name.startswith("data_") and name.endswith(".jpg"):
            idx = int(name[5:-4])
            if idx >= start:
                start = idx + 1
    return start


def show_preview(img, text):
    img.draw_string_advanced(4, 6, 18, text, color=30)
    img.draw_string_advanced(4, 30, 14, SCENE_ID, color=30)
    if SHOW:
        Display.show_image(img)


sensor = None
log = None
try:
    mkdirs()
    start = next_index()
    log_path = OUT_DIR + "/spot_log.csv"
    fresh = True
    try:
        os.stat(log_path)
        fresh = False
    except OSError:
        pass
    log = open(log_path, "a")
    if fresh:
        log.write("idx,name,ticks_ms,scene_id,mode,distance_cm,lateral_cm,heading_deg,expected_path,mean,min,max,median,exposure,ae_locked,clean_bytes,debug_bytes\n")
    log.flush()

    sensor = Sensor(id=1, width=1280, height=960, fps=90)
    sensor.reset()
    sensor.set_framesize(width=W, height=H)
    sensor.set_pixformat(Sensor.GRAYSCALE)
    sensor.run()
    if SHOW:
        Display.init(Display.VIRT, width=W, height=H, fps=30, to_ide=True)
    for _ in range(30):
        sensor.snapshot()
    if LOCK_AE:
        sensor.auto_exposure(False)

    for left in range(HOLD_S, 0, -1):
        os.exitpoint()
        img = sensor.snapshot()
        show_preview(img, "hold %ds" % left)
        time.sleep_ms(1000)

    for n in range(N_SHOTS):
        os.exitpoint()
        img = sensor.snapshot()
        ticks = time.ticks_ms()
        idx = start + n
        clean = "%s/data_%04d.jpg" % (OUT_DIR, idx)
        img.save(clean, quality=90)
        clean_bytes = os.stat(clean)[6]
        st = img.get_statistics()
        exposure = sensor.exposure()

        img.draw_line(W // 2, 40, W // 2, H - 1, color=150, thickness=1)
        img.draw_line(0, 40, W - 1, 40, color=90, thickness=1)
        img.draw_line(0, 200, W - 1, 200, color=90, thickness=1)
        img.draw_rectangle(0, H - 42, W, 42, color=255, fill=True)
        img.draw_string_advanced(4, H - 39, 14, "#%04d %s" % (idx, SCENE_ID), color=0)
        img.draw_string_advanced(4, H - 20, 12, "mean=%d expo=%s" % (st.mean(), exposure), color=0)
        debug = "%s/dbg_%04d.jpg" % (OUT_DIR, idx)
        img.save(debug, quality=85)
        debug_bytes = os.stat(debug)[6]
        log.write("%d,data_%04d.jpg,%d,%s,%s,%d,%d,%d,%s,%d,%d,%d,%d,%s,%d,%d,%d\n" % (
            idx, idx, ticks, SCENE_ID, MODE, DISTANCE_CM, LATERAL_CM, HEADING_DEG,
            EXPECTED_PATH, st.mean(), st.min(), st.max(), st.median(), exposure,
            1 if LOCK_AE else 0, clean_bytes, debug_bytes))
        log.flush()
        if SHOW:
            Display.show_image(img)
        time.sleep_ms(150)

    print("SPOT_DONE scene=%s saved=%d first=%04d dir=%s" % (
        SCENE_ID, N_SHOTS, start, OUT_DIR))
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
