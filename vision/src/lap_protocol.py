"""LowSpeedLap独立v2封包，原v1模块保持；无导入时串口副作用。

v2 error是局部推荐转向量，非固定y120偏差；bit2明确历史来源。
只编码／发送，不自动START。处理>100ms、总年龄>=150ms或未明确开启
drive许可时发新序号无效包；STOP用于脚本清理，不能充作车轮停稳证据。
"""
try:
    import ustruct as struct
except ImportError:
    import struct
from vision_protocol import crc16


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
