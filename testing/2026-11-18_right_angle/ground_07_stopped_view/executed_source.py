# RightAngle v5 current L corner + racing arc; KEY start only.

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


def racing_route(parameters):
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
    # nominal_path仅供现有图示／静态包络检查，控制使用上方连续投影路线。
    # 保留原名义圆弧，不通过扩大半径或车道假设来掩盖提前转向。
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


class RightAngleRoute:
    """固定有界候选库与局部细化；初始化预计算只执行一次，不驱动车轮。"""
    def __init__(self):
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
        black, occupied, labels = corner_grid(pixels, _threshold(pixels))
        grid_done = clock() if clock else 0
        anchors = _pair_anchors(black)
        anchors_done = clock() if clock else 0

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

        tracking = self.previous is not None
        local = []
        if tracking:
            local.append(self.previous)
            c, d, yaw, angle = self.previous[5]
            if self.neighbor_key != self.previous[5]:
                self.neighbor_key = self.previous[5]
                self.neighbors = []
                for dc, dd, dy in ((-3,0,0),(3,0,0),(0,-4,0),(0,4,0),(0,0,-5),(0,0,5)):
                    t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                    if t is not None: self.neighbors.append(t)
            local.extend(self.neighbors)
            pool = list(local)
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
        best = None
        best_score = -1e9
        support = [0, 0]
        best_dual = False
        best_corner = 0
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
        fallback = 0
        if tracking and best is None:
            # 局部支持不足时同帧回到完整当前搜索，不能因为滚动库本帧没扫到
            # 邻近新几何而人为制造失线。所有旧关联／单侧／白路面门保持。
            for t in self.templates:
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
        for _, seed in seeds[:1]:
            c, d, yaw, angle = seed[5]
            if self.refine_key != seed[5]:
                self.refine_key = seed[5]
                self.refinements = []
                offsets = [(dc,dd,dy) for dc in (-6,0,6)
                           for dd in ((0,) if angle == 0 else (-10,0,10)) for dy in (-10,0,10)]
                for dc,dd,dy in offsets:
                    t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                    if t is not None: self.refinements.append(t)
            for t in self.refinements:
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
        if not best_dual: risk = 1.0
        # 直道沿用32点误差；有90度几何时下方改用外入切弯圆弧和24点纯追踪。
        target = best[2][6] if risk > 0 else best[2][3]
        steering = max(-1000, min(1000, round(math.atan2(target[0], max(5, target[1]))/math.radians(55)*1000)))
        route = best[2]
        if angle > 1 and not (yaw <= -math.radians(75) and cz < 10):
            if self.racing_key != best[4]:
                self.racing_key = best[4]; self.racing = racing_route(best[4])
            if self.racing is not None:
                route = self.racing['route']; steering = self.racing['steering']
                out['racing_radius'] = self.racing['radius']; out['racing_outset'] = self.racing['outset']
                out['racing_phase'] = self.racing['phase']
                out['arc_entry_distance'] = self.racing['entry_distance']
                out['route_projection_s'] = self.racing['projection_s']
                stage = 'approach' if self.racing['phase']=='entry' else ('turn' if self.racing['phase']=='arc' else 'exit')
        source = 'current_pair' if best_dual else ('current_corner_predicted' if best_corner == 2 else 'current_corner_associated')
        if not best_dual:
            # v5单侧L／弱关联只允许右转或直行，不扩大协议到未经确认的左转。
            # 推荐点仍在入口直道时不额外给10%右转；真正到达圆弧后，右转量
            # 由连续路线自然增大。双侧路径保留有符号修正，允许及时回正。
            steering = max(0,steering)
        # R7实跑出现100→371及负修正→508的切换，来自距离下限覆盖路线。
        # R8取消该下限；留0字段便于与旧逐帧证据比较，不以历史L强行续转。
        out['turn_floor'] = 0
        out.update(valid=valid, source=source, steering=steering,
                   bend=int(round(risk*1000)), confidence=75 if best_dual else (60 if best_corner == 2 else 45), stage=stage,
                   corner_observed=best_corner==2, corner_age_ms=0 if self.corner_at is None else now-self.corner_at,
                   measured_edges='left_and_front' if best_corner==2 else ('pair' if best_dual else 'associated_left'),
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
    def _send(self, data):
        converted = bytearray(data)
        converted[2] = 5
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
        kind=result.get('source'); flags={'current_pair':1,'current_corner_predicted':9,'current_corner_associated':5}.get(kind,0)
        valid=bool(self.allow_drive and result.get('valid') and flags and processing_ms<=100 and age_ms<150)
        steering=int(result.get('steering',0));bend=int(result.get('bend',0));quality=int(result.get('confidence',0))
        if kind=='current_corner_predicted':
            valid=valid and result.get('corner_observed') is True and bend==1000 and steering>=0 and quality>=60
        elif kind=='current_corner_associated':
            evidence_age=result.get('corner_age_ms',700)
            valid=valid and isinstance(evidence_age,int) and 0<=evidence_age<700 and bend==1000 and steering>=0 and quality>=45
        if not (-1000<=steering<=1000 and 0<=bend<=1000 and 0<=quality<=100):raise ValueError('v5 route fields')
        header=bytes((0xa5,0x5a,5,1,12,self.seq));self.seq=(self.seq+1)&255
        data=header+struct.pack('<BBhHHHBB',flags if valid else 0,quality if valid else 0,
            steering if valid else 0,min(age_ms,1000),bend if valid else 0,min(processing_ms,1000),0,0)
        return self._send(data+struct.pack('<H',crc16(data)))

# BEGIN right_angle_canmv.py
"""首弯现场手动入口，默认无动力预览；生成工具另产明确许可的车载副本。

沿用Sensor2／320x240灰度／GH UART2 T11 R12及115200。相机只提供
当前首弯路径许可，任何时候均不发送START。STM32独立限时与KEY负责动作。
启动前先停止旧main脚本，避免两个程序同时占相机或UART；不改main.py。
"""
import gc
import json
import os
import time

ALLOW_DRIVE = False
SHOW_PREVIEW = False
# 无动力预览默认10分钟；生成的正式试跑副本将此值设为0，持续采图到人工停止。
# 0只取消视觉待机期限；STM32的KEY启动、单次12秒及200ms新鲜度监督独立保留。
DURATION_MS = 5000


def _open_log():
    """在/data数据分区新建递增日志，不覆盖原件；异常抛出并退出。

    /sdcard仅保存程序。照片与逐帧日志共同使用/data，避免程序分区写满
    后出现零字节证据文件；存储异常不放宽主板200ms新鲜度保护。
    """
    folder = '/data/right_angle_logs'
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
    raise RuntimeError('right-angle log slots exhausted')


def _write_log(log, text):
    """写入一条完整JSON文本；短写立即报错，不能把空文件当成功留证。

    参数log为当前/data文本流，text为已序列化且带换行的ASCII JSON文本；
    无返回值。写入返回的字符数必须完整，错误由主循环finally撤许可／清理。
    不逐帧sync，避免全分区同步阻塞下一帧；仍沿用每10帧flush。
    """
    if log.write(text) != len(text):
        raise OSError('incomplete /data right-angle log write')


def main():
    """主循环使用有界局部跟踪；逐帧日志保留原始误差与图像处理年龄。

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
        print('[RIGHT ANGLE LOG]', name, 'ALLOW_DRIVE', ALLOW_DRIVE, 'NO AUTO START')
        _write_log(log, json.dumps(dict(event='begin', revision='RIGHT-ANGLE-V5-RACING-8-ARC', allow_drive=ALLOW_DRIVE,
                                  duration_ms=DURATION_MS)) + '\n')
        log.flush()
        mapping = FPIOA()
        mapping.set_function(11, FPIOA.UART2_TXD)
        mapping.set_function(12, FPIOA.UART2_RXD)
        uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
        sender = RightAngleSender(uart.write, ALLOW_DRIVE)
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
        detector = RightAngleRoute()
        detector.clock = time.ticks_ms
        origin = time.ticks_ms()
        index = 0
        previous = None
        previous_sent = None
        previous_log_ms = None
        previous_gc_ms = None
        last_valid_frame = None
        loss_count = 0
        while DURATION_MS == 0 or time.ticks_diff(time.ticks_ms(), origin) < DURATION_MS:
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
            evidence_started = sent
            # 仅缓存最近有效原图，失效包已经发出后再保存前后PGM，不能延迟停车。
            # 最多100次切换留证（约15MB），照片和日志均保存到/data数据分区。
            # 文件名来自当前新编号日志，不覆盖旧图，不改像素。
            # 正常有效循环仅增加一个76800字节副本，无SD图像写入。
            if packet[6] & 1:
                last_valid_frame = (bytes(pixels), index, packet[5])
            elif last_valid_frame is not None and loss_count < 100:
                loss_count += 1
                prefix = name[:-6] + '_loss_%02d' % loss_count
                for suffix, raw in (('_before.pgm', last_valid_frame[0]), ('_after.pgm', pixels)):
                    with open(prefix + suffix, 'wb') as snapshot:
                        snapshot.write(b'P5\n320 240\n255\n')
                        snapshot.write(raw)
                _write_log(log, json.dumps(dict(event='path_lost', prefix=prefix,
                    before_index=last_valid_frame[1], before_sequence=last_valid_frame[2],
                    after_index=index, after_sequence=packet[5], reason=result['reason'])) + '\n')
                log.flush()
                print('[RIGHT ANGLE LOSS]', prefix)
                last_valid_frame = None
            if index == 10:
                diagnostic = name[:-6] + '_view.pgm'
                with open(diagnostic, 'wb') as snapshot:
                    snapshot.write(b'P5\n320 240\n255\n')
                    snapshot.write(pixels)
                print('RIGHT_ANGLE_VIEW', diagnostic)
            record = dict(result)
            evidence_finished = time.ticks_ms()
            # 每帧保留真实序号／来源／处理年龄等证据；完整7点路线每10帧存一次，
            # 减少JSON／SD负担。几何计算及UART封包仍逐帧执行，不降低控制更新率。
            if index % 10 != 0:
                record.pop('route', None)
            record.update(index=index, elapsed_ms=time.ticks_diff(started, origin),
                          path_sequence=packet[5], wire_valid=bool(packet[6] & 1),
                          acquire_ms=time.ticks_diff(acquired, started), processing_ms=time.ticks_diff(processed, copied),
                          to_send_ms=time.ticks_diff(sent, started),
                          interval_ms=None if previous is None else time.ticks_diff(started, previous),
                          send_interval_ms=None if previous_sent is None else time.ticks_diff(sent, previous_sent),
                          evidence_ms=time.ticks_diff(evidence_finished, evidence_started),
                          previous_log_ms=previous_log_ms, previous_gc_ms=previous_gc_ms)
            # 发送后留证、JSON／文件写入及垃圾回收也占用下一帧的新鲜度预算。
            # 写入／回收耗时在下一条记录中回填，避免仅记录图像处理平均值。
            # 均用ticks_diff处理时钟回绕；没有下一帧时不补造最后一次耗时。
            previous = started
            previous_sent = sent
            logging_started = time.ticks_ms()
            _write_log(log, json.dumps(record) + '\n')
            if index % 10 == 0:
                log.flush()
                print('[RIGHT ANGLE]', result['reason'], 'stage', result['stage'], 'err', result['steering'], 'valid', bool(packet[6] & 1), 'ms', record['to_send_ms'])
            if SHOW_PREVIEW and not ALLOW_DRIVE:
                Display.show_image(frame)
            previous_log_ms = time.ticks_diff(time.ticks_ms(), logging_started)
            del pixels, frame
            collection_started = time.ticks_ms()
            gc.collect()
            previous_gc_ms = time.ticks_diff(time.ticks_ms(), collection_started)
    finally:
        if sender is not None:
            try:
                sender.stop()
                time.sleep_ms(10)
            except BaseException as exc:
                print('[RIGHT ANGLE STOP ERROR]', str(exc))
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
                    print('[RIGHT ANGLE CLEANUP ERROR]', name, str(exc))


if __name__ == '__main__':
    main()
