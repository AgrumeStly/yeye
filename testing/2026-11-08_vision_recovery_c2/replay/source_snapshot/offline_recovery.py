"""V-06独立C2候选：局部双边关联与按真实时间管理失效／再捕获。

冻结R1/C1全部原字段保持不变，新增结果只在recovery_observation内。
坐标单位像素、时间单位毫秒。当前实测、历史角色推断和未知严格分开；
不外推缺失侧，不根据赛道宽度补线，也不产生可行驶的整弯轨迹。
"""

from dataclasses import asdict, dataclass
import math

import numpy as np

from offline_curve import CurveDetector


@dataclass(frozen=True)
class RecoveryConfig:
    """开发数据上的保守门槛，均非官方要求或实车控制参数。"""

    component_min_area: int = 80  # 已有至少6行内缘锚点时，允许裁短的内侧黑带。
    component_min_span: int = 25
    component_vote_fraction: float = .85
    anchor_min_y_span: int = 25
    reacquire_ms: int = 80  # 至少两次当前观测且真实间隔达到此值才稳定。
    session_gap_ms: int = 700  # 数据稀疏时清空角色／方向，不把旧图当连续。
    history_ttl_ms: int = 300  # 仅诊断的旧方向／角色最多保存此时长。
    jump_margin_px: float = 15.
    max_edge_rate_px_s: float = 220.  # 图像运动拒绝门槛，非车辆速度。
    role_gate_px: float = 20.


