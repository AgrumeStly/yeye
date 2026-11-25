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
JOINT_RUN_WINDOW_MS = 40150  # 正常看见第二弯出口即结束；含STM32 40秒上限及150ms调度余量。
FRAME_BYTES = 320 * 240
RECORD_LIMIT = 768
PHOTO_LIMIT = 8


class RightAngleVoiceSender(RightAngleSender):
    wire_version = 9
    flags_by_source = {'current_pair': 1, 'current_corner_predicted': 9,
                       'current_single_forecast': 5, 'short_corridor_forecast': 5,
                       'current_front_forecast': 5}

    def start(self, packet):
        """刚发出的当前双侧或当前L形可起步，当前出口弱关联仅许可续行。"""
        if packet[6] not in (1, 9) or packet[7] < 40:
            raise ValueError('Go requires current pair or L corner')
        return send_voice_start(self, packet)


class JointAngleVoiceSender(RightAngleVoiceSender):
    """联合弯配对沿用20字节帧，80／56标记旧直道双边／当前直道单边。"""
    wire_version = 12
    flags_by_source = dict(RightAngleVoiceSender.flags_by_source, current_straight_rail=5, straight_pair=1)


class RunEvidence:
    """一次发令窗口的固定容量日志。只在STOP发出或窗口结束后写入/data。"""

    def __init__(self, wire_version=9):
        self.wire_version = wire_version
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
        sent_packet = packet is not None
        seq, flags, quality = (packet[5], packet[6], packet[7]) if sent_packet else (None, None, None)
        previous = self.last
        age_at_next = None if previous is None else time.ticks_diff(sent, previous[0]) + 2
        stage = result['stage']
        row = (started, seq, flags, stage, result['reason'], result['steering'], result['bend'],
               time.ticks_diff(acquired, started), time.ticks_diff(sent, started),
               None if previous is None else time.ticks_diff(sent, previous[1]), age_at_next, kws_ms,
               quality, result['source'], previous_phone_ms)
        if self.wire_version >= 10:
            row += (result.get('road_section'),)
        if self.wire_version >= 12:
            row += (sent_packet, result.get('vision_mode'), result.get('support'), result.get('searched_candidates'),
                    result.get('arc_entry_distance'), result.get('geometry_failures'))
        self.records[self.count % RECORD_LIMIT] = row
        self.count += 1
        if not self.issue and ((sent_packet and not flags) or (age_at_next is not None and age_at_next >= 200)):
            before = () if previous is None else ((previous[0], previous[2], bytes(self.last_pixels)),)
            self.issue = before + ((started, seq if sent_packet else 256, bytes(pixels)),)
        if not sent_packet:
            return  # 保留最近真实PATH的时间、序号和画面，无包帧不能刷新源年龄。
        if (self.last_photo_at is None or stage != previous[3] or
                time.ticks_diff(started, self.last_photo_at) >= 1000):
            self.photos[self.photo_count % PHOTO_LIMIT] = (started, seq, bytes(pixels))
            self.photo_count += 1
            self.last_photo_at = started
        self.last_pixels[:] = pixels
        self.last = (started, sent, seq, stage)

    def save(self, event, at, error=None):
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
        columns = ('start_ms', 'seq', 'flags', 'stage', 'reason', 'steering', 'bend', 'acquire_ms',
                   'to_send_ms', 'send_interval_ms', 'previous_source_age_ms', 'kws_ms',
                   'confidence', 'source', 'previous_phone_ms')
        if self.wire_version >= 10:
            columns += ('road_section',)
        if self.wire_version >= 12:
            columns += ('transmitted', 'vision_mode', 'support', 'searched_candidates', 'arc_entry_distance',
                        'straight_geometry_failures')
        with open(prefix + '.jsonl', 'w') as log:
            log.write(json.dumps(dict(event=event, script_error=error, time_ms=at, go_sent_ms=self.go_at, wire_version=self.wire_version,
                dropped_records=max(0, self.count - RECORD_LIMIT),
                columns=columns)) + '\n')
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

    def finish(self, event, at, error=None):
        cleanup(lambda: self.save(event, at) if error is None else self.save(event, at, error))
        self.reset()


