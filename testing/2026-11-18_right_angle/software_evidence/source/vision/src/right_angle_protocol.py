"""首弯独立v4，帧布局沿用v2，版本与直道v3隔离；不发START。"""
from lap_protocol import LapSender
from vision_protocol import crc16


class RightAngleSender(LapSender):
    def _send(self, data):
        converted = bytearray(data)
        converted[2] = 4
        checksum = crc16(converted[:18])
        converted[18] = checksum & 255
        converted[19] = checksum >> 8
        return super()._send(bytes(converted))

    def path(self, result, processing_ms, age_ms):
        """接纳当前双侧及观察器限定的当前关联单侧；历史与超龄发新无效包。"""
        current = dict(result)
        current['valid'] = bool(result.get('valid') and result.get('source') in
                               ('current_pair', 'current_single_associated'))
        current['source'] = result.get('source') if current['valid'] else 'unknown'
        if current['source'] == 'current_single_associated' and age_ms >= 120:
            current['valid'] = False
        return super().path(current, processing_ms, age_ms)
