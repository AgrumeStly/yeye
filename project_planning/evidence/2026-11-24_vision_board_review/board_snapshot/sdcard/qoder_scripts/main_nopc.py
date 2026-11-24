# main_nopc.py — 无电脑现场采集：上电自启、拍完自停、蜂鸣器提示
# 用法：电脑上把本文件写为 /sdcard/main.py，断电，接 5V 电源（Type-C）。
# 时间线：上电启动几秒 -> 预热 -> 等 START_WAIT_S 秒（给你摆车）-> 短鸣=开拍 ->
#         N_FRAMES 张拍完 -> 长鸣=结束 -> 自停 idle（不会重复拍，下次上电才再跑）。
# 出错时鸣 3 短声。回电脑后它仍会自启：先停脚本再删 /sdcard/main.py。
# 输出 /data/captures/dataset/：data_ 干净图 + collect_log.csv（SAVE_DBG=True 才多一份 dbg_ 调试图）
import time, os
from machine import FPIOA, PWM
from media.sensor import *
from media.media import *

START_WAIT_S = 3     # 上电后给你几秒摆车/对准
PERIOD_MS = 200       # 每张间隔；300 张 = 60 秒
N_FRAMES = 300
OUT_DIR = "/data/captures/dataset"
RES = "qv"            # "qv" = 320x240 算法分辨率；"hd" 只当母版
COLOR = False         # 灰度 = 算法输入
LOCK_AE = False
SAVE_DBG = False      # False = 只存干净图（现场写卡减半，节拍稳在 200ms）
REF_MARKS = ((155, "20cm"), (100, "40cm"), (78, "60cm"))

W, H = (1280, 960) if RES == "hd" else (320, 240)
FS = 24 if W >= 1280 else 14
FMT = Sensor.RGB565 if COLOR else Sensor.GRAYSCALE
TAGC = "rgb" if COLOR else "gray"
LBL = "Lmean" if COLOR else "mean"

fp = FPIOA()
fp.set_function(61, FPIOA.PWM1)
buzzer = PWM(1, freq=4000, duty=0)


def beep(ms=120):
    buzzer.duty(50)
    time.sleep_ms(ms)
    buzzer.duty(0)
    time.sleep_ms(80)


def annotate(img, idx, ticks, st, expo):
    for row, lab in REF_MARKS:
        y = int(row * H / 240)
        img.draw_line(0, y, W - 1, y, color=(255, 0, 0) if COLOR else 90, thickness=1)
        img.draw_string_advanced(4, y - FS - 2, FS, lab,
                                 color=(255, 0, 0) if COLOR else 60)
    img.draw_line(W // 2, 0, W // 2, H - 1,
                  color=(0, 200, 0) if COLOR else 150, thickness=1)
    bar = int(FS * 3.4)
    img.draw_rectangle(0, H - bar, W, bar, color=(255, 255, 255), fill=True)
    img.draw_string_advanced(4, H - bar + 2, FS,
                             "#%04d main %s t=%d" % (idx, TAGC, ticks),
                             color=(0, 0, 0))
    img.draw_string_advanced(4, H - bar + FS + 4, FS,
                             "%s=%d min=%d max=%d expo=%s" % (
                                 LBL, st.mean(), st.min(), st.max(), expo),
                             color=(0, 0, 0))
    return img


sensor = None
log = None
saved = 0
try:
    try:
        os.mkdir(OUT_DIR)
    except OSError:
        pass

    start = 1
    for nm in os.listdir(OUT_DIR):
        if nm.startswith("data_") and nm.endswith(".jpg"):
            n = int(nm[5:-4])
            if n >= start:
                start = n + 1

    sensor = Sensor(width=1280, height=960, fps=90)
    sensor.reset()
    sensor.set_framesize(width=W, height=H)
    sensor.set_pixformat(FMT)
    sensor.run()

    for _ in range(25):
        img = sensor.snapshot()
    if LOCK_AE:
        sensor.auto_exposure(False)
    expo = sensor.exposure()

    log_path = OUT_DIR + "/collect_log.csv"
    fresh = True
    try:
        os.stat(log_path)
        fresh = False
    except OSError:
        pass
    log = open(log_path, "a")
    log.write("# SESSION mode=main res=%s %dx%d color=%s period_ms=%d wait_s=%d lock_ae=%s start=%d\n" % (
        RES, W, H, TAGC, PERIOD_MS, START_WAIT_S, LOCK_AE, start))
    log.write("# ref_marks=%s\n" % (REF_MARKS,))
    if fresh:
        log.write("idx,name,ticks_ms,mode,mean,min,max,median,exposure,clean_bytes,debug_bytes\n")
    log.flush()
    print("MAIN_NOPC %dx%d frames=%d period=%dms wait=%ds start=%d dbg=%s exposure=%s" % (
        W, H, N_FRAMES, PERIOD_MS, START_WAIT_S, start, SAVE_DBG, expo))

    left = START_WAIT_S
    while left > 0:
        os.exitpoint()
        time.sleep(1)
        left -= 1

    beep()                      # 短鸣 = 开拍
    print("BEEP_START")
    t_next = time.ticks_ms() + PERIOD_MS
    for i in range(N_FRAMES):
        os.exitpoint()
        img = sensor.snapshot()
        st = img.get_statistics()
        ticks = time.ticks_ms()
        idx = start + saved
        clean = "%s/data_%04d.jpg" % (OUT_DIR, idx)
        img.save(clean, quality=90)
        cb = os.stat(clean)[6]
        ex = sensor.exposure()
        db = 0
        if SAVE_DBG:
            annotate(img, idx, ticks, st, ex)
            dbg = "%s/dbg_%04d.jpg" % (OUT_DIR, idx)
            img.save(dbg, quality=85)
            db = os.stat(dbg)[6]
        log.write("%d,data_%04d.jpg,%d,main,%d,%d,%d,%d,%s,%d,%d\n" % (
            idx, idx, ticks, st.mean(), st.min(), st.max(), st.median(), ex, cb, db))
        log.flush()
        saved += 1
        if saved % 50 == 0:
            print("COLLECTED %d last=#%04d %s=%d" % (saved, idx, LBL, st.mean()))
        d = time.ticks_diff(t_next, time.ticks_ms())
        if d > 0:
            time.sleep_ms(d)
        t_next = time.ticks_ms() + PERIOD_MS

    print("MAIN_DONE saved=%d last=#%04d dir=%s" % (saved, start + saved - 1, OUT_DIR))
    beep(500)                   # 长鸣 = 结束
except BaseException as e:
    print("ERROR:", e)
    print("STOPPED saved=%d dir=%s" % (saved, OUT_DIR))
    for _ in range(3):
        beep()                  # 3 短声 = 出错
    raise
finally:
    if log is not None:
        log.close()
    if isinstance(sensor, Sensor):
        sensor.stop()
    buzzer.duty(0)
    buzzer.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
