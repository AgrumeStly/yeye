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
