# 语音首弯 v9。等待本地 Go。

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
"""L1独立试跑候选：稀疏灰度网格＋当前二维道路模板，无NumPy/OpenCV。

复用昨晚的道路几何思路，重新限制搜索和内存；不导入或修改T2/BP1。
输入320×240连续灰度缓冲、会话内真实毫秒。当前黑组件、双边／单边关联
和短历史分别输出，不把画外模板当实测。平面横向比例仍未实测，全部输出
都是试跑候选，须先板上计时和现场无动力目视核对，不能称已安全可控。
"""
import math
from array import array

WIDTH = 320
HEIGHT = 240
GRID_STEP=6  # 电脑全量对照保持4；实板合并包显式生成6像素网格以降低已测网格耗时。
GW = WIDTH//GRID_STEP
GH = HEIGHT//GRID_STEP
GY0=(40+GRID_STEP-1)//GRID_STEP
GY1=(228-3)//GRID_STEP+1


def _hypot(x,z):
    """使用MicroPython基础sqrt，不依赖部分固件未提供的math.hypot。"""
    return math.sqrt(x*x+z*z)


def _pixel(x, z):
    """候选地面cm→像素；沿用中央20/40/60cm标定＋未验横向gain48。

    原点在车头投影。返回None代表画外，绝不夹到画面边缘制造假观测。
    这里只复用几何假设，不把一维留出验证外推为全图准确性。
    """
    if z <= 2:
        return None
    y = (7802.22222222222 - 38.11111111111108*z)/(z+15.555555555555546)
    px = 159.5+x*(y+38.11111111111108)/48.
    if not (4 <= px < 316 and 40 <= y < 228):
        return None
    return int(y)//GRID_STEP*GW+int(px)//GRID_STEP


def _point(cx, cz, u, v, s):
    direction = u if s < 0 else v
    return cx+s*direction[0], cz+s*direction[1]


def _template(c, d, yaw, angle):
    """生成双侧偏置折线，左右按行驶方向定义，不按像素左右排序。

    返回投影网格采样／局部中心路线／转向候选。所有模板在启动时预计算，
    运行时只做灰度网格查表，避免在每帧搜索中重复三角函数和大数组。
    """
    u = math.sin(yaw), math.cos(yaw)
    v = math.sin(yaw+angle), math.cos(yaw+angle)
    cx, cz = c*u[1]+d*u[0], -c*u[0]+d*u[1]
    na, nb = (u[1], -u[0]), (v[1], -v[0])
    denominator = 1+u[0]*v[0]+u[1]*v[1]
    ox, oz = (na[0]+nb[0])*25/denominator, (na[1]+nb[1])*25/denominator
    ta = min(0., -cx*u[0]-cz*u[1])
    tb = max(0., -cx*v[0]-cz*v[1])
    pa, pb = _point(cx, cz, u, v, ta), _point(cx, cz, u, v, tb)
    nearest = ta if pa[0]*pa[0]+pa[1]*pa[1] <= pb[0]*pb[0]+pb[1]*pb[1] else tb
    origin = _point(cx, cz, u, v, nearest)
    if origin[0]*origin[0]+origin[1]*origin[1] > 24*24:
        return None
    sides = []
    for sign in (-1, 1):
        cells = set()
        for s in range(-120, 145, 6):
            x,z = _point(cx, cz, u, v, s)
            p = _pixel(x+sign*ox, z+sign*oz)
            if p is not None:
                cells.add(p)
        sides.append(array('H', sorted(cells)))
    if max(len(sides[0]),len(sides[1])) < 9:
        return None
    centers = []
    route = []
    for distance in (8, 16, 24, 32, 40, 48, 56):
        p = _point(cx, cz, u, v, nearest+distance)
        route.append(p)
        index = _pixel(*p)
        if index is not None:
            centers.append(index)
    target = route[3]
    steering = max(-1000, min(1000, round(math.atan2(target[0], max(5., target[1]))/math.radians(55)*1000)))
    return sides, array('H', centers), route, steering, (cx,cz,yaw,angle), (c,d,yaw,angle)


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


def _anchor_distance(t,anchors):
    """参照点到模型两条有向中心射线的距离；不能用无限延长线穿过内角。"""
    cx,cz,yaw,angle=t[4]; u=(math.sin(yaw),math.cos(yaw)); v=(math.sin(yaw+angle),math.cos(yaw+angle))
    distances=[]
    for x,z,_ in anchors:
        dx,dz=x-cx,z-cz
        a=min(0.,dx*u[0]+dz*u[1]); b=max(0.,dx*v[0]+dz*v[1])
        distances.append(min(_hypot(dx-a*u[0],dz-a*u[1]),_hypot(dx-b*v[0],dz-b*v[1])))
    return sum(distances)/len(distances) if distances else 0


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


def send_voice_start(sender, path_packet):
    """发送一次与刚发PATH序号绑定的Go。调用者先检查当前路径可用于起步。"""
    if not sender.allow_drive or not path_packet[6] & 1:
        raise ValueError('START requires a valid current PATH')
    data = bytes((0xa5, 0x5a, sender.wire_version, 2, 12, sender.cmd_seq,
                  0, 0, path_packet[5], 0, 0, 0, 0, 0, 0, 0, 1, 0))
    sender.cmd_seq = (sender.cmd_seq + 1) & 255
    return sender._send(data + struct.pack('<H', crc16(data)))

# BEGIN right_angle_racing.py
"""从T2二维折角生成外入、切弯、外出的圆弧候选，不强制沿道路中线。

几何沿用T2的入／出射线及法向偏置，移除桌面NumPy/OpenCV依赖。
单位均为现有投影代理单位，30半径／5偏置／14轮距是待实跑细调参数，
不能称全图厘米标定或已经证明车辆包络不触线。只在当前边界有支持时调用。
"""
import math

RACING_RADIUS = 30.0
RACING_OUTSET = 5.0
RACING_TRACK = 14.0  # 名义控制轮距代理量；未归档实测，不当作硬件尺寸事实。


def _racing_point(distance, radius, outset):
    """按连续弧长返回局部路线点(x,z)，坐标及弧长均为投影代理单位。

    distance=0是入弯直线与圆弧的切点；负值在入口直道，正值先走圆弧，
    超过四分之一圆周后进入出口直道。三个区间位置／切向连续，不按离散
    点号跳转，也不把相机看到角点等同于车辆已经到达入弯点。
    """
    tangent = outset-radius
    arc_length = radius*math.pi/2
    if distance < 0:
        return -outset, tangent+distance
    if distance <= arc_length:
        angle = distance/radius
        return radius-outset-radius*math.cos(angle), tangent+radius*math.sin(angle)
    return radius-outset+distance-arc_length, outset


