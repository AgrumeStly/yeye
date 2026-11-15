"""Lite-K230D上电手推采图：准备→长音→限时保存原图→落盘→双长音。

作为/sdcard/main.py独立运行，无电脑、UART、运动控制或额外标记依赖。
保存未叠加320×240灰度JPEG序列和逐帧软件时间／哈希，便于现有离线回放。
蜂鸣器GPIO61/PWM1，参考立创Lite板文档；不驱动电机、风扇或外部针脚。
"""

import os
import sys
import time
import json
import hashlib
from binascii import hexlify

VERSION = "push-capture-1"
SCENE = "board_smoke"             # 当前只采锐角完整进出；不是算法识别出的角度。
PREPARE_MS = 1000              # 摄像头／存储检查后准备15秒；系统自身启动时间另计。
CAPTURE_MS = 3000              # 开始长音结束后采45秒；按时间停止，不识别终点。
INTERVAL_MS = 100               # 保存启动最小间隔100ms，目标上限10张/秒，实际以日志为准。
MAX_FRAMES = 1200               # 意外配置保护；提前撞上限算失败，不能发完成提示。
WARMUP_FRAMES = 10
JPEG_QUALITY = 95
SENSOR_ID = 2
WIDTH, HEIGHT = 320, 240
HMIRROR, VFLIP = False, False   # 沿用最终安装，不改变视场或镜像。
SD_ROOT = "/sdcard"
MIN_FREE_BYTES = 32*1024*1024   # 启动至少32MiB；只检查可用空间，绝不清理旧文件。
RESERVE_BYTES = 8*1024*1024     # 运行中每10帧检查，低于8MiB失败停止。
START_BEEP_MS = 600
DONE_BEEP_MS = 450


def _sync():
    """请求同步已关闭文件；不声称能抵抗写卡途中断电。"""
    if hasattr(os, "sync"):
        os.sync()


def _is_directory(path):
    """只检查目录；非ENOENT错误原样上报，不掩盖卡故障。"""
    try:
        return bool(os.stat(path)[0] & 0x4000)
    except OSError as exc:
        if exc.args and exc.args[0] == 2:
            return False
        raise


def _free_bytes():
    """statvfs的f_frsize×f_bavail，单位字节；板上已确认接口可用。"""
    stats = os.statvfs(SD_ROOT)
    return stats[1]*stats[4]


def _new_session():
    """仅在真实TF挂载点下新建唯一会话；不覆盖原件，不在无卡时造挂载点。"""
    if not _is_directory(SD_ROOT):
        raise RuntimeError("TF card mount missing")
    if _free_bytes() < MIN_FREE_BYTES:
        raise RuntimeError("TF free space below startup reserve")
    root = SD_ROOT+"/captures"
    try:
        os.mkdir(root)
    except OSError as exc:
        if not (exc.args and exc.args[0] == 17 and _is_directory(root)):
            raise
    for number in range(1, 10000):
        path = root+"/push_"+SCENE+"_%04d" % number
        try:
            os.mkdir(path)
            return path
        except OSError as exc:
            if not (exc.args and exc.args[0] == 17 and _is_directory(path)):
                raise
    raise RuntimeError("No unused push session number")


def _json_file(path, value):
    """同步临时JSON再改名，仅处理本会话目标EEXIST；两步替换有断电窗口。

    此固件rename不覆盖目标。仅在EEXIST时移除本次会话的旧session.json，
    其他权限／卡故障直接抛出；.tmp和部分图保留供校验器拒绝不完整会话。
    """
    temporary = path+".tmp"
    with open(temporary, "w") as stream:
        stream.write(json.dumps(value)+"\n")
        stream.flush()
    _sync()
    try:
        os.rename(temporary, path)
    except OSError as exc:
        if not (exc.args and exc.args[0] == 17) or _is_directory(path):
            raise
        os.remove(path)
        os.rename(temporary, path)
    _sync()


def _file_integrity(path):
    """复读JPEG的首尾及SHA-256，不缓存整段数据；PC另做真实解码校验。"""
    digest, size, first, tail = hashlib.sha256(), 0, None, b""
    with open(path, "rb") as stream:
        while True:
            block = stream.read(4096)
            if not block:
                break
            if first is None:
                first = block[:2]
            tail = (tail+block)[-2:]
            size += len(block)
            digest.update(block)
    if first != b"\xff\xd8" or tail != b"\xff\xd9" or size < 4:
        raise RuntimeError("JPEG marker check failed: "+path)
    return size, hexlify(digest.digest()).decode("ascii")


