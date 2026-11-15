"""V-06 T2：多帧地面运动、二维弯道模板及五节点赛道先验的离线候选。

目的：替代P1逐图像行保持宽度的假设，研究相机转动时的二维推荐路线。
所有推断仅访问当前及历史；图像坐标为像素，模型地面坐标为候选cm，
时间为原采集软件ms。中央纵向标定不能证明全图度量准确，横向投影
另加平地、固定相机和50cm直道宽度假设；因此输出始终不可直接控制。
本模块不导入串口、相机或电机，不改变R1/C1/C2/P1及唯一20字节协议。
"""

from dataclasses import asdict, dataclass
import math

import cv2
import numpy as np


@dataclass(frozen=True)
class TemporalRouteConfig:
    """开发参数，均非官方评分门槛；真实板上耗时和全图几何尚未验收。"""

    width_cm: float = 50.
    lateral_projection_gain: float = 48.  # 由初始直道50cm与像素宽度作近似，需记录残差。
    history_ms: int = 1200
    gap_ms: int = 700
    history_max_frames: int = 6
    max_flow_step_cm: float = 24.
    max_flow_yaw_deg: float = 35.
    min_flow_inliers: int = 10
    flow_residual_cm: float = 2.
    fit_support_cm: float = 3.
    prediction_limit_ms: int = 1200
    lap_limit: int = 1  # 比赛目标一圈；两圈录像仅在评估模式继续观察。


class GroundProjection:
    """候选平面投影：中央20/40/60cm约束＋另行声明的横向平地假设。

    世界坐标X向车右、Z向车前，原点候选为车头最前端地面投影。
    a/b/h精确通过三条中央量距点；横向gain独立，不能称完整标定。
    投影只供离线几何研究；原已验证范围仍是中央20～60cm。
    """

    def __init__(self, gain=48.):
        y = np.array([198., 113., 73.]); z = np.array([20., 40., 60.])
        self.a, self.b, self.h = np.linalg.solve(np.column_stack([y, np.ones(3), z]), y*z)
        self.gain = gain
        self.matrix = np.array([[gain, 0, -159.5*gain], [0, self.a, self.b], [0, 1, -self.h]])
        self.inverse = np.linalg.inv(self.matrix)

    @staticmethod
    def transform(points, matrix):
        """投影有限二维点；分母接近0时返回NaN，由调用者剔除而非夹边。"""
        p = np.asarray(points, dtype=float).reshape(-1, 2)
        q = np.column_stack([p, np.ones(len(p))]) @ matrix.T
        good = np.abs(q[:, 2]) > 1e-6
        result = np.full((len(p), 2), np.nan)
        result[good] = q[good, :2]/q[good, 2:]
        return result

    def ground(self, points):
        """像素→候选地面cm；不可用返回NaN。"""
        return self.transform(points, self.matrix)

    def image(self, points):
        """候选地面cm→像素；不把画外点夹成可信边界。"""
        return self.transform(points, self.inverse)


