"""独立悬空动力台架输入，不是相机观测，也不是自主循迹。

只有主控实际确认当前LowSpeedLap目标、run_ms=3000、phase=2、
轮子完全悬空后，才明确开启本入口。发送有效的人工固定控制输入供验证
通信→差速策略→PI→PWM；不发START，仍由主控车载KEY触发单次3秒。
不得用于地面／比赛，不修改真实视觉脚本的ALLOW_DRIVE或main.py。
"""
import time
from lap_protocol import LapSender

ENABLED=False
SCENARIO='straight'  # straight=40/40目标；right=60/20；left=20/60，均为软件目标而非实测RPM。
DURATION_MS=600000
PERIOD_MS=50


def main():
    """默认空闲；显式启动后提供600秒固定输入窗口，结束发STOP并排空UART。

    脚本无法读取STM32配置，不能自行保证3秒运行上限；主控必须已在Watch
    核对run_ms=3000且选择3秒目标。整个窗口没有自动START，反复KEY会触发
    反复3秒，因此每次起动只按一次；仅在明确安排重复轮次时，正常停稳后
    另等至少5秒再起动，异常则停止后续。若轮子已非悬空，必须先停止此诊断。
    """
    if not ENABLED:
        print('[MOTOR BENCH IDLE] manual suspension and 3000ms MCU limit required; no UART opened')
        return
    if SCENARIO not in ('straight','right','left') or not 10000<=DURATION_MS<=600000 or PERIOD_MS!=50:
        raise ValueError('only bounded suspended motor bench scenarios are supported')
    from machine import UART,FPIOA
    import os
    fpioa=FPIOA(); fpioa.set_function(11,FPIOA.UART2_TXD); fpioa.set_function(12,FPIOA.UART2_RXD)
    uart=UART(UART.UART2,baudrate=115200,bits=UART.EIGHTBITS,parity=UART.PARITY_NONE,stop=UART.STOPBITS_ONE)
    sender=LapSender(uart.write,allow_drive=True)
    steering={'straight':0,'right':500,'left':-500}[SCENARIO]
    # 这份数据明确是人工台架刺激。source_age=0表示刚生成固定命令，绝不是
    # 某张储存图片的新鲜相机年龄；不用它宣称真实双边／识别正确或可跑圈。
    fixture=dict(valid=True,source='bench_fixture',steering=steering,bend=0,confidence=80)
    count=0
    try:
        sender.stop(); time.sleep_ms(10)
        print('[BENCH FIXTURE READY]',SCENARIO,'600s input window; NO CAMERA; NO START; suspended wheels; MCU run_ms must be 3000')
        origin=time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(),origin)<DURATION_MS:
            os.exitpoint()
            sender.path(fixture,processing_ms=0,age_ms=0); count+=1
            time.sleep_ms(PERIOD_MS)
    finally:
        try:
            sender.stop(); time.sleep_ms(10)
        finally:
            uart.deinit()
    print('[MOTOR BENCH DONE]',count,'fixture paths; no automatic START; no vision/lap acceptance')


if __name__=='__main__': main()
