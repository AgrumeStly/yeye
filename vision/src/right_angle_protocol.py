"""首弯v5：双侧、当前L形预测、短时出口关联分别编码，不发START。"""
from lap_protocol import LapSender
from vision_protocol import crc16
try:
    import ustruct as struct
except ImportError:
    import struct


class RightAngleSender(LapSender):
    wire_version = 5
    flags_by_source = {'current_pair': 1, 'current_corner_predicted': 9, 'current_corner_associated': 5}

    def _send(self, data):
        converted = bytearray(data)
        converted[2] = self.wire_version
        checksum = crc16(converted[:18])
        converted[18] = checksum & 255
        converted[19] = checksum >> 8
        return super()._send(bytes(converted))

    def path(self, result, processing_ms, age_ms):
        """v5 bit3为当前左纵／前横L，bit2为有当前支持的短期出口关联。
        不接收纯历史或普通一根单直边；当前L不依赖先前双侧，可人工启动右转。
        """
        if not isinstance(processing_ms,int) or not isinstance(age_ms,int) or min(processing_ms,age_ms)<0:
            raise ValueError('explicit nonnegative timing required')
        kind=result.get('source'); flags=self.flags_by_source.get(kind,0)
        valid=bool(self.allow_drive and result.get('valid') and flags and processing_ms<=100 and age_ms<150)
        steering=int(result.get('steering',0));bend=int(result.get('bend',0));quality=int(result.get('confidence',0))
        if kind=='current_corner_predicted':
            # 联合弯外边仍确认右转，但允许赛车线在进／出弯短时向左回正。
            valid=valid and result.get('corner_observed') is True and bend==1000 and (self.wire_version == 10 or steering>=0) and quality>=60
        elif kind=='current_corner_associated':
            evidence_age=result.get('corner_age_ms',700)
            valid=valid and isinstance(evidence_age,int) and 0<=evidence_age<700 and bend==1000 and steering>=0 and quality>=45
        elif kind == 'current_front_forecast':
            valid = valid and quality == 58 and result.get('front_support', 0) >= 5
        elif kind in ('current_single_forecast', 'short_corridor_forecast'):
            valid = valid and (50 <= quality < 58 if kind == 'current_single_forecast' else 40 <= quality < 50)
        if not (-1000<=steering<=1000 and 0<=bend<=1000 and 0<=quality<=100):raise ValueError('v5 route fields')
        header=bytes((0xa5,0x5a,self.wire_version,1,12,self.seq));self.seq=(self.seq+1)&255
        data=header+struct.pack('<BBhHHHBB',flags if valid else 0,quality if valid else 0,
            steering if valid else 0,min(age_ms,1000),bend if valid else 0,min(processing_ms,1000),0,0)
        return self._send(data+struct.pack('<H',crc16(data)))
