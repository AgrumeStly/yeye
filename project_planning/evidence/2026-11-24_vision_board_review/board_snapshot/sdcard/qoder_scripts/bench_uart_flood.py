# 台架验证：等10秒后连发 STOP 帧 8 秒（避开K230启动噪声）
import time
from machine import UART, FPIOA

UART_TX = 11
UART_RX = 12
BAUD = 115200
VER = 5

try:
    fpioa = FPIOA()
    fpioa.set_function(UART_TX, FPIOA.UART2_TXD)
    fpioa.set_function(UART_RX, FPIOA.UART2_RXD)
    uart = UART(UART.UART2, BAUD, bits=8, parity=UART.PARITY_NONE,
                stop=UART.STOPBITS_ONE, tx=UART_TX, rx=UART_RX)
except Exception as e:
    print('[FLOOD3] uart init err:', e)
    raise

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

def cmd_frame(seq):
    b = bytearray(20)
    b[0] = 0xA5; b[1] = 0x5A; b[2] = VER; b[3] = 2; b[4] = 12
    b[5] = seq & 0xFF
    b[16] = 2
    c = crc16(b[:18])
    b[18] = c & 0xFF; b[19] = (c >> 8) & 0xFF
    return bytes(b)

print('[FLOOD3] wait 10s')
time.sleep(10)
seq = 0
n = 0
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 8000:
    uart.write(cmd_frame(seq))
    seq = (seq + 1) & 0xFF
    n += 1
print('[FLOOD3] sent %d frames in %d ms' % (n, time.ticks_diff(time.ticks_ms(), t0)))
