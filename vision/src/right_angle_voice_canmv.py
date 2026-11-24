"""K230 语音首弯、分置信度续行和只读手机图传入口。"""
import json
import os
import time
from lap_protocol import send_voice_start
from right_angle_protocol import RightAngleSender
from right_angle_route import RightAngleRoute
from right_angle_phone import open_phone_preview
from voice_keywords import GO, STOP, READY_REPLY, VoiceKeywords, cleanup

# STM32最多运行12000ms，从发送Go起再给150ms留出串口及本板调度余量。
RUN_WINDOW_MS = 12150
FRAME_BYTES = 320 * 240
RECORD_LIMIT = 768
PHOTO_LIMIT = 8


class RightAngleVoiceSender(RightAngleSender):
    wire_version = 8
    flags_by_source = {'current_pair': 1, 'current_corner_predicted': 9,
                       'current_single_forecast': 5, 'short_corridor_forecast': 5}

    def start(self, packet):
        """刚发出的当前双侧或当前L形可起步，当前出口弱关联仅许可续行。"""
        if packet[6] not in (1, 9) or packet[7] < 40:
            raise ValueError('Go requires current pair or L corner')
        return send_voice_start(self, packet)


class RunEvidence:
    """一次发令窗口的固定容量日志。只在STOP发出或窗口结束后写入/data。"""

    def __init__(self):
        self.last_pixels = bytearray(FRAME_BYTES)
        self.reset()

    def reset(self):
        self.records = [None] * RECORD_LIMIT
        self.photos = [None] * PHOTO_LIMIT
        self.issue = ()
        self.count = self.photo_count = 0
        self.last = self.last_photo_at = self.go_at = None

    def record(self, pixels, result, packet, started, sent, acquired, kws_ms, previous_phone_ms):
        """串口发送后记一帧。时间均为K230毫秒，照片保留相机原灰度。

        age_at_next估算上一帧在本次发送时的年龄，包含2ms名义串口时间；
        首次无效或本地年龄跨200ms时单独保留相邻图，供配对STM32停车环。
        """
        seq, flags = packet[5], packet[6]
        previous = self.last
        age_at_next = None if previous is None else time.ticks_diff(sent, previous[0]) + 2
        stage = result['stage']
        row = (started, seq, flags, stage, result['reason'], result['steering'], result['bend'],
               time.ticks_diff(acquired, started), time.ticks_diff(sent, started),
               None if previous is None else time.ticks_diff(sent, previous[1]), age_at_next, kws_ms,
               packet[7], result['source'], previous_phone_ms)
        self.records[self.count % RECORD_LIMIT] = row
        self.count += 1
        if not self.issue and (not flags or (age_at_next is not None and age_at_next >= 200)):
            before = () if previous is None else ((previous[0], previous[2], bytes(self.last_pixels)),)
            self.issue = before + ((started, seq, bytes(pixels)),)
        if (self.last_photo_at is None or stage != previous[3] or
                time.ticks_diff(started, self.last_photo_at) >= 1000):
            self.photos[self.photo_count % PHOTO_LIMIT] = (started, seq, bytes(pixels))
            self.photo_count += 1
            self.last_photo_at = started
        self.last_pixels[:] = pixels
        self.last = (started, sent, seq, stage)

    def save(self, event, at):
        """每次发令使用独立文件名。写入错误报告到终端，且不会触发新的运动。"""
        if self.go_at is None:
            return
        folder = '/data/right_angle_logs'
        try:
            os.stat(folder)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
            os.mkdir(folder)
        for index in range(1, 1001):
            prefix = folder + '/voice_%04d' % index
            try:
                os.stat(prefix + '.jsonl')
            except OSError as exc:
                if not exc.args or exc.args[0] != 2:
                    raise
                break
        else:
            raise RuntimeError('right-angle voice log slots exhausted')
        with open(prefix + '.jsonl', 'w') as log:
            log.write(json.dumps(dict(event=event, time_ms=at, go_sent_ms=self.go_at, wire_version=8,
                dropped_records=max(0, self.count - RECORD_LIMIT),
                columns=('start_ms', 'seq', 'flags', 'stage', 'reason', 'steering', 'bend', 'acquire_ms',
                         'to_send_ms', 'send_interval_ms', 'previous_source_age_ms', 'kws_ms',
                         'confidence', 'source', 'previous_phone_ms'))) + '\n')
            for count in range(max(0, self.count - RECORD_LIMIT), self.count):
                log.write(json.dumps(self.records[count % RECORD_LIMIT]) + '\n')
        for group, photos in (('route', self.photos), ('issue', self.issue)):
            for photo in photos:
                if photo is not None:
                    at_ms, seq, raw = photo
                    with open('%s_%s_%d_%03d.pgm' % (prefix, group, at_ms, seq), 'wb') as pgm:
                        pgm.write(b'P5\n320 240\n255\n')
                        pgm.write(raw)
        print('[RIGHT ANGLE VOICE LOG]', prefix, event, self.count)

    def finish(self, event, at):
        cleanup(lambda: self.save(event, at))
        self.reset()


