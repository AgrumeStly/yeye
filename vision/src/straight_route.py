"""直道专用观测器：只读当前双边，不搜索转弯模板、不沿用历史路径。

输入固定320x240灰度字节。复用现有黑块采样／双边白走廊检查，使用
已有近似投影只计算纠偏代理量；输出不是经过完整标定的厘米或航向。
无导入时相机／UART副作用，可在电脑和CanMV执行同一核心。
"""
from lite_lap_route import _threshold, _grid, _pair_anchors


class StraightRoute:
    """每帧只拟合一条直道，至少三帧／80ms一致后才许可。

    横向项使车回到道路中央，斜率项使车头顺道路方向；不能仅用横向
    偏差等到压线再纠正。增益与几何门槛为现场待验候选。
    """
    def __init__(self):
        self.reset()

    def reset(self):
        """失线、异常时间或几何跳变后撤销连续许可，没有历史续跑。"""
        self.last_at = None
        self.previous_error = None
        self.stable = 0
        self.stable_at = 0

    def update(self, pixels, now):
        """now为本次取图开始的相对毫秒；返回原始误差及拒绝原因。

        无效帧也必须发送新序号无效包，不能只停止打印或重复上一有效包。
        近似坐标的30／50参照必须处于当前真实支持范围内；直道弯折或
        靠边超出微调能力时撤许可，绝不把直线外推穿过锐角。
        """
        result = dict(valid=False, source='unknown', steering=0, bend=0,
                      confidence=0, support=0, reason='no_pair')
        if len(pixels) != 320 * 240 or not isinstance(now, int) or now < 0:
            self.reset()
            result['reason'] = 'input'
            return result
        timing_ok = self.last_at is None or 0 < now - self.last_at <= 150
        if not timing_ok:
            self.reset()
        self.last_at = now
        threshold = _threshold(pixels)
        black, _, _ = _grid(pixels, threshold)
        points = _pair_anchors(black)
        result.update(threshold=threshold, support=len(points))
        if len(points) < 8:
            self.stable = 0
            self.previous_error = None
            return result
        count = len(points)
        mx = sum(p[0] for p in points) / count
        mz = sum(p[1] for p in points) / count
        low = min(p[1] for p in points)
        high = max(p[1] for p in points)
        denominator = sum((p[1] - mz) ** 2 for p in points)
        slope = sum((p[1] - mz) * (p[0] - mx) for p in points) / max(0.001, denominator)
        near = mx + slope * (30 - mz)
        far = mx + slope * (50 - mz)
        residual = (sum((p[0] - mx - slope * (p[1] - mz)) ** 2 for p in points) / count) ** 0.5
        # 只比较短半段斜率会把6像素网格的一格跳变放大成假折角：
        # 2026-11-18地面第1961帧支持13行、整体残差0.475却因斜率差>0.12停车。
        # 改为比较斜率变化在实际支持跨度内形成的横向弯折量，并限制单点残差。
        # 所有量沿用近似投影代理单位，不冒称已标定厘米；缺半段／跨度不足仍拒绝。
        slopes = []
        half_spans = []
        for half in ([p for p in points if p[1] <= mz], [p for p in points if p[1] > mz]):
            if len(half) < 3:
                continue
            hx = sum(p[0] for p in half) / len(half)
            hz = sum(p[1] for p in half) / len(half)
            den = sum((p[1] - hz) ** 2 for p in half)
            slopes.append(sum((p[1] - hz) * (p[0] - hx) for p in half) / max(0.001, den))
            half_spans.append(max(p[1] for p in half) - min(p[1] for p in half))
        max_residual = max(abs(p[0] - mx - slope * (p[1] - mz)) for p in points)
        slope_delta = abs(slopes[0] - slopes[1]) if len(slopes) == 2 else None
        # 等长V形折线对整段直线的最大偏离约为斜率差×半跨度/4；
        # 这里用该有界几何量筛折角，避免无量纲斜率误差与实际观测长度脱节。
        deflection = slope_delta * min(half_spans) / 4 if slope_delta is not None else None
        result.update(half_slope_delta=slope_delta, bend_deflection=deflection,
                      max_residual=max_residual, half_depth_spans=half_spans)
        result.update(near_error=near, far_error=far, heading_proxy=slope,
                      residual=residual, depth_min=low, depth_max=high)
        gates = (('depth_coverage', low <= 30 and high >= 50 and high - low >= 25),
                 ('position', abs(near) <= 12 and abs(far) <= 18),
                 ('heading', abs(slope) <= 0.35), ('global_fit', residual <= 1.2),
                 ('single_point_fit', max_residual <= 1.8),
                 ('two_halves', len(slopes) == 2 and min(half_spans) >= 8),
                 ('bend_displacement', deflection is not None and deflection <= 1.5))
        failures = [name for name, passed in gates if not passed]
        result['geometry_failures'] = failures
        if failures:
            self.stable = 0
            self.previous_error = None
            result['reason'] = 'outside_straight_envelope'
            return result
        error = max(-1.0, min(1.0, 0.7 * near / 25.0 + 1.2 * slope))
        if self.previous_error is None or abs(error - self.previous_error) > 0.22 or not timing_ok:
            self.stable = 1
            self.stable_at = now
        else:
            self.stable += 1
        self.previous_error = error
        result.update(valid=self.stable >= 3 and now - self.stable_at >= 80,
                      source='current_pair', steering=int(round(error * 1000)),
                      confidence=80, reason='ready' if self.stable >= 3 and now - self.stable_at >= 80 else 'stabilizing')
        return result
