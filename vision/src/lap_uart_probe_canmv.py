"""独立无动力UART2探针：仅无效路径＋清理STOP，永不发送START／有效路径。

先主控确认电机动力物理断开；工作副本ENABLED=True才运行，默认仅IDLE。
无需相机或其它项目模块，保持main.py／采集许可。用于先排除三线／引脚／
115200／CRC／v2接收错误，不把PC发送或Keil计数当真实整车验收。
"""
import time
try:
    import ustruct as struct
except ImportError:
    import struct

ENABLED=False


def packet(sequence,steering=0,stop=False):
    """v2探针保持flags=0、confidence=0；error仅展示符号，不能启动电机。"""
    data=bytes((0xa5,0x5a,2,2 if stop else 1,12,sequence))
    data+=struct.pack('<BBhHHHBB',0,0,steering,0,0,0,2 if stop else 0,0)
    crc=0xffff
    for byte in data:
        crc^=byte<<8
        for _ in range(8): crc=((crc<<1)^0x1021)&0xffff if crc&0x8000 else (crc<<1)&0xffff
    return data+struct.pack('<H',crc)


def send(uart,data):
    """短写只补余下字节，0/None失败即退出，依赖STM32独立断流停车。"""
    offset=0
    while offset<len(data):
        count=uart.write(data[offset:])
        if not isinstance(count,int) or count<=0 or count>len(data)-offset:
            raise OSError('UART write incomplete')
        offset+=count


def main():
    if not ENABLED:
        print('[UART PROBE IDLE] explicit ENABLED=True; motor power must remain disconnected')
        return
    from machine import UART,FPIOA
    import os
    fpioa=FPIOA(); fpioa.set_function(11,FPIOA.UART2_TXD); fpioa.set_function(12,FPIOA.UART2_RXD)
    uart=UART(UART.UART2,baudrate=115200,bits=UART.EIGHTBITS,parity=UART.PARITY_NONE,stop=UART.STOPBITS_ONE)
    sequence=0
    try:
        for steering in (0,600,-600):
            print('[INVALID_PATH_ONLY]',steering,'3 seconds; flags=0; no START')
            for _ in range(60):
                os.exitpoint(); send(uart,packet(sequence,steering)); sequence=(sequence+1)&255
                time.sleep_ms(50)
    finally:
        try:
            send(uart,packet(0,stop=True))
            # UART.write返回表示驱动接受字节，不能据此认定最后CRC已离开发送器。
            # 115200/8N1的20字节约1.74ms；留10ms排空余量再释放UART，避免
            # 紧接deinit截断末尾STOP。真实接收仍以STM32计数／状态为证据。
            time.sleep_ms(10)
        finally: uart.deinit()
    print('[UART PROBE DONE] check real STM32 parser/steering/flags/PWM; no movement acceptance')


if __name__=='__main__': main()
