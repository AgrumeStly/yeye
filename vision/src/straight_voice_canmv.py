"""K230脱机直道与语音入口，由生成工具和既有R2直道算法合成main.py。"""
import os
import time
from straight_route import StraightRoute
from straight_protocol import StraightSender
from lap_protocol import send_voice_start

from voice_keywords import GO, STOP, READY_REPLY, VoiceKeywords, cleanup

RUN_WINDOW_MS = 2150  # STM32最多撤驱动前运行2000ms，留150ms调度余量。


class StraightVoiceSender(StraightSender):
    wire_version = 6

    def start(self, path_packet):
        """提交一次Go，引用刚发送的当前有效PATH。PATH和CMD使用独立序号。"""
        return send_voice_start(self, path_packet)


def log_event(*fields):
    """仅在零驱动等待、发STOP或窗口结束后记录，不在循迹期间写存储卡。"""
    print('[STRAIGHT VOICE]', *fields)
    try:
        with open('/data/straight_voice.log', 'a') as log:
            log.write(' '.join(str(field) for field in fields) + '\n')
    except OSError:
        pass


def drive(sensor, channel, gray, sender, voice):
    """每轮先封包相机结果，再读音频。Go仅可用于下一帧，Stop先发帧再播报。"""
    # 相机和语音设备初始化成功后播一次。play设置麦克风尾音屏蔽，
    # 循迹循环随即开始建立双边许可，屏蔽解除前poll只丢弃录音。
    voice.play(READY_REPLY)
    detector = StraightRoute()
    origin = time.ticks_ms()
    pending_go = run_until = previous = None
    max_interval = max_kws = 0
    log_event('ready', 'v6')
    while True:
        os.exitpoint()
        started = time.ticks_ms()
        frame = sensor.snapshot(chn=channel)
        if (frame.width(), frame.height(), frame.format()) != (320, 240, gray):
            raise ValueError('Expected a 320x240 grayscale frame')
        pixels = frame.bytearray()
        copied = time.ticks_ms()
        result = detector.update(pixels, time.ticks_diff(started, origin))
        del pixels, frame
        processed = time.ticks_ms()
        packet = sender.path(result, time.ticks_diff(processed, copied), time.ticks_diff(processed, started))

        if pending_go is not None:
            if packet[6] & 1 and packet[7] >= 40 and time.ticks_diff(processed, pending_go) < 200:
                sender.start(packet)
                run_until = time.ticks_add(time.ticks_ms(), RUN_WINDOW_MS)
                max_interval = max_kws = 0
                previous = started
            else:
                log_event('go_no_fresh_pair', processed, result['reason'])
            pending_go = None
            continue
        if run_until is not None:
            max_interval = max(max_interval, time.ticks_diff(started, previous))
            previous = started
            if time.ticks_diff(processed, run_until) >= 0:
                run_until = None
                log_event('go_sent_window_elapsed', processed, 'path_interval_max_ms', max_interval, 'kws_max_ms', max_kws)
                voice.play(GO)
                continue
        keyword = voice.poll()
        recognized = time.ticks_ms()
        if run_until is not None:
            max_kws = max(max_kws, time.ticks_diff(recognized, processed))
        if keyword == STOP:
            sender.stop()
            sender.stop()
            sender.stop()
            run_until = None
            log_event('stop_sent', recognized, 'path_interval_max_ms', max_interval, 'kws_max_ms', max_kws)
            voice.play(STOP)
        elif run_until is None:
            if keyword == GO:
                pending_go = recognized
            elif keyword in (1, 4):
                log_event('local_reply', keyword)
                voice.play(keyword)


def main():
    from machine import FPIOA, UART
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.media import MediaManager
    import image

    sensor = uart = sender = voice = None
    media = False
    try:
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS,
                    parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender = StraightVoiceSender(uart.write, allow_drive=True)
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=320, height=240, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False)
        sensor.set_vflip(False)
        MediaManager.init()
        media = True
        voice = VoiceKeywords(mapping)
        sensor.run()
        drive(sensor, CAM_CHN_ID_0, image.GRAYSCALE, sender, voice)
    finally:
        if sender is not None:
            def stop_link():
                sender.stop()
                time.sleep_ms(10)  # 出口先留时间让STOP发完，再释放UART。
            cleanup(stop_link)
        if voice is not None:
            cleanup(voice.close)
        if sensor is not None:
            cleanup(sensor.stop)
        if media:
            time.sleep_ms(100)
            cleanup(MediaManager.deinit)
        if uart is not None:
            cleanup(uart.deinit)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        log_event('exit', repr(exc))
        raise
