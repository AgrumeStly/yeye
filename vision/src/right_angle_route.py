"""首个直角弯：只搜索直道与顺时针90度右弯，不按时间排定转弯。

320x240灰度输入，复用既有近似地面投影／网格／黑块组件。每帧重新
检查黑边、白走廊及局部路线关联。上一模型只缩小搜索范围，不能
代替当前像素支持；当前左纵／前横L可独立预测右转，普通单直边不能启动。
投影仍是候选代理坐标，不能把模板宽度当作实测车体余量。
"""
import math
from right_angle_racing import racing_route
from right_angle_grid import corner_grid
from lite_lap_route import (_threshold, _grid, _pair_anchors, _template,
                            _anchor_distance, _hypot, _point, _pixel)


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
