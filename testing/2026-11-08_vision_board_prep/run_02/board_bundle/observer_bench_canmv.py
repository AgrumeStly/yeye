# SOURCE: vision/src/board_observer_core.py
"""BP1可移植灰度诊断核，只使用Python基础类型，不依赖OpenCV／NumPy。

该核仅迁移固定参考行周围的黑段／双边几何诊断；没有C2全图连通域与
双侧转角验证，也没有F1终点模块。因此diagnostic_valid绝不能当协议
PATH_VALID；顶层valid始终False。用于先测API、内存、时延和像素符号，
不是完整识别替代，也不是可上车轨迹。输入缓冲只读，不留前帧图像。
"""


def _median(values):
    """短灰度序列中位数；偶数时取中间两数平均，仅用于诊断阈值。"""
    ordered=sorted(values);n=len(ordered)
    return ordered[n//2] if n%2 else (ordered[n//2-1]+ordered[n//2])/2


def _threshold(pixels):
    """ROI每4列／5行采样直方图，计算大津与65百分位上限。

    与电脑R1全ROI阈值不同，必须在回归表单独比较，不能称逐像素等价。
    最多2480次缓冲读取及256次阈值循环，不复制完整图像。
    """
    hist=[0]*256
    for y in range(65,216,5):
        for x in range(0,320,4):hist[pixels[y*320+x]]+=1
    total=sum(hist);total_sum=sum(i*count for i,count in enumerate(hist))
    lower_count=0;lower_sum=0;best=-1;otsu=0;percentile=255;seen=0
    for i,count in enumerate(hist):
        seen+=count
        if seen>=total*.65 and percentile==255:percentile=i
        lower_count+=count;lower_sum+=i*count
        upper_count=total-lower_count
        if lower_count and upper_count:
            between=(lower_sum/lower_count-(total_sum-lower_sum)/upper_count)**2*lower_count*upper_count
            if between>best:best=between;otsu=i
    return max(20,min(100,otsu,percentile-18))


def detect_gray(pixels,width=320,height=240):
    """输入连续单通道uint8缓冲，320×240／76800字节；所有坐标像素。

    每5行取三行中值；黑段3..55px、白内侧对比≥12灰度级、两条实际
    黑段之间55..300px且白内部；多解不强选，最多两行中断、有限斜移。
    至少6行／25px、透视增长≥0.2且覆盖y120才给诊断偏差。未扫描二维
    连通域，不能证明两段属于不同道路边界；所有结果保持诊断身份。
    """
    output=dict(revision='board-probe-bp1',valid=False,quality=0.,diagnostic_valid=False,
                deviation_px=None,deviation_normalized=None,reference_y=120,pair_samples=[],
                threshold=None,reason='diagnostic_subset_not_C2',control_ready=False,
                full_turn_path_available=False,finish_state='not_ported')
    if width!=320 or height!=240 or pixels is None or len(pixels)!=76800:
        output['reason']='unsupported_gray_buffer';return output
    threshold=_threshold(pixels);output['threshold']=threshold
    best=[];chain=[];missing_rows=0
    for y in range(65,216,5):
        profile=bytearray(320)
        for x in range(320):
            a=pixels[(y-1)*320+x];b=pixels[y*320+x];c=pixels[(y+1)*320+x]
            profile[x]=a+b+c-min(a,b,c)-max(a,b,c)
        runs=[];start=None
        for x in range(321):
            dark=x<320 and profile[x]<=threshold
            if dark and start is None:start=x
            if not dark and start is not None:
                end=x-1
                if 3<=end-start+1<=55:
                    value=_median(profile[start:end+1])
                    lc=_median(profile[max(0,start-8):start])-value if start>3 else -1
                    rc=_median(profile[end+1:min(320,end+9)])-value if end<316 else -1
                    if max(lc,rc)>=12:runs.append((start,end,lc,rc))
                start=None
        # 复杂文字行直接拒绝，限制每行最多8条黑段，避免组合数失控。
        pairs=[]
        if len(runs)<=8:
            for i,left in enumerate(runs):
                for right in runs[i+1:]:
                    lx,rx=left[1],right[0]
                    if not 3<lx<rx<316 or not 55<=rx-lx<=300 or min(left[3],right[2])<12:continue
                    if sum(v<=threshold for v in profile[lx+2:rx-1])/max(1,rx-lx-3)>.08:continue
                    pairs.append(dict(y=y,left=lx,right=rx))
        if len(pairs)!=1:
            missing_rows+=1
            if missing_rows>2:
                if len(chain)>len(best):best=chain
                chain=[]
            continue
        pair=pairs[0]
        if chain and (pair['y']-chain[-1]['y']>15 or max(abs(pair[s]-chain[-1][s]) for s in ('left','right'))>2.8*(pair['y']-chain[-1]['y'])+3):
            if len(chain)>len(best):best=chain
            chain=[]
        chain.append(pair);missing_rows=0
    if len(chain)>len(best):best=chain
    output['pair_samples']=best
    if len(best)<6 or best[-1]['y']-best[0]['y']<25:return output
    ys=[p['y'] for p in best];widths=[p['right']-p['left'] for p in best]
    mean_y=sum(ys)/len(ys);mean_width=sum(widths)/len(widths)
    growth=sum((y-mean_y)*(w-mean_width) for y,w in zip(ys,widths))/sum((y-mean_y)**2 for y in ys)
    density=len(best)/((ys[-1]-ys[0])/5+1)
    quality=min(1.,len(best)/12)*density
    if growth<.2 or quality<.45 or not ys[0]<=120<=ys[-1]:return output
    upper=max((p for p in best if p['y']<=120),key=lambda p:p['y'])
    lower=min((p for p in best if p['y']>=120),key=lambda p:p['y'])
    if lower['y']-upper['y']>15:return output
    middle_a=(upper['left']+upper['right'])/2;middle_b=(lower['left']+lower['right'])/2
    middle=middle_a if upper['y']==lower['y'] else middle_a+(middle_b-middle_a)*(120-upper['y'])/(lower['y']-upper['y'])
    deviation=middle-159.5
    output.update(diagnostic_valid=True,deviation_px=deviation,
                  deviation_normalized=max(-1000,min(1000,round(deviation/159.5*1000))),quality=quality)
    return output


# SOURCE: vision/src/vision_protocol.py
"""PC／MicroPython共用20字节编码器及受限发送器，无导入时串口副作用。

唯一规格为control/docs/protocol_v1_draft.md。本模块不扩字段、不自动
发送START或STOP。路径新鲜度、处理超限、无当前观测均编码为新序号
无效包；历史方向、近场中点和终点观察门不可冒充固定y120偏差。
"""

try:
    import ustruct as struct
except ImportError:
    import struct


def crc16(data):
    """CRC-16/CCITT-FALSE；校验范围0..17字节，结果小端写入18..19。"""
    crc=0xffff
    for byte in data:
        crc^=byte<<8
        for _ in range(8):
            crc=((crc<<1)^0x1021)&0xffff if crc&0x8000 else (crc<<1)&0xffff
    return crc


def encode_path(sequence,error=0,valid=False,confidence=0,heading=0,bend=0,processing_ms=0,finish=False):
    """按原协议编码；偏差右正，heading单位0.01度，耗时毫秒。

    heading／bend没有经验证定义时保持0；绝不把C2左右提示强行量化为
    物理角度或500以上的弯强度（主控会因此改变演示基础请求）。
    """
    if not (0<=sequence<=255 and -1000<=error<=1000 and 0<=confidence<=100 and
            -9000<=heading<=9000 and 0<=bend<=1000 and 0<=processing_ms<=1000):
        raise ValueError('path field out of protocol range')
    head=bytes((0xa5,0x5a,1,1,12,sequence))
    body=struct.pack('<BBhhHHBB',int(bool(valid))|(int(bool(finish))<<1),confidence,
                     error,heading,bend,processing_ms,0,0)
    data=head+body
    return data+struct.pack('<H',crc16(data))


def encode_command(sequence,command):
    """1 START／2 STOP／3 STATUS；本函数只编码，不解释为实际执行许可。"""
    if not 0<=sequence<=255 or command not in (1,2,3):raise ValueError('bad command')
    data=bytes((0xa5,0x5a,1,2,12,sequence))+bytes(10)+bytes((command,0))
    return data+struct.pack('<H',crc16(data))


class RecognitionSender:
    """两种type独立递增，0..255回绕；调用者注入writer，不自动打开端口。

    allow_valid_path默认False：板上诊断核未完成C2关联验证，不能发可信
    路径。电脑离线交叉验证可显式置True，但不会连接真实串口。
    """

    def __init__(self,writer=None,allow_valid_path=False):
        self.writer=writer
        self.allow_valid_path=allow_valid_path
        self.path_sequence=0
        self.command_sequence=0

    def _send(self,data):
        """短写继续发送剩余字节；不重复整包，0／None立即报错避免死循环。

        写入长度不是对端接收／CRC正确证明；故障时停止应用并让STM32
        既有200ms断流逻辑生效，不能用这项软件处理宣称车辆已停稳。
        """
        if self.writer is None:return data
        offset=0
        while offset<len(data):
            count=self.writer(data[offset:])
            if not isinstance(count,int) or not 0<count<=len(data)-offset:
                raise OSError('UART short/failed write')
            offset+=count
        return data

    def path(self,result,finish=None,processing_ms=0,source_age_ms=0):
        """将真实C2当前固定行结果映射原协议，其余状态只能发无效。

        source_age_ms为采集开始到发送前的保守本地年龄，必须用真实时间。
        旧录制离线生成包的年龄0仅模拟字节映射，不宣称实时新鲜。处理
        超100ms或年龄≥200ms立即无效；超1000ms只饱和字段，不隐瞒超限。
        """
        if (not isinstance(processing_ms,(int,float)) or not isinstance(source_age_ms,(int,float)) or
                processing_ms<0 or source_age_ms<0 or processing_ms!=processing_ms or
                source_age_ms!=source_age_ms or processing_ms==float('inf') or source_age_ms==float('inf')):
            raise ValueError('finite nonnegative processing and age required')
        obs=result.get('recovery_observation',{})
        valid=bool(self.allow_valid_path and result.get('valid') and obs.get('fixed_reference_observed') and
                   obs.get('temporal_state')=='stable_observation' and processing_ms<=100 and source_age_ms<200)
        error=result.get('deviation_normalized') if valid else 0
        if valid and (not isinstance(error,int) or not -1000<=error<=1000):
            raise ValueError('valid current y120 normalized deviation required')
        confidence=max(0,min(100,round(result.get('quality',0)*100))) if valid else 0
        f=finish or {}
        finish_flag=bool(f.get('observation',{}).get('visible') and f.get('state')=='finish_line_seen')
        data=encode_path(self.path_sequence,error=error,valid=valid,confidence=confidence,
                         heading=0,bend=0,processing_ms=min(1000,int(processing_ms+.999)),finish=finish_flag)
        self.path_sequence=(self.path_sequence+1)&255
        return self._send(data)

    def command(self,command):
        """仅供明确的人工无动力联调触发；识别循环不调用此方法。"""
        data=encode_command(self.command_sequence,command)
        self.command_sequence=(self.command_sequence+1)&255
        return self._send(data)


# SOURCE: vision/src/observer_bench_canmv.py
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