class GroundMotion:
    """稀疏金字塔LK＋前后向检查＋候选地面RANSAC，估计相邻地面变换。

    使用地面候选ROI，不依赖场外家具定位。非平面背景、模糊、大跳变或
    内点分布不足时拒绝运动更新；不能以失败次数伪造里程或恒定转速。
    """

    def __init__(self, projection, config):
        self.projection = projection; self.config = config; self.previous = None

    def reset(self):
        """会话或时钟重置时丢弃前帧，防止跨会话光流。"""
        self.previous = None

    def update(self, gray):
        """输入当前320×240灰度，返回前帧→当前的刚体矩阵与诊断。"""
        old = self.previous; self.previous = gray.copy()
        out = dict(available=False, reason='first_frame', inliers=0, matches=0,
                   yaw_deg=None, translation_cm=None, residual_cm=None)
        if old is None:
            return None, out
        roi = np.zeros_like(gray); roi[55:228, 12:308] = 255
        points = cv2.goodFeaturesToTrack(old, maxCorners=200, qualityLevel=.008,
                                        minDistance=5, mask=roi, blockSize=5)
        if points is None or len(points) < 12:
            out['reason'] = 'too_few_ground_features'; return None, out
        now, ok, _ = cv2.calcOpticalFlowPyrLK(old, gray, points, None,
                    winSize=(25, 25), maxLevel=3,
                    criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT, 30, .01))
        back, bok, _ = cv2.calcOpticalFlowPyrLK(gray, old, now, None, winSize=(25, 25), maxLevel=3)
        p = points.reshape(-1, 2); q = now.reshape(-1, 2)
        good = (ok.ravel() > 0)&(bok.ravel() > 0)&(np.linalg.norm(back.reshape(-1, 2)-p, axis=1) < 1.5)
        good &= (q[:, 0] > 2)&(q[:, 0] < 317)&(q[:, 1] > 45)&(q[:, 1] < 235)
        p = self.projection.ground(p[good]); q = self.projection.ground(q[good])
        out['matches'] = len(p)
        if len(p) < 12:
            out['reason'] = 'forward_backward_rejected'; return None, out
        affine, inliers = cv2.estimateAffinePartial2D(p, q, method=cv2.RANSAC,
                ransacReprojThreshold=self.config.flow_residual_cm, maxIters=1000, confidence=.99)
        if affine is None:
            out['reason'] = 'ransac_failed'; return None, out
        chosen = inliers.ravel().astype(bool); n = int(chosen.sum()); out['inliers'] = n
        if n < self.config.min_flow_inliers or n/len(p) < .5:
            out['reason'] = 'insufficient_inliers'; return None, out
        # RANSAC先寻找一致点；随后强制刚体，禁止把缩放误差累计为虚假路宽。
        a = p[chosen]; b = q[chosen]; ac = a.mean(axis=0); bc = b.mean(axis=0)
        u, _, vt = np.linalg.svd((a-ac).T@(b-bc)); rotation = vt.T@u.T
        if np.linalg.det(rotation) < 0:
            vt[-1] *= -1; rotation = vt.T@u.T
        t = bc-rotation@ac
        residual = np.linalg.norm(a@rotation.T+t-b, axis=1)
        angle = math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))
        scale = float(np.linalg.norm(affine[:, 0])); span = np.ptp(a, axis=0)
        out.update(yaw_deg=angle, translation_cm=t.tolist(), residual_cm=float(np.median(residual)),
                   fitted_scale=scale, span_cm=span.tolist())
        if not .88 < scale < 1.12 or abs(angle) > self.config.max_flow_yaw_deg or np.linalg.norm(t) > self.config.max_flow_step_cm:
            out['reason'] = 'motion_jump_or_scale'; return None, out
        if span[0] < 12 or span[1] < 12 or np.median(residual) > 1.6:
            out['reason'] = 'degenerate_or_nonplanar'; return None, out
        matrix = np.eye(3); matrix[:2, :2] = rotation; matrix[:2, 2] = t
        out.update(available=True, reason=None)
        return matrix, out


