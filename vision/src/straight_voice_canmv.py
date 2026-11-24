"""K230脱机直道与语音入口，由生成工具和既有R2直道算法合成main.py。"""
import os
import time
from straight_route import StraightRoute
from straight_protocol import StraightSender
from vision_protocol import crc16

RATE = 16000
CHUNK = 4800  # 已有KWS模型每次输入300ms单声道PCM。
CHUNK_MS = 300
WAVDIR = '/sdcard/examples/utils/'
REPLIES = ('', 'wozai.wav', 'go_new.wav', 'stop_new.wav', 'wow_new.wav')
GO = 2
STOP = 3
RUN_WINDOW_MS = 2150  # STM32最多撤驱动前运行2000ms，留150ms调度余量。


class StraightVoiceSender(StraightSender):
    wire_version = 6

    def start(self, path_packet):
        """提交一次Go，引用刚发送的当前有效PATH。PATH和CMD使用独立序号。"""
        if not self.allow_drive or not path_packet[6] & 1:
            raise ValueError('START requires a valid current PATH')
        data = bytes((0xA5, 0x5A, self.wire_version, 2, 12, self.cmd_seq,
                      0, 0, path_packet[5], 0, 0, 0, 0, 0, 0, 0, 1, 0))
        self.cmd_seq = (self.cmd_seq + 1) & 255
        checksum = crc16(data)
        return self._send(data + bytes((checksum & 255, checksum >> 8)))


class StraightKeywords:
    """沿用现有KPU模型、MIC增益、分类及右声道功放。模型和Audio均由本脚本独占。"""

    def __init__(self, mapping):
        from machine import Pin, FPIOA
        from media.pyaudio import PyAudio, paInt16, LEFT_RIGHT
        import media.wave as wave
        import nncase_runtime as nn
        import ulab.numpy as np
        import aidemo
        import struct

        self.wave, self.nn, self.np = wave, nn, np
        self.aidemo, self.struct = aidemo, struct
        self.input = self.output = self.fp = self.kpu = self.amp = None
        self.last = 0
        self.go_ready = False  # 上电或播报后先听到背景，防重复触发或把扬声器当发令。
        self.ignore_until = None
        self.audio = PyAudio()
        try:
            for name in REPLIES[1:]:
                wav = self.open_reply(name)
                wav.close()
            nn.shrink_memory_pool()
            self.fp = aidemo.kws_fp_create()
            self.kpu = nn.kpu()
            self.kpu.load_kmodel('/sdcard/examples/kmodel/multi_kws.kmodel')
            self.cache = np.zeros((1, 256, 105), dtype=np.float)
            mapping.set_function(10, FPIOA.GPIO10)
            self.amp = Pin(10, Pin.OUT, pull=Pin.PULL_NONE, drive=7)
            self.amp.value(1)
            self.input = self.audio.open(format=paInt16, channels=1, rate=RATE,
                                         input=True, frames_per_buffer=CHUNK)
            self.output = self.audio.open(format=paInt16, channels=2, rate=RATE,
                                          output=True, frames_per_buffer=CHUNK)
            self.input.volume(40)
            self.output.volume(100, LEFT_RIGHT)
        except BaseException:
            self.close()
            raise

    def open_reply(self, name):
        wav = self.wave.open(WAVDIR + name, 'rb')
        if (wav.get_framerate(), wav.get_sampwidth(), wav.get_channels()) != (RATE, 2, 1):
            wav.close()
            raise ValueError('Invalid reply WAV: ' + name)
        return wav

    def poll(self):
        """最多读取一块，CanMV v1.8短等待10ms。返回新命中标签，0代表没有命令。"""
        pcm = self.input.read(block=False)
        if self.ignore_until is not None:
            if time.ticks_diff(time.ticks_ms(), self.ignore_until) >= 0:
                self.ignore_until = None
            return 0  # 继续取出并丢弃播报及尾音采样，保持麦克风队列新鲜。
        if pcm is None:
            return 0
        if len(pcm) != CHUNK * 2:
            raise ValueError('Unexpected KWS PCM frame length')
        samples = [self.struct.unpack_from('<h', pcm, offset)[0] for offset in range(0, len(pcm), 2)]
        mean = sum(samples) / CHUNK
        normalized = [sample - mean for sample in samples]
        features = self.aidemo.kws_preprocess(self.fp, normalized)[0]
        self.kpu.set_input_tensor(0, self.nn.from_numpy(self.np.array(features).reshape((1, 30, 40))))
        self.kpu.set_input_tensor(1, self.nn.from_numpy(self.cache))
        self.kpu.run()
        logits = self.kpu.get_output_tensor(0).to_numpy()
        self.cache = self.kpu.get_output_tensor(1).to_numpy()
        scores = self.np.max(logits, axis=1)[0]
        label = int(self.np.argmax(scores)) if float(self.np.max(scores)) > 0.5 else 0
        previous = self.last
        self.last = label
        if label == 0:
            self.go_ready = True
        if label == GO:
            ready = self.go_ready
            self.go_ready = False
            return GO if ready else 0
        return label if label != previous else 0

    def play(self, label):
        """仅在没有活跃运行窗口或刚发STOP后调用，因为WAV及扬声器可阻塞。"""
        wav = self.open_reply(REPLIES[label])
        started = time.ticks_ms()
        frames = 0
        try:
            pcm = wav.read_frames(CHUNK)
            while pcm:
                # 输出设备要求整块大小，末块补零；沿用已有单声道转右路的接法。
                stereo = bytearray(CHUNK * 4)
                for sample_at in range(0, len(pcm), 2):
                    stereo[sample_at * 2 + 2:sample_at * 2 + 4] = pcm[sample_at:sample_at + 2]
                if self.output.write(stereo) != 0:
                    raise OSError('Speaker write failed')
                frames += 1
                self.input.read(block=False)
                pcm = wav.read_frames(CHUNK)
        finally:
            wav.close()
        self.cache = self.np.zeros((1, 256, 105), dtype=self.np.float)
        self.last = 0
        self.go_ready = False
        remaining = max(0, frames * CHUNK_MS - time.ticks_diff(time.ticks_ms(), started))
        self.ignore_until = time.ticks_add(time.ticks_ms(), remaining + CHUNK_MS * 2)

    def close(self):
        """逐项释放资源，设备清理失败时仍继续关功放及销毁特征提取器。"""
        actions = []
        for stream in (self.input, self.output):
            if stream is not None:
                actions.extend((stream.stop_stream, stream.close))
        actions.append(self.audio.terminate)
        if self.amp is not None:
            actions.append(lambda: self.amp.value(0))
        if self.fp is not None:
            actions.append(lambda: self.aidemo.kws_fp_destroy(self.fp))
        for action in actions:
            cleanup(action)
        self.kpu = self.cache = None


def cleanup(action):
    try:
        action()
    except BaseException as exc:
        print('[STRAIGHT VOICE CLEANUP]', repr(exc))


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
        voice = StraightKeywords(mapping)
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
