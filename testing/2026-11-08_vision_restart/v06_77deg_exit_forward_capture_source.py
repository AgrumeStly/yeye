"""K230D/CanMV 单文件采图入口；在 CanMV 中运行，不用电脑 Python 执行。

用途：为静态视场、距离参照及V-06弯道检查提供预览和无软件叠加的灰度原图／日志。
只使用摄像头、IDE虚拟预览和TF卡，不导入UART、GPIO或电机模块。
下方是现场配置区。姿态标签与参照距离按主控实际摆位填写，安装及图像配置保持固定。
"""

import os
import sys
import time
import json
import hashlib
from binascii import hexlify

VERSION = "capture-canmv-2"
SENSOR_ID = 2                    # 立创默认CSI2；须与实际排线插座一致，不自动试探其他接口。
SD_ROOT = "/sdcard"             # 只使用已挂载TF卡，不格式化、不回退写入板内其他目录。
POSE = "center"                # V-06：主控反馈沿出口前移约30cm后摆好，双边预览可见；实际位移未独立测量。
PREVIEW_ONLY = False            # 当前出弯位置正式保存3张，与出口朝向组对照；不代表自动运动或连续跟踪。
FRAME_COUNT = 3                 # 每次静态采样3张；不会自行切换姿态或持续录制整圈。
COUNTDOWN_MS = 5000             # 预热后倒计时，单位毫秒；期间保持持续取新帧。
INTERVAL_MS = 500               # 两次保存启动的最小间隔，包含写卡时间，不保证实际帧率。
WARMUP_FRAMES = 30              # 丢弃启动过渡帧；不宣称曝光已锁定或已达到特定数值。
JPEG_QUALITY = 95
WIDTH, HEIGHT = 320, 240
HMIRROR, VFLIP = False, False
MOUNT_HEIGHT_MM = None          # 没有实测就保持None，不用0伪装实测高度。
PITCH_DEG = None
REFERENCE_FRONT_CM = []         # 距离标定已交付，本阶段先收起参照线／量尺，不沿用上次20／30／40cm标签。


def _sync():
    """刷写文件后请求文件系统同步；仍须程序结束后再拔卡，无法保证断电原子性。"""
    if hasattr(os, "sync"):
        os.sync()


def _is_directory(path):
    """检查挂载点／目录存在且类型正确，不擅自创建一个假的TF卡挂载点。"""
    try:
        return bool(os.stat(path)[0] & 0x4000)
    except OSError as exc:
        if exc.args and exc.args[0] == 2:
            return False
        raise


def _mkdir(path):
    """只允许已存在的目录；存储只读／空间不足等错误原样上报，不能当作重名跳过。"""
    try:
        os.mkdir(path)
    except OSError as exc:
        if not (exc.args and exc.args[0] == 17 and _is_directory(path)):
            raise


def _new_session():
    """在TF卡captures下建立唯一会话；不追加旧会话，不覆盖已有data编号。"""
    if not _is_directory(SD_ROOT):
        raise RuntimeError("TF card mount missing: " + SD_ROOT)
    root = SD_ROOT + "/captures"
    _mkdir(root)
    for number in range(1, 10000):
        path = root + "/v03_" + POSE + "_%04d" % number
        try:
            os.mkdir(path)
            return path
        except OSError as exc:
            if not (exc.args and exc.args[0] == 17):
                raise
    raise RuntimeError("No unused capture session number")


def _json_file(path, value):
    """将value写为path处的JSON，成功无返回值；失败抛出，保留临时文件供排查。

    path仅用于本次新会话的session.json，不用于改写旧照片或既有会话。
    先写完并同步.tmp，再改名。当前CanMV文件系统在目标已存在时返回EEXIST，
    因而只对此错误移除当前目标文件再改名；其他错误原样上报，不删除目标。
    移除到改名之间存在断电窗口，不宣称原子替换；缺失／不完整会话须拒绝验收。
    """
    temporary = path + ".tmp"
    with open(temporary, "w") as stream:
        stream.write(json.dumps(value) + "\n")
        stream.flush()
    _sync()
    try:
        os.rename(temporary, path)
    except OSError as exc:
        # 板上已实测rename不覆盖目标。仅处理EEXIST且目标不是目录的情况；
        # 不把只读、空间不足、路径错误等故障误判为重名并删除已有文件。
        if not (exc.args and exc.args[0] == 17) or _is_directory(path):
            raise
        os.remove(path)
        _sync()
        os.rename(temporary, path)  # 再失败则保留.tmp并抛出，不能打印成功。
    _sync()