class RoadTemplates:
    """在候选鸟瞰平面匹配两侧带宽固定的直道／折角二维模型。

    模型边界始终称推断：模板只表达已知路宽及节点角度先验，当前黑色
    像素接近模型时才有支持。模板不得被重命名为实测双边；单带两面
    不形成50cm净宽。搜索保留当前支持率、分侧支持和次优差距诊断。
    """

    # 网格1候选cm/格；X[-100,100]，Z[-40,150]，包含转弯后侧向道路。
    grid_transform = np.array([[1., 0., 100.], [0., -1., 150.], [0., 0., 1.]])
    shape = (201, 191)

    def __init__(self, projection, config):
        self.projection = projection; self.config = config
        self.warp = self.grid_transform@projection.matrix
        self.anchors = np.empty((0, 2))

    def evidence(self, gray, threshold):
        """只保留有延伸尺度的黑组件，削弱散字；不能保证排除全部印字。"""
        dark = (gray <= threshold).astype(np.uint8); dark[:35] = 0; dark[231:] = 0
        count, labels, stats, _ = cv2.connectedComponentsWithStats(dark)
        clean = np.zeros_like(dark)
        for i in range(1, count):
            if stats[i, cv2.CC_STAT_AREA] >= 90 and max(stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]) >= 35:
                # 背景黑墙不是地面黑带：拒绝附着ROI上缘且宽厚填充的大块。
                # 该判据仍可能漏掉低矮背景，不能宣称具备语义分割能力。
                x,y,w,h,area=stats[i]
                if y<=36 and w>=280 and area>=5500 and area/(w*h)>.35:
                    continue
                clean[labels == i] = 255
        bev = cv2.warpPerspective(clean, self.warp, self.shape, flags=cv2.INTER_NEAREST)
        visible = np.zeros_like(gray); visible[35:231] = 255
        valid = cv2.warpPerspective(visible, self.warp, self.shape, flags=cv2.INTER_NEAREST) > 0
        distance = cv2.distanceTransform((bev == 0).astype(np.uint8), cv2.DIST_L2, 3)
        return bev, valid, distance

    @staticmethod
    def geometry(parameters, angle_deg, width=50.):
        """生成双边两条射线和中心路线；参数为角点X/Z与入口朝向弧度。

        左右指沿行驶方向，不按图像x排序。锐角处用真实二维偏置线相交
        连接，避免横行均值跨过内侧尖角。几何仍是先验，非实测标定。
        """
        params = np.atleast_2d(parameters); yaw = params[:, 2]
        incoming = np.stack([np.sin(yaw), np.cos(yaw)], axis=1)
        outgoing = np.stack([np.sin(yaw+math.radians(angle_deg)), np.cos(yaw+math.radians(angle_deg))], axis=1)
        normal_a = np.stack([incoming[:, 1], -incoming[:, 0]], axis=1)
        normal_b = np.stack([outgoing[:, 1], -outgoing[:, 0]], axis=1)
        corner_offset = (normal_a+normal_b)/(1+np.sum(normal_a*normal_b, axis=1))[:, None]*width/2
        positions = np.concatenate([np.arange(-140., 0., 4.), np.arange(0., 145., 4.)])
        directions = np.where((positions < 0)[None, :, None], incoming[:, None], outgoing[:, None])
        rays = positions[None, :, None]*directions
        # 偏置折线的顶点与原中心角点不在相同沿程位置，分别从偏置顶点采样。
        left = params[:, None, :2]-corner_offset[:, None]+rays
        right = params[:, None, :2]+corner_offset[:, None]+rays
        center = params[:, None, :2]+rays
        return left, right, center

    def score(self, parameters, angle, valid, distance, prior=None):
        """向量化比较两条模型边与当前／对齐历史黑像素的距离。

        仅可见网格参与；无支持的画外模型不获奖励。截断距离降低文字
        干扰，分侧支持单独保留。先验惩罚只平滑，不把缺证据变成观测。
        """
        params = np.atleast_2d(parameters); left, right, _ = self.geometry(params, angle, self.config.width_cm)
        all_points = np.stack([left, right], axis=1)
        x = np.rint(all_points[..., 0]+100).astype(int); y = np.rint(150-all_points[..., 1]).astype(int)
        bounds = (x >= 0)&(x < self.shape[0])&(y >= 0)&(y < self.shape[1])
        xc = np.clip(x, 0, self.shape[0]-1); yc = np.clip(y, 0, self.shape[1]-1)
        seen = bounds&valid[yc, xc]; d = distance[yc, xc]
        support = (d <= self.config.fit_support_cm)&seen
        count = seen.sum(axis=(1, 2)); side_count = seen.sum(axis=2)
        side_support = support.sum(axis=2)/np.maximum(1, side_count)
        loss = (np.minimum(d, 12)*seen).sum(axis=(1, 2))/np.maximum(1, count)
        # 观测多的模型略优，避免只让极短一截与印字巧合相交而得高分。
        loss += np.maximum(0, 22-count)*.35
        yaw=params[:,2];u=np.column_stack([np.sin(yaw),np.cos(yaw)])
        v=np.column_stack([np.sin(yaw+math.radians(angle)),np.cos(yaw+math.radians(angle))])
        def distances_to_rays(points):
            # 各点到两条有方向射线的最短距离，不能用无限直线穿过内弯。
            delta=points[None]-params[:,None,:2]
            first=delta-np.minimum(0,np.sum(delta*u[:,None],axis=2))[...,None]*u[:,None]
            second=delta-np.maximum(0,np.sum(delta*v[:,None],axis=2))[...,None]*v[:,None]
            return np.minimum(np.linalg.norm(first,axis=2),np.linalg.norm(second,axis=2))
        origin_distance=distances_to_rays(np.zeros((1,2)))[:,0]
        loss+=np.maximum(0,origin_distance-23)*.6
        loss[origin_distance>40]=100
        if len(self.anchors):
            anchor_error=distances_to_rays(self.anchors)
            loss+=np.minimum(anchor_error,30).mean(axis=1)*.65
        if prior is not None:
            loss += np.minimum(np.linalg.norm(params[:, :2]-prior[:2], axis=1), 60)*.018
            delta = (params[:, 2]-prior[2]+np.pi)%(2*np.pi)-np.pi
            loss += np.abs(delta)*.7
        loss[count < 12] = 100
        return loss, side_support, count

    def fit(self, valid, distance, angle, prior=None, broad=True):
        """先粗搜再局部细化；历史变换只作为候选起点，当前图可推翻它。"""
        pools = []
        if broad:
            c, d, yaw = np.meshgrid(np.arange(-28, 29, 7.), np.arange(12, 145, 10.),
                                     np.deg2rad(np.arange(-35, 36, 10.)), indexing='ij')
            pools.append(np.column_stack([(c*np.cos(yaw)+d*np.sin(yaw)).ravel(),
                                          (-c*np.sin(yaw)+d*np.cos(yaw)).ravel(), yaw.ravel()]))
        if prior is not None:
            dx, dz, dy = np.meshgrid([-12., -6., 0., 6., 12.], [-12., -6., 0., 6., 12.],
                                      np.deg2rad([-12., -6., 0., 6., 12.]), indexing='ij')
            pools.append(prior+np.column_stack([dx.ravel(), dz.ravel(), dy.ravel()]))
        parameters = np.vstack(pools)
        loss, _, _ = self.score(parameters, angle, valid, distance, prior)
        best = parameters[np.argmin(loss)]
        dx, dz, dy = np.meshgrid([-3., 0., 3.], [-3., 0., 3.], np.deg2rad([-3., 0., 3.]), indexing='ij')
        refine = best+np.column_stack([dx.ravel(), dz.ravel(), dy.ravel()])
        values, supports, counts = self.score(refine, angle, valid, distance, prior)
        i = int(np.argmin(values)); p = refine[i]
        return dict(parameters=p, loss=float(values[i]), side_support=supports[i].tolist(),
                    visible_samples=int(counts[i]), angle_deg=angle)


