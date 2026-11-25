"""从当前灰度网格重估首弯外边；坐标沿用现有地面投影代理单位。"""
import math
from lite_lap_route import GRID_STEP, GW, GY0, GY1, _pixel

# 持续单侧证据和瞬时白走廊的上限分别核对；低置信度帧不能续租强观测。
PREDICTION_ANCHOR_MS = 1200
PREDICTION_GAP_MS = 240


def _project_row(gy):
    y = gy * GRID_STEP + 1
    return ((7802.22222222222 - 15.555555555555546 * y) / (y + 38.11111111111108),
            48.0 / (y + 38.11111111111108))


def _left_rail(black):
    """在近区多行找细黑边与它右侧的白区，拟合车道左边直线。

    使用未扩张黑格求中心；平行背景或断裂噪声不能用一个采样点参与拟合。
    返回行驶方向、法向偏移和最远实测投影。单靠此结果不会确认新弯。
    """
    samples = []
    rows = range((108 + GRID_STEP - 1) // GRID_STEP, 216 // GRID_STEP, 18 // GRID_STEP)
    for gy in rows:
        base = gy * GW
        start = None
        for gx in range(1, GW - 4):
            if black[base + gx]:
                if start is None:
                    start = gx
            elif start is not None:
                if 2 <= gx - start <= 60 // GRID_STEP and not any(black[base + gx:base + gx + 4]):
                    z, scale = _project_row(gy)
                    x = ((start + gx - 1) * GRID_STEP / 2 + 1 - 159.5) * scale
                    samples.append((x, z))
                    break
                start = None
    if len(samples) < 4:
        return None
    dx, dz = samples[0][0] - samples[-1][0], samples[0][1] - samples[-1][1]
    length = math.sqrt(dx * dx + dz * dz)
    if length < 8:
        return None
    ux, uz = dx / length, dz / length
    yaw = math.atan2(ux, uz)
    offsets = [uz * x - ux * z for x, z in samples]
    offset = sum(offsets) / len(offsets)
    if not (-48 <= offset <= -8 and -1.3 <= yaw <= 0.44 and max(offsets) - min(offsets) <= 4):
        return None
    return ux, uz, yaw, offset, max(ux * x + uz * z for x, z in samples)


def fitted_outer_l(black, occupied, template, angle=math.pi / 2):
    """用左外边两臂的当前像素求交，返回指定右转角的已验证模板或None。

    横边沿左边方向的投影应近似等长，按4代理单位归桶。用不同横向
    区段计票，并验证实际连接处、两臂覆盖和内侧白区。网格和候选数有界。
    """
    rail = _left_rail(black)
    if rail is None:
        return None
    ux, uz, yaw, offset, last = rail
    right_angle = angle > 1
    slope = 0 if right_angle else math.cos(angle) / math.sin(angle)
    start_margin = 5 if right_angle else -4
    votes = {}
    first_row = max(GY0 + 3, (60 + GRID_STEP - 1) // GRID_STEP)
    for gy in range(first_row, min(GY1, 162 // GRID_STEP)):
        base = gy * GW
        z, scale = _project_row(gy)
        for gx in range(1, GW - 1):
            if not black[base + gx]:
                continue
            x = (gx * GRID_STEP + 1 - 159.5) * scale
            lateral = uz * x - ux * z - offset
            # 钝角处的出弯臂沿来向仍有前进分量，扣掉后才得到两臂的交点纵距。
            along = ux * x + uz * z - lateral * slope
            if 8 <= lateral <= 85 and start_margin <= along - last <= 90:
                key = round(along / 4)
                votes[key] = votes.get(key, 0) | (1 << int(lateral / 5))
    # 每个桶最多17个横向区段；用定宽掩码，避免为每个黑格分配集合。
    ranked = [(bin(mask).count('1'), key) for key, mask in votes.items()]
    ranked.sort(reverse=True)
    for support, key in ranked[:3]:
        if support < (6 if right_angle else 4):
            break
        along = key * 4
        join = _pixel(offset * uz + along * ux, -offset * ux + along * uz)
        if join is None or not occupied[join]:
            continue
        candidate = template(offset + 25, along - (25 if right_angle else 25 * math.tan(angle / 2)), yaw, angle)
        if candidate is None:
            continue
        arms = candidate[6][:2]
        if (all(len(arm) >= 3 and sum(occupied[i] for i in arm) >= 0.70 * len(arm) for arm in arms)
                and len(candidate[8]) >= 4 and sum(black[i] for i in candidate[8]) <= len(candidate[8]) // 5
                and not any(black[i] for i in candidate[1])):
            return candidate
    return None


def fitted_left_forecast(black, previous, template):
    """只见左边时重估横向偏差和朝向，沿用最近模型的弯点纵向位置。

    当前纵边无法单独推断前方弯点，因此仅用于短程预测，不能续租双边/L形。
    """
    rail = _left_rail(black)
    if rail is None:
        return None
    ux, uz, yaw, offset, _ = rail
    cx, cz, _, angle = previous[4]
    return template(offset + 25, cx * ux + cz * uz, yaw, angle)


def fitted_front_edge(black, previous, template):
    """已知右弯后，沿预期前横线的法向取样，逐帧重估前线距离和角度。

    单条线约束方向和法向距离。弯心沿线坐标沿用上次模型，直到新双侧可见。
    采样只看当前未扩张黑格，隔开墙面上沿；输出代理坐标与实测格数。
    """
    cx, cz, yaw, angle = previous[4]
    # 在出弯坐标里，原前边始终是左边。直角和钝角只相差出弯方向的旋转量。
    heading = yaw + angle
    ux, uz = math.sin(heading), math.cos(heading)
    across_center = cx * ux + cz * uz
    depth = -(cx * uz - cz * ux) + 25
    samples = []
    used = set()
    across_start = across_center + 25 * math.tan(angle / 2)
    for across in range(round(across_start) - 42, round(across_start) + 36, 7):
        for shift in (0, -3, 3, -6, 6, -9, 9, -12, 12, -15, 15):
            forward = depth + shift
            cell = _pixel(across * ux - forward * uz, across * uz + forward * ux)
            if cell is None or cell // GW < GY0 + 3 or not black[cell]:
                continue
            if cell not in used:
                used.add(cell)
                samples.append((across, forward))
            break
    if len(samples) < 5 or samples[-1][0] - samples[0][0] < 28:
        return None
    mean_across = sum(p[0] for p in samples) / len(samples)
    mean_depth = sum(p[1] for p in samples) / len(samples)
    variance = sum((p[0] - mean_across) ** 2 for p in samples)
    slope = sum((p[0] - mean_across) * (p[1] - mean_depth) for p in samples) / variance
    if abs(slope) > 0.45 or max(abs(z - mean_depth - slope * (x - mean_across)) for x, z in samples) > 6:
        return None
    change = -math.atan(slope)
    updated_yaw = yaw + change
    if not -math.radians(105) <= updated_yaw <= math.radians(30):
        return None
    front = mean_depth * math.cos(change) + mean_across * math.sin(change)
    heading += change
    ux, uz = math.sin(heading), math.cos(heading)
    across_center = cx * ux + cz * uz
    x, z = across_center * ux + (25 - front) * uz, across_center * uz - (25 - front) * ux
    a, b = math.sin(updated_yaw), math.cos(updated_yaw)
    candidate = template(x * b - z * a, x * a + z * b, updated_yaw, angle)
    if candidate is None:
        return None
    return candidate, len(samples), front


def clear_predicted_corridor(pixels, black, threshold, route, minimum=3):
    """检查最靠近车的四个可见路线格，相机近端盲区的不计入。"""
    cells = set()
    for point in route:
        cell = _pixel(*point)
        if cell is None or cell in cells:
            continue
        x, y = cell % GW * GRID_STEP + 1, cell // GW * GRID_STEP + 1
        if black[cell] or pixels[y * 320 + x] <= threshold:
            return False
        cells.add(cell)
        if len(cells) == 4:
            return True
    return len(cells) >= minimum
