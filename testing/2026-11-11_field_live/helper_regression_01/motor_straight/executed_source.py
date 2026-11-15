# Suspended motor fixture only; NOT CAMERA; default IDLE; never START

# BEGIN vision_protocol.py
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

    def path(self,result,finish=None,processing_ms=0,source_age_ms=None):
        """将真实C2当前固定行结果映射原协议，其余状态只能发无效。

        source_age_ms为采集开始到发送前的保守本地年龄，必须用真实时间。
        旧录制离线生成包的年龄0仅模拟字节映射，不宣称实时新鲜。处理
        超100ms或年龄≥200ms立即无效；超1000ms只饱和字段，不隐瞒超限。
        """
        age_known=source_age_ms is not None
        if not age_known:source_age_ms=200  # 年龄未知不默认为新鲜，可信路径关闭。
        if (not isinstance(processing_ms,(int,float)) or not isinstance(source_age_ms,(int,float)) or
                processing_ms<0 or source_age_ms<0 or processing_ms!=processing_ms or
                source_age_ms!=source_age_ms or processing_ms==float('inf') or source_age_ms==float('inf')):
            raise ValueError('finite nonnegative processing and age required')
        obs=result.get('recovery_observation',{})
        valid=bool(age_known and self.allow_valid_path and result.get('valid') and obs.get('fixed_reference_observed') and
                   obs.get('temporal_state')=='stable_observation' and processing_ms<=100 and source_age_ms<200)
        error=result.get('deviation_normalized') if valid else 0
        if valid and (not isinstance(error,int) or not -1000<=error<=1000):
            raise ValueError('valid current y120 normalized deviation required')
        confidence=max(0,min(100,round(result.get('quality',0)*100))) if valid else 0
        f=finish or {}
        finish_flag=bool(age_known and source_age_ms<200 and processing_ms<=100 and
                         f.get('observation',{}).get('visible') and f.get('state')=='finish_line_seen')
        data=encode_path(self.path_sequence,error=error,valid=valid,confidence=confidence,
                         heading=0,bend=0,processing_ms=min(1000,int(processing_ms+.999)),finish=finish_flag)
        self.path_sequence=(self.path_sequence+1)&255
        return self._send(data)

    def command(self,command):
        """仅供明确的人工无动力联调触发；识别循环不调用此方法。"""
        data=encode_command(self.command_sequence,command)
        self.command_sequence=(self.command_sequence+1)&255
        return self._send(data)

# BEGIN lap_protocol.py
"""LowSpeedLap独立v2封包，原v1模块保持；无导入时串口副作用。

v2 error是局部推荐转向量，非固定y120偏差；bit2明确历史来源。
只编码／发送，不自动START。处理>100ms、总年龄>=150ms或未明确开启
drive许可时发新序号无效包；STOP用于脚本清理，不能充作车轮停稳证据。
"""
try:
    import ustruct as struct
except ImportError:
    import struct


class LapSender:
    def __init__(self,writer=None,allow_drive=False):
        self.writer=writer; self.allow_drive=allow_drive; self.seq=0; self.cmd_seq=0

    def _send(self,data):
        if self.writer is not None:
            offset=0
            while offset<len(data):
                written=self.writer(data[offset:])
                if not isinstance(written,int) or written<=0 or written>len(data)-offset:
                    raise OSError('UART short write failed; STM32 timeout must remain enabled')
                offset+=written
        return data

    def path(self,result,processing_ms,age_ms):
        if not isinstance(processing_ms,int) or not isinstance(age_ms,int) or processing_ms<0 or age_ms<0:
            raise ValueError('explicit nonnegative integer processing and acquisition age required')
        history=result.get('source')=='history'
        # history的年龄必须从最后有当前支持的模型算起，不能被空白新帧刷新。
        # 未提供证据年龄时默认过期；接收端也按120ms而非200ms执行监督。
        evidence_age=result.get('evidence_age_ms',120) if history else 0
        if not isinstance(evidence_age,int) or evidence_age<0:
            raise ValueError('known nonnegative model evidence age required')
        total_age=age_ms+evidence_age
        valid=bool(self.allow_drive and result.get('valid') and processing_ms<=100 and
                   total_age<(120 if history else 150))
        steering=int(result.get('steering',0)) if valid else 0
        bend=int(result.get('bend',0)) if valid else 0
        quality=int(result.get('confidence',0)) if valid else 0
        if not (-1000<=steering<=1000 and 0<=bend<=1000 and 0<=quality<=100):
            raise ValueError('invalid L1 local route fields')
        flags=int(valid)|(4 if valid and result.get('source')=='history' else 0)|(
            8 if valid and result.get('source')=='current_single_associated' else 0)
        header=bytes((0xa5,0x5a,2,1,12,self.seq)); self.seq=(self.seq+1)&255
        data=header+struct.pack('<BBhHHHBB',flags,quality,steering,min(total_age,1000),bend,min(processing_ms,1000),0,0)
        return self._send(data+struct.pack('<H',crc16(data)))

    def stop(self):
        header=bytes((0xa5,0x5a,2,2,12,self.cmd_seq)); self.cmd_seq=(self.cmd_seq+1)&255
        data=header+bytes(10)+bytes((2,0))
        return self._send(data+struct.pack('<H',crc16(data)))

# BEGIN lap_motor_bench_canmv.py
"""独立悬空动力台架输入，不是相机观测，也不是自主循迹。

只有主控实际确认当前LowSpeedLap目标、run_ms=3000、phase=2、
轮子完全悬空后，才明确开启本入口。发送有效的人工固定控制输入供验证
通信→差速策略→PI→PWM；不发START，仍由主控车载KEY触发单次3秒。
不得用于地面／比赛，不修改真实视觉脚本的ALLOW_DRIVE或main.py。
"""
import time

ENABLED=True
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