class TemporalRouteDetector:
    """会话状态：有限对齐历史、累计视觉转角、五节点阶段和局部推荐线。

    地图初始化仅由主控确认的起点条件开启；其他静态组/旧会话不给全图
    节点定位。赛程一圈，评估模式允许第二圈继续记录但禁止额外起停指令。
    """

    turn_angles = [90., 38.5, 103., 38.5, 90.]
    nodes = ['bottom_left', 'left_shoulder', 'apex_77', 'right_shoulder', 'bottom_right']

    def __init__(self, config=None, use_history=True, use_map=True):
        self.config = config or TemporalRouteConfig(); self.projection = GroundProjection(self.config.lateral_projection_gain)
        self.templates = RoadTemplates(self.projection, self.config)
        self.motion = GroundMotion(self.projection, self.config)
        self.use_history = use_history; self.use_map = use_map; self.reset()

    def reset(self):
        """清空会话内像素历史与位置；节点不是永久车载记忆。"""
        self.session = None; self.last_ms = None; self.history = []; self.model = None
        self.yaw_total = 0.; self.motion_missing_ms = 0.; self.last_evidence_ms = None
        self.motion.reset(); self.steps = 0
        self.passed_nodes=0; self.corner_engaged=False; self.engaged_ms=None
        self.finish_events=0; self.last_finish_event=None; self.last_transition_ms=None

    def parameters(self):
        """导出配置与已声明几何假设，方便回放哈希与板上依赖审查。"""
        return dict(config=asdict(self.config), projection=self.projection.matrix.tolist(),
                    projection_status='central_1D_plus_unvalidated_lateral_plane_assumption',
                    use_history=self.use_history, use_map=self.use_map, turns=self.turn_angles,
                    initial='whole vehicle right of start line, heading left, clockwise; operator confirmed',
                    evaluation='two laps observed; competition target one lap; no automatic STOP')

    def update(self, gray, timestamp_ms, session, threshold, map_initialized=False, pair_samples=None, finish_event=None):
        """仅当前帧和真实历史输入；输出模型线及诊断，不改固定y120偏差。"""
        if gray is None or gray.shape != (240, 320) or gray.dtype != np.uint8:
            raise ValueError('expected 320x240 uint8 grayscale')
        c = self.config; reason = None
        valid_time = isinstance(timestamp_ms, (int, float)) and np.isfinite(timestamp_ms) and timestamp_ms >= 0
        if session != self.session:
            self.reset(); self.session = session; reason = 'session_reset'
        elif not valid_time or (self.last_ms is not None and (timestamp_ms <= self.last_ms or timestamp_ms-self.last_ms > c.gap_ms)):
            self.reset(); self.session = session; reason = 'clock_or_capture_gap_reset'
        dt = timestamp_ms-self.last_ms if valid_time and self.last_ms is not None else 0
        self.last_ms = timestamp_ms if valid_time else None; self.steps += 1
        matrix, motion = self.motion.update(gray)
        if not valid_time:
            matrix = None; self.history = []; self.model = None; self.motion.reset()
        if matrix is not None and self.use_history:
            self.yaw_total += motion['yaw_deg']; self.motion_missing_ms = max(0., self.motion_missing_ms-dt*.15)
            warped = []
            grid_motion = self.templates.grid_transform@matrix@np.linalg.inv(self.templates.grid_transform)
            for h in self.history:
                if 0 <= timestamp_ms-h['ms'] <= c.history_ms:
                    image = cv2.warpPerspective(h['image'], grid_motion, self.templates.shape, flags=cv2.INTER_NEAREST)
                    warped.append(dict(image=image, ms=h['ms']))
            self.history = warped
            if self.model is not None:
                self.model[:2] = GroundProjection.transform(self.model[None, :2], matrix)[0]
                self.model[2] -= math.radians(motion['yaw_deg'])
        elif self.steps > 1:
            self.history = []; self.model = None; self.motion_missing_ms += dt
        bev, visible, current_distance = self.templates.evidence(gray, float(threshold if threshold is not None else 90))
        anchors=pair_samples or []
        self.templates.anchors=self.projection.ground([[(p['left']+p['right'])/2,p['y']] for p in anchors]) if anchors else np.empty((0,2))
        fused = bev.copy()
        if self.use_history:
            for h in self.history:
                # 对齐后的历史只有限保留，当前黑色证据权重更高；不闭合整幅白区。
                fused = np.maximum(fused, (h['image']*(max(0., 1-(timestamp_ms-h['ms'])/c.history_ms)*.65)).astype(np.uint8))
        fused_distance = cv2.distanceTransform((fused < 80).astype(np.uint8), cv2.DIST_L2, 3)
        if valid_time:
            self.history.append(dict(image=bev, ms=timestamp_ms)); self.history = self.history[-c.history_max_frames:]
        # 地图阶段暂由累计右转角给出候选；配合模型残差诊断，不能宣称精确地图定位。
        total = max(0., self.yaw_total)
        cumulative = np.cumsum(self.turn_angles)
        relocalized=False
        if finish_event is not None and finish_event!=self.last_finish_event and valid_time and map_initialized:
            self.last_finish_event=finish_event;self.finish_events+=1
            # 已有独立F1因果事件作为整圈拓扑锚点；不能证明车尾越线。
            # 漏掉的节点计数显式记为重新定位，不伪称逐弯均跟踪成功。
            self.passed_nodes=5*self.finish_events;self.corner_engaged=False;self.model=None;relocalized=True
        node=self.passed_nodes%5;lap=self.passed_nodes//5
        heading=total%360
        angle = self.turn_angles[node] if self.use_map and map_initialized else 90.
        incoming_heading = 0. if node == 0 else cumulative[node-1]
        prior = self.model
        corner = self.templates.fit(visible, fused_distance, angle, prior, broad=True)
        # 直道用同一几何表达，但角度0时顶点无物理意义，评分能避免凭空强加转弯。
        straight = self.templates.fit(visible, fused_distance, 0., None, broad=True)
        active_corner = corner['loss']+.25 < straight['loss']
        fit = corner if active_corner else straight
        selected = fit['parameters']; selected_angle = fit['angle_deg']
        direct_loss, direct_support, _ = self.templates.score(selected[None], selected_angle, visible, current_distance)
        support = direct_support[0]
        # 当前有C2支持时，路线还必须与同帧中点相容；单侧支持不能叫双边观测。
        anchor_error=None
        if len(self.templates.anchors):
            center_points=self.templates.geometry(selected,selected_angle,c.width_cm)[2][0]
            anchor_error=float(np.median(np.min(np.linalg.norm(self.templates.anchors[:,None]-center_points[None],axis=2),axis=1)))
        supported = max(support) >= .55 and float(direct_loss[0]) < 5. and (anchor_error is None or anchor_error<=6.)
        progress=-math.degrees(selected[2])
        if self.use_map and map_initialized and valid_time and active_corner and supported:
            if not self.corner_engaged and -12<=progress<=angle*.55 and 0<selected[1]<80:
                self.corner_engaged=True;self.engaged_ms=timestamp_ms
            if self.corner_engaged and progress>=angle*.65 and timestamp_ms-self.engaged_ms>=250:
                self.passed_nodes+=1;self.corner_engaged=False;self.last_transition_ms=timestamp_ms
                self.model=None
        if supported and valid_time:
            self.last_evidence_ms = timestamp_ms; self.model = selected.copy()
        age = timestamp_ms-self.last_evidence_ms if valid_time and self.last_evidence_ms is not None else None
        inferred = supported or (age is not None and age <= c.prediction_limit_ms and matrix is not None)
        left, right, center = self.templates.geometry(selected, selected_angle, c.width_cm)
        # 规划从车头附近向前，保留弯中侧向段；只输出观察窗口内的路线，不补车后。
        path = center[0]; keep = (path[:, 1] >= 12)&(path[:, 1] <= 125)&(np.abs(path[:, 0]) <= 100)
        path = path[keep]
        def pixels(points):
            p = self.projection.image(points)
            p = p[np.isfinite(p).all(axis=1)]
            return np.round(p, 2).tolist()
        return dict(revision='v06-t2', time_reset=reason, capture_ms=timestamp_ms,
             motion=motion, history_frames=len(self.history), yaw_total_deg=round(self.yaw_total, 3),
             map=dict(initialized=bool(map_initialized and self.use_map and valid_time), node=self.nodes[node],
                      lap_observation=lap+1, competition_lap_limit=c.lap_limit,
                      heading_deg=round(heading, 2), state='geometry_sequence_hypothesis',
                      engaged=self.corner_engaged,passed_node_count=self.passed_nodes,
                      finish_observations=self.finish_events,finish_anchor_relocalized=relocalized,
                      competition_finish_seen=self.finish_events>=c.lap_limit,
                      missing_motion_ms=round(self.motion_missing_ms), whole_vehicle_finish_verified_by_camera=False),
             state='current_supported_model' if supported else 'history_prediction' if inferred else 'map_prior_only',
             advice='slow_required' if inferred else 'stop_required',
             model=dict(parameters=selected.tolist(), angle_deg=selected_angle, corner_selected=active_corner,
                        loss=fit['loss'], straight_loss=straight['loss'], corner_loss=corner['loss'],
                        current_side_support=support.tolist(), visible_samples=fit['visible_samples'],
                        anchor_error_cm=anchor_error,last_supported_age_ms=age),
             recommended_path_px=pixels(path), model_left_px=pixels(left[0]), model_right_px=pixels(right[0]),
             recommended_path_ground=path.tolist(),
             path_basis='current_and_past_constrained_geometric_hypothesis' if inferred else 'unverified_nominal_prior',
             protocol_valid=False, control_ready=False, vehicle_clearance_verified=False,
             fixed_y120_redefined=False)
