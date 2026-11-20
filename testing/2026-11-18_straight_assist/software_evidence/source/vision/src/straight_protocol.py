"""直道独立v3发送器；帧结构沿用v2，版本隔离避免旧循迹视觉误配。

只允许当前双边直道且bend=0。不发START；STM32仍须车载KEY人工启动。
"""
from lap_protocol import LapSender
from vision_protocol import crc16


class StraightSender(LapSender):
    def _send(self, data):
        """在完整v2封包基础上改v3并重算CRC，短写处理继续复用生产发送器。"""
        converted = bytearray(data)
        converted[2] = 3
        checksum = crc16(converted[:18])
        converted[18] = checksum & 255
        converted[19] = checksum >> 8
        return super()._send(bytes(converted))

    def path(self, result, processing_ms, age_ms):
        """明确拒绝历史、单边和非零弯道输入；无效时仍发新序号包。"""
        current = dict(result)
        current['valid'] = bool(result.get('valid') and result.get('source') == 'current_pair' and result.get('bend') == 0)
        current['source'] = 'current_pair' if current['valid'] else 'unknown'
        return super().path(current, processing_ms, age_ms)