def drive(sensor, channel, gray, sender, voice, evidence, phone=None, joint=False):
    """一轮先采并发送PATH，再读一次短等待音频。Go发令始终绑定新鲜PATH序号。

    单L及出口弱关联按当前图像续行。联合版模型暂未匹配、且无明确压线证据时等下一帧，
    STM32仍以最后发出的源图年龄监督。明确阻断的无效帧立即发出。
    车上没有执行回执，窗口表示已发Go。窗口内不打印、不播放WAV、不写存储。
    """
    detector = RightAngleRoute(predictive=True, joint=joint)
    origin = time.ticks_ms()
    detector.clock = lambda: time.ticks_diff(time.ticks_ms(), origin)
    voice.play(READY_REPLY)
    pending_go = run_until = None
    phone_ms = 0
    print('[RIGHT ANGLE VOICE] ready v%d' % sender.wire_version)
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
        processing = time.ticks_diff(processed, copied)
        age = time.ticks_diff(processed, started)
        skip = (joint and run_until is not None and (result['reason'] == 'observation_missed' or
                (result['valid'] and (processing > 100 or age >= 150))))
        # 跳过不确证或过期帧，不更新时间戳。语音Stop和本地记录完成逻辑照常处理。
        packet = None if skip else sender.path(result, processing, age)
        sent = time.ticks_ms()
        if pending_go is not None:
            remaining = (700 if joint else 200) - time.ticks_diff(sent, pending_go)
            if packet[6] in (1, 9) and packet[7] >= 40 and remaining > 0:
                evidence.go_at = sent  # 串口异常时finally仍可保存窗口起点。
                sender.start(packet)
                run_until = time.ticks_add(sent, JOINT_RUN_WINDOW_MS if joint else RUN_WINDOW_MS)
                evidence.record(pixels, result, packet, started, sent, acquired, 0, phone_ms)
                pending_go = None
                continue
            if not joint or remaining <= 0:
                print('[RIGHT ANGLE VOICE] go_blocked', result['reason'])
                pending_go = None
            if not joint:
                continue
        keyword = voice.poll()
        recognized = time.ticks_ms()
        completed = joint and run_until is not None and packet is not None and packet[6] and result.get('joint_complete', False)
        if keyword == STOP or completed:
            pending_go = None
            for _ in range(3):
                sender.stop()
        if run_until is not None:
            if packet is not None or joint:
                evidence.record(pixels, result, packet, started, sent, acquired, time.ticks_diff(recognized, sent), phone_ms)
            if keyword == STOP or completed or time.ticks_diff(recognized, run_until) >= 0:
                event = 'stop_sent' if keyword == STOP else 'joint_complete' if completed else 'go_window_elapsed'
                evidence.finish(event, recognized)
                run_until = None
                if joint:
                    detector.reset()
                if keyword == STOP or not joint:
                    voice.play(STOP if keyword == STOP else GO)
        elif keyword == STOP:
            voice.play(STOP)
        elif keyword == GO and pending_go is None:
            if joint:
                # 先说“收到”，然后重新采一张图再发START。播报期间车辆尚未启动。
                voice.acknowledge_go()
            pending_go = time.ticks_ms() if joint else recognized
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


def main(joint=False, go_pcm=None):
    """初始化既有GC2093、UART2和语音资源。上电等待本地Go，退出先撤驱动。"""
    from machine import FPIOA, UART
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.media import MediaManager
    import image

    sensor = uart = sender = voice = evidence = phone = error = None
    media = False
    try:
        if not joint:
            phone = open_phone_preview()
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS,
                    parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender_type = JointAngleVoiceSender if joint else RightAngleVoiceSender
        sender = sender_type(uart.write, allow_drive=True)
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=320, height=240, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False)
        sensor.set_vflip(False)
        MediaManager.init()
        media = True
        voice = VoiceKeywords(mapping, go_pcm)
        evidence = RunEvidence(sender.wire_version)
        sensor.run()
        drive(sensor, CAM_CHN_ID_0, image.GRAYSCALE, sender, voice, evidence, phone, joint)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        if sender is not None:
            def stop_link():
                sender.stop()
                time.sleep_ms(10)  # 给最后一个20字节帧留出完成串口发送的时间。
            cleanup(stop_link)
        if sensor is not None:
            cleanup(sensor.stop)
        if evidence is not None and evidence.go_at is not None:
            evidence.finish('script_exit', time.ticks_ms(), error)
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
