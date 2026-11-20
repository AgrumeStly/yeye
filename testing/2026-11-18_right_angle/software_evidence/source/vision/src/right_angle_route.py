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
    return t+(arms,)


class RightAngleRoute:
    """固定有界候选库与局部细化；初始化预计算只执行一次，不驱动车轮。"""
    def __init__(self):
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
        black, occupied, labels = _grid(pixels, _threshold(pixels))
        anchors = _pair_anchors(black)

        def evaluate(t):
            sides, centers = t[0], t[1]
            counts = [sum(occupied[i] for i in side) for side in sides]
            ratios = [counts[j]/max(1, len(sides[j])) for j in (0, 1)]
            if len(centers) < 1 or any(black[i] for i in centers):
                return None
            error = _anchor_distance(t, anchors) if anchors else 0
            if anchors and error > 10:
                return None
            distance = self.distance(t, self.previous) if self.previous else 0
            if self.previous is not None and distance > 18:
                return None
            ids = [{labels[i] for i in side if occupied[i]} for side in sides]
            dual = len(centers) >= 3 and all(counts[j] >= 4 and ratios[j] >= 0.55 for j in (0, 1))
            dual = dual and bool(ids[0]-ids[1] and ids[1]-ids[0])
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

        pool = list(self.templates)
        if self.previous is not None:
            pool.append(self.previous)
            c, d, yaw, angle = self.previous[5]
            for dc, dd, dy in ((-3,0,0),(3,0,0),(0,-4,0),(0,4,0),(0,0,-5),(0,0,5)):
                t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                if t is not None: pool.append(t)
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
        seeds.sort(key=lambda item: -item[0])
        # 最佳区域27点细搜，范围固定；不在相机循环调用全赛道模板搜索。
        for _, seed in seeds[:1]:
            c, d, yaw, angle = seed[5]
            for dc in (-6, 0, 6):
                for dd in ((0,) if angle == 0 else (-10, 0, 10)):
                    for dy in (-10, 0, 10):
                        t = _corner_template(c+dc, d+dd, yaw+math.radians(dy), angle)
                        if t is None: continue
                        candidate = evaluate(t)
                        if candidate is None: continue
                        score, dual, single, counts = candidate
                        if (dual or single) and score > best_score:
                            best, best_score, support = t, score, counts
                            best_dual = dual
        out.update(support=support, searched_candidates=len(pool)+27,
                   anchors=len(anchors))
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