class Beeper:
    """仅接管已确认板载蜂鸣器；固定4kHz，不循环重启采集。

    PWM0/1/2共享频率，本程序不配置风扇或其他PWM。构造／清理保证静音；
    未识别的板型拒绝运行，不把标准板GPIO43误用于Lite。
    """

    def __init__(self):
        from machine import PWM, FPIOA
        board = os.uname()[-1]
        if board == "k230d_canmv_lushanpi_lite":
            pin = 61
        elif board == "k230_canmv_lckfb":
            pin = 43
        else:
            raise RuntimeError("Unsupported board for onboard beeper: "+board)
        self.fpioa = FPIOA()
        self.fpioa.set_function(pin, FPIOA.PWM1)
        self.pwm = PWM(1, freq=4000, duty=0)
        print("[BEEPER]", board, "GPIO", pin, "PWM1")

    def signal(self, count, duration_ms, gap_ms=200):
        """发count声；时长／间隔单位毫秒，任何中断均先撤销蜂鸣占空比。"""
        for i in range(count):
            try:
                self.pwm.duty(50)
                time.sleep_ms(duration_ms)
            finally:
                self.pwm.duty(0)
            if i+1 < count:
                time.sleep_ms(gap_ms)

    def close(self):
        """关闭占空比并释放PWM；清理错误不允许伪装为成功采集。"""
        try:
            self.pwm.duty(0)
        finally:
            self.pwm.deinit()


