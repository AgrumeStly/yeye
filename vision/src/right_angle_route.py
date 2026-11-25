"""首个直角弯：只搜索直道与顺时针90度右弯，不按时间排定转弯。

320x240灰度输入，复用既有近似地面投影／网格／黑块组件。每帧重新
检查黑边、白走廊及局部路线关联。上一模型只缩小搜索范围，不能
代替当前像素支持；当前左纵／前横L可独立预测右转，普通单直边不能启动。
投影仍是候选代理坐标，不能把模板宽度当作实测车体余量。
"""
import math
from right_angle_racing import JOINT_OUTSET, joint_racing_route, racing_route
from right_angle_grid import corner_grid, sample_black_rows
from right_angle_prediction import PREDICTION_ANCHOR_MS, PREDICTION_GAP_MS, clear_predicted_corridor
from right_angle_prediction import fitted_outer_l, fitted_left_forecast, fitted_front_edge
from right_angle_prediction import fitted_straight_rail, STRAIGHT_CONTROL_ROWS, turn_ahead
from straight_route import StraightRoute
from lite_lap_route import (_threshold, _grid, _pair_anchors, _template,
                            _anchor_distance, _hypot, _point, _pixel)

OBTUSE_TURN = math.radians(39)  # 图1约141°内角对应车头右转约39°。


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
        # 直道没有折角臂，不需要重复投影。
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


def _along_exit_edge(t, outset=0):
    """车头接近出弯方向时，把已跟踪的前线作为出口左边推算中线。"""
    cx, cz, yaw, angle = t[4]
    heading = yaw + angle
    if heading > math.radians(15):
        return None
    nx, nz = math.cos(heading), -math.sin(heading)
    offset = cx*nx + cz*nz - outset
    return [(offset*nx-ahead*nz, offset*nz+ahead*nx) for ahead in (8, 16, 24, 32, 40, 48, 56)]


def _same_rail(first, first_turn, second, second_turn=0):
    """用方向和法向截距判断相邻模型是否观测到同一条车道中线，距离为代理单位。"""
    ax, az, ayaw, _ = first[4]
    bx, bz, byaw, _ = second[4]
    ayaw += first_turn
    byaw += second_turn
    return (abs(ayaw - byaw) <= math.radians(24) and
            abs(ax*math.cos(ayaw) - az*math.sin(ayaw) -
                (bx*math.cos(byaw) - bz*math.sin(byaw))) <= 12)


def _corridor_blocked(black, route):
    """旧推荐线上两个不同的可见实黑投影格才确认受阻。"""
    cells = {_pixel(*point) for point in route}
    return sum(black[cell] for cell in cells if cell is not None) >= 2