def racing_route(parameters, include_nominal=True):
    """返回当前模型的推荐线、差速请求及圆弧曲率，右正。

    parameters=(cx,cz,yaw,angle)来自当前观测模板；先外侧准备，再用圆弧
    连接两条路段。先把车头原点投影到入口直线／圆弧／出口直线，取真正
    最近点的连续弧长，再前视24代理单位。避免旧离散最近点带来的4单位
    跳动，更不使用角点纵距55..15强制施加30%..65%右转。
    返回路线、差速千分比、最近点阶段及距离；差速比≈轮距*x/(x²+z²)。
    左右符号由当前路线决定；只有调用方已确认的当前路径才能授予许可。
    不使用KEY后的累计时间，未知角度返回None，几何仍未标定为实际厘米。
    """
    cx,cz,yaw,angle = parameters
    if abs(angle-math.pi/2) > 0.01:
        return None
    u=(math.sin(yaw),math.cos(yaw)); n=(u[1],-u[0])
    radius=RACING_RADIUS; offset=RACING_OUTSET
    # 车辆原点在入弯道路局部坐标中的位置。比较三段的最近候选，不能仅
    # 根据角点在相机坐标中的cz判断何时转弯；车头已经偏转时cz尤其不足。
    qx = -cx*n[0]-cz*n[1]
    qz = -cx*u[0]-cz*u[1]
    tangent=offset-radius
    arc_length=radius*math.pi/2
    angle_on_arc=max(0.0,min(math.pi/2,math.atan2(qz-tangent,radius-offset-qx)))
    choices=((min(0.0,qz-tangent),(-offset,min(qz,tangent))),
             (radius*angle_on_arc,(radius-offset-radius*math.cos(angle_on_arc),
                                   tangent+radius*math.sin(angle_on_arc))),
             (arc_length+max(0.0,qx-(radius-offset)),(max(qx,radius-offset),offset)))
    nearest_distance, _ = min(choices,key=lambda item:(item[1][0]-qx)**2+(item[1][1]-qz)**2)
    phase='entry' if nearest_distance<0 else ('arc' if nearest_distance<arc_length else 'exit')
    route=[]
    for ahead in (8,16,24,32,40,48,56):
        x,z=_racing_point(nearest_distance+ahead,radius,offset)
        route.append((cx+x*n[0]+z*u[0],cz+x*n[1]+z*u[1]))
    # 完整名义线只用于离线图示／包络检查，车载逐帧计算直接使用上方7点。
    points=[]
    if include_nominal:
        local=[]
        for along in range(-140,int(tangent),4):
            local.append((-offset,float(along)))
        for degree in range(0,91,5):
            a=math.radians(degree)
            local.append((radius-offset-radius*math.cos(a),offset-radius+radius*math.sin(a)))
        for along in range(int(radius-offset)+4,146,4):
            local.append((float(along),offset))
        points=[(cx+x*n[0]+z*u[0],cz+x*n[1]+z*u[1]) for x,z in local]
    x,z=route[2]
    ratio=RACING_TRACK*x/max(25.0,x*x+z*z)
    ratio=max(-0.65,min(0.65,ratio))
    return dict(route=route,nominal_path=points,steering=int(round(ratio*1000)),radius=radius,
                outset=offset,lookahead=24,geometry_calibrated=False,phase=phase,
                projection_s=nearest_distance,entry_distance=max(0.0,-nearest_distance))

# BEGIN right_angle_grid.py
"""首弯网格：只剥离上沿厚背景，保留与背景偶然接触的细长赛道边。

沿用既有6像素采样／组件／一格容差，不改直道或旧整圈模块的_grid。
修复实图run_0007_loss_03：ROI黑墙与L形边界连接后，旧版删除整个组件，
真实左边和前横边同时变成0。新版本只删上沿连通的厚核及一格外扩。
"""
from array import array


