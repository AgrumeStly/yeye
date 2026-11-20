"""首弯网格：只剥离上沿厚背景，保留与背景偶然接触的细长赛道边。

沿用既有6像素采样／组件／一格容差，不改直道或旧整圈模块的_grid。
修复实图run_0007_loss_03：ROI黑墙与L形边界连接后，旧版删除整个组件，
真实左边和前横边同时变成0。新版本只删上沿连通的厚核及一格外扩。
"""
from array import array
from lite_lap_route import GRID_STEP, GW, GH, GY0, GY1


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
