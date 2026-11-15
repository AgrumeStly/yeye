"""V-06电脑端弯道观测候选；复用冻结R1，所有坐标／阈值均为像素。

固定y120偏差保持R1原义。新增近场段和双边关联转角只供离线审核，
不是控制轨迹、转角角度或电机指令。无跨帧状态，不根据文件名识别场景。
"""

from dataclasses import asdict, dataclass

import cv2
import numpy as np

from offline_boundary import BoundaryConfig, BoundaryDetector


@dataclass(frozen=True)
class CurveConfig:
    """连续黑带候选参数；未经官方色块／动态数据验证，不作为比赛指标。"""

    component_top: int = 30  # 外弯肘部可能高于R1的y65；仅用于二维形状观测。
    component_min_area: int = 250
    component_min_span: int = 60
    component_support_fraction: float = 0.85
    component_inset: int = 1  # 朝已观测黑段内部取样，避开三行中值边缘的1像素抖动。
    near_bottom_y: int = 200
    polygon_epsilon: float = 6.0
    arm_min_length: float = 30.0
    incoming_min_dy: float = 30.0
    outgoing_max_slope: float = 0.5
    anchor_distance: float = 6.0
    min_anchor_points: int = 6


class CurveDetector:
    """每帧独立提取；R1原字段逐项保持，新增信息统一放curve_observation。

    近弯参考行缺侧时，可以记录较近的实测双边段，但valid仍是固定y120
    是否可用。近场不输出另一个可混用的deviation。单侧、短文字误配和
    两条同向场外线继续拒绝；两个黑带轮廓也不能冒充道路双边。
    """

    def __init__(self, boundary_config=None, curve_config=None):
        self.baseline = BoundaryDetector(boundary_config)
        self.config = curve_config or CurveConfig()

    def parameters(self):
        """记录R1与候选的全部实际参数，供复跑；不修改冻结参数文件。"""
        return dict(boundary=self.baseline.parameters(), curve=asdict(self.config))

    def _components(self, image, threshold):
        """用原灰度全局阈值构建连通域，不闭合间隙、不修改原图。

        连通域用于验证已观测双边确属两条不同长黑带，及关联二维肘部。
        反光造成断裂时允许拒绝新增观测，不能跨断点补连通关系。此实现
        适用于当前连续黑带，尚不适用于官方分离色块的拓扑关联。
        """
        c, b = self.config, self.baseline.config
        mask = (image <= threshold).astype(np.uint8)
        mask[:c.component_top] = 0
        mask[b.roi_bottom+1:] = 0
        _, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        strong = {i for i in range(1, len(stats))
                  if stats[i, cv2.CC_STAT_AREA] >= c.component_min_area
                  and max(stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT])
                  >= c.component_min_span}
        return labels, strong

    def _anchored_components(self, path, labels, strong):
        """双边内缘逐点投票，不把一条黑带两面配成双边；返回关联ID或None。

        R1内缘来自三行中值，单行端点可能相差1像素；仅朝已知黑段内部
        偏移1像素查询连通域，内缘坐标不移动。不在周围任意搜索；局部
        反光或文字导致关联不足时拒绝。
        """
        ids = {}
        for side in ('left', 'right'):
            inset = -self.config.component_inset if side == 'left' else self.config.component_inset
            votes = [int(labels[p['y'], p[side]+inset]) for p in path]
            chosen = max(strong, key=votes.count) if strong else 0
            if not chosen or votes.count(chosen)/len(path) < self.config.component_support_fraction:
                return None
            ids[side] = chosen
        return ids if ids['left'] != ids['right'] else None

    def _corners(self, path, side, component, labels):
        """找与实测内缘同侧的肘部；拟合只简化观测轮廓，不向外延长线段。

        肘部须有向下的入弯臂、近水平的出弯臂，两臂均足够长且顶点远离
        图像／ROI裁切边。入弯臂须贴合至少6个该侧实测点，防止误用同一
        黑带背面的轮廓。返回图像中的左／右展开方向，不是地面转角角度。
        """
        c, b = self.config, self.baseline.config
        contours, _ = cv2.findContours((labels == component).astype(np.uint8),
                                      cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        anchors = np.array([[p[side], p['y']] for p in path], dtype=float)
        for contour in contours:
            polygon = cv2.approxPolyDP(contour, c.polygon_epsilon, True).reshape(-1, 2)
            for i, vertex in enumerate(polygon):
                x, y = map(int, vertex)
                if not (b.border_margin < x < b.width-1-b.border_margin
                        and c.component_top+b.border_margin < y < b.roi_bottom-b.border_margin):
                    continue
                neighbors = (polygon[i-1], polygon[(i+1) % len(polygon)])
                for incoming, outgoing in (neighbors, neighbors[::-1]):
                    v_in, v_out = incoming-vertex, outgoing-vertex
                    if (v_in[1] < c.incoming_min_dy or np.linalg.norm(v_in) < c.arm_min_length
                            or abs(v_out[0]) < c.arm_min_length
                            or abs(v_out[1]) > c.outgoing_max_slope*abs(v_out[0])):
                        continue
                    # 只比较投影在线段范围内的点，严禁拿外推直线贴合点。
                    t = (anchors-vertex) @ v_in / float(v_in @ v_in)
                    distance = np.linalg.norm(anchors-(vertex+t[:, None]*v_in), axis=1)
                    supported = (t >= 0) & (t <= 1) & (distance <= c.anchor_distance)
                    if int(supported.sum()) < c.min_anchor_points:
                        continue
                    candidates.append(dict(side=side, vertex=dict(x=x, y=y),
                                           incoming_end=dict(x=int(incoming[0]), y=int(incoming[1])),
                                           outgoing_end=dict(x=int(outgoing[0]), y=int(outgoing[1])),
                                           direction='right' if v_out[0] > 0 else 'left',
                                           anchor_count=int(supported.sum()),
                                           anchor_error_px=round(float(np.mean(distance[supported])), 3),
                                           state='observed_contour_vertex'))
        # 多个近似轮廓肘部不能靠排序选择控制方向；保留全部供双侧一致性检查。
        return candidates

    def detect(self, image):
        """输入与R1相同；返回R1原结果及独立观测，不改图、不保存前帧。

        只允许R1所有几何／质量门槛已过、唯一欠缺为固定参考行覆盖的近段
        进入补充观测。两侧肘部同向时才提示转向，单边肘部仅留诊断。
        无图／无对比／支持不足时所有新增路径和方向从空值开始。
        """
        result = self.baseline.detect(image)
        observation = dict(revision='v06-c1', near_field=dict(available=False, y_range=None, centerline=[]),
                           accepted_pair_samples=[], corners=[], turn_hint=None,
                           status='insufficient_observed_geometry', reasons=[],
                           control_ready=False, full_turn_path_available=False)
        result['curve_observation'] = observation
        path = result['pair_samples']
        if result['threshold'] is None or not path:
            observation['reasons'] = ['no_supported_pair']
            return result
        if result['reasons'] and result['reasons'] != ['reference_row_not_bracketed']:
            observation['reasons'] = ['baseline_geometry_or_quality_rejected']
            return result
        if path[-1]['y'] < self.config.near_bottom_y:
            observation['reasons'] = ['pair_not_connected_to_near_field']
            return result
        if not result['valid'] and path[0]['y'] <= result['reference_y']:
            observation['reasons'] = ['missing_near_field_not_a_shorter_preview']
            return result
        labels, strong = self._components(image, result['threshold'])
        ids = self._anchored_components(path, labels, strong)
        if ids is None:
            observation['reasons'] = ['pair_not_anchored_to_two_distinct_long_bands']
            return result
        observation['accepted_pair_samples'] = [dict(p) for p in path]
        observation['near_field'] = dict(available=True, y_range=[path[0]['y'], path[-1]['y']],
                                        centerline=[dict(x=(p['left']+p['right'])/2, y=p['y']) for p in path])
        for side in ('left', 'right'):
            observation['corners'].extend(self._corners(path, side, ids[side], labels))
        side_directions = [{p['direction'] for p in observation['corners'] if p['side'] == side}
                           for side in ('left', 'right')]
        if len(side_directions[0]) == 1 and side_directions[0] == side_directions[1]:
            observation['turn_hint'] = next(iter(side_directions[0]))
            observation['status'] = 'paired_bend_observed'
        else:
            observation['status'] = 'near_field_only'
            observation['reasons'] = ['no_unambiguous_two_sided_bend']
        return result