def _file_integrity(path):
    """复读编码后JPEG，检查首尾标志并计算SHA-256；不等于已验证解码或图像内容。"""
    digest = hashlib.sha256()
    size = 0
    first = None
    tail = b""
    with open(path, "rb") as stream:
        while True:
            block = stream.read(4096)
            if not block:
                break
            if first is None:
                first = block[:2]
            tail = (tail + block)[-2:]
            size += len(block)
            digest.update(block)
    if first != b"\xff\xd8" or tail != b"\xff\xd9" or size < 4:
        raise RuntimeError("Saved JPEG failed marker check: " + path)
    return size, hexlify(digest.digest()).decode("ascii")


def _validate_config():
    """在任何存储／摄像头操作前拒绝错误标签和时间参数，防止目录穿越或空采集。"""
    if POSE not in ("center", "offset_left", "offset_right", "heading_left", "heading_right"):
        raise ValueError("Unknown POSE")
    if (WIDTH, HEIGHT) != (320, 240):
        raise ValueError("This capture profile requires 320x240")
    for value, lower, upper in ((FRAME_COUNT, 1, 600), (COUNTDOWN_MS, 0, 60000),
                                (INTERVAL_MS, 1, 60000), (WARMUP_FRAMES, 1, 300),
                                (JPEG_QUALITY, 1, 100)):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("Invalid capture count/timing/quality")
    if SENSOR_ID not in (0, 1, 2):
        raise ValueError("Invalid CSI sensor id")


