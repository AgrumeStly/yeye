"""V-05三线组的非盲辅助读数与一维候选换算；不修改原图或车辆参数。

窗口在人工看过原图后选定，仅定位中央杜邦线身，不用于通用检测或准确率评价。
本脚本只依赖v03_center_0005，候选在30cm独立验证采集前冻结。
"""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    """读取3帧及人工选定窗口，保存读数／哈希和未验收模型，无返回值。

    输入距车头地面投影的距离单位为cm，像素x右正、y下正且从0开始。
    仅将x159列作为同一中央观察方向；跨列读数用于显示线身弯曲，
    不以较大区域平均值伪装精确地面直线。文件缺失／解码失败时直接拒绝。
    """
    evidence = Path(__file__).resolve().parent
    root = evidence.parent.parent
    source = root / "vision/data/captures/final_mount_20261108/v03_center_0005"
    files = sorted(source.glob("data_*.jpg"))
    if len(files) != 3:
        raise ValueError("Exactly three verified original frames are required")
    windows = [(20, 192, 206), (40, 105, 119), (60, 67, 82)]
    frames = []
    for file in files:
        gray = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
        if gray is None or gray.shape != (240, 320):
            raise ValueError("Invalid original image: " + str(file))
        measurements = []
        for distance_cm, lo, hi in windows:
            measurements.append(dict(distance_cm=distance_cm, y_window=[lo, hi],
                center_x159_darkest_y=int(np.argmin(gray[lo:hi, 159]) + lo),
                x145_175_darkest_y=(np.argmin(gray[lo:hi, 145:176], axis=0) + lo).tolist(),
                x159_gray_profile=gray[lo:hi, 159].tolist()))
        frames.append(dict(file=file.name,
            sha256=hashlib.sha256(file.read_bytes()).hexdigest(), measurements=measurements))
    distances = np.array([20., 40., 60.])
    ys = np.array([np.median([f["measurements"][i]["center_x159_darkest_y"]
                              for f in frames]) for i in range(3)])
    if not np.all(np.diff(ys) < 0):
        raise ValueError("Reference rows must decrease as distance increases")
    # 一维射影形式y=(a*d+b)/(d+c)。三个参数由三个点恰好解出，
    # 拟合点残差为零不证明准确；逆式仅作为20..60cm区间的待验证候选。
    a, b, c = np.linalg.solve(np.column_stack((distances, np.ones(3), -ys)), ys * distances)
    def distance_at(y):
        return float((b - y * c) / (y - a))
    def row_at(distance_cm):
        return float((a * distance_cm + b) / (distance_cm + c))
    payload = dict(status="candidate_frozen_before_independent_30cm_validation",
        source=str(source.relative_to(root)), distance_source="operator_report_20_40_60_cm",
        center_column_x=159, windows_are_post_view_nonblind=True,
        frames=frames, fit_distance_cm=distances.tolist(), fit_rows_y=ys.tolist(),
        model="y=(a*d+b)/(d+c); d_cm=(b-y*c)/(y-a)",
        coefficients=dict(a=float(a), b=float(b), c=float(c)),
        measured_distance_interval_cm=[20, 60], candidate_row_interval=[float(ys[-1]), float(ys[0])],
        y120_candidate_cm=distance_at(120),
        held_out_30cm_prediction_y=row_at(30),
        row_distance_candidates={str(y): distance_at(y) for y in [80,100,120,140,160,180,198]},
        limitations=["No independent validation yet; exact three-point fit is not an accuracy metric",
                    "Round wire height, slight bends, shadows, unknown ruler precision and distortion remain",
                    "Central direction only; do not extrapolate outside measured interval or use as full homography",
                    "No camera, detector, firmware or controller parameter is updated"])
    out = evidence / "distance_model_candidate.json"
    if out.exists():
        raise FileExistsError("Preserve frozen candidate; do not overwrite " + str(out))
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key:payload[key] for key in ["fit_rows_y", "coefficients",
        "y120_candidate_cm", "held_out_30cm_prediction_y", "row_distance_candidates"]}, indent=2))


if __name__ == "__main__":
    main()