def _straight_reference(t, racing):
    """给当前单边重拟合限定参考直段。圆弧中间仍由实测弯边或短预测负责。"""
    cx, cz, yaw, angle = t[4]
    if angle == 0:
        return t
    if racing['entry_distance'] >= 12:
        return _corner_template(t[5][0], 50, yaw, 0)
    heading = yaw + angle
    if racing['phase'] == 'exit' and abs(heading) <= math.radians(16):
        offset = cx*math.cos(heading) - cz*math.sin(heading)
        return _corner_template(offset, 50, heading, 0)
    return None


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
    def __init__(self, predictive=False, joint=False):
        self.predictive = predictive
        self.joint = joint
        self.outset = JOINT_OUTSET if joint else 0
        self.straight = StraightRoute() if joint else None
        self.clock = None  # 可选板上ticks_ms，只计耗时，不改变几何判断或源年龄。
        self.templates = []
        for angle in (0, 90):
            for yaw in ((-30, -15, 0, 15, 30) if angle == 0 else (-90, -60, -30, 0, 15)):
                for c in (-12, 0, 12):
                    for d in ((50,) if angle == 0 else (0, 10, 20, 40, 60, 80)):
                        t = _corner_template(c, d, math.radians(yaw), math.radians(angle))
                        if t is not None:
                            self.templates.append(t)
        self.obtuse_templates = []
        self.straight_templates = [t for t in self.templates if t[4][3] == 0]
        if joint:
            for yaw in (-45, -30, -15, 0, 15):
                for c in (-10, 0, 10):
                    for d in (0, 16, 34, 56, 80):
                        t = _corner_template(c, d, math.radians(yaw), OBTUSE_TURN)
                        if t is not None:
                            self.obtuse_templates.append(t)
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
        self.rail_at = None
        self.forecast_route = self.forecast_command = None
        self.front_model = self.front_at = None
        self.racing_key = None
        self.racing = None
        self.first_corner = False
        self.first_exit = None
        self.second_corner = False
        self.second_exit = None
        self.second_exit_at = None
        self.preview_at = None
        if self.straight is not None:
            self.straight.reset()

    def curve(self, parameters):
        """联合版和首弯版共用候选搜索及稳定确认，各自采用对应的控制线。"""
        if self.joint:
            if parameters[3] > 1:
                return racing_route(parameters, include_nominal=False)
            return joint_racing_route(parameters)
        return racing_route(parameters, include_nominal=not self.predictive)

    @staticmethod
    def distance(a, b):
        return sum(_hypot(a[2][i][0]-b[2][i][0], a[2][i][1]-b[2][i][1])
                   for i in (0, 2, 4))/3

    def _use_straight(self, result, reference, now):
        """采用旧直道解，更新实际走廊，供下一帧只见一侧时重新估计。"""
        near, slope = result['near_error'], result['heading_proxy']
        offset = self.outset / math.cos(reference[4][2])
        route = [(near + (z-30)*slope - offset, z) for z in (16, 24, 30, 38, 46, 54, 62)]
        steering = round(StraightRoute.command(near - offset, slope) * 1000)
        self.previous = reference
        self.stable, self.stable_at = self.straight.stable, self.straight.stable_at
        self.forecast_route, self.forecast_command = route, (steering, 0)
        self.forecast_anchor_at = self.visible_edge_at = now
        if self.first_exit is not None:
            self.first_exit = reference
        result.update(source='straight_pair', stage='straight', steering=steering, route=route,
                      road_section='connector' if self.first_exit else 'start_straight',
                      geometry_calibrated=False, parameters=reference[4], vision_mode='near_mid')
        return result

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
        straight = reference = None
        if self.joint and (not self.first_corner or self.first_exit is not None) and not self.second_corner:
            # 双边直道只扫旧算法实际使用的近／中区行，无需每帧做连通域或展开全部弯道模板。
            bands = sample_black_rows(pixels, threshold, STRAIGHT_CONTROL_ROWS)
            straight = self.straight.update_anchors(_pair_anchors(bands), now, threshold)
            if straight['valid']:
                slope = straight['heading_proxy']
                yaw = math.atan(slope)
                offset = (straight['near_error'] - 30*slope) * math.cos(yaw)
                reference = _corner_template(offset, 50, yaw, 0)
                if reference is not None:
                    preview_due = self.preview_at is None or now-self.preview_at >= 70
                    if preview_due:
                        self.preview_at = now
                    if not preview_due or not turn_ahead(pixels, threshold, reference):
                        return self._use_straight(straight, reference, now)
        black, occupied, labels = corner_grid(pixels, threshold)
        grid_done = clock() if clock else 0
        anchors = _pair_anchors(black)
        anchors_done = clock() if clock else 0
        tracking = self.previous is not None
        quick, front = None, None
        tried_angle = None
        active_angle = self.previous[4][3] if tracking else 0
        straight_entry = self.joint and tracking and active_angle == 0
        if reference is not None:
            tried_angle = OBTUSE_TURN if self.first_exit is not None else math.pi/2
            match = fitted_outer_l(black, occupied, _corner_template, tried_angle)
            if (match is not None and _same_rail(reference, 0, match) and
                    self.curve(match[4])['entry_distance'] <= 38):
                quick = match
            else:
                return self._use_straight(straight, reference, now)
        if quick is None and self.joint and self.first_exit is not None and not self.second_corner and tried_angle is None:
            # 出直角弯后，只有接在当前出弯车道上的两条实测外臂才能切换弯型。
            match = fitted_outer_l(black, occupied, _corner_template, OBTUSE_TURN)
            if (match is not None and _same_rail(self.first_exit, self.first_exit[4][3], match)
                    and (not anchors or _current_anchor_distance(match, anchors) <= 10)):
                quick = match
        if quick is None and self.predictive and tracking and not anchors and active_angle > 0:
            # 已跟踪的折角先用当前外边直接拟合，节省整组邻居/精化生成。
            # 左臂渐出画后，只关联上帧已确认的前线方向和距离。
            match = fitted_outer_l(black, occupied, _corner_template, active_angle)
            if match is not None and self.distance(match, self.previous) <= 24:
                quick = match
            elif _still_has_l(self.previous, black, occupied):
                quick = self.previous
            elif self.front_at is not None and now-self.front_at < PREDICTION_GAP_MS:
                match = fitted_front_edge(black, self.front_model, _corner_template)
                if match is not None:
                    front_route = _along_exit_edge(match[0], self.outset) or self.curve(match[0][4])['route']
                    if clear_predicted_corridor(pixels, black, threshold, front_route):
                        quick, front = match[0], (match[1], match[2])

        def evaluate(t):
            angle = t[4][3]
            if self.joint and angle > 0:
                if angle > 1 and (self.second_corner or (self.first_exit is not None and active_angle <= 1)):
                    return None
                if angle == OBTUSE_TURN and not self.second_corner and (
                        self.first_exit is None or not _same_rail(self.first_exit, self.first_exit[4][3], t)):
                    return None
            sides, centers = t[0], t[1]
            counts = [sum(occupied[i] for i in side) for side in sides]
            ratios = [counts[j]/max(1, len(sides[j])) for j in (0, 1)]
            if any(black[i] for i in centers):
                return None
            error = _current_anchor_distance(t, anchors) if anchors else 0
            if anchors and error > 10:
                return None
            distance = self.distance(t, self.previous) if self.previous else 0
            same_entry = straight_entry and angle > 0 and _same_rail(self.previous, 0, t)
            if distance > 18 and not same_entry and not (
                    self.joint and angle == OBTUSE_TURN and not self.second_corner):
                return None
            dual = len(centers) >= 3 and all(counts[j] >= 4 and ratios[j] >= 0.55 for j in (0, 1))
            if dual:
                ids = [{labels[i] for i in side if occupied[i]} for side in sides]
                dual = bool(ids[0]-ids[1] and ids[1]-ids[0])
            # 直道必须有逐行双边走廊；转弯允许用两条二维边界证明当前支持。
            dual = dual and (bool(anchors) or angle > 0)
            if self.joint and dual and angle > 0 and (not self.first_corner or (angle == OBTUSE_TURN and not self.second_corner)):
                # 两条平行直边也可能匹配角点模板。从直道切入任何新弯时必须实测同一侧两臂。
                dual = any(all(len(arm) >= 3 and sum(occupied[i] for i in arm) >= max(3, .65 * len(arm))
                               for arm in side) for side in (t[6][:2], t[6][2:]))
            # 当前左外边的入弯臂和出弯臂共同证明折角，不要求右侧边界出现，
            # 也不要求此前先得到双侧许可。只有一根直带不满足此判据。
            corner = False
            associated = False
            min_yaw = -angle - math.radians(5) if angle == OBTUSE_TURN else -math.radians(85)
            if angle > 0 and min_yaw <= t[4][2] <= math.radians(25):
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
            if angle > 0: score -= 0.12
            if dual: score += 0.5
            elif corner: score += 0.3
            return score, dual, (2 if corner else (1 if associated else 0)), counts

        templates = self.templates
        if self.joint and self.first_exit is not None:
            if self.second_corner:
                templates = self.straight_templates + self.obtuse_templates
            else:
                templates = self.templates + self.obtuse_templates
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
            for _ in range(min(12, len(templates))):
                pool.append(templates[self.search_cursor % len(templates)])
                self.search_cursor = (self.search_cursor+1) % len(templates)
        else:
            # 启动／失线重获保留原全库搜索；未经当前支持和稳定门不授予运动许可。
            pool = templates
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
        anchor_fresh = self.forecast_anchor_at is not None and now-self.forecast_anchor_at < PREDICTION_ANCHOR_MS
        rail_fresh = self.rail_at is not None and now-self.rail_at < PREDICTION_GAP_MS
        if self.predictive and not best_dual and not fitted:
            # 右边出画时，直接用当前左纵／前横交点补充离散库。当前两臂拟合
            # 成功便跳过整库重扫与27点精化，给测到过峰值的K230留出时间。
            match = fitted_outer_l(black, occupied, _corner_template,
                                   OBTUSE_TURN if self.first_exit is not None else math.pi / 2)
            if (match is not None and (not anchors or _current_anchor_distance(match, anchors) <= 10)
                    and (not tracking or self.distance(match, self.previous) <= 24 or
                         (straight_entry and _same_rail(self.previous, 0, match)))
                    and (not self.joint or self.first_exit is None or self.second_corner or
                         _same_rail(self.first_exit, self.first_exit[4][3], match))):
                best, best_score = match, 2.0
                support = [sum(occupied[i] for i in side) for side in best[0]]
                best_corner = 2
                fitted = True
            elif self.joint and tracking and best_corner != 2 and (anchor_fresh or rail_fresh):
                # 只有当前至少四行测到同一侧，且角度和截距跟上次一致，才逐帧续接直道单边。
                reference = _straight_reference(self.previous, self.racing)
                rail = fitted_straight_rail(black, reference, _corner_template) if reference is not None else None
                if rail is not None:
                    yaw = rail[4][2]
                    nx, nz = math.cos(yaw), -math.sin(yaw)
                    line = [(x - self.outset*nx, z - self.outset*nz) for x, z in rail[2]]
                    if clear_predicted_corridor(pixels, black, threshold, line):
                        best, forecast = rail, 4
                        support = [sum(occupied[i] for i in side) for side in rail[0]]
            if not fitted and not forecast and anchor_fresh:
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
            if (best is None and (anchor_fresh or rail_fresh) and self.visible_edge_at is not None
                    and now-self.visible_edge_at < PREDICTION_GAP_MS
                    and clear_predicted_corridor(pixels, black, threshold, self.forecast_route)):
                best, forecast = self.previous, 2
        fallback = 0
        if tracking and best is None:
            # 局部支持不足时同帧回到完整当前搜索，不能因为滚动库本帧没扫到
            # 邻近新几何而人为制造失线。所有旧关联／单侧／白路面门保持。
            for t in templates:
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
        out.update(support=support, searched_candidates=len(pool)+recovery+fallback+refined, vision_mode='corner_search',
                   recovery_candidates=recovery,
                   anchors=len(anchors), search_mode='fallback' if fallback else ('tracking' if tracking else 'acquire'))
        if clock:
            out['profile_ms'] = dict(grid=grid_done-begun, anchors=anchors_done-grid_done,
                                     search=clock()-anchors_done)
        if best is None:
            if self.joint:
                # 模型落空只表示这一帧没有新路线。明确看到旧路线受阻才立即撤许可。
                if self.forecast_route is None or not _corridor_blocked(black, self.forecast_route):
                    out['reason'] = 'observation_missed'
                    return out
                out['reason'] = 'corridor_blocked'
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
        exit_aligned = yaw + angle <= math.radians(15)
        if angle == 0 or (angle > 0 and exit_aligned and cz < 10):
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
        if angle > 0 and (self.joint or not (exit_aligned and cz < 10)):
            if self.racing_key != best[4]:
                self.racing_key = best[4]; self.racing = self.curve(best[4])
            if self.racing is not None:
                route = self.racing['route']; steering = self.racing['steering']
                out['racing_radius'] = self.racing['radius']; out['racing_outset'] = self.racing['outset']
                out['racing_phase'] = self.racing['phase']
                out['arc_entry_distance'] = self.racing['entry_distance']
                out['route_projection_s'] = self.racing['projection_s']
                stage = 'approach' if self.racing['phase']=='entry' else ('turn' if self.racing['phase']=='arc' else 'exit')
                if self.joint and best_dual:
                    # 双边时提前适量减速，钝角用较大半径，回正后释放弯速限制。
                    # 处于弯模型时保留0.2，确保驶出弧后若只剩当前出口边，STM32仍有最近弯道锚点。
                    maximum = 1.0 if angle > 1 else 0.68
                    risk = max(0.2, maximum * (1 - self.racing['entry_distance'] / 38)) if stage != 'exit' else 0.2
        elif self.joint and angle == 0:
            # 直道、首弯出口、第二弯入口都以同一条外偏线为目标。
            nx, nz = math.cos(yaw), -math.sin(yaw)
            route = [(x - self.outset*nx, z - self.outset*nz) for x, z in route]
            x, z = route[3]
            steering = round(max(-1, min(1, math.atan2(x, max(5, z))/math.radians(55)))*1000)
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
                exit_route = _along_exit_edge(best, self.outset)
                if exit_route is not None:
                    # 原横线已转成沿行驶方向的左边。用它的法向偏移和新朝向回正。
                    route = exit_route
                    x, z = route[3]
                    steering = max(-1000, min(1000, round(math.atan2(x, max(5, z))/math.radians(55)*1000)))
                    stage, risk = 'exit', 0.0
            elif forecast == 4:
                source, confidence = 'current_straight_rail', 56
                slope = math.tan(yaw)
                near = (best[5][0] - self.outset) / math.cos(yaw) + 30*slope
                steering = round(StraightRoute.command(near, slope)*1000)
            elif forecast == 1:
                source, confidence = 'current_single_forecast', 55
            else:
                source, confidence = 'short_corridor_forecast', 45
                route = self.forecast_route
                if self.joint:
                    steering, risk = self.forecast_command
            valid = valid and clear_predicted_corridor(pixels, black, threshold, route)
        elif not best_dual and not self.joint:
            # v5单侧L／弱关联只允许右转或直行，不扩大协议到未经确认的左转。
            # 推荐点仍在入口直道时不额外给10%右转；真正到达圆弧后，右转量
            # 由连续路线自然增大。双侧路径保留有符号修正，允许及时回正。
            steering = max(0,steering)
        if self.joint and valid:
            # 两边或外侧两臂已确认时，额外核对看得见的实际赛车线；未使用模板假定的黑格。
            if not forecast:
                valid = clear_predicted_corridor(pixels, black, threshold, route, minimum=0)
            if valid:
                self._advance_joint(best, best_dual, best_corner, forecast, now)
                if self.second_exit_at is not None and now - self.second_exit_at >= 450:
                    out['joint_complete'] = True
                out['road_section'] = ('obtuse_exit' if self.second_exit_at is not None else 'obtuse'
                                       if self.second_corner else 'connector' if self.first_exit is not None
                                       else 'right_angle' if angle else 'start_straight')
        if self.predictive and valid:
            if self.joint and forecast == 4:
                self.rail_at = now
            elif self.joint and not forecast and risk >= 0.2:
                self.rail_at = None
            if not forecast or forecast == 3:
                self.forecast_anchor_at = now
                if angle > 0 and (best_corner == 2 or forecast == 3 or round(risk*1000) >= 200):
                    self.front_model, self.front_at = best, now
                else:
                    self.front_model = self.front_at = None
            if forecast != 2:
                self.visible_edge_at = now
                self.forecast_route = route
                self.forecast_command = steering, risk
        # R7实跑出现100→371及负修正→508的切换，来自距离下限覆盖路线。
        # R8取消该下限；留0字段便于与旧逐帧证据比较，不以历史L强行续转。
        out['turn_floor'] = 0
        reason = 'ready' if valid else 'stabilizing'
        if self.joint and not valid:
            # 新拟合可信度不足或白区证据短缺时，既不发新转向也不刷新上一帧的时钟。
            if self.forecast_route is not None and _corridor_blocked(black, self.forecast_route):
                reason = 'corridor_blocked'
            else:
                reason = 'observation_missed'
        out.update(valid=valid, source=source, steering=steering,
                   bend=int(round(risk*1000)), confidence=confidence, stage=stage,
                   corner_observed=best_corner==2, corner_age_ms=0 if self.corner_at is None else now-self.corner_at,
                   measured_edges=('none' if forecast == 2 else 'front' if forecast == 3 else 'single' if forecast == 1 else
                                   'straight_rail' if forecast == 4 else 'left_and_front' if best_corner == 2 else
                                   'pair' if best_dual else 'associated_left'),
                   path_kind='racing_arc_prediction' if angle>0 else 'straight_observation',
                   path_visibility='projected' if best[1] else 'predicted_near_blind',
                   parameters=list(best[4]), route=route, score=best_score,
                   reason=reason)
        return out

    def _advance_joint(self, best, dual, corner, forecast, now):
        """依据现在看到的弧尾或出弯双边推进弯序，毫秒仅用于确认钝角出口。"""
        _, _, yaw, angle = best[4]
        observed = dual or corner == 2 or forecast == 3
        near_exit = (angle > 0 and abs(yaw + angle) <= math.radians(16) and
                     self.racing is not None and self.racing['exit_s'] >= -5)
        last_bend = self.front_model
        connected_exit = False
        if angle == 0 and dual and last_bend is not None:
            _, _, previous_yaw, previous_angle = last_bend[4]
            # 车头转过后原角点可能直接出画，用当前两条出口边确认上一已跟踪弯道。
            if self.racing_key == last_bend[4] and abs(previous_yaw + previous_angle) <= math.radians(20):
                connected_exit = (self.racing['exit_s'] >= -10 and _same_rail(last_bend, previous_angle, best))
        if angle > 1 and not self.second_corner and near_exit and observed:
            self.first_exit = best
        elif not self.second_corner and connected_exit and last_bend[4][3] > 1:
            self.first_exit = best
        elif not self.second_corner and angle == 0 and dual and self.first_exit is not None:
            if _same_rail(self.first_exit, self.first_exit[4][3], best):
                self.first_exit = best
        if angle == OBTUSE_TURN and (dual or corner == 2):
            self.second_corner = True
        if angle > 1 and (dual or corner == 2):
            self.first_corner = True
        if not self.second_corner:
            return
        if angle == OBTUSE_TURN and near_exit and observed:
            self.second_exit = best
        elif connected_exit and last_bend[4][3] == OBTUSE_TURN:
            self.second_exit = best
        # 有出弯双边，或实测外边且车头已越过切点，才开始连续观察出口；
        # 单条无新证据的历史路线不能让本段正常结束。
        exit_now = (self.second_exit is not None and
                    ((angle == 0 and dual and _same_rail(self.second_exit, self.second_exit[4][3], best)) or
                     (angle == OBTUSE_TURN and near_exit and observed and self.racing['exit_s'] >= 12)))
        if exit_now:
            if angle == 0:
                self.second_exit = best
            if self.second_exit_at is None:
                self.second_exit_at = now
        else:
            self.second_exit_at = None
