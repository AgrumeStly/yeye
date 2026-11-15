"""LowSpeedLap L1手动入口：idle／SD回放／live；不读写main.py或采集许可。

默认idle，UART和drive许可关闭。先SD比对、再无动力live计时／收包，确认
当前几何与速度后才允许受控悬空。启动始终由STM32 KEY完成，相机脚本不
发START。最终现场连续一圈仍待实测，不能由预览路线或主机测试替代。
"""
import gc
import json
import os
import time
from lite_lap_route import LiteLapRoute
from lap_protocol import LapSender

MODE='idle'
UART_ENABLED=False
ALLOW_DRIVE=False
UART_CONFIG={'id':2,'tx_pin':11,'rx_pin':12}
SENSOR_ID=2
DURATION_MS=300000
SHOW_PREVIEW=True  # 仅无动力诊断显示；ALLOW_DRIVE=True时不做IDE图像传输。
SEARCH_BUDGET=48  # 每帧滚动粗搜上限；加最多7个前帧局部邻居，不执行电脑完整细搜。
SD_SESSION='/sdcard/captures/push_full_lap_0001'
SD_FRAME_IDS=(1,98,100,109,111,120,142,143,177,191,271,275,285,300,370,
              378,392,408,409,419,421,422,457,483,508,520,550,560,571,578)


def _uart():
    """只使用官方已核实GH串口2；V不接，3.3V逻辑、T/R交叉、G共地。"""
    from machine import UART,FPIOA
    if UART_CONFIG!={'id':2,'tx_pin':11,'rx_pin':12}:
        raise ValueError('verify any UART mapping change against actual board before running')
    fpioa=FPIOA(); fpioa.set_function(11,FPIOA.UART2_TXD); fpioa.set_function(12,FPIOA.UART2_RXD)
    return UART(UART.UART2,baudrate=115200,bits=UART.EIGHTBITS,parity=UART.PARITY_NONE,stop=UART.STOPBITS_ONE)


def main():
    """默认无设备副作用；任何退出尽力发送STOP并清理媒体，不自动重启。

    时间分别记录取图／字节复制／算法／发包。软件snapshot边界不等于曝光
    时间；真实端到端延迟仍需观察。GC、日志、IDE显示若阻塞，STM32独立
    200ms断流撤驱动，不能放宽门槛掩盖板上性能不足。
    """
    if MODE=='idle':
        print('[L1 IDLE] explicit sd_replay/live required; no camera/UART/main.py changes')
        return
    if MODE not in ('sd_replay','live') or (MODE=='sd_replay' and (UART_ENABLED or ALLOW_DRIVE)):
        raise ValueError('SD replay must have UART and drive disabled')
    import image
    sensor=uart=sender=None; media=False; display=False
    try:
        if UART_ENABLED:
            uart=_uart()
        sender=LapSender(uart.write if uart is not None else None,ALLOW_DRIVE)
        if uart is not None:
            sender.stop()
        print('[L1 INIT] precomputing local templates; no START')
        detector=LiteLapRoute(search_budget=SEARCH_BUDGET); gc.collect()
        print('[L1 READY]',len(detector.templates),'templates','free_heap',gc.mem_free())
        if MODE=='live':
            from media.sensor import Sensor,CAM_CHN_ID_0
            from media.display import Display
            from media.media import MediaManager
            sensor=Sensor(id=SENSOR_ID); sensor.reset()
            sensor.set_framesize(width=320,height=240,chn=CAM_CHN_ID_0)
            sensor.set_pixformat(Sensor.GRAYSCALE,chn=CAM_CHN_ID_0)
            sensor.set_hmirror(False); sensor.set_vflip(False)
            display=True; Display.init(Display.VIRT,width=320,height=240,to_ide=True)
            media=True; MediaManager.init(); sensor.run()
        origin=time.ticks_ms(); index=0; previous_start=None
        detector.clock=lambda: time.ticks_diff(time.ticks_ms(),origin)
        while True:
            os.exitpoint()
            if MODE=='sd_replay' and index>=len(SD_FRAME_IDS):
                break
            started=time.ticks_ms()
            if MODE=='live' and time.ticks_diff(started,origin)>=DURATION_MS:
                break
            if MODE=='sd_replay':
                frame=image.Image(SD_SESSION+'/data_%04d.jpg'%SD_FRAME_IDS[index]).to_grayscale()
                # 非连续SD选片禁止时间融合，每图独立，仅对照空间搜索结果。
                detector.reset()
            else:
                frame=sensor.snapshot(chn=CAM_CHN_ID_0)
            acquired=time.ticks_ms()
            if (frame.width(),frame.height(),frame.format())!=(320,240,image.GRAYSCALE):
                raise ValueError('actual grayscale buffer layout mismatch')
            pixels=frame.bytearray(); copied=time.ticks_ms()
            result=detector.update(pixels,time.ticks_diff(started,origin))
            processed=time.ticks_ms(); processing=time.ticks_diff(processed,copied)
            packet=sender.path(result,processing,time.ticks_diff(processed,started))
            sent=time.ticks_ms(); index+=1
            record=dict(index=index,source=result['source'],valid=result['valid'],wire_valid=bool(packet[6]&1),
                steering=result['steering'],bend=result['bend'],support=result['support'],
                acquire_ms=time.ticks_diff(acquired,started),copy_ms=time.ticks_diff(copied,acquired),
                processing_ms=processing,to_send_ms=time.ticks_diff(sent,started),
                interval_ms=None if previous_start is None else time.ticks_diff(started,previous_start),
                free_heap=gc.mem_free(),drive_allowed=ALLOW_DRIVE)
            record['profile_ms']=result.get('profile_ms',{})
            record['searched_candidates']=result.get('searched_candidates')
            previous_start=started
            if MODE=='live' and SHOW_PREVIEW and not ALLOW_DRIVE:
                # 预览只在诊断模式显示原图，避免把模型线画成实际观测。
                # 当前候选参数／source／steering在同一帧日志核对；显示耗时计入
                # 下一帧interval，不能把不含IDE传输的算法时间称端到端周期。
                Display.show_image(frame)
            if MODE=='sd_replay' or index%10==0 or not result['valid']:
                print(json.dumps(record))
            del pixels,frame
            gc.collect()
    finally:
        if sender is not None and uart is not None:
            try:
                sender.stop()
                # 即便相机初始化早期失败、后面没有媒体清理延时，也给最后
                # 20字节STOP留出有界发送时间，不能write后立即deinit。
                time.sleep_ms(10)
            except BaseException as exc:
                print('[STOP_SEND_ERROR]',str(exc))
        for name,cleanup in (('sensor',sensor.stop if sensor is not None else None),
                             ('display',Display.deinit if display else None),
                             ('media',MediaManager.deinit if media else None),
                             ('uart',uart.deinit if uart is not None else None)):
            if cleanup is not None:
                try:
                    if name=='media': time.sleep_ms(100)
                    cleanup()
                except BaseException as exc:
                    print('[CLEANUP_ERROR]',name,str(exc))
    print('[L1 DONE] no autonomous lap/physical stop acceptance implied')


if __name__=='__main__':
    main()
