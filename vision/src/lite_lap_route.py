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
GRID_STEP=4  # 电脑全量对照保持4；实板合并包显式生成6像素网格以降低已测网格耗时。
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


class LiteLapRoute:
    """只因果使用当前图／上一次已接受路线；无帧号或预先排定转弯时间。

    首次／重捕获至少连续2帧双边，单边只允许与仍关联的上一模型延续。
    无任何当前支持时最多保持120ms且明确标history，之后无效；会话间隔
    >200ms清历史和启动稳定计数。录像4Hz不能用于证明实时控制通过。
    """
    def __init__(self,search_budget=None):
        # None保留完整电脑搜索；实板显式限制每帧候选数量，不能靠放宽超时运行。
        self.search_budget=search_budget; self.search_cursor=0; self.clock=None
        self.templates=[]
        for angle_deg in (0,38.5,90,103):
            yaws=range(-30,31,10) if angle_deg==0 else range(-int(angle_deg)-10,31,15)
            for yaw_deg in yaws:
                for c in (-18,-9,0,9,18):
                    for d in ((50,) if angle_deg==0 else range(-30,106,15)):
                        t=_template(c,d,math.radians(yaw_deg),math.radians(angle_deg))
                        if t is not None:
                            self.templates.append(t)
        self.reset()

    def reset(self):
        self.previous=None; self.previous_at=None; self.last_at=None; self.stable=0; self.search_cursor=0

    @staticmethod
    def _association(a,b):
        # 比较局部路线点，避免直道同一条线的不同“角点位置”造成虚假大跳。
        return sum(_hypot(a[2][i][0]-b[2][i][0],a[2][i][1]-b[2][i][1]) for i in (0,2,4))/3

    def update(self,pixels,now):
        """输入连续灰度字节及会话毫秒；输出局部转向量，不冒充固定y120偏差。"""
        if len(pixels)!=WIDTH*HEIGHT or not isinstance(now,int):
            raise ValueError('320x240 grayscale and integer session milliseconds required')
        if self.last_at is not None and (now<self.last_at or now-self.last_at>200):
            self.reset()
        self.last_at=now
        clock=self.clock; started=clock() if clock else 0
        threshold=_threshold(pixels); black,occupied,labels=_grid(pixels,threshold)
        grid_finished=clock() if clock else 0
        anchors=_pair_anchors(black)
        anchors_finished=clock() if clock else 0
        best=None; best_score=-1e9; dual=False; support=(0,0)
        coarse=[]
        def score_template(t,coarse_search=False):
            sides,centers=t[0],t[1]
            counts=[sum(occupied[i] for i in side) for side in sides]
            ratios=[counts[j]/max(1,len(sides[j])) for j in (0,1)]
            anchor_error=_anchor_distance(t,anchors)
            both=bool(anchors) and anchor_error<8 and all(counts[j]>=4 and ratios[j]>=.50 for j in (0,1))
            if both:
                # 同一当前组件不能被解释为两条边界；离散色块可有多个组件。
                left_ids={labels[i] for i in sides[0] if occupied[i]}
                right_ids={labels[i] for i in sides[1] if occupied[i]}
                both=bool(left_ids-right_ids and right_ids-left_ids)
            associated=self.previous is not None and self._association(t,self.previous)<14
            single=associated and max(counts)>=9 and max(ratios)>=.65
            if centers and sum(black[i] for i in centers)/len(centers)>.25:
                return None
            score=sum(min(1.,r) for r in ratios)+min(sum(counts),35)*.018
            if anchors:
                if anchor_error>12: return None
                score-=anchor_error*.10
            if both:
                score+=.5
            if self.previous is not None:
                distance=self._association(t,self.previous)
                # 已有历史时双边也不能跨越到不相干远处黑物。
                if distance>24:
                    return None
                score-=min(distance,30)*.025
            score-=abs(t[3])*.00008
            if coarse_search:
                return score,both,single,counts
            if not both and not single:
                return None
            return score,both,single,counts
        # 粗网格仅用于定位搜索区域，不能因粗模板碰巧支持就不再细化。
        # 最佳4个区域作3×3×3局部细搜；每帧不保留图像或无限增长的缓存。
        if self.search_budget is None:
            pool=self.templates
        else:
            # 滚动粗搜只使用当前帧证据；不累积旧分数冒充当前支持。
            # 始终重新验证上一模型，再沿c/d/yaw各轴局部修正，共7个邻居。
            pool=[]
            if self.previous is not None:
                pool.append(self.previous)
                c,d,yaw,angle=self.previous[5]
                for dc,dd,dy in ((-3,0,0),(3,0,0),(0,-4,0),(0,4,0),(0,0,-5),(0,0,5)):
                    neighbor=_template(c+dc,d+dd,yaw+math.radians(dy),angle)
                    if neighbor is not None: pool.append(neighbor)
            for _ in range(min(self.search_budget,len(self.templates))):
                pool.append(self.templates[self.search_cursor]); self.search_cursor=(self.search_cursor+1)%len(self.templates)
        for t in pool:
            evaluated=score_template(t,True)
            if evaluated is None:
                continue
            score,both,single,counts=evaluated
            if len(coarse)<4 or score>coarse[-1][0]:
                coarse.append((score,t)); coarse.sort(key=lambda item:-item[0]); coarse=coarse[:4]
            if not both and not single:
                continue
            if score>best_score:
                best=t; best_score=score; dual=both; support=tuple(counts)
        # 实板每帧只做上述有界局部搜索；完整108候选细搜保留给电脑对照。
        for _,seed in (coarse if self.search_budget is None else ()):
            c,d,yaw,angle=seed[5]
            for dc in (-4.5,0,4.5):
                for dd in ((0,) if angle==0 else (-7.5,0,7.5)):
                    for dy in (-5,0,5):
                        t=_template(c+dc,d+dd,yaw+math.radians(dy),angle)
                        if t is None:
                            continue
                        evaluated=score_template(t)
                        if evaluated is None:
                            continue
                        score,both,single,counts=evaluated
                        if score>best_score:
                            best=t; best_score=score; dual=both; support=tuple(counts)
        output=dict(revision='lite-lap-L1' if self.search_budget is None else 'lite-lap-L1-bounded',valid=False,source='unknown',steering=0,bend=0,
                    confidence=0,threshold=threshold,route=[],support=list(support),
                    anchors=[list(p) for p in anchors],evidence_age_ms=0,geometry_calibrated=False,control_ready=False)
        if best is not None:
            self.stable=self.stable+1 if dual else self.stable
            self.previous=best; self.previous_at=now
            valid=self.stable>=2
            output.update(valid=valid,source='current_pair' if dual else 'current_single_associated',
                steering=best[3],bend=min(1000,abs(best[3])+int(best[4][3]>0)*300),
                confidence=(70 if dual else 45) if valid else 0,route=best[2],
                parameters=list(best[4]),score=best_score)
        elif self.previous is not None and now-self.previous_at<=120:
            output.update(valid=self.stable>=2,source='history',steering=self.previous[3],
                          bend=1000,confidence=40,route=self.previous[2],evidence_age_ms=now-self.previous_at)
        else:
            self.previous=None; self.stable=0
        if clock:
            output['profile_ms']=dict(grid=grid_finished-started,anchors=anchors_finished-grid_finished,search=clock()-anchors_finished)
        output['searched_candidates']=len(pool)
        return output