def main():
    """初始化→预热→倒计时→保存有限张→释放资源；异常保留未完成状态并再次抛出。

    Sensor/Display/Media来自板上固件，延迟导入让电脑能检查辅助逻辑。
    Media初始化后再run遵循厂家完整示例；每个阶段有显式记录和失败清理。
    ticks_diff处理板上毫秒计数回绕。时间是软件调用边界，非曝光或同步时间。
    """
    _validate_config()
    import image as image_module
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.display import Display
    from media.media import MediaManager

    sensor = None
    display_attempted = media_attempted = False
    session = None
    manifest = None
    primary_error = None
    cleanup_errors = []
    saved = 0
    print("[START]", VERSION, "pose=" + POSE)
    try:
        if not PREVIEW_ONLY:
            session = _new_session()
            manifest = dict(schema=1, version=VERSION, state="initializing", saved_count=0,
                            requested_count=FRAME_COUNT, pose_label=POSE,
                            pose_label_source="operator_setting_not_measurement",
                            width=WIDTH, height=HEIGHT, pixel_format="grayscale",
                            sensor_id=SENSOR_ID, hmirror=HMIRROR, vflip=VFLIP,
                            crop_policy="firmware_default_no_explicit_roi_or_crop",
                            mount_height_mm=MOUNT_HEIGHT_MM, pitch_deg=PITCH_DEG,
                            reference_front_cm=REFERENCE_FRONT_CM,
                            distance_origin="vehicle_front_edge", exposure_policy="firmware_auto_not_locked",
                            firmware_version=sys.version, countdown_ms=COUNTDOWN_MS,
                            interval_ms=INTERVAL_MS, jpeg_quality=JPEG_QUALITY,
                            clock_note="ticks_ms_call_boundaries_not_exposure_time")
            _json_file(session + "/session.json", manifest)
            # 唯一新目录中创建日志；每张成功保存／校验后才写一行，不混入自由文本。
            with open(session + "/frames.jsonl", "w"):
                pass
            print("[SESSION]", session)
        sensor = Sensor(id=SENSOR_ID)
        sensor.reset()
        sensor.set_framesize(width=WIDTH, height=HEIGHT, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(HMIRROR)
        sensor.set_vflip(VFLIP)
        display_attempted = True
        Display.init(Display.VIRT, width=WIDTH, height=HEIGHT, to_ide=True)
        media_attempted = True
        MediaManager.init()
        sensor.run()
        print("[READY] warming up; keep vehicle still")
        for _ in range(WARMUP_FRAMES):
            os.exitpoint()
            frame = sensor.snapshot(chn=CAM_CHN_ID_0)
            Display.show_image(frame)
        started = time.ticks_ms()
        last_capture = None
        last_countdown = None
        if manifest is not None:
            manifest["state"] = "capturing"
            _json_file(session + "/session.json", manifest)
        while True:
            os.exitpoint()
            snapshot_start = time.ticks_ms()
            frame = sensor.snapshot(chn=CAM_CHN_ID_0)
            snapshot_end = time.ticks_ms()
            # Image.format()使用image模块枚举，不能假定与Sensor配置枚举相同。
            if (frame.width(), frame.height(), frame.format()) != (WIDTH, HEIGHT, image_module.GRAYSCALE):
                raise RuntimeError("Actual camera output does not match grayscale 320x240 profile")
            Display.show_image(frame)  # 不画线、不压缩原地预览，保存与预览使用同一新帧。
            if PREVIEW_ONLY:
                continue
            elapsed = time.ticks_diff(snapshot_end, started)
            if elapsed < COUNTDOWN_MS:
                remaining = (COUNTDOWN_MS - elapsed + 999) // 1000
                if remaining != last_countdown:
                    print("[COUNTDOWN]", remaining)
                    last_countdown = remaining
                continue
            if last_capture is not None and time.ticks_diff(snapshot_end, last_capture) < INTERVAL_MS:
                continue
            filename = "data_%04d.jpg" % (saved + 1)
            temporary = session + "/pending_" + filename
            frame.save(temporary, quality=JPEG_QUALITY)
            _sync()
            size, digest = _file_integrity(temporary)
            os.rename(temporary, session + "/" + filename)
            row = dict(frame_id=saved + 1, file=filename, pose_label=POSE,
                       width=frame.width(), height=frame.height(), pixel_format="grayscale",
                       snapshot_start_ticks_ms=snapshot_start, snapshot_end_ticks_ms=snapshot_end,
                       elapsed_ms=elapsed, snapshot_call_ms=time.ticks_diff(snapshot_end, snapshot_start),
                       bytes=size, sha256=digest)
            with open(session + "/frames.jsonl", "a") as stream:
                stream.write(json.dumps(row) + "\n")
                stream.flush()
            _sync()
            saved += 1
            last_capture = snapshot_end
            manifest["saved_count"] = saved
            _json_file(session + "/session.json", manifest)
            print("[SAVED]", filename, "bytes=", size)
            if saved == FRAME_COUNT:
                manifest["state"] = "complete"
                break
    except BaseException as exc:
        primary_error = exc
        if manifest is not None:
            manifest["state"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
            manifest["error"] = str(exc)
        print("[CAPTURE_FAILED]", str(exc))
        raise
    finally:
        # 分别清理，某一步出错仍尝试其余步骤，且不覆盖最初的异常。
        for name, action in (("sensor", sensor.stop if sensor is not None else None),
                             ("display", Display.deinit if display_attempted else None),
                             ("media", MediaManager.deinit if media_attempted else None)):
            if action is not None:
                try:
                    if name == "media":
                        time.sleep_ms(100)
                    action()
                except BaseException as exc:
                    cleanup_errors.append(name + ": " + str(exc))
        if manifest is not None:
            manifest["saved_count"] = saved
            manifest["cleanup_errors"] = cleanup_errors
            try:
                _json_file(session + "/session.json", manifest)
            except BaseException as exc:
                if primary_error is None:
                    raise
                print("[MANIFEST_WRITE_FAILED]", str(exc))
        if cleanup_errors:
            print("[CLEANUP_FAILED]", cleanup_errors)
            if primary_error is None:
                raise RuntimeError("Capture cleanup failed")
    # 只有最终元数据落盘和资源释放都未报错，才给出成功提示。
    if not PREVIEW_ONLY:
        print("[DONE]", session, "saved=", saved)


if __name__ == "__main__":
    main()
