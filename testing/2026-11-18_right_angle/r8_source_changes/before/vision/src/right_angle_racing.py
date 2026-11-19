"""从T2二维折角生成外入、切弯、外出的圆弧候选，不强制沿道路中线。

几何沿用T2的入／出射线及法向偏置，移除桌面NumPy/OpenCV依赖。
单位均为现有投影代理单位，30半径／5偏置／14轮距是待实跑细调参数，
不能称全图厘米标定或已经证明车辆包络不触线。只在当前边界有支持时调用。
"""
import math

RACING_RADIUS = 30.0
RACING_OUTSET = 5.0
RACING_TRACK = 14.0  # 名义控制轮距代理量；未归档实测，不当作硬件尺寸事实。


def corner_turn_floor(parameters):
    """返回已确认右弯进入近区时的最小差速请求，单位千分比，范围0..650。

    仅由调用方在当前L或有效的当前出口边关联下使用，不能单独授予路径许可。
    旧版24点纯追踪可能仍落在入弯直线上，近角点时只给100甚至0，车头继续
    逼近横边。现在按当前角点纵向距离55..15逐步给300..650，保持向右切弯。
    yaw接近-75度时取消此下限，让出口观测接管回正；没有固定时间盲转。
    数字都是待实跑的投影代理参数，主板仍限制轮速、PWM和关联700ms期限。
    """
    _, cz, yaw, angle = parameters
    if abs(angle-math.pi/2) > 0.01 or cz > 55 or yaw <= -math.radians(75):
        return 0
    progress = max(0.0, min(1.0, (55-cz)/40))
    return int(round(300+350*progress))


def racing_route(parameters):
    """返回当前模型的推荐线、差速请求及圆弧曲率，右正。

    parameters=(cx,cz,yaw,angle)来自当前观测模板；先外侧准备，再用圆弧
    连接两条路段。对折角用路径参考点最近位置向前24代理单位取纯追踪点，
    差速比≈轮距*x/(x²+z²)。无固定转弯时间，也不把角点本身直接设为冲刺目标。
    """
    cx,cz,yaw,angle = parameters
    if abs(angle-math.pi/2) > 0.01:
        return None
    u=(math.sin(yaw),math.cos(yaw)); n=(u[1],-u[0])
    radius=RACING_RADIUS; offset=RACING_OUTSET
    local=[]
    tangent=offset-radius
    for along in range(-140,int(tangent),4):
        local.append((-offset,float(along)))
    for degree in range(0,91,5):
        a=math.radians(degree)
        local.append((radius-offset-radius*math.cos(a),offset-radius+radius*math.sin(a)))
    for along in range(int(radius-offset)+4,146,4):
        local.append((float(along),offset))
    points=[(cx+x*n[0]+z*u[0],cz+x*n[1]+z*u[1]) for x,z in local]
    nearest=min(range(len(points)),key=lambda i:points[i][0]**2+points[i][1]**2)
    route=[]; wanted=(8,16,24,32,40,48,56); distance=0.0; j=0
    for i in range(nearest+1,len(points)):
        ax,az=points[i-1];bx,bz=points[i]
        step=math.sqrt((bx-ax)**2+(bz-az)**2)
        while j<len(wanted) and distance+step>=wanted[j]:
            fraction=(wanted[j]-distance)/max(step,0.001)
            route.append((ax+(bx-ax)*fraction,az+(bz-az)*fraction));j+=1
        distance+=step
        if j==len(wanted):break
    if len(route)<7:return None
    x,z=route[2]
    ratio=RACING_TRACK*x/max(25.0,x*x+z*z)
    ratio=max(-0.65,min(0.65,ratio))
    return dict(route=route,nominal_path=points,steering=int(round(ratio*1000)),radius=radius,
                outset=offset,lookahead=24,geometry_calibrated=False)
