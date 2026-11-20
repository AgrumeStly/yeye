"""首个直角弯：只搜索直道与顺时针90度右弯，不按时间排定转弯。

320x240灰度输入，复用既有近似地面投影／网格／黑块组件。每帧重新
检查黑边、白走廊及局部路线关联。上一模型只缩小搜索范围，不能
代替当前像素支持；单侧仅允许已确认弯道、当前折角两臂及2秒短租期。
投影仍是候选代理坐标，不能把模板宽度当作实测车体余量。
"""
import math
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
        return t+(((), (), (), ()), vectors)
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
    return t+(arms, vectors)


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
                    for d in ((50,) if angle == 0 else (0, 20, 40, 60, 80)):
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
        self.pair_at = None
        self.corner_pair = False
        self.search_cursor = 0
        self.neighbor_key = None
        self.neighbors = []
        self.refine_key = None
        self.refinements = []

    @staticmethod
    def distance(a, b):
        return sum(_hypot(a[2][i][0]-b[2][i][0], a[2][i][1]-b[2][i][1])
                   for i in (0, 2, 4))/3

    def update(self, pixels, now):
        """now为取图开始的会话ms；任何拒绝均返回新无效观测，禁止沿用旧命令。

        入弯横边可能令逐行左右配对消失：双侧模式须不同组件分别支持
        同一个90度模型且至少3个可见白色中线采样；已确认近弯后单侧
        模式须当前折角两臂及至少1个白色中线采样，最多2秒等待双侧重获。
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
        black, occupied, labels = _grid(pixels, _threshold(pixels))
        grid_done = clock() if clock else 0
        anchors = _pair_anchors(black)
        anchors_done = clock() if clock else 0

        def evaluate(t):
            sides, centers = t[0], t[1]
            counts = [sum(occupied[i] for i in side) for side in sides]
            ratios = [counts[j]/max(1, len(sides[j])) for j in (0, 1)]
            if len(centers) < 1 or any(black[i] for i in centers):
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
            single = False
            if (self.corner_pair and self.pair_at is not None and now-self.pair_at < 2000
                    and self.previous is not None and distance < 12 and t[4][3] > 1):
                for j in (0, 1):
                    arms = t[6][2*j:2*j+2]
                    if counts[j] >= 12 and ratios[j] >= 0.75 and all(
                            len(arm) >= 3 and sum(occupied[i] for i in arm) >= 3
                            and sum(occupied[i] for i in arm)/len(arm) >= 0.65 for arm in arms):
                        single = True
            # 样本仅一格的画外短边不能凭100%命中率压过真正有多点支持的模型。
            score = sum(min(ratios[j], counts[j]/4) for j in (0, 1))
            score += min(sum(counts), 35)*0.018-error*0.10-distance*0.025
            # 出口直线与画外角点模型可能同样解释当前两条直边；优先简单直线，
            # 防止把不可见角点当作仍须大差速的转弯证据。
            if t[4][3] > 1: score -= 0.12
            if dual: score += 0.5
            return score, dual, single, counts

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
            # 每帧重新验证上次模型及6个邻居，并滚动查看12个当前粗候选。
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
        for t in pool:
            candidate = evaluate(t)
            if candidate is None: continue
            score, dual, single, counts = candidate
            seeds.append((score, t))
            if (dual or single) and score > best_score:
                best, best_score, support = t, score, counts
                best_dual = dual
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
        out.update(support=support, searched_candidates=len(pool)+fallback+refined,
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
        if best_dual:
            self.pair_at = now
            # 只有当前确实看见前方90度弯的双侧才开放短时单侧；
            # 普通直线及画外角点别名不能取得单侧转弯许可。
            self.corner_pair = angle > 1 and 10 < cz < 85 and yaw > -math.radians(75)
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
        # 直角弯用56代理单位的前视点提前转向，避免32点尚在直道时一直直行，
        # 等角点进入相机下方盲区才开始大幅差速；直道沿用32点小量纠偏。
        target = best[2][6] if risk > 0 else best[2][3]
        steering = max(-1000, min(1000, round(math.atan2(target[0], max(5, target[1]))/math.radians(55)*1000)))
        out.update(valid=valid, source='current_pair' if best_dual else 'current_single_associated', steering=steering,
                   bend=int(round(risk*1000)), confidence=75 if best_dual else 45, stage=stage,
                   parameters=list(best[4]), route=best[2], score=best_score,
                   reason='ready' if valid else 'stabilizing')
        return out
