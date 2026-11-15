"""电脑端灰度道路基线。仅依赖 OpenCV/NumPy，不是 CanMV 板上程序。

所有距离是像素；原点在左上，x 向右、y 向下。本模块无跨帧状态，
每次调用重建候选与路径，避免旧路径在失线后被当成新识别结果。
"""

from dataclasses import asdict, dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class BoundaryConfig:
    """320×240输入的集中参数；未经标定，不把像素宽度换成真实路宽。"""

    width: int = 320
    height: int = 240
    roi_top: int = 65
    roi_bottom: int = 215
    row_step: int = 5
    band_radius: int = 1
    threshold_floor: int = 20
    threshold_ceiling: int = 100
    background_margin: int = 18
    min_contrast: int = 12
    min_run: int = 3
    max_run: int = 55
    border_margin: int = 3
    min_pair_width: int = 55
    max_pair_width: int = 300
    max_interior_dark: float = 0.08
    max_gap_rows: int = 2
    max_dx_per_dy: float = 2.8
    min_pair_points: int = 6
    min_pair_span: int = 25
    reference_y: int = 120
    reference_tolerance: int = 10
    min_quality: float = 0.45


class BoundaryDetector:
    """逐帧检测器；不保存前帧宽度、斜率或中线，无需圈界或初始化图。"""

    def __init__(self, config=None):
        self.config = config or BoundaryConfig()

    def _runs(self, image):
        """窄带灰度中值抑制单像素噪声，找有白侧对比的深色条。

        ROI大津阈值受背景灰度上限约束，避免整块灰地板被阈为黑色。
        候选必须具有宽度和侧边对比；黑块外侧可出画，但朝道路的内边缘
        必须真正在图内发生明暗过渡，不能把图像边框当道路边界。
        返回逐行候选；每个候选保留左右端，配对时只取面向白路面的内侧。
        """
        c = self.config
        roi = image[c.roi_top:c.roi_bottom + 1]
        otsu, _ = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        threshold = float(np.clip(min(otsu, np.percentile(roi, 65) - c.background_margin),
                                  c.threshold_floor, c.threshold_ceiling))
        rows = []
        for y in range(c.roi_bottom, c.roi_top - 1, -c.row_step):
            profile = np.median(image[y-c.band_radius:y+c.band_radius+1], axis=0)
            mask = profile <= threshold
            changes = np.diff(np.r_[False, mask, False].astype(np.int8))
            starts, ends = np.flatnonzero(changes == 1), np.flatnonzero(changes == -1) - 1
            runs = []
            for start, end in zip(starts.tolist(), ends.tolist()):
                if not (c.min_run <= end-start+1 <= c.max_run):
                    continue
                dark = float(np.median(profile[start:end+1]))
                left_contrast = (float(np.median(profile[max(0, start-8):start])) - dark
                                 if start > c.border_margin else -1.)
                right_contrast = (float(np.median(profile[end+1:min(c.width, end+9)])) - dark
                                  if end < c.width-1-c.border_margin else -1.)
                if max(left_contrast, right_contrast) >= c.min_contrast:
                    runs.append(dict(start=start, end=end, lc=left_contrast, rc=right_contrast))
            rows.append(dict(y=y, runs=runs, mask=mask))
        return threshold, rows

    def _pair_path(self, rows):
        """在同帧由近到远建立候选对的有向图，取支持最多且连续的路径。

        不取全图最左/最右黑像素。每个候选对要求白色内部、合理局部间距、
        两个朝内的明暗过渡；相邻窄带允许有限斜移和最多两条缺失窄带。
        间距限制仅用于拒绝退化配对，绝不拿固定宽度补出另一边。
        转角可能导致同一行多个交点，此基线仍可能误关联，必须保留审核证据。
        """
        c = self.config
        nodes = []
        for row_index, row in enumerate(rows):
            for i, left in enumerate(row['runs']):
                for right in row['runs'][i+1:]:
                    lx, rx = left['end'], right['start']
                    if lx <= c.border_margin or rx >= c.width-1-c.border_margin:
                        continue
                    if not c.min_pair_width <= rx-lx <= c.max_pair_width:
                        continue
                    if min(left['rc'], right['lc']) < c.min_contrast:
                        continue
                    interior_dark = float(row['mask'][lx+2:rx-1].mean())
                    if interior_dark > c.max_interior_dark:
                        continue
                    center = (lx+rx)/2
                    # 中心只作轻微排序偏好，不强制车道跨过图像中心。
                    reward = 1.0 - abs(center-(c.width-1)/2)/c.width*0.12
                    node = dict(y=row['y'], left=lx, right=rx, row=row_index,
                                score=reward, previous=None, count=1)
                    for previous in reversed(nodes):
                        gap = row_index-previous['row']
                        if gap > c.max_gap_rows+1:
                            break
                        if gap <= 0:
                            continue
                        dy = previous['y']-row['y']
                        dl, dr = abs(lx-previous['left']), abs(rx-previous['right'])
                        if max(dl, dr) > c.max_dx_per_dy*dy+3:
                            continue
                        score = previous['score']+reward-0.004*(dl+dr)-0.12*(gap-1)
                        if score > node['score']:
                            node.update(score=score, previous=previous, count=previous['count']+1)
                    nodes.append(node)
        if not nodes:
            return []
        node = max(nodes, key=lambda n: n['score'])
        path = []
        while node is not None:
            path.append(dict(y=node['y'], left=node['left'], right=node['right']))
            node = node['previous']
        return sorted(path, key=lambda p: p['y'])

    def _single_path(self, rows):
        """没有双边时保留最长单条可见候选链；不推断缺失侧或中线。

        左右标签由候选链平均横坐标相对画面中心给出，只是审核用的暂定侧别。
        单边视角本来就可能无法区分弯内/弯外，结果明确注明侧别有歧义。
        """
        c = self.config
        nodes = []
        for row_index, row in enumerate(rows):
            for run in row['runs']:
                x = (run['start']+run['end'])/2
                n = dict(row=row_index, y=row['y'], x=x, run=run, score=1., previous=None)
                for p in reversed(nodes):
                    gap = row_index-p['row']
                    if gap > c.max_gap_rows+1:
                        break
                    if gap <= 0:
                        continue
                    dx, dy = abs(x-p['x']), p['y']-n['y']
                    if dx <= c.max_dx_per_dy*dy+3:
                        score = p['score']+1.-0.008*dx-0.12*(gap-1)
                        if score > n['score']:
                            n.update(score=score, previous=p)
                nodes.append(n)
        if not nodes:
            return None, []
        node = max(nodes, key=lambda n: n['score'])
        chain = []
        while node is not None:
            chain.append(node)
            node = node['previous']
        side = 'left' if np.mean([n['x'] for n in chain]) < (c.width-1)/2 else 'right'
        points = [dict(x=n['run']['end' if side == 'left' else 'start'], y=n['y'],
                       state='visible') for n in reversed(chain)]
        return side, points

    def detect(self, image):
        """输入uint8二维灰度图；返回可JSON序列化结果，失败中线为空且偏差为null。

        仅双边路径在y=120附近有实测支持并通过覆盖检查才提供可用中线。
        偏差为该参考行中点减159.5，右为正；归一值除以159.5并限幅。
        线性插值只在同帧相邻双边点之间，禁止向缺失侧/视野外外推。
        """
        c = self.config
        result = dict(valid=False, quality=0., reasons=[], left=[], right=[], centerline=[],
                      left_state='missing', right_state='missing', pair_samples=[],
                      reference_y=c.reference_y, deviation_px=None, deviation_normalized=None,
                      threshold=None, temporal_state='none')
        if image is None or image.dtype != np.uint8 or image.shape != (c.height, c.width):
            result['reasons'] = ['unsupported_image_shape_or_type']
            return result
        if np.ptp(image[c.roi_top:c.roi_bottom+1]) < c.min_contrast:
            result['reasons'] = ['no_contrast_no_road']
            return result
        threshold, rows = self._runs(image)
        result['threshold'] = threshold
        path = self._pair_path(rows)
        result['pair_samples'] = path
        if path:
            for side in ('left', 'right'):
                result[side] = [dict(x=p[side], y=p['y'], state='visible') for p in path]
                result[side+'_state'] = 'visible'
            span = path[-1]['y']-path[0]['y']
            density = len(path)/(span/c.row_step+1)
            quality = min(1., len(path)/12)*density
            result['quality'] = round(quality, 4)
            if len(path) < c.min_pair_points or span < c.min_pair_span:
                result['reasons'].append('insufficient_pair_support')
            # 参考区域不能随当前视野任意移动，防止偏差的含义跨帧变化。
            ys = np.array([p['y'] for p in path])
            if not (ys[0] <= c.reference_y <= ys[-1]):
                result['reasons'].append('reference_row_not_bracketed')
            elif np.min(abs(ys-c.reference_y)) > c.reference_tolerance:
                result['reasons'].append('reference_row_gap')
            if quality < c.min_quality:
                result['reasons'].append('low_pair_quality')
            if not result['reasons']:
                result['valid'] = True
                result['centerline'] = [dict(x=(p['left']+p['right'])/2, y=p['y']) for p in path]
                centers = [(p['left']+p['right'])/2 for p in path]
                deviation = float(np.interp(c.reference_y, ys, centers)-(c.width-1)/2)
                result['deviation_px'] = round(deviation, 3)
                result['deviation_normalized'] = int(np.clip(round(deviation/((c.width-1)/2)*1000), -1000, 1000))
        else:
            side, points = self._single_path(rows)
            if side is not None:
                result[side] = points
                result[side+'_state'] = 'visible'
                result['reasons'] = ['single_boundary_only_side_ambiguous']
            else:
                result['reasons'] = ['no_boundary_candidates']
        return result

    def parameters(self):
        """供回放保存实际使用的完整参数，避免文档参数与运行结果脱节。"""
        return asdict(self.config)