def _validate_config():
    """在硬件／存储前拒绝错误标签、时序和帧数，防目录穿越与过早截断。"""
    if SCENE not in ("corner_77", "full_lap", "board_smoke"):
        raise ValueError("Unknown scene")
    for value, low, high in ((PREPARE_MS, 0, 60000), (CAPTURE_MS, 100, 300000),
                             (INTERVAL_MS, 10, 1000), (MAX_FRAMES, 1, 4000),
                             (WARMUP_FRAMES, 1, 300), (JPEG_QUALITY, 1, 100)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError("Invalid capture configuration")
    if MAX_FRAMES < (CAPTURE_MS+INTERVAL_MS-1)//INTERVAL_MS:
        raise ValueError("MAX_FRAMES would truncate timed capture")
    if (WIDTH, HEIGHT) != (320, 240) or SENSOR_ID != 2:
        raise ValueError("Keep confirmed camera profile")


def main():
    """一次上电只采一组：预检／预热→准备→开始提示→限时采图→释放／落盘→结束提示。

    采图与写卡在主循环顺序执行，不用中断写文件，不累积图像队列。
    ticks_diff处理回绕，时间是软件调用边界；目标间隔不保证真实帧率。
    完成双长音仅在文件与元数据同步、相机／媒体清理全部成功后发出。
    失败发5短音两组，保留failed／interrupted状态，禁止发成功提示。
    """
    _validate_config()
    beeper = sensor = None
    media_attempted = False
    session = manifest = None
    saved, last_capture, started = 0, None, None
    cleanup_errors = []
    failure = None
    print("[PUSH_START]", VERSION, SCENE)
    try:
        beeper = Beeper()
        session = _new_session()
        manifest = dict(schema=2, version=VERSION, state="initializing", scene=SCENE,
                        motion_source="hand_push_not_autonomous", saved_count=0,
                        planned_duration_ms=CAPTURE_MS, prepare_ms=PREPARE_MS,
                        interval_ms=INTERVAL_MS, max_frames=MAX_FRAMES,
                        width=WIDTH, height=HEIGHT, pixel_format="grayscale",
                        sensor_id=SENSOR_ID, hmirror=HMIRROR, vflip=VFLIP,
                        jpeg_quality=JPEG_QUALITY, firmware_version=sys.version,
                        exposure_policy="firmware_auto_not_locked",
                        clock_note="software_snapshot_call_boundaries_not_exposure_time",
                        elapsed_origin="after_start_beep", free_bytes_at_start=_free_bytes())
        _json_file(session+"/session.json", manifest)
        with open(session+"/frames.jsonl", "w"):
            pass
        print("[PUSH_SESSION]", session)
        import image as image_module
        from media.sensor import Sensor, CAM_CHN_ID_0
        from media.media import MediaManager
        sensor = Sensor(id=SENSOR_ID)
        sensor.reset()
        sensor.set_framesize(width=WIDTH, height=HEIGHT, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(HMIRROR)
        sensor.set_vflip(VFLIP)
        media_attempted = True
        MediaManager.init()
        sensor.run()
        for _ in range(WARMUP_FRAMES):
            os.exitpoint()
            frame = sensor.snapshot(chn=CAM_CHN_ID_0)
        # 准备期持续丢弃新帧使自动曝光跟随，且先验证JPEG写卡，避免无卡空响开始音。
        preflight = session+"/preflight.jpg"
        frame.save(preflight, quality=JPEG_QUALITY)
        _sync()
        _file_integrity(preflight)
        os.remove(preflight)
        _sync()
        manifest["state"] = "preparing"
        _json_file(session+"/session.json", manifest)
        print("[PUSH_PREPARE]", PREPARE_MS)
        prepare_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), prepare_start) < PREPARE_MS:
            os.exitpoint()
            frame = sensor.snapshot(chn=CAM_CHN_ID_0)
        beeper.signal(1, START_BEEP_MS)
        started = time.ticks_ms()
        manifest["state"] = "capturing"
        manifest["start_ticks_ms"] = started
        _json_file(session+"/session.json", manifest)
        print("[PUSH_RECORDING]", CAPTURE_MS)
        checkpoint = started
        while time.ticks_diff(time.ticks_ms(), started) < CAPTURE_MS:
            os.exitpoint()
            snapshot_start = time.ticks_ms()
            frame = sensor.snapshot(chn=CAM_CHN_ID_0)
            snapshot_end = time.ticks_ms()
            elapsed = time.ticks_diff(snapshot_start, started)
            if elapsed >= CAPTURE_MS:
                break
            if (frame.width(), frame.height(), frame.format()) != (WIDTH, HEIGHT, image_module.GRAYSCALE):
                raise RuntimeError("Actual image is not grayscale 320x240")
            if last_capture is not None and time.ticks_diff(snapshot_start, last_capture) < INTERVAL_MS:
                continue
            if saved >= MAX_FRAMES:
                raise RuntimeError("Frame guard reached before duration")
            filename = "data_%04d.jpg" % (saved+1)
            temporary = session+"/pending_"+filename
            frame.save(temporary, quality=JPEG_QUALITY)
            size, digest = _file_integrity(temporary)
            os.rename(temporary, session+"/"+filename)
            row = dict(frame_id=saved+1, file=filename, scene=SCENE,
                       width=WIDTH, height=HEIGHT, pixel_format="grayscale",
                       snapshot_start_ticks_ms=snapshot_start, snapshot_end_ticks_ms=snapshot_end,
                       elapsed_ms=elapsed, snapshot_call_ms=time.ticks_diff(snapshot_end, snapshot_start),
                       bytes=size, sha256=digest)
            with open(session+"/frames.jsonl", "a") as stream:
                stream.write(json.dumps(row)+"\n")
                stream.flush()
            _sync()
            saved += 1
            manifest["saved_count"] = saved
            last_capture = snapshot_start
            # 不每张重写session.json；每秒检查点加逐帧JSONL，兼顾写卡开销和故障证据。
            if time.ticks_diff(time.ticks_ms(), checkpoint) >= 1000:
                _json_file(session+"/session.json", manifest)
                checkpoint = time.ticks_ms()
                print("[PUSH_SAVED]", saved, "elapsed_ms", elapsed)
            if saved % 10 == 0 and _free_bytes() < RESERVE_BYTES:
                raise RuntimeError("TF free space below running reserve")
        if not saved:
            raise RuntimeError("No frames saved")
        manifest["capture_elapsed_ms"] = time.ticks_diff(time.ticks_ms(), started)
        manifest["stop_reason"] = "duration_reached"
        manifest["state"] = "finalizing"
    except BaseException as exc:
        failure = exc
        print("[PUSH_FAILED]", str(exc))
    finally:
        # 先停采集、释放媒体，再同步最终元数据；此时仍不发完成提示。
        if sensor is not None:
            try:
                sensor.stop()
            except BaseException as exc:
                cleanup_errors.append("sensor: "+str(exc))
        if media_attempted:
            try:
                time.sleep_ms(100)
                MediaManager.deinit()
            except BaseException as exc:
                cleanup_errors.append("media: "+str(exc))
        if manifest is not None:
            manifest["saved_count"] = saved
            manifest["cleanup_errors"] = cleanup_errors
            manifest["state"] = ("interrupted" if isinstance(failure, KeyboardInterrupt) else "failed") if failure else ("failed" if cleanup_errors else "complete")
            if failure:
                manifest["error"] = str(failure)
            try:
                _json_file(session+"/session.json", manifest)
            except BaseException as exc:
                failure = failure or exc
                print("[PUSH_MANIFEST_FAILED]", str(exc))
        try:
            if failure or cleanup_errors:
                if beeper is not None:
                    for _ in range(2):
                        beeper.signal(5, 100, 100)
                        time.sleep_ms(500)
            elif manifest is not None:
                print("[PUSH_FILES_CLOSED]", session, saved)
                beeper.signal(2, DONE_BEEP_MS)
                print("[PUSH_DONE]", session, "saved", saved)
        finally:
            if beeper is not None:
                beeper.close()
    if failure:
        raise failure
    if cleanup_errors:
        raise RuntimeError("Capture cleanup failed")
    return session


if __name__ == "__main__":
    main()