class RecoveryDetector:
    """每个会话单独实例或显式传会话键；不得用文件名／帧号选择算法分支。"""

    def __init__(self, config=None):
        self.spatial = CurveDetector()
        self.config = config or RecoveryConfig()
        self.reset()

    def reset(self):
        """会话、时钟倒退、超时或调用方复位均丢弃历史，不留下转向指令。"""
        self.session = None
        self.last_ms = None
        self.last_pair = None
        self.last_pair_ms = None
        self.stable_since_ms = None
        self.support_count = 0
        self.last_turn = None
        self.last_turn_ms = None

    def parameters(self):
        """保存实际R1、C1及C2参数，支持源码和证据快照复跑。"""
        return dict(**self.spatial.parameters(), recovery=asdict(self.config))

    def _pair(self, image, baseline):
        """只验证同帧已测内缘；解除C1固定近端门槛但不降低R1几何门槛。

        黑带须分别关联两个不同连通域，且每侧锚点本身有足够纵向跨度。
        这避免将同一黑带两面配成道路双边。较短黑带门槛只作用于有六行
        直接支持的裁切段；反光／连接／印字不能通过时明确拒绝。
        """
        path = baseline['pair_samples']
        if (baseline['threshold'] is None or not path or
                set(baseline['reasons'])-{'reference_row_not_bracketed'}):
            return [], [], 'r1_geometry_or_quality_rejected'
        labels, _ = self.spatial._components(image, baseline['threshold'])
        ids = {}
        for side in ('left', 'right'):
            inset = -1 if side == 'left' else 1
            votes = [int(labels[p['y'], p[side]+inset]) for p in path]
            nonzero = set(votes)-{0}
            if not nonzero:
                return [], [], 'missing_dark_component_anchor'
            chosen = max(nonzero, key=votes.count)
            supported = [p for p, vote in zip(path, votes) if vote == chosen]
            ys, xs = np.where(labels == chosen)
            if (len(supported)/len(path) < self.config.component_vote_fraction or
                    supported[-1]['y']-supported[0]['y'] < self.config.anchor_min_y_span or
                    len(ys) < self.config.component_min_area or
                    max(int(np.ptp(ys)), int(np.ptp(xs))) < self.config.component_min_span):
                return [], [], 'insufficient_distinct_component_support'
            ids[side] = chosen
        if ids['left'] == ids['right']:
            return [], [], 'same_component_road_roles_unresolved'
        corners = []
        for side in ('left', 'right'):
            corners.extend(self.spatial._corners(path, side, ids[side], labels))
        return [dict(p) for p in path], corners, None

    @staticmethod
    def _difference(first, second):
        """同一y实测锚点比较；没有重合行时未知，禁止外推来消除突变。"""
        previous = {p['y']: p for p in first}
        differences = [max(abs(p['left']-previous[p['y']]['left']),
                           abs(p['right']-previous[p['y']]['right']))
                       for p in second if p['y'] in previous]
        return float(np.median(differences)) if len(differences) >= 3 else None

    def detect(self, image, timestamp_ms, session_key):
        """输入采集软件真实毫秒与会话键；只用本帧和历史，绝不接收未来帧。

        返回当前局部实测点、固定y120可用性、重新捕获进度、有限历史推断
        及减速／停车建议。建议只是给后续控制评审的状态，不发送运动指令。
        时间缺失／重复也清空时序，避免把人工10fps播放时间代替采集时钟。
        """
        b = self.spatial.detect(image)
        valid_time = (isinstance(timestamp_ms, (int, float)) and not isinstance(timestamp_ms, bool)
                      and math.isfinite(timestamp_ms) and timestamp_ms >= 0 and session_key is not None)
        reset_reason = None
        if not valid_time:
            reset_reason = 'missing_or_invalid_capture_time'
        elif self.session != session_key:
            reset_reason = 'session_changed'
        elif self.last_ms is not None and timestamp_ms <= self.last_ms:
            reset_reason = 'non_increasing_capture_time'
        elif self.last_ms is not None and timestamp_ms-self.last_ms > self.config.session_gap_ms:
            reset_reason = 'capture_gap_timeout'
        if reset_reason:
            self.reset()
        now = timestamp_ms if valid_time else None
        pair, corners, rejection = self._pair(image, b)
        difference = None
        jump = False
        if pair and self.last_pair and now is not None and self.last_pair_ms is not None:
            dt = now-self.last_pair_ms
            if 0 < dt <= self.config.session_gap_ms:
                difference = self._difference(self.last_pair, pair)
                jump = difference is None or difference > (self.config.jump_margin_px+
                       self.config.max_edge_rate_px_s*dt/1000)
        if pair and valid_time:
            if self.stable_since_ms is None or jump or self.support_count == 0:
                self.stable_since_ms = now
                self.support_count = 1
            else:
                self.support_count += 1
            stable = self.support_count >= 2 and now-self.stable_since_ms >= self.config.reacquire_ms
            self.last_pair, self.last_pair_ms = pair, now
        else:
            stable = False
            self.support_count = 0
            self.stable_since_ms = None
        directions = [{c['direction'] for c in corners if c['side'] == side}
                      for side in ('left', 'right')]
        turn = next(iter(directions[0])) if (len(directions[0]) == 1 and directions[0] == directions[1]) else None
        if turn and valid_time:
            self.last_turn, self.last_turn_ms = turn, now
        history = dict(state='unknown', turn_hint=None, turn_age_ms=None, boundary_role=None,
                       role_age_ms=None, usable_as_current_path=False)
        if valid_time and self.last_turn_ms is not None:
            age = now-self.last_turn_ms
            if not turn and 0 <= age <= self.config.history_ttl_ms:
                history.update(state='historical_inference', turn_hint=self.last_turn, turn_age_ms=age)
            elif age > self.config.history_ttl_ms:
                self.last_turn = self.last_turn_ms = None
        # 单边角色只作有限历史推断：当前单边点与上一对实测点同y比较，
        # 只有一个角色满足门槛才记录；不生成另一侧，也不给偏差／转向。
        if valid_time and not pair and self.last_pair_ms is not None:
            age = now-self.last_pair_ms
            single = b['unpaired_boundary']
            if age <= self.config.history_ttl_ms and single:
                prior = {p['y']: p for p in self.last_pair}
                errors = {}
                for side in ('left', 'right'):
                    values = [abs(p['x']-prior[p['y']][side]) for p in single['points'] if p['y'] in prior]
                    if len(values) >= 6:
                        errors[side] = float(np.median(values))
                matches = [s for s, error in errors.items() if error <= self.config.role_gate_px]
                if len(matches) == 1:
                    history.update(state='historical_inference', boundary_role=matches[0], role_age_ms=age)
        reference = bool(pair and pair[0]['y'] <= 120 <= pair[-1]['y'] and b['valid'])
        near = bool(pair and pair[-1]['y'] >= self.spatial.config.near_bottom_y)
        observation = dict(revision='v06-c2', current_state='direct_pair_observed' if pair else 'unknown',
             pair_samples=pair, centerline=[dict(x=(p['left']+p['right'])/2, y=p['y']) for p in pair],
             y_range=[pair[0]['y'], pair[-1]['y']] if pair else None,
             near_available=near, fixed_reference_observed=reference,
             fixed_reference_deviation_px=b['deviation_px'] if reference else None,
             turn_hint=turn, corners=corners, historical=history, timestamp_ms=now,
             temporal_state=('stable_observation' if stable else 'reacquiring') if pair and valid_time else 'unknown',
             time_reset=reset_reason, edge_jump=jump, edge_difference_px=difference,
             stable_support_count=self.support_count, rejection=rejection,
             advice='monitor_only' if reference and stable else ('slow_down_required' if near else 'stop_required'),
             control_ready=False, full_turn_path_available=False)
        b['recovery_observation'] = observation
        self.session, self.last_ms = session_key if valid_time else None, now
        return b