def _peel_background(black, component):
    """从ROI上沿的3x3实黑厚核出发，只删除厚背景本体。

    细长黑边即便与墙有单格连接，也不能把整条边升级为厚背景；其余位置
    的厚核（例如近处较宽的胶带）不靠细桥连到上沿厚核，不会跟着被删除。
    不制造任何新黑像素；原始PGM和去背景黑格分开，可复现真实支持。
    """
    core=set()
    for index in component:
        x=index%GW; y=index//GW
        if not (1<=x<GW-1 and GY0<y<GY1-1):continue
        if all(black[index+dy*GW+dx] for dy in (-1,0,1) for dx in (-1,0,1)):
            core.add(index)
    queue=[index for index in core if index//GW<=GY0+2]
    wall=set(queue);at=0
    while at<len(queue):
        index=queue[at];at+=1
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                other=index+dy*GW+dx
                if other in core and other not in wall:
                    wall.add(other);queue.append(other)
    for index in component:
        if any(index+dy*GW+dx in wall for dy in (-1,0,1) for dx in (-1,0,1)):
            black[index]=0


def corner_grid(pixels, threshold):
    """输入320x240灰度及阈值，返回当前黑格／容差网格／组件标签。

    4点至少2黑才采黑；小于3格的噪声组件仍拒绝。一格扩张只用于模型
    采样容差，不充作真实黑边。所有容器大小受320x240网格固定上界限制。
    """
    black=bytearray(GW*GH);labels=array('H',[0]*(GW*GH))
    for gy in range(GY0,GY1):
        for gx in range(1,GW-1):
            p=gy*GRID_STEP*320+gx*GRID_STEP
            black[gy*GW+gx]=int((int(pixels[p]<=threshold)+int(pixels[p+2]<=threshold)+
                int(pixels[p+640]<=threshold)+int(pixels[p+642]<=threshold))>=2)
    number=0
    for start in range(GY0*GW,GY1*GW):
        if not black[start] or labels[start]:continue
        number+=1;labels[start]=number;queue=[start];at=0;top=0
        while at<len(queue):
            index=queue[at];at+=1;x=index%GW;y=index//GW
            if y==GY0:top+=1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nx=x+dx;ny=y+dy
                    if not (0<=nx<GW and GY0<=ny<GY1):continue
                    other=ny*GW+nx
                    if black[other] and not labels[other]:
                        labels[other]=number;queue.append(other)
        if len(queue)<3:
            for index in queue:black[index]=0
        elif top>120//GRID_STEP and len(queue)>4000//(GRID_STEP*GRID_STEP):
            _peel_background(black,queue)
    expanded=bytearray(GW*GH);near_labels=array('H',[0]*(GW*GH))
    for index in range(GY0*GW,GY1*GW):
        if not black[index]:continue
        x=index%GW;y=index//GW
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if 0<=x+dx<GW and 0<=y+dy<GH:
                    other=index+dy*GW+dx;expanded[other]=1
                    if not near_labels[other]:near_labels[other]=labels[index]
    return black,expanded,near_labels

# BEGIN right_angle_prediction.py
"""从当前灰度网格重估首弯外边；坐标沿用现有地面投影代理单位。"""
import math

# 持续单侧证据和瞬时白走廊的上限分别核对；低置信度帧不能续租强观测。
PREDICTION_ANCHOR_MS = 1200
PREDICTION_GAP_MS = 240


def _project_row(gy):
    y = gy * GRID_STEP + 1
    return ((7802.22222222222 - 15.555555555555546 * y) / (y + 38.11111111111108),
            48.0 / (y + 38.11111111111108))


def _left_rail(black):
    """在近区多行找细黑边与它右侧的白区，拟合车道左边直线。

    使用未扩张黑格求中心；平行背景或断裂噪声不能用一个采样点参与拟合。
    返回行驶方向、法向偏移和最远实测投影。单靠此结果不会确认新弯。
    """
    samples = []
    rows = range((108 + GRID_STEP - 1) // GRID_STEP, 216 // GRID_STEP, 18 // GRID_STEP)
    for gy in rows:
        base = gy * GW
        start = None
        for gx in range(1, GW - 4):
            if black[base + gx]:
                if start is None:
                    start = gx
            elif start is not None:
                if 2 <= gx - start <= 60 // GRID_STEP and not any(black[base + gx:base + gx + 4]):
                    z, scale = _project_row(gy)
                    x = ((start + gx - 1) * GRID_STEP / 2 + 1 - 159.5) * scale
                    samples.append((x, z))
                    break
                start = None
    if len(samples) < 4:
        return None
    dx, dz = samples[0][0] - samples[-1][0], samples[0][1] - samples[-1][1]
    length = math.sqrt(dx * dx + dz * dz)
    if length < 8:
        return None
    ux, uz = dx / length, dz / length
    yaw = math.atan2(ux, uz)
    offsets = [uz * x - ux * z for x, z in samples]
    offset = sum(offsets) / len(offsets)
    if not (-48 <= offset <= -8 and -1.3 <= yaw <= 0.44 and max(offsets) - min(offsets) <= 4):
        return None
    return ux, uz, yaw, offset, max(ux * x + uz * z for x, z in samples)


def fitted_outer_l(black, occupied, template):
    """用左纵边和前方横边的当前像素求交，再返回已检验的90度模板或None。

    横边沿左边方向的投影应近似等长，按4代理单位归桶。用不同横向
    区段计票，并验证实际连接处、两臂覆盖和内侧白区。网格和候选数有界。
    """
    rail = _left_rail(black)
    if rail is None:
        return None
    ux, uz, yaw, offset, last = rail
    votes = {}
    first_row = max(GY0 + 3, (60 + GRID_STEP - 1) // GRID_STEP)
    for gy in range(first_row, min(GY1, 162 // GRID_STEP)):
        base = gy * GW
        z, scale = _project_row(gy)
        for gx in range(1, GW - 1):
            if not black[base + gx]:
                continue
            x = (gx * GRID_STEP + 1 - 159.5) * scale
            lateral = uz * x - ux * z - offset
            along = ux * x + uz * z
            if 8 <= lateral <= 85 and 5 <= along - last <= 90:
                key = round(along / 4)
                votes[key] = votes.get(key, 0) | (1 << int(lateral / 5))
    # 每个桶最多17个横向区段；用定宽掩码，避免为每个黑格分配集合。
    ranked = [(bin(mask).count('1'), key) for key, mask in votes.items()]
    ranked.sort(reverse=True)
    for support, key in ranked[:3]:
        if support < 6:
            break
        along = key * 4
        join = _pixel(offset * uz + along * ux, -offset * ux + along * uz)
        if join is None or not occupied[join]:
            continue
        candidate = template(offset + 25, along - 25, yaw, math.pi / 2)
        if candidate is None:
            continue
        arms = candidate[6][:2]
        if (all(len(arm) >= 3 and sum(occupied[i] for i in arm) >= 0.70 * len(arm) for arm in arms)
                and len(candidate[8]) >= 4 and sum(black[i] for i in candidate[8]) <= len(candidate[8]) // 5
                and not any(black[i] for i in candidate[1])):
            return candidate
    return None


def fitted_left_forecast(black, previous, template):
    """只见左边时重估横向偏差和朝向，沿用最近模型的弯点纵向位置。

    当前纵边无法单独推断前方弯点，因此仅用于短程预测，不能续租双边/L形。
    """
    rail = _left_rail(black)
    if rail is None:
        return None
    ux, uz, yaw, offset, _ = rail
    cx, cz, _, angle = previous[4]
    return template(offset + 25, cx * ux + cz * uz, yaw, angle)


def fitted_front_edge(black, previous, template):
    """已知右弯后，沿预期前横线的法向取样，逐帧重估前线距离和角度。

    单条线约束方向和法向距离。弯心沿线坐标沿用上次模型，直到新双侧可见。
    采样只看当前未扩张黑格，隔开墙面上沿；输出代理坐标与实测格数。
    """
    c, d, yaw, angle = previous[5]
    ux, uz = math.sin(yaw), math.cos(yaw)
    depth = d + 25
    samples = []
    used = set()
    for across in range(round(c) - 17, round(c) + 61, 7):
        for shift in (0, -3, 3, -6, 6, -9, 9, -12, 12, -15, 15):
            forward = depth + shift
            cell = _pixel(across * uz + forward * ux, -across * ux + forward * uz)
            if cell is None or cell // GW < GY0 + 3 or not black[cell]:
                continue
            if cell not in used:
                used.add(cell)
                samples.append((across, forward))
            break
    if len(samples) < 5 or samples[-1][0] - samples[0][0] < 28:
        return None
    mean_across = sum(p[0] for p in samples) / len(samples)
    mean_depth = sum(p[1] for p in samples) / len(samples)
    variance = sum((p[0] - mean_across) ** 2 for p in samples)
    slope = sum((p[0] - mean_across) * (p[1] - mean_depth) for p in samples) / variance
    if abs(slope) > 0.45 or max(abs(z - mean_depth - slope * (x - mean_across)) for x, z in samples) > 6:
        return None
    change = -math.atan(slope)
    updated_yaw = yaw + change
    if not -math.radians(105) <= updated_yaw <= math.radians(30):
        return None
    front = mean_depth * math.cos(change) + mean_across * math.sin(change)
    updated_c = c * math.cos(change) - d * math.sin(change)
    candidate = template(updated_c, front - 25, updated_yaw, angle)
    if candidate is None:
        return None
    return candidate, len(samples), front


def clear_predicted_corridor(pixels, black, threshold, route):
    """检查最靠近车的四个可见路线格，相机近端盲区的不计入。"""
    cells = set()
    for point in route:
        cell = _pixel(*point)
        if cell is None or cell in cells:
            continue
        x, y = cell % GW * GRID_STEP + 1, cell // GW * GRID_STEP + 1
        if black[cell] or pixels[y * 320 + x] <= threshold:
            return False
        cells.add(cell)
        if len(cells) == 4:
            return True
    return len(cells) >= 3

# BEGIN right_angle_route.py
"""首个直角弯：只搜索直道与顺时针90度右弯，不按时间排定转弯。

320x240灰度输入，复用既有近似地面投影／网格／黑块组件。每帧重新
检查黑边、白走廊及局部路线关联。上一模型只缩小搜索范围，不能
代替当前像素支持；当前左纵／前横L可独立预测右转，普通单直边不能启动。
投影仍是候选代理坐标，不能把模板宽度当作实测车体余量。
"""
import math


def _corner_template(c, d, yaw, angle):
    """附加两侧边界的入／出弯臂采样，单边许可必须实际看到折角两臂。

    不把一根直黑带或全无当前支持的旧模型称作单边转弯证据。
    采样使用与原模板一致的代理投影，未标定部分不生成真实厘米结论。
    """
    t = _template(c, d, yaw, angle)
    if t is None: return None
    cx, cz = t[4][:2]
    u = math.sin(yaw), math.cos(yaw)
    v = math.sin(yaw+angle), math.cos(yaw+angle)
    vectors = (cx, cz, u[0], u[1], v[0], v[1])
    if angle == 0:
        # 单侧转弯许可只使用90度模型；直道不必重复投影四组无用的折角臂。
        return t+(((), (), (), ()), vectors, ())
    den = 1+u[0]*v[0]+u[1]*v[1]
    ox, oz = (u[1]+v[1])*25/den, (-u[0]-v[0])*25/den
    arms = []
    for sign in (-1, 1):
        for direction in (-1, 1):
            cells = set()
            for distance in (6,12,18,24,30,36,42):
                x, z = _point(cx, cz, u, v, direction*distance)
                cell = _pixel(x+sign*ox, z+sign*oz)
                if cell is not None: cells.add(cell)
            arms.append(tuple(cells))
    interior=set()
    for direction in (-1,1):
        normal=(u[1],-u[0]) if direction<0 else (v[1],-v[0])
        for distance in (6,12,18,24,30,36,42):
            x,z=_point(cx,cz,u,v,direction*distance)
            # 向内10代理单位取白区，避开黑带厚度和粗模板数格误差；不补造边界。
            cell=_pixel(x-ox+10*normal[0],z-oz+10*normal[1])
            if cell is not None:interior.add(cell)
    return t+(arms, vectors, tuple(interior))


def _current_anchor_distance(t, anchors):
    """与原双射线距离等价，复用模板方向，逐点只做一次sqrt。

    sqrt单调，因此min(sqrt(a),sqrt(b))等于sqrt(min(a,b))。
    不更改几何门槛或历史条件，避免每候选重复三角函数和中间列表分配。
    """
    cx, cz, ux, uz, vx, vz = t[7]
    total = 0.0
    for x,z,_ in anchors:
        dx = x-cx; dz = z-cz
        a = min(0.0, dx*ux+dz*uz); b = max(0.0, dx*vx+dz*vz)
        ax = dx-a*ux; az = dz-a*uz; bx = dx-b*vx; bz = dz-b*vz
        total += math.sqrt(min(ax*ax+az*az, bx*bx+bz*bz))
    return total/len(anchors) if anchors else 0.0


def _along_exit_edge(t):
    """车头接近出弯方向时，把已跟踪的前线作为出口左边推算中线。"""
    _, d, yaw, _ = t[5]
    if yaw > -math.radians(75):
        return None
    heading = yaw + math.pi/2
    nx, nz = math.cos(heading), -math.sin(heading)
    return [(-d*nx-ahead*nz, -d*nz+ahead*nx) for ahead in (8, 16, 24, 32, 40, 48, 56)]


def _still_has_l(t, black, occupied):
    """复核上一候选的两条外臂和内侧白区，避免冷启动退成单边许可。"""
    if not -math.radians(85) <= t[4][2] <= math.radians(25):
        return False
    side = t[0][0]
    count = sum(occupied[cell] for cell in side)
    return (count >= 12 and count >= .75 * len(side) and len(t[8]) >= 4
            and sum(black[cell] for cell in t[8]) <= len(t[8]) // 5
            and not any(black[cell] for cell in t[1])
            and all(len(arm) >= 3 and sum(occupied[cell] for cell in arm) >= max(3, .65 * len(arm))
                    for arm in t[6][:2]))


class RightAngleRoute:
    """固定有界候选库与局部细化；初始化预计算只执行一次，不驱动车轮。"""
    def __init__(self, predictive=False):
        self.predictive = predictive
        self.clock = None  # 可选板上ticks_ms，只计耗时，不改变几何判断或源年龄。
        self.templates = []
        for angle in (0, 90):
            for yaw in ((-30, -15, 0, 15, 30) if angle == 0 else (-90, -60, -30, 0, 15)):
                for c in (-12, 0, 12):
                    for d in ((50,) if angle == 0 else (0, 10, 20, 40, 60, 80)):
                        t = _corner_template(c, d, math.radians(yaw), math.radians(angle))
                        if t is not None:
                            self.templates.append(t)
        self.reset()

    def reset(self):
        """失线后不保存有效许可；重获必须重新满足3帧／80ms门槛。"""
        self.previous = None
        self.last_at = None
        self.stable = 0
        self.stable_at = 0
        self.search_cursor = 0
        self.neighbor_key = None
        self.neighbors = []
        self.recovery_key = None
        self.recoveries = []
        self.refine_key = None
        self.refinements = []
        self.corner_at = None
        self.forecast_anchor_at = self.visible_edge_at = None
        self.forecast_route = None
        self.front_model = self.front_at = None
        self.racing_key = None
        self.racing = None

    @staticmethod
    def distance(a, b):
        return sum(_hypot(a[2][i][0]-b[2][i][0], a[2][i][1]-b[2][i][1])
                   for i in (0, 2, 4))/3

    def update(self, pixels, now):
        """now为取图开始的会话ms；任何拒绝均返回新无效观测，禁止沿用旧命令。

        双侧模式须不同组件支持同一个模型及当前白色路径。左纵／前横
        L单独确认时，只由当前外边两臂和朝道路内侧的白区预测缺失右边与
        圆弧；中线在近端盲区时仍可预测。出口单直边只允许700ms当前关联。
        同一横黑带不能借两面冒充两侧边界，历史／空白帧不能刷新许可。
        """
        out = dict(valid=False, source='unknown', steering=0, bend=0,
                   confidence=0, support=[0, 0], reason='no_current_pair',
                   stage='unknown', geometry_calibrated=False)
        if len(pixels) != 76800 or not isinstance(now, int) or now < 0:
            self.reset(); out['reason'] = 'input'; return out
        if self.last_at is not None and not 0 < now-self.last_at <= 150:
            self.reset()
        self.last_at = now
        clock = self.clock
        begun = clock() if clock else 0
        threshold = _threshold(pixels)
        black, occupied, labels = corner_grid(pixels, threshold)
        grid_done = clock() if clock else 0
        anchors = _pair_anchors(black)
        anchors_done = clock() if clock else 0
        tracking = self.previous is not None
        quick, front = None, None
        if self.predictive and tracking and not anchors and self.previous[4][3] > 1:
            # 已跟踪的折角先用当前外边直接拟合，节省整组邻居/精化生成。
            # 左臂渐出画后，只关联上帧已确认的前线方向和距离。
            match = fitted_outer_l(black, occupied, _corner_template)
            if match is not None and self.distance(match, self.previous) <= 24:
                quick = match
            elif _still_has_l(self.previous, black, occupied):
                quick = self.previous
            elif self.front_at is not None and now-self.front_at < PREDICTION_GAP_MS:
                match = fitted_front_edge(black, self.front_model, _corner_template)
                if match is not None:
                    front_route = _along_exit_edge(match[0]) or racing_route(match[0][4], include_nominal=False)['route']
                    if clear_predicted_corridor(pixels, black, threshold, front_route):
                        quick, front = match[0], (match[1], match[2])

        def evaluate(t):
            sides, centers = t[0], t[1]
            counts = [sum(occupied[i] for i in side) for side in sides]
            ratios = [counts[j]/max(1, len(sides[j])) for j in (0, 1)]
            if any(black[i] for i in centers):
                return None
            error = _current_anchor_distance(t, anchors) if anchors else 0
            if anchors and error > 10:
                return None
            distance = self.distance(t, self.previous) if self.previous else 0
            if self.previous is not None and distance > 18:
                return None
            dual = len(centers) >= 3 and all(counts[j] >= 4 and ratios[j] >= 0.55 for j in (0, 1))
            if dual:
                ids = [{labels[i] for i in side if occupied[i]} for side in sides]
                dual = bool(ids[0]-ids[1] and ids[1]-ids[0])
            # 直道必须有逐行双边走廊；转弯允许用两条二维边界证明当前支持。
            dual = dual and (bool(anchors) or t[4][3] > 1)
            # 当前左外边的入弯臂＋前方横臂共同证明L形，不要求右侧边界出现，
            # 也不要求此前先得到双侧许可。只有一根直带不满足此判据。
            corner = False
            associated = False
            if t[4][3] > 1 and -math.radians(85) <= t[4][2] <= math.radians(25):
                arms = t[6][:2]  # 只用左外边：左纵边与前方横边，不误用内侧L或文字。
                corner = counts[0] >= 12 and ratios[0] >= 0.75 and all(
                    len(arm)>=3 and sum(occupied[i] for i in arm)>=3
                    and sum(occupied[i] for i in arm)/len(arm)>=0.65 for arm in arms)
                # 中线可能在相机近端盲区，但L的两条边朝道路内侧必须有当前白区。
                # 这仍是当前形状证据，不能用旧图或一根黑直线填补全部视野。
                corner = corner and len(t[8])>=4 and sum(black[i] for i in t[8])<=len(t[8])//5
                # 转弯后仅剩当前出口边时，用上一已确认L的角色作短期关联。
                # 当前仍需12个支持格及白色路径，最多700ms，空白从不续行。
                associated = (not corner and self.corner_at is not None and now-self.corner_at < 700
                    and self.previous is not None and distance<12 and counts[0]>=12 and ratios[0]>=0.75)
            # 没有可见中线时，未通过当前L／当前出口支持的模型仅作精化种子，
            # 不能成为有效路径；否则近端盲区会在粗搜阶段把正确角点邻域一起删掉。
            # 样本仅一格的画外短边不能凭100%命中率压过真正有多点支持的模型。
            score = sum(min(ratios[j], counts[j]/4) for j in (0, 1))
            score += min(sum(counts), 35)*0.018-error*0.10-distance*0.025
            # 出口直线与画外角点模型可能同样解释当前两条直边；优先简单直线，
            # 防止把不可见角点当作仍须大差速的转弯证据。
            if t[4][3] > 1: score -= 0.12
            if dual: score += 0.5
            elif corner: score += 0.3
            return score, dual, (2 if corner else (1 if associated else 0)), counts

        if quick is not None:
            pool = []
        elif tracking:
            c, d, yaw, angle = self.previous[5]
            if self.neighbor_key != self.previous[5]:
                self.neighbor_key = self.previous[5]
                self.neighbors = []
                for dc, dd, dy in ((-3,0,0),(3,0,0),(0,-4,0),(0,4,0),(0,0,-5),(0,0,5)):
                    t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                    if t is not None: self.neighbors.append(t)
            pool = [self.previous]
            pool.extend(self.neighbors)
            # 正常帧只验证上次模型及6个邻居，并滚动查看12个当前粗候选。
            # 仅复用预计算几何，不保留旧像素分数；新的弯道仍能随当前图像进入搜索。
            # 已有模型时不再每帧遍历全库并重建27个细化模板，减少源年龄空档。
            for _ in range(min(12, len(self.templates))):
                pool.append(self.templates[self.search_cursor])
                self.search_cursor = (self.search_cursor+1) % len(self.templates)
        else:
            # 启动／失线重获保留原全库搜索；未经当前支持和稳定门不授予运动许可。
            pool = list(self.templates)
        seeds = []
        best = quick
        best_score = 2.0 if quick is not None else -1e9
        support = [sum(occupied[i] for i in side) for side in quick[0]] if quick is not None else [0, 0]
        best_dual = False
        best_corner = 2 if quick is not None and front is None else 0
        for t in pool:
            candidate = evaluate(t)
            if candidate is None: continue
            score, dual, single, counts = candidate
            seeds.append((score, t))
            if (dual or single) and score > best_score:
                best, best_score, support = t, score, counts
                best_dual = dual
                best_corner = single
        recovery = 0
        if tracking and best is None:
            # 真实1315→1316帧需要c/d同时变化；六个轴向邻居都失配时，先查8个
            # 耦合邻居再全库重获。仅失败帧构建它们，避免每个正常帧增加投影耗时，
            # 导致处理超过100ms反而撤销许可。每个候选仍走完全相同的当前证据门。
            c,d,yaw,angle=self.previous[5]
            if self.recovery_key != self.previous[5]:
                self.recovery_key=self.previous[5]
                self.recoveries=[]
                offsets=[(dc,dd,0) for dc in (-3,3) for dd in (-4,4)]
                offsets += [(0,dd,dy) for dd in (-4,4) for dy in (-5,5)]
                for dc,dd,dy in offsets:
                    t=_corner_template(c+dc,d+dd,yaw+math.radians(dy),angle)
                    if t is not None:self.recoveries.append(t)
            for t in self.recoveries:
                recovery += 1
                candidate=evaluate(t)
                if candidate is None:continue
                score,dual,single,counts=candidate
                seeds.append((score,t))
                if (dual or single) and score>best_score:
                    best,best_score,support=t,score,counts
                    best_dual=dual;best_corner=single
        forecast = 3 if front is not None else 0
        fitted = quick is not None
        if self.predictive and not best_dual and not fitted:
            # 右边出画时，直接用当前左纵／前横交点补充离散库。当前两臂拟合
            # 成功便跳过整库重扫与27点精化，给测到过峰值的K230留出时间。
            match = fitted_outer_l(black, occupied, _corner_template)
            if (match is not None and (not anchors or _current_anchor_distance(match, anchors) <= 10)
                    and (not tracking or self.distance(match, self.previous) <= 24)):
                best, best_score = match, 2.0
                support = [sum(occupied[i] for i in side) for side in best[0]]
                best_corner = 2
                fitted = True
            elif self.forecast_anchor_at is not None and now-self.forecast_anchor_at < PREDICTION_ANCHOR_MS:
                # 降级时依次尝试当前单边和短时白走廊。单边重新计算模型；
                # 白走廊只沿最近路线短时前进，不从空白画面生成新转弯。
                if best_corner == 1:
                    forecast = 1
                elif best is None:
                    left_fit = fitted_left_forecast(black, self.previous, _corner_template)
                    if (left_fit is not None and self.distance(left_fit, self.previous) < 12
                            and len(left_fit[1]) >= 4 and not any(black[i] for i in left_fit[1])):
                        best, forecast = left_fit, 1
                        support = [sum(occupied[i] for i in side) for side in best[0]]
                    else:
                        for _, t in sorted(seeds, key=lambda item: -item[0])[:8]:
                            if len(t[1]) < 4 or self.distance(t, self.previous) >= 12:
                                continue
                            counts = [sum(occupied[i] for i in side) for side in t[0]]
                            if any(count >= 9 and count >= 0.62 * len(side) and sum(black[i] for i in side) >= 3
                                   for count, side in zip(counts, t[0])):
                                best, support, forecast = t, counts, 1
                                break
                    if (best is None and self.visible_edge_at is not None
                            and now-self.visible_edge_at < PREDICTION_GAP_MS
                            and clear_predicted_corridor(pixels, black, threshold, self.forecast_route)):
                        best, forecast = self.previous, 2
        fallback = 0
        if tracking and best is None:
            # 局部支持不足时同帧回到完整当前搜索，不能因为滚动库本帧没扫到
            # 邻近新几何而人为制造失线。所有旧关联／单侧／白路面门保持。
            for t in self.templates:
                # K230运行时搜索达到本帧预算就结束，给封包和串口留余量。
                if self.predictive and clock and clock()-begun >= 78:
                    break
                fallback += 1
                candidate = evaluate(t)
                if candidate is None: continue
                score, dual, single, counts = candidate
                seeds.append((score, t))
                if (dual or single) and score > best_score:
                    best, best_score, support = t, score, counts
                    best_dual = dual
                    best_corner = single
        seeds.sort(key=lambda item: -item[0])
        refined = 0
        # 几何精化保持原27点；只缓存当前seed的预计算模板，分数仍逐帧重算。
        # seed不变时不再每帧重新计算三角函数／投影／折角臂；缓存大小固定。
        for _, seed in (() if fitted or forecast else seeds[:1]):
            c, d, yaw, angle = seed[5]
            if self.refine_key != seed[5]:
                self.refine_key = seed[5]
                self.refinements = []
                offsets = [(dc,dd,dy) for dc in (-6,0,6)
                           for dd in ((0,) if angle == 0 else (-10,0,10)) for dy in (-10,0,10)]
                for dc,dd,dy in offsets:
                    if self.predictive and tracking and clock and clock()-begun >= 78:
                        self.refine_key = None  # 尚未构完，下一帧可补足。
                        break
                    t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                    if t is not None: self.refinements.append(t)
            for t in self.refinements:
                if self.predictive and tracking and clock and clock()-begun >= 84:
                    break
                refined += 1
                candidate = evaluate(t)
                if candidate is None: continue
                score, dual, single, counts = candidate
                if (dual or single) and score > best_score:
                    best, best_score, support = t, score, counts
                    best_dual = dual
                    best_corner = single
        out.update(support=support, searched_candidates=len(pool)+recovery+fallback+refined,
                   recovery_candidates=recovery,
                   anchors=len(anchors), search_mode='fallback' if fallback else ('tracking' if tracking else 'acquire'))
        if clock:
            out['profile_ms'] = dict(grid=grid_done-begun, anchors=anchors_done-grid_done,
                                     search=clock()-anchors_done)
        if best is None:
            self.reset()
            self.last_at = now
            return out
        if self.previous is None:
            self.stable = 1; self.stable_at = now
        else:
            self.stable += 1
        self.previous = best
        cx, cz, yaw, angle = best[4]
        if best_corner == 2:
            self.corner_at = now
        if angle == 0 or (yaw <= -math.radians(75) and cz < 10):
            risk = 0
            stage = 'straight' if angle == 0 else 'exit'
        else:
            # 远处先降速；当角点接近或车头已转入弯内时持续低速。
            # 这些量来自当前模板，不是从人工KEY开始累计的转弯时刻。
            risk = max(0.0, min(1.0, (85-cz)/45))
            if yaw < -math.radians(15): risk = 1.0
            stage = 'approach' if cz > 40 and yaw > -math.radians(15) else 'turn'
        valid = self.stable >= 3 and now-self.stable_at >= 80
        if not best_dual and not forecast: risk = 1.0
        # 直道沿用32点误差；有90度几何时下方改用外入切弯圆弧和24点纯追踪。
        target = best[2][6] if risk > 0 else best[2][3]
        steering = max(-1000, min(1000, round(math.atan2(target[0], max(5, target[1]))/math.radians(55)*1000)))
        route = best[2]
        if angle > 1 and not (yaw <= -math.radians(75) and cz < 10):
            if self.racing_key != best[4]:
                self.racing_key = best[4]; self.racing = racing_route(best[4], include_nominal=not self.predictive)
            if self.racing is not None:
                route = self.racing['route']; steering = self.racing['steering']
                out['racing_radius'] = self.racing['radius']; out['racing_outset'] = self.racing['outset']
                out['racing_phase'] = self.racing['phase']
                out['arc_entry_distance'] = self.racing['entry_distance']
                out['route_projection_s'] = self.racing['projection_s']
                stage = 'approach' if self.racing['phase']=='entry' else ('turn' if self.racing['phase']=='arc' else 'exit')
        source = 'current_pair' if best_dual else ('current_corner_predicted' if best_corner == 2 else 'current_corner_associated')
        confidence = 75 if best_dual else (60 if best_corner == 2 else 45)
        if self.predictive and not best_dual and best_corner != 2 and not forecast:
            # 全库重获/精化也可能找到旧式出口单边。和直接找到的单边使用同一时限。
            if self.forecast_anchor_at is None or now-self.forecast_anchor_at >= PREDICTION_ANCHOR_MS:
                forecast = 0
                valid = False
            else:
                forecast = 1
        if forecast:
            # 前方白区有支持才下发预测。暂时无边线只延续已有路线，不更新边线时钟。
            if forecast == 3:
                source, confidence = 'current_front_forecast', 58
                out.update(front_support=front[0], front_distance=front[1])
                exit_route = _along_exit_edge(best)
                if exit_route is not None:
                    # 原横线已转成沿行驶方向的左边。用它的法向偏移和新朝向回正。
                    route = exit_route
                    x, z = route[3]
                    steering = max(-1000, min(1000, round(math.atan2(x, max(5, z))/math.radians(55)*1000)))
                    stage, risk = 'exit', 0.0
            elif forecast == 1:
                source, confidence = 'current_single_forecast', 55
            else:
                source, confidence = 'short_corridor_forecast', 45
                route = self.forecast_route
            valid = valid and clear_predicted_corridor(pixels, black, threshold, route)
        elif not best_dual:
            # v5单侧L／弱关联只允许右转或直行，不扩大协议到未经确认的左转。
            # 推荐点仍在入口直道时不额外给10%右转；真正到达圆弧后，右转量
            # 由连续路线自然增大。双侧路径保留有符号修正，允许及时回正。
            steering = max(0,steering)
        if self.predictive and valid:
            if not forecast or forecast == 3:
                self.forecast_anchor_at = now
                if angle > 1 and (best_corner == 2 or forecast == 3 or round(risk*1000) >= 200):
                    self.front_model, self.front_at = best, now
                else:
                    self.front_model = self.front_at = None
            if forecast != 2:
                self.visible_edge_at = now
                self.forecast_route = route
        # R7实跑出现100→371及负修正→508的切换，来自距离下限覆盖路线。
        # R8取消该下限；留0字段便于与旧逐帧证据比较，不以历史L强行续转。
        out['turn_floor'] = 0
        out.update(valid=valid, source=source, steering=steering,
                   bend=int(round(risk*1000)), confidence=confidence, stage=stage,
                   corner_observed=best_corner==2, corner_age_ms=0 if self.corner_at is None else now-self.corner_at,
                   measured_edges=('none' if forecast == 2 else 'front' if forecast == 3 else 'single' if forecast == 1 else
                                   'left_and_front' if best_corner == 2 else 'pair' if best_dual else 'associated_left'),
                   path_kind='racing_arc_prediction' if angle>1 else 'straight_observation',
                   path_visibility='projected' if best[1] else 'predicted_near_blind',
                   parameters=list(best[4]), route=route, score=best_score,
                   reason='ready' if valid else 'stabilizing')
        return out

# BEGIN right_angle_protocol.py
"""首弯v5：双侧、当前L形预测、短时出口关联分别编码，不发START。"""
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
            valid=valid and result.get('corner_observed') is True and bend==1000 and steering>=0 and quality>=60
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

# BEGIN voice_keywords.py
"""K230 ??????????????????????????"""
import time

RATE = 16000
CHUNK = 4800  # 已有KWS模型每次输入300ms单声道PCM。
CHUNK_MS = 300
WAVDIR = '/sdcard/examples/utils/'
REPLIES = ('', 'wozai.wav', 'go_new.wav', 'stop_new.wav', 'wow_new.wav')
READY_REPLY = 1  # 复用已有的“我在”语音，不额外分发WAV。
GO = 2
STOP = 3

class VoiceKeywords:
    """沿用现有KPU模型、MIC增益、分类及右声道功放。模型和Audio均由本脚本独占。"""

    def __init__(self, mapping):
        from machine import Pin, FPIOA
        from media.pyaudio import PyAudio, paInt16, LEFT_RIGHT
        import media.wave as wave
        import nncase_runtime as nn
        import ulab.numpy as np
        import aidemo
        import struct

        self.wave, self.nn, self.np = wave, nn, np
        self.aidemo, self.struct = aidemo, struct
        self.input = self.output = self.fp = self.kpu = self.amp = None
        self.last = 0
        self.go_ready = False  # 上电或播报后先听到背景，防重复触发或把扬声器当发令。
        self.ignore_until = None
        self.audio = PyAudio()
        try:
            for name in REPLIES[1:]:
                wav = self.open_reply(name)
                wav.close()
            nn.shrink_memory_pool()
            self.fp = aidemo.kws_fp_create()
            self.kpu = nn.kpu()
            self.kpu.load_kmodel('/sdcard/examples/kmodel/multi_kws.kmodel')
            self.cache = np.zeros((1, 256, 105), dtype=np.float)
            mapping.set_function(10, FPIOA.GPIO10)
            self.amp = Pin(10, Pin.OUT, pull=Pin.PULL_NONE, drive=7)
            self.amp.value(1)
            self.input = self.audio.open(format=paInt16, channels=1, rate=RATE,
                                         input=True, frames_per_buffer=CHUNK)
            self.output = self.audio.open(format=paInt16, channels=2, rate=RATE,
                                          output=True, frames_per_buffer=CHUNK)
            self.input.volume(40)
            self.output.volume(100, LEFT_RIGHT)
        except BaseException:
            self.close()
            raise

    def open_reply(self, name):
        wav = self.wave.open(WAVDIR + name, 'rb')
        if (wav.get_framerate(), wav.get_sampwidth(), wav.get_channels()) != (RATE, 2, 1):
            wav.close()
            raise ValueError('Invalid reply WAV: ' + name)
        return wav

    def poll(self):
        """最多读取一块，CanMV v1.8短等待10ms。返回新命中标签，0代表没有命令。"""
        pcm = self.input.read(block=False)
        if self.ignore_until is not None:
            if time.ticks_diff(time.ticks_ms(), self.ignore_until) >= 0:
                self.ignore_until = None
            return 0  # 继续取出并丢弃播报及尾音采样，保持麦克风队列新鲜。
        if pcm is None:
            return 0
        if len(pcm) != CHUNK * 2:
            raise ValueError('Unexpected KWS PCM frame length')
        samples = [self.struct.unpack_from('<h', pcm, offset)[0] for offset in range(0, len(pcm), 2)]
        mean = sum(samples) / CHUNK
        normalized = [sample - mean for sample in samples]
        features = self.aidemo.kws_preprocess(self.fp, normalized)[0]
        self.kpu.set_input_tensor(0, self.nn.from_numpy(self.np.array(features).reshape((1, 30, 40))))
        self.kpu.set_input_tensor(1, self.nn.from_numpy(self.cache))
        self.kpu.run()
        logits = self.kpu.get_output_tensor(0).to_numpy()
        self.cache = self.kpu.get_output_tensor(1).to_numpy()
        scores = self.np.max(logits, axis=1)[0]
        label = int(self.np.argmax(scores)) if float(self.np.max(scores)) > 0.5 else 0
        previous = self.last
        self.last = label
        if label == 0:
            self.go_ready = True
        if label == GO:
            ready = self.go_ready
            self.go_ready = False
            return GO if ready else 0
        return label if label != previous else 0

    def play(self, label):
        """仅在没有活跃运行窗口或刚发STOP后调用，因为WAV及扬声器可阻塞。"""
        wav = self.open_reply(REPLIES[label])
        started = time.ticks_ms()
        frames = 0
        try:
            pcm = wav.read_frames(CHUNK)
            while pcm:
                # 输出设备要求整块大小，末块补零；沿用已有单声道转右路的接法。
                stereo = bytearray(CHUNK * 4)
                for sample_at in range(0, len(pcm), 2):
                    stereo[sample_at * 2 + 2:sample_at * 2 + 4] = pcm[sample_at:sample_at + 2]
                if self.output.write(stereo) != 0:
                    raise OSError('Speaker write failed')
                frames += 1
                self.input.read(block=False)
                pcm = wav.read_frames(CHUNK)
        finally:
            wav.close()
        self.cache = self.np.zeros((1, 256, 105), dtype=self.np.float)
        self.last = 0
        self.go_ready = False
        remaining = max(0, frames * CHUNK_MS - time.ticks_diff(time.ticks_ms(), started))
        self.ignore_until = time.ticks_add(time.ticks_ms(), remaining + CHUNK_MS * 2)

    def close(self):
        """逐项释放资源，设备清理失败时仍继续关功放及销毁特征提取器。"""
        actions = []
        for stream in (self.input, self.output):
            if stream is not None:
                actions.extend((stream.stop_stream, stream.close))
        actions.append(self.audio.terminate)
        if self.amp is not None:
            actions.append(lambda: self.amp.value(0))
        if self.fp is not None:
            actions.append(lambda: self.aidemo.kws_fp_destroy(self.fp))
        for action in actions:
            cleanup(action)
        self.kpu = self.cache = None


def cleanup(action):
    try:
        action()
    except BaseException as exc:
        print('[VOICE CLEANUP]', repr(exc))

# BEGIN right_angle_phone.py
"""手机浏览器的只读首弯画面。相机与路线计算由主循环拥有。"""
import json
import time

PHONE_PORT = 8080
# 目标约12帧/秒；仍在每次控车循环最多发送一次，慢连接不会忙等。
PHONE_INTERVAL_MS = 83
PHONE_CHUNK = 8192
PHONE_CONFIG = '/sdcard/right_angle_wifi.json'

PAGE = b"""<!doctype html><html lang="zh"><meta charset="utf-8">
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Right-angle preview</title>
<style>body{margin:0;background:#141414;color:#eee;text-align:center;font:16px sans-serif}
img{width:min(100%,800px);height:auto}button{margin:12px} .rot{transform:rotate(180deg)}</style>
<button id="r">&#26059;&#36716;</button><br><img id="v" alt="Live camera">
<script>const v=document.querySelector('#v');function connect(){v.src='/stream?'+Date.now()}
v.onerror=()=>setTimeout(connect,1000);document.querySelector('#r').onclick=()=>v.classList.toggle('rot');
connect()</script>"""
MJPEG_HEADER = (b'HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=frame\r\n'
                b'Cache-Control: no-store\r\nConnection: close\r\n\r\n')


def _phone_point(point):
    """地面代理坐标映射成原相机像素。画外点舍弃，不把线延伸到画面边缘。"""
    x, z = point
    if z <= 2:
        return None
    py = (7802.22222222222 - 38.11111111111108 * z) / (z + 15.555555555555546)
    px = 159.5 + x * (py + 38.11111111111108) / 48
    return (int(px), int(py)) if 0 <= px < 320 and 32 <= py < 240 else None


def annotate_preview(frame, result, packet):
    """给已完成控制计算的同一帧叠加线路。圆点与线段来自实际控制候选点。"""
    points = [_phone_point(point) for point in result.get('route', ())]
    shade = 255 if packet[6] & 1 else 150
    for start, end in zip(points, points[1:]):
        if start is not None and end is not None:
            frame.draw_line(start[0], start[1], end[0], end[1], color=shade, thickness=3)
    for point in points:
        if point is not None:
            frame.draw_circle(point[0], point[1], 3, color=shade, thickness=1)
    mode = {'current_pair': 'PAIR', 'current_corner_predicted': 'L CORNER',
            'current_single_forecast': 'ONE EDGE', 'short_corridor_forecast': 'SHORT PRED',
            'current_front_forecast': 'FRONT EDGE'}.get(result['source'], 'NO PATH')
    frame.draw_rectangle(0, 0, 320, 28, color=0, fill=True)
    frame.draw_string_advanced(4, 1, 13, '%s %s q%d' % (mode, result['stage'], result['confidence']), color=255)
    frame.draw_string_advanced(4, 14, 13, 'seq %03d  steer %+d  permit %d' %
                               (packet[5], result['steering'], int(bool(packet[6] & 1))), color=255)


class PhonePreview:
    """一次只服务一个浏览器。每次最多一次接收和一次定长发送，无等待重试。"""

    def __init__(self, server):
        self.server = server
        self.client = None
        self.last_frame = None
        self._reset_client()

    def _reset_client(self):
        if self.client is not None:
            try:
                self.client.close()
            except OSError:
                pass
        self.client = None
        self.request = bytearray()
        self.pending = b''
        self.offset = 0
        self.stream = False
        self.deadline = None

    def close(self):
        self._reset_client()
        self.server.close()

    def step(self, frame, result, packet, encode_allowed):
        """主循环已发送PATH、已保存原像素后调用。网络慢时分帧发或丢弃连接。"""
        now = time.ticks_ms()
        try:
            if self.client is None:
                self.client, _ = self.server.accept()
                self.client.setblocking(False)
                self.deadline = time.ticks_add(now, 900)
            if self.deadline is not None and time.ticks_diff(now, self.deadline) >= 0:
                self._reset_client()
                return
            if not self.stream and not self.pending:
                incoming = self.client.recv(512)
                if incoming is None:
                    return
                if not incoming:
                    self._reset_client()
                    return
                self.request.extend(incoming)
                if len(self.request) > 1536:
                    self._reset_client()
                    return
                if self.request.find(b'\r\n\r\n') < 0:
                    return
                fields = bytes(self.request).split(b'\r\n', 1)[0].split()
                if len(fields) < 2 or fields[0] != b'GET':
                    self._reset_client()
                    return
                self.stream = fields[1].split(b'?', 1)[0] == b'/stream'
                self.pending = MJPEG_HEADER if self.stream else (
                    ('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %d\r\n'
                     'Connection: close\r\n\r\n' % len(PAGE)).encode() + PAGE)
            if (self.stream and not self.pending and encode_allowed
                    and (self.last_frame is None or time.ticks_diff(now, self.last_frame) >= PHONE_INTERVAL_MS)):
                annotate_preview(frame, result, packet)
                jpeg = frame.to_jpeg(quality=55).bytearray()
                self.pending = (('--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n'
                                 % len(jpeg)).encode() + bytes(jpeg) + b'\r\n')
                self.deadline = time.ticks_add(now, 900)
                self.last_frame = now
            if self.pending:
                sent = self.client.send(memoryview(self.pending)[self.offset:self.offset + PHONE_CHUNK])
                if sent:
                    self.offset += sent
                    if self.offset == len(self.pending):
                        if not self.stream:
                            self._reset_client()
                            return
                        self.pending = b''
                        self.offset = 0
                        self.deadline = None
                    else:
                        self.deadline = time.ticks_add(now, 900)
        except OSError as exc:
            if not exc.args or exc.args[0] not in (11, 35, 110, 116):
                self._reset_client()


def open_phone_preview():
    """开机连接已有队内热点并返回非阻塞服务器。失败时车载功能照常等待Go。"""
    server = None
    try:
        import socket
        import network

        with open(PHONE_CONFIG) as handle:
            config = json.load(handle)
        if not config.get('enabled'):
            return None
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        if not wifi.isconnected():
            key = config['ssid_key'].encode('utf-8')
            target = next((ap for ap in wifi.scan() if key in getattr(ap, 'ssid', b'')), None)
            if target is None:
                print('[PHONE] hotspot not found')
                return None
            wifi.connect(target.ssid, config['password'])
            for _ in range(25):
                if wifi.isconnected():
                    break
                time.sleep_ms(200)
        if not wifi.isconnected():
            print('[PHONE] hotspot connection timeout')
            return None
        ip = wifi.ifconfig()[0]
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ip, PHONE_PORT))
        server.listen(2)
        server.setblocking(False)
        print('[PHONE] http://%s:%d/' % (ip, PHONE_PORT))
        return PhonePreview(server)
    except Exception:
        if server is not None:
            try:
                server.close()
            except OSError:
                pass
        print('[PHONE] preview unavailable')
        return None

# BEGIN right_angle_voice_canmv.py
"""K230 语音首弯、分置信度续行和只读手机图传入口。"""
import json
import os
import time

# STM32最多运行12000ms，从发送Go起再给150ms留出串口及本板调度余量。
RUN_WINDOW_MS = 12150
FRAME_BYTES = 320 * 240
RECORD_LIMIT = 768
PHOTO_LIMIT = 8


class RightAngleVoiceSender(RightAngleSender):
    wire_version = 9
    flags_by_source = {'current_pair': 1, 'current_corner_predicted': 9,
                       'current_single_forecast': 5, 'short_corridor_forecast': 5,
                       'current_front_forecast': 5}

    def start(self, packet):
        """刚发出的当前双侧或当前L形可起步，当前出口弱关联仅许可续行。"""
        if packet[6] not in (1, 9) or packet[7] < 40:
            raise ValueError('Go requires current pair or L corner')
        return send_voice_start(self, packet)


class RunEvidence:
    """一次发令窗口的固定容量日志。只在STOP发出或窗口结束后写入/data。"""

    def __init__(self):
        self.last_pixels = bytearray(FRAME_BYTES)
        self.reset()

    def reset(self):
        self.records = [None] * RECORD_LIMIT
        self.photos = [None] * PHOTO_LIMIT
        self.issue = ()
        self.count = self.photo_count = 0
        self.last = self.last_photo_at = self.go_at = None

    def record(self, pixels, result, packet, started, sent, acquired, kws_ms, previous_phone_ms):
        """串口发送后记一帧。时间均为K230毫秒，照片保留相机原灰度。

        age_at_next估算上一帧在本次发送时的年龄，包含2ms名义串口时间；
        首次无效或本地年龄跨200ms时单独保留相邻图，供配对STM32停车环。
        """
        seq, flags = packet[5], packet[6]
        previous = self.last
        age_at_next = None if previous is None else time.ticks_diff(sent, previous[0]) + 2
        stage = result['stage']
        row = (started, seq, flags, stage, result['reason'], result['steering'], result['bend'],
               time.ticks_diff(acquired, started), time.ticks_diff(sent, started),
               None if previous is None else time.ticks_diff(sent, previous[1]), age_at_next, kws_ms,
               packet[7], result['source'], previous_phone_ms)
        self.records[self.count % RECORD_LIMIT] = row
        self.count += 1
        if not self.issue and (not flags or (age_at_next is not None and age_at_next >= 200)):
            before = () if previous is None else ((previous[0], previous[2], bytes(self.last_pixels)),)
            self.issue = before + ((started, seq, bytes(pixels)),)
        if (self.last_photo_at is None or stage != previous[3] or
                time.ticks_diff(started, self.last_photo_at) >= 1000):
            self.photos[self.photo_count % PHOTO_LIMIT] = (started, seq, bytes(pixels))
            self.photo_count += 1
            self.last_photo_at = started
        self.last_pixels[:] = pixels
        self.last = (started, sent, seq, stage)

    def save(self, event, at):
        """每次发令使用独立文件名。写入错误报告到终端，且不会触发新的运动。"""
        if self.go_at is None:
            return
        folder = '/data/right_angle_logs'
        try:
            os.stat(folder)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
            os.mkdir(folder)
        for index in range(1, 1001):
            prefix = folder + '/voice_%04d' % index
            try:
                os.stat(prefix + '.jsonl')
            except OSError as exc:
                if not exc.args or exc.args[0] != 2:
                    raise
                break
        else:
            raise RuntimeError('right-angle voice log slots exhausted')
        with open(prefix + '.jsonl', 'w') as log:
            log.write(json.dumps(dict(event=event, time_ms=at, go_sent_ms=self.go_at, wire_version=9,
                dropped_records=max(0, self.count - RECORD_LIMIT),
                columns=('start_ms', 'seq', 'flags', 'stage', 'reason', 'steering', 'bend', 'acquire_ms',
                         'to_send_ms', 'send_interval_ms', 'previous_source_age_ms', 'kws_ms',
                         'confidence', 'source', 'previous_phone_ms'))) + '\n')
            for count in range(max(0, self.count - RECORD_LIMIT), self.count):
                log.write(json.dumps(self.records[count % RECORD_LIMIT]) + '\n')
        for group, photos in (('route', self.photos), ('issue', self.issue)):
            for photo in photos:
                if photo is not None:
                    at_ms, seq, raw = photo
                    with open('%s_%s_%d_%03d.pgm' % (prefix, group, at_ms, seq), 'wb') as pgm:
                        pgm.write(b'P5\n320 240\n255\n')
                        pgm.write(raw)
        print('[RIGHT ANGLE VOICE LOG]', prefix, event, self.count)

    def finish(self, event, at):
        cleanup(lambda: self.save(event, at))
        self.reset()


def drive(sensor, channel, gray, sender, voice, evidence, phone=None):
    """一轮先采并发送PATH，再读一次短等待音频。Go只用于下一帧，不排队。

    单L及出口弱关联按当前图像续行。失效帧立即交给STM32，不沿用旧转向量。
    车上没有执行回执，窗口表示已发Go。窗口内不打印、不播放WAV、不写存储。
    """
    detector = RightAngleRoute(predictive=True)
    origin = time.ticks_ms()
    detector.clock = lambda: time.ticks_diff(time.ticks_ms(), origin)
    voice.play(READY_REPLY)
    pending_go = run_until = None
    phone_ms = 0
    print('[RIGHT ANGLE VOICE] ready v9')
    while True:
        os.exitpoint()
        started = time.ticks_ms()
        frame = sensor.snapshot(chn=channel)
        acquired = time.ticks_ms()
        if (frame.width(), frame.height(), frame.format()) != (320, 240, gray):
            raise ValueError('Expected a 320x240 grayscale frame')
        pixels = frame.bytearray()
        copied = time.ticks_ms()
        result = detector.update(pixels, time.ticks_diff(started, origin))
        processed = time.ticks_ms()
        packet = sender.path(result, time.ticks_diff(processed, copied), time.ticks_diff(processed, started))
        sent = time.ticks_ms()
        if pending_go is not None:
            if packet[6] in (1, 9) and packet[7] >= 40 and time.ticks_diff(sent, pending_go) < 200:
                evidence.go_at = sent  # 串口异常时finally仍可保存窗口起点。
                sender.start(packet)
                run_until = time.ticks_add(sent, RUN_WINDOW_MS)
                evidence.record(pixels, result, packet, started, sent, acquired, 0, phone_ms)
            else:
                print('[RIGHT ANGLE VOICE] go_blocked', result['reason'])
            pending_go = None
            continue
        keyword = voice.poll()
        recognized = time.ticks_ms()
        if keyword == STOP:
            for _ in range(3):
                sender.stop()
        if run_until is not None:
            evidence.record(pixels, result, packet, started, sent, acquired, time.ticks_diff(recognized, sent), phone_ms)
            if keyword == STOP or time.ticks_diff(recognized, run_until) >= 0:
                evidence.finish('stop_sent' if keyword == STOP else 'go_window_elapsed', recognized)
                run_until = None
                voice.play(STOP if keyword == STOP else GO)
        elif keyword == STOP:
            voice.play(STOP)
        elif keyword == GO:
            pending_go = recognized
        elif keyword in (1, 4):
            voice.play(keyword)
        if phone is not None:
            # 待机没有动力窗口，继续更新手机画面，避免场景复杂时65ms门一直挡住JPEG。
            # Go已识别时先等下一张控制图；运行期间仅在有足够路径时序余量时编码。
            # 原始取证已复制，图传异常只关闭预览，不能中断首弯控制循环。
            phone_at = time.ticks_ms()
            encode_allowed = pending_go is None and (
                run_until is None or time.ticks_diff(phone_at, started) <= 65)
            try:
                phone.step(frame, result, packet, encode_allowed)
            except Exception:
                cleanup(phone.close)
                phone = None
            phone_ms = time.ticks_diff(time.ticks_ms(), phone_at)
        else:
            phone_ms = 0


def main():
    """初始化既有GC2093、UART2和语音资源。上电等待本地Go，退出先撤驱动。"""
    from machine import FPIOA, UART
    from media.sensor import Sensor, CAM_CHN_ID_0
    from media.media import MediaManager
    import image

    sensor = uart = sender = voice = evidence = phone = None
    media = False
    try:
        phone = open_phone_preview()
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS,
                    parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender = RightAngleVoiceSender(uart.write, allow_drive=True)
        sensor = Sensor(id=2)
        sensor.reset()
        sensor.set_framesize(width=320, height=240, chn=CAM_CHN_ID_0)
        sensor.set_pixformat(Sensor.GRAYSCALE, chn=CAM_CHN_ID_0)
        sensor.set_hmirror(False)
        sensor.set_vflip(False)
        MediaManager.init()
        media = True
        voice = VoiceKeywords(mapping)
        evidence = RunEvidence()
        sensor.run()
        drive(sensor, CAM_CHN_ID_0, image.GRAYSCALE, sender, voice, evidence, phone)
    finally:
        if sender is not None:
            def stop_link():
                sender.stop()
                time.sleep_ms(10)  # 给最后一个20字节帧留出完成串口发送的时间。
            cleanup(stop_link)
        if sensor is not None:
            cleanup(sensor.stop)
        if evidence is not None and evidence.go_at is not None:
            evidence.finish('script_exit', time.ticks_ms())
        if voice is not None:
            cleanup(voice.close)
        if phone is not None:
            cleanup(phone.close)
        if media:
            time.sleep_ms(100)
            cleanup(MediaManager.deinit)
        if uart is not None:
            cleanup(uart.deinit)


if __name__ == '__main__':
    main()
