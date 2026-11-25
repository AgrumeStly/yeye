"""K230 ??????????????????????????"""
import time

RATE = 16000
CHUNK = 4800  # 已有KWS模型每次输入300ms单声道PCM。
CHUNK_MS = 300
WAVDIR = '/sdcard/examples/utils/'
REPLIES = ('', 'wozai.wav', 'go_new.wav', 'stop_new.wav', 'wow_new.wav')
READY_REPLY = 1  # 复用已有的“我在”语音，不额外分发WAV。
GO = 2
STOP = 3

class VoiceKeywords:
    """沿用现有KPU模型、MIC增益、分类及右声道功放。模型和Audio均由本脚本独占。"""

    def __init__(self, mapping, go_pcm=None):
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
        # 联合弯的“收到”在上电时转换为整块右声道PCM，识别后不读卡、不转码。
        self.go_audio = tuple(self.stereo(go_pcm[i:i + CHUNK * 2])
                              for i in range(0, len(go_pcm), CHUNK * 2)) if go_pcm else ()
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
                if self.output.write(self.stereo(pcm)) != 0:
                    raise OSError('Speaker write failed')
                frames += 1
                self.input.read(block=False)
                pcm = wav.read_frames(CHUNK)
        finally:
            wav.close()
        self.after_reply(started, frames, CHUNK_MS * 2)

    @staticmethod
    def stereo(pcm):
        """把16位单声道样本送到车载右路功放，末块补零到300ms。"""
        stereo = bytearray(CHUNK * 4)
        for sample_at in range(0, len(pcm), 2):
            stereo[sample_at * 2 + 2:sample_at * 2 + 4] = pcm[sample_at:sample_at + 2]
        return stereo

    def acknowledge_go(self):
        """识别Go后立即送入已缓存的“收到”，此时尚未发送车辆START。"""
        started = time.ticks_ms()
        for block in self.go_audio:
            if self.output.write(block) != 0:
                raise OSError('Speaker write failed')
            self.input.read(block=False)
        self.after_reply(started, len(self.go_audio), 100)

    def after_reply(self, started, frames, tail_ms):
        """丢弃扬声器回采的尾音，再恢复本地Stop识别。参数均为块数或毫秒。"""
        self.cache = self.np.zeros((1, 256, 105), dtype=self.np.float)
        self.last = 0
        self.go_ready = False
        remaining = max(0, frames * CHUNK_MS - time.ticks_diff(time.ticks_ms(), started))
        self.ignore_until = time.ticks_add(time.ticks_ms(), remaining + tail_ms)

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
        print('[VOICE CLEANUP]', repr(exc))
