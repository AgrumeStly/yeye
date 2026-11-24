import time, os, gc
from machine import FPIOA, PWM
from media.sensor import *
from media.display import *
from media.media import *
SCENE_ID = "d01_straight_run01"
OUT_DIR = "/data/captures/d01_straight_run01"
EXPECTED_PATH = "both"
SPEED_NOTE = "slow_push"
N_FRAMES = 300
PERIOD_MS = 200
START_WAIT_S = 5
LOCK_AE = True
SHOW =  False
W, H = 320, 240
def mkdirs():
    for path in ("/data/captures", OUT_DIR):
        try:
            os.mkdir(path)
        except OSError:
            pass
def beep(ms=120):
    buzzer.duty(50)
    time.sleep_ms(ms)
    buzzer.duty(0)
    time.sleep_ms(80)
sensor = None
buzzer = None
log = None
saved = 0
first_ticks = None
last_ticks = None
try:
    fp = FPIOA()
    fp.set_function(61, FPIOA.PWM1)
    buzzer = PWM(1, freq=4000, duty=0)
    mkdirs()
    start = 1
    for name in os.listdir(OUT_DIR):
        if name.startswith("data_") and name.endswith(".jpg"):
            idx = int(name[5:-4])
            if idx >= start:
                start = idx + 1
    sensor = Sensor(id=1, width=1280, height=960, fps=90)
    sensor.reset()
    sensor.set_framesize(width=W, height=H)
    sensor.set_pixformat(Sensor.GRAYSCALE)
    sensor.set_hmirror(True)
    sensor.set_vflip(True)
    sensor.run()
    if SHOW:
        Display.init(Display.VIRT, width=W, height=H, fps=30, to_ide=True)
    for _ in range(30):
        sensor.snapshot()
    if LOCK_AE:
        sensor.auto_exposure(False)
    log_path = OUT_DIR + "/collect_log.csv"
    fresh = True
    try:
        os.stat(log_path)
        fresh = False
    except OSError:
        pass
    log = open(log_path, "a")
    log.write("# SESSION scene=%s expected=%s speed=%s res=%dx%d gray=1 period_ms=%d lock_ae=%d start=%d wait_s=%d\n" % (
        SCENE_ID, EXPECTED_PATH, SPEED_NOTE, W, H, PERIOD_MS, 1 if LOCK_AE else 0, start, START_WAIT_S))
    if fresh:
        log.write("idx,name,ticks_ms,scene_id,expected_path,speed_note,mean,min,max,median,exposure,clean_bytes,debug_bytes\n")
    log.flush()
    print("COLLECT scene=%s start=%04d exposure=%s wait=%ds" % (
        SCENE_ID, start, sensor.exposure(), START_WAIT_S))
    for left in range(START_WAIT_S, 0, -1):
        os.exitpoint()
        img = sensor.snapshot()
        if SHOW:
            img.draw_string_advanced(4, 6, 18, "start %ds" % left, color=30)
            Display.show_image(img)
        time.sleep_ms(1000)
    beep()
    print("BEEP_START")
    next_ticks = time.ticks_ms() + PERIOD_MS
    for n in range(N_FRAMES):
        os.exitpoint()
        img = sensor.snapshot()
        ticks = time.ticks_ms()
        if first_ticks is None:
            first_ticks = ticks
        last_ticks = ticks
        idx = start + saved
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
        log.write("%d,data_%04d.jpg,%d,%s,%s,%s,%d,%d,%d,%d,%s,%d,%d\n" % (
            idx, idx, ticks, SCENE_ID, EXPECTED_PATH, SPEED_NOTE,
            st.mean(), st.min(), st.max(), st.median(), exposure,
            clean_bytes, debug_bytes))
        log.flush()
        saved += 1
        if SHOW:
            Display.show_image(img)
        if saved % 25 == 0:
            print("COLLECTED %d last=#%04d mean=%d" % (saved, idx, st.mean()))
        if saved % 50 == 0:
            gc.collect()
        delay = time.ticks_diff(next_ticks, time.ticks_ms())
        if delay > 0:
            time.sleep_ms(delay)
        next_ticks = time.ticks_ms() + PERIOD_MS
    print("COLLECT_DONE scene=%s saved=%d last=#%04d dir=%s" % (
        SCENE_ID, saved, start + saved - 1, OUT_DIR))
    if saved > 1:
        elapsed = time.ticks_diff(last_ticks, first_ticks)
        if elapsed > 0:
            print("ACTUAL interval_ms=%.1f fps=%.2f" % (
                elapsed / float(saved - 1), 1000.0 * (saved - 1) / elapsed))
    print("MEM_FREE", gc.mem_free())
    beep(500)
    print("BEEP_DONE")
except BaseException as e:
    print("ERROR:", e)
    print("STOPPED scene=%s saved=%d dir=%s" % (SCENE_ID, saved, OUT_DIR))
    if buzzer is not None:
        for _ in range(3):
            beep()
    raise
finally:
    if log is not None:
        log.close()
    if isinstance(sensor, Sensor):
        sensor.stop()
    if buzzer is not None:
        buzzer.duty(0)
        buzzer.deinit()
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)