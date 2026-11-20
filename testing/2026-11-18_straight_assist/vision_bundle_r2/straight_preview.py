# StraightAssist v3 generated file; no automatic motor START.

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

# BEGIN lite_lap_route.py
from array import array

WIDTH=320

HEIGHT=240

GRID_STEP=6

GW=WIDTH//GRID_STEP

GH=HEIGHT//GRID_STEP

GY0=(40+GRID_STEP-1)//GRID_STEP

GY1=(228-3)//GRID_STEP+1

def _threshold(pixels):
    """稀疏大津阈值，按现有黑白场景加灰度上限；光照泛化待现场核验。"""
    hist = [0]*256
    for y in range(60,220,8):
        for x in range(4,316,8):
            hist[pixels[y*WIDTH+x]] += 1
    total=sum(hist); value=sum(i*n for i,n in enumerate(hist))
    n0=s0=0; best=-1.; threshold=40
    for i,n in enumerate(hist):
        n0+=n; s0+=i*n; n1=total-n0
        if n0 and n1:
            score=(s0/n0-(value-s0)/n1)**2*n0*n1
            if score>best:
                best=score; threshold=i
    return max(20,min(100,threshold))

def _grid(pixels, threshold):
    """每网格内取4个灰度样本；至少2个黑才标黑，减少JPEG孤点。

    当前组件以8邻域关联，最小3格；既允许连续带也保留分离小色块。
    膨胀一格仅容许采样误差，不把分离两侧当同一组件；标签只用于拒绝
    同一黑带两面被误当双边。标签不是边界语义真值。
    """
    # CanMV v1.8-0实板不支持array乘整数；先建立有界零列表再构造H数组。
    # 临时列表最多4800项，避免为了填零依赖桌面Python的array.__mul__。
    black=bytearray(GW*GH); labels=array('H',[0]*(GW*GH))
    for gy in range(GY0,GY1):
        y=gy*GRID_STEP
        for gx in range(1,GW-1):
            x=gx*GRID_STEP; p=y*WIDTH+x
            black[gy*GW+gx]=int((int(pixels[p]<=threshold)+int(pixels[p+2]<=threshold)+
                int(pixels[p+2*WIDTH]<=threshold)+int(pixels[p+2*WIDTH+2]<=threshold))>=2)
    component=0
    for start in range(GY0*GW,GY1*GW):
        if not black[start] or labels[start]:
            continue
        component+=1; labels[start]=component; queue=[start]; at=0
        minx=maxx=start%GW; miny=maxy=start//GW
        while at<len(queue):
            index=queue[at]; at+=1; x=index%GW; y=index//GW
            minx=min(minx,x); maxx=max(maxx,x); miny=min(miny,y); maxy=max(maxy,y)
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nx,ny=x+dx,y+dy
                    if not (0<=nx<GW and GY0<=ny<GY1):
                        continue
                    ni=ny*GW+nx
                    if black[ni] and not labels[ni]:
                        labels[ni]=component; queue.append(ni)
        # 拒绝极小噪点及ROI上沿实际横跨较宽区域的厚背景，单位均为网格。
        # 不能用整个组件的横向包围盒宽度判断“宽厚”：真实斜线从远到近
        # 横跨很多列，但每一行仍很窄。旧判断会在已保存的左右偏航原图
        # 中误删一侧完整边界，导致双边参照为空、车辆无法取得有效路径。
        # 仅在组件接触ROI上沿时数该行真实黑格，不增加／补画任何像素；
        # 面积门槛及后续白走廊、分离组件、模板支持、连续双帧保护都保留。
        # 额外计数只对接触上沿的组件做一次有界遍历，不执行完整模板搜索。
        top_cells=sum(1 for index in queue if index//GW==GY0) if miny==GY0 else 0
        if len(queue)<3 or (top_cells>120//GRID_STEP and len(queue)>4000//(GRID_STEP*GRID_STEP)):
            for index in queue:
                black[index]=0
    expanded=bytearray(GW*GH); near_labels=array('H',[0]*(GW*GH))
    for index in range(GY0*GW,GY1*GW):
        if not black[index]:
            continue
        x=index%GW; y=index//GW
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if 0<=x+dx<GW and 0<=y+dy<GH:
                    ni=index+dy*GW+dx; expanded[ni]=1
                    if not near_labels[ni]:
                        near_labels[ni]=labels[index]
    return black,expanded,near_labels

def _pair_anchors(black):
    """当前多行的双边白色走廊参照，仅用于约束模板与首次启动。

    候选宽度容许平面假设／姿态误差，但必须有两条分离黑段和白内侧。
    锐角仅一条横带时通常没有此参照；不把同一横带的两面当双边。
    行搜索是局部几何检查，不提供文字／真实道路的语义证明。
    """
    anchors=[]
    for gy in range((72+GRID_STEP-1)//GRID_STEP,216//GRID_STEP+1,2):
        runs=[]; start=None
        for gx in range(GW):
            dark=bool(black[gy*GW+gx])
            if dark and start is None: start=gx
            if not dark and start is not None:
                if 1<=gx-start<=56//GRID_STEP: runs.append((start,gx-1))
                start=None
        if len(runs)>8: continue
        y=gy*GRID_STEP+(GRID_STEP-1)/2; expected=50*(y+38.11111111111108)/48
        pairs=[]
        for left in runs:
            for right in runs:
                lx,rx=left[1]*GRID_STEP+GRID_STEP/2,right[0]*GRID_STEP+GRID_STEP/2
                if not (0<rx-lx and .72*expected<=rx-lx<=1.5*expected): continue
                lo,hi=left[1]+1,right[0]
                if any(black[gy*GW+i] for i in range(lo,hi)): continue
                z=(7802.22222222222-15.555555555555546*y)/(y+38.11111111111108)
                x=((lx+rx)/2-159.5)*48/(y+38.11111111111108)
                pairs.append((x,z,y))
        if len(pairs)==1: anchors.append(pairs[0])
    # 分离的单行巧合不足以证明两侧走廊。
    if len(anchors)<3 or max(p[2] for p in anchors)-min(p[2] for p in anchors)<16:
        return []
    return anchors

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

# BEGIN straight_route.py
"""直道专用观测器：只读当前双边，不搜索转弯模板、不沿用历史路径。

输入固定320x240灰度字节。复用现有黑块采样／双边白走廊检查，使用
已有近似投影只计算纠偏代理量；输出不是经过完整标定的厘米或航向。
无导入时相机／UART副作用，可在电脑和CanMV执行同一核心。
"""


class StraightRoute:
    """每帧只拟合一条直道，至少三帧／80ms一致后才许可。

    横向项使车回到道路中央，斜率项使车头顺道路方向；不能仅用横向
    偏差等到压线再纠正。增益与几何门槛为现场待验候选。
    """
    def __init__(self):
        self.reset()

    def reset(self):
        """失线、异常时间或几何跳变后撤销连续许可，没有历史续跑。"""
        self.last_at = None
        self.previous_error = None
        self.stable = 0
        self.stable_at = 0

    def update(self, pixels, now):
        """now为本次取图开始的相对毫秒；返回原始误差及拒绝原因。

        无效帧也必须发送新序号无效包，不能只停止打印或重复上一有效包。
        近似坐标的30／50参照必须处于当前真实支持范围内；直道弯折或
        靠边超出微调能力时撤许可，绝不把直线外推穿过锐角。
        """
        result = dict(valid=False, source='unknown', steering=0, bend=0,
                      confidence=0, support=0, reason='no_pair')
        if len(pixels) != 320 * 240 or not isinstance(now, int) or now < 0:
            self.reset()
            result['reason'] = 'input'
            return result
        timing_ok = self.last_at is None or 0 < now - self.last_at <= 150
        if not timing_ok:
            self.reset()
        self.last_at = now
        threshold = _threshold(pixels)
        black, _, _ = _grid(pixels, threshold)
        points = _pair_anchors(black)
        result.update(threshold=threshold, support=len(points))
        if len(points) < 8:
            self.stable = 0
            self.previous_error = None
            return result
        count = len(points)
        mx = sum(p[0] for p in points) / count
        mz = sum(p[1] for p in points) / count
        low = min(p[1] for p in points)
        high = max(p[1] for p in points)
        denominator = sum((p[1] - mz) ** 2 for p in points)
        slope = sum((p[1] - mz) * (p[0] - mx) for p in points) / max(0.001, denominator)
        near = mx + slope * (30 - mz)
        far = mx + slope * (50 - mz)
        residual = (sum((p[0] - mx - slope * (p[1] - mz)) ** 2 for p in points) / count) ** 0.5
        # 只比较短半段斜率会把6像素网格的一格跳变放大成假折角：
        # 2026-11-18地面第1961帧支持13行、整体残差0.475却因斜率差>0.12停车。
        # 改为比较斜率变化在实际支持跨度内形成的横向弯折量，并限制单点残差。
        # 所有量沿用近似投影代理单位，不冒称已标定厘米；缺半段／跨度不足仍拒绝。
        slopes = []
        half_spans = []
        for half in ([p for p in points if p[1] <= mz], [p for p in points if p[1] > mz]):
            if len(half) < 3:
                continue
            hx = sum(p[0] for p in half) / len(half)
            hz = sum(p[1] for p in half) / len(half)
            den = sum((p[1] - hz) ** 2 for p in half)
            slopes.append(sum((p[1] - hz) * (p[0] - hx) for p in half) / max(0.001, den))
            half_spans.append(max(p[1] for p in half) - min(p[1] for p in half))
        max_residual = max(abs(p[0] - mx - slope * (p[1] - mz)) for p in points)
        slope_delta = abs(slopes[0] - slopes[1]) if len(slopes) == 2 else None
        # 等长V形折线对整段直线的最大偏离约为斜率差×半跨度/4；
        # 这里用该有界几何量筛折角，避免无量纲斜率误差与实际观测长度脱节。
        deflection = slope_delta * min(half_spans) / 4 if slope_delta is not None else None
        result.update(half_slope_delta=slope_delta, bend_deflection=deflection,
                      max_residual=max_residual, half_depth_spans=half_spans)
        result.update(near_error=near, far_error=far, heading_proxy=slope,
                      residual=residual, depth_min=low, depth_max=high)
        gates = (('depth_coverage', low <= 30 and high >= 50 and high - low >= 25),
                 ('position', abs(near) <= 12 and abs(far) <= 18),
                 ('heading', abs(slope) <= 0.35), ('global_fit', residual <= 1.2),
                 ('single_point_fit', max_residual <= 1.8),
                 ('two_halves', len(slopes) == 2 and min(half_spans) >= 8),
                 ('bend_displacement', deflection is not None and deflection <= 1.5))
        failures = [name for name, passed in gates if not passed]
        result['geometry_failures'] = failures
        if failures:
            self.stable = 0
            self.previous_error = None
            result['reason'] = 'outside_straight_envelope'
            return result
        error = max(-1.0, min(1.0, 0.7 * near / 25.0 + 1.2 * slope))
        if self.previous_error is None or abs(error - self.previous_error) > 0.22 or not timing_ok:
            self.stable = 1
            self.stable_at = now
        else:
            self.stable += 1
        self.previous_error = error
        result.update(valid=self.stable >= 3 and now - self.stable_at >= 80,
                      source='current_pair', steering=int(round(error * 1000)),
                      confidence=80, reason='ready' if self.stable >= 3 and now - self.stable_at >= 80 else 'stabilizing')
        return result

# BEGIN straight_protocol.py
"""直道独立v3发送器；帧结构沿用v2，版本隔离避免旧循迹视觉误配。

只允许当前双边直道且bend=0。不发START；STM32仍须车载KEY人工启动。
"""


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

# BEGIN straight_assist_canmv.py
"""直道现场手动入口，默认无动力预览；生成工具另产明确许可的车载副本。

沿用Sensor2／320x240灰度／GH UART2 T11 R12及115200。相机只提供
当前直道许可，任何时候均不发送START。STM32独立限时与KEY负责动作。
启动前先停止旧main脚本，避免两个程序同时占相机或UART；不改main.py。
"""
import gc
import json
import os
import time

ALLOW_DRIVE = False
SHOW_PREVIEW = True
DURATION_MS = 600000


def _open_log():
    """只在SD新建递增日志，不覆盖原件；SD异常抛出并退出。"""
    folder = '/sdcard/straight_logs'
    try:
        os.stat(folder)
    except OSError as exc:
        if not exc.args or exc.args[0] != 2:
            raise
        os.mkdir(folder)
    for index in range(1, 1001):
        name = folder + '/run_%04d.jsonl' % index
        try:
            os.stat(name)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
            return name, open(name, 'w')
    raise RuntimeError('straight log slots exhausted')


def main():
    """主循环不做全赛道模板搜索；逐帧日志保留原始误差与图像处理年龄。

    实际snapshot调用边界不等于曝光时间；板上时序和地面表现仍需实测。
    许可副本不传IDE图像，避免图像传输影响控制。失效立即发无效路径，
    异常／退出尽力发STOP；若发送器也失败，接收端200ms保护仍生效。
    """
    from machine import UART, FPIOA
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.display import Display
    from media.media import MediaManager
    import image
    sensor = uart = sender = log = None
    display = media = False
    try:
        name, log = _open_log()
        print('[STRAIGHT LOG]', name, 'ALLOW_DRIVE', ALLOW_DRIVE, 'NO AUTO START')
        log.write(json.dumps(dict(event='begin', revision='STRAIGHT-V3-2', allow_drive=ALLOW_DRIVE)) + '\n')
        log.flush()
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender = StraightSender(uart.write, ALLOW_DRIVE)
        sender.stop()
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=320, height=240, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False)
        sensor.set_vflip(False)
        display = True
        Display.init(Display.VIRT, width=320, height=240, to_ide=SHOW_PREVIEW)
        media = True
        MediaManager.init()
        sensor.run()
        detector = StraightRoute()
        origin = time.ticks_ms()
        index = 0
        previous = None
        while time.ticks_diff(time.ticks_ms(), origin) < DURATION_MS:
            os.exitpoint()
            started = time.ticks_ms()
            frame = sensor.snapshot(chn=CAM_CHN_ID_0)
            acquired = time.ticks_ms()
            if (frame.width(), frame.height(), frame.format()) != (320, 240, image.GRAYSCALE):
                raise ValueError('actual grayscale frame mismatch')
            pixels = frame.bytearray()
            copied = time.ticks_ms()
            result = detector.update(pixels, time.ticks_diff(started, origin))
            processed = time.ticks_ms()
            packet = sender.path(result, time.ticks_diff(processed, copied), time.ticks_diff(processed, started))
            sent = time.ticks_ms()
            index += 1
            record = dict(result)
            record.update(index=index, elapsed_ms=time.ticks_diff(started, origin),
                          path_sequence=packet[5], wire_valid=bool(packet[6] & 1),
                          acquire_ms=time.ticks_diff(acquired, started), processing_ms=time.ticks_diff(processed, copied),
                          to_send_ms=time.ticks_diff(sent, started),
                          interval_ms=None if previous is None else time.ticks_diff(started, previous))
            previous = started
            log.write(json.dumps(record) + '\n')
            if index % 10 == 0:
                log.flush()
                print('[STRAIGHT]', result['reason'], 'err', result['steering'], 'valid', bool(packet[6] & 1), 'ms', record['to_send_ms'])
            if SHOW_PREVIEW and not ALLOW_DRIVE:
                Display.show_image(frame)
            del pixels, frame
            gc.collect()
    finally:
        if sender is not None:
            try:
                sender.stop()
                time.sleep_ms(10)
            except BaseException as exc:
                print('[STRAIGHT STOP ERROR]', str(exc))
        for name, cleanup in (('sensor', sensor.stop if sensor is not None else None),
                              ('display', Display.deinit if display else None),
                              ('media', MediaManager.deinit if media else None),
                              ('uart', uart.deinit if uart is not None else None),
                              ('log', log.close if log is not None else None)):
            if cleanup is not None:
                try:
                    if name == 'media':
                        time.sleep_ms(100)  # 沿用现有CanMV媒体释放间隔，避免停止相机后立刻释放缓冲。
                    cleanup()
                except BaseException as exc:
                    print('[STRAIGHT CLEANUP ERROR]', name, str(exc))


if __name__ == '__main__':
    main()