def drive(sensor, channel, gray, sender, voice, evidence, phone=None):
    """一轮先采并发送PATH，再读一次短等待音频。Go只用于下一帧，不排队。

    单L及出口弱关联按当前图像续行。失效帧立即交给STM32，不沿用旧转向量。
    车上没有执行回执，窗口表示已发Go。窗口内不打印、不播放WAV、不写存储。
    """
    detector = RightAngleRoute(predictive=True)
    origin = time.ticks_ms()
    voice.play(READY_REPLY)
    pending_go = run_until = None
    phone_ms = 0
    print('[RIGHT ANGLE VOICE] ready v8')
    while True:
        os.exitpoint()
        started = time.ticks_ms()
        frame = sensor.snapshot(chn=channel)
        acquired = time.ticks_ms()
        if (frame.width(), frame.height(), frame.format()) != (320, 240, gray):
            raise ValueError('Expected a 320x240 grayscale frame')
        pixels = frame.bytearray()
        copied = time.ticks_ms()
        result = detector.update(pixels, time.ticks_diff(started, origin))
        processed = time.ticks_ms()
        packet = sender.path(result, time.ticks_diff(processed, copied), time.ticks_diff(processed, started))
        sent = time.ticks_ms()
        if pending_go is not None:
            if packet[6] in (1, 9) and packet[7] >= 40 and time.ticks_diff(sent, pending_go) < 200:
                evidence.go_at = sent  # 串口异常时finally仍可保存窗口起点。
                sender.start(packet)
                run_until = time.ticks_add(sent, RUN_WINDOW_MS)
                evidence.record(pixels, result, packet, started, sent, acquired, 0, phone_ms)
            else:
                print('[RIGHT ANGLE VOICE] go_blocked', result['reason'])
            pending_go = None
            continue
        keyword = voice.poll()
        recognized = time.ticks_ms()
        if keyword == STOP:
            for _ in range(3):
                sender.stop()
        if run_until is not None:
            evidence.record(pixels, result, packet, started, sent, acquired, time.ticks_diff(recognized, sent), phone_ms)
            if keyword == STOP or time.ticks_diff(recognized, run_until) >= 0:
                evidence.finish('stop_sent' if keyword == STOP else 'go_window_elapsed', recognized)
                run_until = None
                voice.play(STOP if keyword == STOP else GO)
        elif keyword == STOP:
            voice.play(STOP)
        elif keyword == GO:
            pending_go = recognized
        elif keyword in (1, 4):
            voice.play(keyword)
        if phone is not None:
            # 待机没有动力窗口，继续更新手机画面，避免场景复杂时65ms门一直挡住JPEG。
            # Go已识别时先等下一张控制图；运行期间仅在有足够路径时序余量时编码。
            # 原始取证已复制，图传异常只关闭预览，不能中断首弯控制循环。
            phone_at = time.ticks_ms()
            encode_allowed = pending_go is None and (
                run_until is None or time.ticks_diff(phone_at, started) <= 65)
            try:
                phone.step(frame, result, packet, encode_allowed)
            except Exception:
                cleanup(phone.close)
                phone = None
            phone_ms = time.ticks_diff(time.ticks_ms(), phone_at)
        else:
            phone_ms = 0


def main():
    """初始化既有GC2093、UART2和语音资源。上电等待本地Go，退出先撤驱动。"""
    from machine import FPIOA, UART
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.media import MediaManager
    import image

    sensor = uart = sender = voice = evidence = phone = None
    media = False
    try:
        phone = open_phone_preview()
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS,
                    parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender = RightAngleVoiceSender(uart.write, allow_drive=True)
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=320, height=240, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False)
        sensor.set_vflip(False)
        MediaManager.init()
        media = True
        voice = VoiceKeywords(mapping)
        evidence = RunEvidence()
        sensor.run()
        drive(sensor, CAM_CHN_ID_0, image.GRAYSCALE, sender, voice, evidence, phone)
    finally:
        if sender is not None:
            def stop_link():
                sender.stop()
                time.sleep_ms(10)  # 给最后一个20字节帧留出完成串口发送的时间。
            cleanup(stop_link)
        if sensor is not None:
            cleanup(sensor.stop)
        if evidence is not None and evidence.go_at is not None:
            evidence.finish('script_exit', time.ticks_ms())
        if voice is not None:
            cleanup(voice.close)
        if phone is not None:
            cleanup(phone.close)
        if media:
            time.sleep_ms(100)
            cleanup(MediaManager.deinit)
        if uart is not None:
            cleanup(uart.deinit)


if __name__ == '__main__':
    main()
