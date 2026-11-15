"""用未参与拟合的30cm新摆位检查冻结候选；只读候选和原图，不修改参数。

中央x159取点、逐列灰度窗口及预测146.17均在下载验证图前确定。
人工仍已知目标距离与预测，因此属于留出距离验证，不是盲标。
"""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


FROZEN_SHA256 = "a42dfc005fc3719be50c0cb22eedfb7051996f6ec4444a01ebc5aadcb8bcafc0"


def main():
    """读取固定会话的3张原图，保留灰度取点及相对30cm的误差，无返回值。

    距离单位cm、行号从0开始。三帧是同一次静态摆位的重复采图，不能
    作为三次独立物理验证。候选哈希变化／图像不合格／结果已存在均拒绝，
    防止不知情重拟合或覆盖原证据。没有预设官方精度阈值，报告实际误差。
    """
    evidence = Path(__file__).resolve().parent
    root = evidence.parent.parent
    model_file = evidence / "distance_model_candidate.json"
    model_bytes = model_file.read_bytes()
    model_hash = hashlib.sha256(model_bytes).hexdigest()
    if model_hash != FROZEN_SHA256:
        raise ValueError("Frozen model was modified")
    model = json.loads(model_bytes)
    a, b, c = (model["coefficients"][key] for key in ("a", "b", "c"))
    def distance_at(y):
        return float((b - y * c) / (y - a))
    source = root / "vision/data/captures/final_mount_20261108/v03_center_0006"
    files = sorted(source.glob("data_*.jpg"))
    if len(files) != 3:
        raise ValueError("Exactly three verified original images required")
    frames = []
    for file in files:
        gray = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
        if gray is None or gray.shape != (240, 320):
            raise ValueError("Invalid original image: " + str(file))
        measurements = []
        for distance_cm, lo, hi in [(20,190,208), (30,125,181), (40,102,122)]:
            y = int(np.argmin(gray[lo:hi, 159]) + lo)
            measurements.append(dict(operator_distance_cm=distance_cm, y_window=[lo,hi],
                center_x159_darkest_y=y,
                x145_175_darkest_y=(np.argmin(gray[lo:hi,145:176],axis=0)+lo).tolist(),
                x159_gray_profile=gray[lo:hi,159].tolist(),
                model_distance_cm=distance_at(y), signed_distance_error_cm=distance_at(y)-distance_cm))
        frames.append(dict(file=file.name, sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                           measurements=measurements))
    rows30 = [frame["measurements"][1]["center_x159_darkest_y"] for frame in frames]
    y30 = float(np.median(rows30))
    payload = dict(status="single_held_out_distance_evaluated_no_refit", model_sha256=model_hash,
        source=str(source.relative_to(root)), operator_distance_cm=30,
        operator_distance_basis="Contextual confirmation after move 60cm wire to 30cm instruction",
        expected_30cm_y=model["held_out_30cm_prediction_y"], observed_30cm_y=rows30,
        signed_row_error_px=y30-model["held_out_30cm_prediction_y"],
        mapped_30cm_cm=distance_at(y30), signed_distance_error_cm=distance_at(y30)-30,
        reading_only_y_plus_minus_2px_distance_cm=sorted([distance_at(y30-2),distance_at(y30+2)]),
        frames=frames,
        limitations=["One held-out physical distance with three frames; not blind annotation or full-range accuracy",
            "Unknown ruler precision, round wire height/bends, lens distortion and mount repeatability remain",
            "The +/-2px calculation covers reading variation only; not total error or a confidence interval",
            "No refit, no controller change, no dynamic or vehicle acceptance"])
    out = evidence / "distance_30cm_validation.json"
    if out.exists():
        raise FileExistsError("Preserve validation evidence: " + str(out))
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:payload[key] for key in ["model_sha256", "expected_30cm_y", "observed_30cm_y",
        "signed_row_error_px", "mapped_30cm_cm", "signed_distance_error_cm",
        "reading_only_y_plus_minus_2px_distance_cm"]},indent=2))


if __name__ == "__main__":
    main()
