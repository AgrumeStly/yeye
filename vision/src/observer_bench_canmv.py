"""V-08独立板上诊断入口；默认idle，无启动相机／UART／写卡副作用。

仅供主控下一次明确的无动力验证。不要保存为main.py；现有一次采集
许可不读不写。本入口不发送START／STOP，BP1包始终PATH_VALID=0。
代码在电脑做模型与字节交叉检查；实际API、内存和速度仍待K230D验。
"""

import gc
import json
import os
import time
from binascii import hexlify

from board_observer_core import detect_gray
from vision_protocol import RecognitionSender


MODE='idle'  # idle／sd_replay／live；手动明确更改才运行，不自动选模式。
UART_ENABLED=False
UART_CONFIG=None  # 未冻结K230侧引脚；以后明确填{id,tx_pin,rx_pin}，不猜默认接线。
SENSOR_ID=2
LIVE_DURATION_MS=30000
SD_SESSION='/sdcard/captures/push_full_lap_0001'
# 这些编号只选择回放材料，不传给检测函数，也不参与识别判据。
SD_FRAME_IDS=(1,98,100,109,111,120,142,143,177,191,271,275,285,300,370,
              378,392,408,409,419,421,422,457,483,508,520,550,560,571,578)


def _uart(config):
    """仅在主控显式启用且已核实引脚时初始化115200/8N1，不自动探测端口。

    FPIOA示例值不是本车接线；UART_CONFIG缺失立即拒绝。主控先查冲突、
    3.3V与共地，STM32端PA2/PA3按唯一资源文档核实；本函数不改STM32。
    """
    if config is None or set(config)!=set(('id','tx_pin','rx_pin')):
        raise ValueError('UART pin mapping must be explicitly verified first')
    from machine import UART,FPIOA
    if config['id'] not in (1,2,3,4) or config['tx_pin']==config['rx_pin']:
        raise ValueError('unsupported UART mapping')
    fpioa=FPIOA()
    fpioa.set_function(config['tx_pin'],getattr(FPIOA,'UART%d_TXD'%config['id']))
    fpioa.set_function(config['rx_pin'],getattr(FPIOA,'UART%d_RXD'%config['id']))
    return UART(getattr(UART,'UART%d'%config['id']),baudrate=115200,bits=UART.EIGHTBITS,
                parity=UART.PARITY_NONE,stop=UART.STOPBITS_ONE)


def _one(frame,sender,started,acquired,source_kind,index):
    """只读当前图像，分开记录取帧／缓冲复制／算法／到发送前时间及内存。

    JPEG回放的取图耗时是SD读图与解码，不称相机性能。live的snapshot
    调用边界也不等于曝光时刻。串口发送只传新识别摘要，无效不延用旧值。
    """
    import image
    if (frame.width(),frame.height(),frame.format())!=(320,240,image.GRAYSCALE):
        raise ValueError('expected actual 320x240 grayscale image')
    free_before=gc.mem_free()
    copy_start=time.ticks_ms()
    pixels=frame.bytearray()
    copied=time.ticks_ms()
    if len(pixels)!=76800:raise ValueError('image buffer stride/layout not validated')
    result=detect_gray(pixels)
    processed=time.ticks_ms()
    algorithm_ms=time.ticks_diff(processed,copied)
    age=time.ticks_diff(processed,started)
    packet=sender.path(result,processing_ms=algorithm_ms,source_age_ms=age)
    sent=time.ticks_ms()
    print(json.dumps(dict(version='observer-bench-bp1',source_kind=source_kind,index=index,
          acquire_ms=time.ticks_diff(acquired,started),buffer_copy_ms=time.ticks_diff(copied,copy_start),
          algorithm_ms=algorithm_ms,to_uart_ms=time.ticks_diff(sent,started),
          capture_age_before_uart_ms=age,free_before=free_before,free_after=gc.mem_free(),
          diagnostic_valid=result['diagnostic_valid'],deviation_px=result['deviation_px'],
          deviation_normalized=result['deviation_normalized'],threshold=result['threshold'],
          wire_valid=bool(packet[6]&1),wire_hex=hexlify(packet).decode(),
          control_ready=False,finish_state='not_ported',uart_enabled=UART_ENABLED)))


def main():
    """默认立即返回；实体运行由主控明确操作，任何失败清理后原样上报。

    live最多30秒，不保存原图、不读写采集许可、不启动运动。程序卡顿时
    没有Python软件定时器能保证实时发包，须保留STM32独立断流保护。
    """
    if MODE=='idle':
        print('[IDLE] Set explicit sd_replay or live; UART disabled by default; no main.py deployment')
        return
    if MODE not in ('sd_replay','live'):raise ValueError('unsupported explicit diagnostic mode')
    sensor=None;uart=None;display_attempted=False;media_attempted=False
    try:
        if UART_ENABLED:uart=_uart(UART_CONFIG)
        sender=RecognitionSender(uart.write if uart is not None else None,allow_valid_path=False)
        if MODE=='sd_replay':
            import image
            for index in SD_FRAME_IDS:
                os.exitpoint();gc.collect()
                started=time.ticks_ms()
                frame=image.Image(SD_SESSION+'/data_%04d.jpg'%index).to_grayscale()
                acquired=time.ticks_ms()
                _one(frame,sender,started,acquired,'sd_decode_not_camera',index)
                del frame
            return
        from media.sensor import Sensor,CAM_CHN_ID_0
        from media.display import Display
        from media.media import MediaManager
        sensor=Sensor(id=SENSOR_ID);sensor.reset()
        sensor.set_framesize(width=320,height=240,chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE,chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False);sensor.set_vflip(False)
        display_attempted=True
        Display.init(Display.VIRT,width=320,height=240,to_ide=True)
        media_attempted=True;MediaManager.init();sensor.run()
        origin=time.ticks_ms();index=0
        while time.ticks_diff(time.ticks_ms(),origin)<LIVE_DURATION_MS:
            os.exitpoint();gc.collect();index+=1
            started=time.ticks_ms()
            frame=sensor.snapshot(chn=CAM_CHN_ID_0)
            acquired=time.ticks_ms()
            _one(frame,sender,started,acquired,'live_snapshot_software_boundary',index)
            del frame
    finally:
        errors=[]
        for name,cleanup in [('sensor',sensor.stop if sensor is not None else None),
                             ('display',Display.deinit if display_attempted else None),
                             ('media',MediaManager.deinit if media_attempted else None),
                             ('uart',uart.deinit if uart is not None else None)]:
            if cleanup is not None:
                try:
                    if name=='media':time.sleep_ms(100)
                    cleanup()
                except BaseException as exc:errors.append(name+': '+str(exc))
        if errors:print('[CLEANUP_ERRORS]',errors)
    print('[DIAGNOSTIC_DONE] no movement, no automatic finish/stop acceptance')


if __name__=='__main__':
    main()
