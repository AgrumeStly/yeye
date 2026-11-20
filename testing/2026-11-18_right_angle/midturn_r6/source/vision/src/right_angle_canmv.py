"""首弯现场手动入口，默认无动力预览；生成工具另产明确许可的车载副本。

沿用Sensor2／320x240灰度／GH UART2 T11 R12及115200。相机只提供
当前首弯路径许可，任何时候均不发送START。STM32独立限时与KEY负责动作。
启动前先停止旧main脚本，避免两个程序同时占相机或UART；不改main.py。
"""
import gc
import json
import os
import time
from right_angle_route import RightAngleRoute
from right_angle_protocol import RightAngleSender

ALLOW_DRIVE = False
SHOW_PREVIEW = True
# 无动力预览默认10分钟；生成的正式试跑副本将此值设为0，持续采图到人工停止。
# 0只取消视觉待机期限；STM32的KEY启动、单次12秒及200ms新鲜度监督独立保留。
DURATION_MS = 600000


def _open_log():
    """只在SD新建递增日志，不覆盖原件；SD异常抛出并退出。"""
    folder = '/sdcard/right_angle_logs'
    try:
        os.stat(folder)
    except OSError as exc:
        if not exc.args or exc.args[0] != 2:
            raise
        os.mkdir(folder)
    for index in range(1, 1001):
        name = folder + '/run_%04d.jsonl' % index
        try:
            os.stat(name)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
            return name, open(name, 'w')
    raise RuntimeError('straight log slots exhausted')


def main():
    """主循环使用有界局部跟踪；逐帧日志保留原始误差与图像处理年龄。

    实际snapshot调用边界不等于曝光时间；板上时序和地面表现仍需实测。
    许可副本不传IDE图像，避免图像传输影响控制。失效立即发无效路径，
    异常／退出尽力发STOP；若发送器也失败，接收端200ms保护仍生效。
    """
    from machine import UART, FPIOA
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.display import Display
    from media.media import MediaManager
    import image
    sensor = uart = sender = log = None
    display = media = False
    try:
        name, log = _open_log()
        print('[RIGHT ANGLE LOG]', name, 'ALLOW_DRIVE', ALLOW_DRIVE, 'NO AUTO START')
        log.write(json.dumps(dict(event='begin', revision='RIGHT-ANGLE-V5-RACING-6', allow_drive=ALLOW_DRIVE,
                                  duration_ms=DURATION_MS)) + '\n')
        log.flush()
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender = RightAngleSender(uart.write, ALLOW_DRIVE)
        sender.stop()
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=320, height=240, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False)
        sensor.set_vflip(False)
        display = True
        Display.init(Display.VIRT, width=320, height=240, to_ide=SHOW_PREVIEW)
        media = True
        MediaManager.init()
        sensor.run()
        detector = RightAngleRoute()
        detector.clock = time.ticks_ms
        origin = time.ticks_ms()
        index = 0
        previous = None
        last_valid_frame = None
        loss_count = 0
        while DURATION_MS == 0 or time.ticks_diff(time.ticks_ms(), origin) < DURATION_MS:
            os.exitpoint()
            started = time.ticks_ms()
            frame = sensor.snapshot(chn=CAM_CHN_ID_0)
            acquired = time.ticks_ms()
            if (frame.width(), frame.height(), frame.format()) != (320, 240, image.GRAYSCALE):
                raise ValueError('actual grayscale frame mismatch')
            pixels = frame.bytearray()
            copied = time.ticks_ms()
            result = detector.update(pixels, time.ticks_diff(started, origin))
            processed = time.ticks_ms()
            packet = sender.path(result, time.ticks_diff(processed, copied), time.ticks_diff(processed, started))
            sent = time.ticks_ms()
            index += 1
            # 仅缓存最近有效原图，失效包已经发出后再保存前后PGM，不能延迟停车。
            # 最多100次切换留证（约15MB），避免试跑前摆车就耗尽3组名额。
            # 文件名来自当前新编号日志，不覆盖旧图，不改像素。
            # 正常有效循环仅增加一个76800字节副本，无SD图像写入。
            if packet[6] & 1:
                last_valid_frame = (bytes(pixels), index, packet[5])
            elif last_valid_frame is not None and loss_count < 100:
                loss_count += 1
                prefix = name[:-6] + '_loss_%02d' % loss_count
                for suffix, raw in (('_before.pgm', last_valid_frame[0]), ('_after.pgm', pixels)):
                    with open(prefix + suffix, 'wb') as snapshot:
                        snapshot.write(b'P5\n320 240\n255\n')
                        snapshot.write(raw)
                log.write(json.dumps(dict(event='path_lost', prefix=prefix,
                    before_index=last_valid_frame[1], before_sequence=last_valid_frame[2],
                    after_index=index, after_sequence=packet[5], reason=result['reason'])) + '\n')
                log.flush()
                print('[RIGHT ANGLE LOSS]', prefix)
                last_valid_frame = None
            record = dict(result)
            # 每帧保留真实序号／来源／处理年龄等证据；完整7点路线每10帧存一次，
            # 减少JSON／SD负担。几何计算及UART封包仍逐帧执行，不降低控制更新率。
            if index % 10 != 0:
                record.pop('route', None)
            record.update(index=index, elapsed_ms=time.ticks_diff(started, origin),
                          path_sequence=packet[5], wire_valid=bool(packet[6] & 1),
                          acquire_ms=time.ticks_diff(acquired, started), processing_ms=time.ticks_diff(processed, copied),
                          to_send_ms=time.ticks_diff(sent, started),
                          interval_ms=None if previous is None else time.ticks_diff(started, previous))
            previous = started
            log.write(json.dumps(record) + '\n')
            if index % 10 == 0:
                log.flush()
                print('[RIGHT ANGLE]', result['reason'], 'stage', result['stage'], 'err', result['steering'], 'valid', bool(packet[6] & 1), 'ms', record['to_send_ms'])
            if SHOW_PREVIEW and not ALLOW_DRIVE:
                Display.show_image(frame)
            del pixels, frame
            gc.collect()
    finally:
        if sender is not None:
            try:
                sender.stop()
                time.sleep_ms(10)
            except BaseException as exc:
                print('[RIGHT ANGLE STOP ERROR]', str(exc))
        for name, cleanup in (('sensor', sensor.stop if sensor is not None else None),
                              ('display', Display.deinit if display else None),
                              ('media', MediaManager.deinit if media else None),
                              ('uart', uart.deinit if uart is not None else None),
                              ('log', log.close if log is not None else None)):
            if cleanup is not None:
                try:
                    if name == 'media':
                        time.sleep_ms(100)  # 沿用现有CanMV媒体释放间隔，避免停止相机后立刻释放缓冲。
                    cleanup()
                except BaseException as exc:
                    print('[RIGHT ANGLE CLEANUP ERROR]', name, str(exc))


if __name__ == '__main__':
    main()
