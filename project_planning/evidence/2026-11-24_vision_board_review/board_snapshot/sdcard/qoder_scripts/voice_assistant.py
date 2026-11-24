# voice_assistant.py  开机常驻语音助手（K230D）
# 行为：
#   小南小南 -> 播报“我在”，不发任何 UART 帧
#   Go       -> 发 3 帧 START(type=2,command=1)，再播报 go_new.wav
#               （注：主控当前固件只认 KEY 启动，远程 START 会被应用层拒绝；
#                本脚本只负责发帧，电机是否转由主控固件决定）
#   Stop     -> 发 3 帧 STOP(type=2,command=2)，再播报 stop_new.wav
#   Wow      -> 只播报，不发帧
# 启动方式：由 /sdcard/main.py 开机自启（用户明确启用）。
# 日志：/data/voice_test/uart_events.log（大数据不进 SD 卡）。
import os, time, struct, gc
from media.pyaudio import PyAudio, paInt16, LEFT_RIGHT
import media.wave as wave
from machine import Pin, FPIOA, UART
import nncase_runtime as nn
import ulab.numpy as np
import aidemo

# ===== 可调参数 =====
KMODEL = '/sdcard/examples/kmodel/multi_kws.kmodel'
WAVDIR = '/sdcard/examples/utils/'
DATADIR = '/data/voice_test'
TARGET_VER = 5          # 须等于主控 LAP_WIRE_VERSION（当前 RightAngle v5）
UART_TX = 11
UART_RX = 12
BAUD = 115200
SEND_UART = True
REPEAT = 3              # 连发3帧抗单帧丢失
IN_VOL = 40
OUT_VOL = 100
THRESH = 0.5
RATE = 16000
CHUNK = 4800
COOLDOWN_MS = 800

REPLY = {1: 'wozai.wav', 2: 'go_new.wav', 3: 'stop_new.wav', 4: 'wow_new.wav'}
LABEL = {0: 'background', 1: '小南小南', 2: 'Go', 3: 'Stop', 4: 'Wow'}
CMDNAME = {1: 'START', 2: 'STOP'}

try:
    os.mkdir(DATADIR)
except Exception:
    pass

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

def cmd_frame(seq, command, ver):
    b = bytearray(20)
    b[0] = 0xA5; b[1] = 0x5A
    b[2] = ver
    b[3] = 2
    b[4] = 12
    b[5] = seq & 0xFF
    b[16] = command
    c = crc16(b[:18])
    b[18] = c & 0xFF
    b[19] = (c >> 8) & 0xFF
    return bytes(b)

fpioa = FPIOA()
fpioa.set_function(10, FPIOA.GPIO10)
amp = Pin(10, Pin.OUT, pull=Pin.PULL_NONE, drive=7)
amp.value(1)
fpioa.set_function(UART_TX, FPIOA.UART2_TXD)
fpioa.set_function(UART_RX, FPIOA.UART2_RXD)
uart = UART(UART.UART2, BAUD, bits=8, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE, tx=UART_TX, rx=UART_RX)

p = PyAudio()
ins = p.open(format=paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
outs = p.open(format=paInt16, channels=2, rate=RATE, output=True, frames_per_buffer=CHUNK)
try: ins.volume(IN_VOL)
except Exception: pass
try: outs.volume(OUT_VOL, LEFT_RIGHT)
except Exception: pass

def play(path):
    try: wf = wave.open(path, 'rb')
    except Exception as e: print('wav open err:', path, repr(e)); return
    data = wf.read_frames(CHUNK)
    while data:
        n = len(data) // 2; st = bytearray(n * 4)
        for i in range(n): st[i*4+2:i*4+4] = data[i*2:i*2+2]
        outs.write(st); data = wf.read_frames(CHUNK)
    wf.close()

nn.shrink_memory_pool(); fp = aidemo.kws_fp_create()
kpu = nn.kpu(); kpu.load_kmodel(KMODEL)
cache = np.zeros((1, 256, 105), dtype=np.float)

def recognize(pcm):
    global cache
    vals = [struct.unpack('<h', pcm[i:i+2])[0] for i in range(0, len(pcm), 2)]
    mean = sum(vals) / len(vals); vals = [v - mean for v in vals]
    feats = aidemo.kws_preprocess(fp, vals)[0]
    kpu.set_input_tensor(0, nn.from_numpy(np.array(feats).reshape((1, 30, 40))))
    kpu.set_input_tensor(1, nn.from_numpy(cache)); kpu.run()
    logits = kpu.get_output_tensor(0).to_numpy(); cache = kpu.get_output_tensor(1).to_numpy()
    ml = np.max(logits, axis=1)[0]
    return int(np.argmax(ml)), float(np.max(ml))

logf = None
try: logf = open(DATADIR + '/uart_events.log', 'w')
except Exception: pass
def log(s):
    print(s)
    if logf:
        try: logf.write(s + '\n'); logf.flush()
        except Exception: pass

cmd_seq = 0
def send_cmd(command):
    global cmd_seq
    for _ in range(REPEAT):
        fr = cmd_frame(cmd_seq, command, TARGET_VER)
        cmd_seq = (cmd_seq + 1) % 256
        if SEND_UART:
            uart.write(fr)
        log('[UART] %s ver=%d seq=%d hex=%s' % (CMDNAME[command], TARGET_VER, (cmd_seq - 1) % 256, ' '.join('%02X' % b for b in fr)))

log('=== voice_assistant ready === TARGET_VER=%d' % TARGET_VER)
play(WAVDIR + 'wozai.wav')
log('LISTENING. 小南小南=我在 / Go=发START / Stop=发STOP / Wow=只回应')
last = -1; last_play = 0; hits = {1: 0, 2: 0, 3: 0, 4: 0}; nchunk = 0
try:
    while True:
        os.exitpoint(); pcm = ins.read()
        idx, score = recognize(pcm)
        nchunk += 1
        if nchunk % 20 == 0:
            log('chunk%04d top=%s %.3f' % (nchunk, LABEL[idx], score))
        res = idx if score > THRESH else -1
        now = time.ticks_ms()
        if res in REPLY and res != last and time.ticks_diff(now, last_play) > COOLDOWN_MS:
            hits[res] += 1
            log('[识别] %s score=%.3f hits=%d' % (LABEL[res], score, hits[res]))
            if res == 2:
                send_cmd(1)          # Go -> START（是否被固件接受由主控决定）
            elif res == 3:
                send_cmd(2)          # Stop -> STOP
            play(WAVDIR + REPLY[res])
            last_play = time.ticks_ms()
        last = res; gc.collect()
except KeyboardInterrupt:
    log('stopped by user')
except Exception as e:
    log('异常: %s %r' % (type(e).__name__, e))
finally:
    try:
        ins.stop_stream(); ins.close(); outs.stop_stream(); outs.close()
    except Exception: pass
    try: uart.deinit()
    except Exception: pass
    if logf:
        try: logf.close()
        except Exception: pass
    aidemo.kws_fp_destroy(fp); del kpu; amp.value(0); nn.shrink_memory_pool()
log('=== end === hits=%s' % hits)
