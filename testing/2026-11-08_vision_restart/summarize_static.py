"""汇总本轮五姿态静态证据；只读原件，不调算法、不连接板卡、不驱动实车。

输出文件清单／哈希、姿态来源、粗略人工复核表和y120原灰度条带坐标图。
人工复核已看过算法结果，属于非盲复核；绝不据此计算泛化准确率。
"""

import csv
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vision/tools"))
from verify_capture import verify

EVIDENCE = Path(__file__).resolve().parent
SOURCE = ROOT / "vision/data/captures/final_mount_20261108"
OUTPUT = EVIDENCE / "static_summary"
# 文件名是实际下载会话；位移和角度只是给主控的摆位目标，未独立实测。
POSES = [
    ("center", "v03_center_0002", "center_0002", 0, 0, 80, 239),
    ("offset_left", "v03_offset_left_0001", "offset_left_0001", -5, 0, 107, 267),
    ("offset_right", "v03_offset_right_0001", "offset_right_0001", 5, 0, 55, 215),
    ("heading_left", "v03_heading_left_0001", "heading_left_0001", 0, -5, 109, 274),
    ("heading_right", "v03_heading_right_0001", "heading_right_0001", 0, 5, 34, 197),
]


def sha256(path):
    """返回文件字节SHA-256，用于追溯及核对原件未被派生步骤改动。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    """UTF-8带BOM供Windows表格查看，列名取首行；不回写采集原始日志。"""
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    """检查5个会话和冻结参数，生成15张清单与原灰度坐标条带，不提取新路径。"""
    OUTPUT.mkdir(exist_ok=True)
    manifest, metadata, manual, groups = [], [], [], []
    baseline = json.loads((EVIDENCE / "center_0002/validation.json").read_text(encoding="utf-8"))
    frozen = {name: sha256(ROOT / name) for name in
              ("vision/src/offline_boundary.py", "vision/tools/replay_offline.py", "vision/tools/verify_capture.py")}
    if any(digest != baseline["code_hashes"][name] for name, digest in frozen.items()):
        raise RuntimeError("Frozen source differs from centered review")
    parameters = (EVIDENCE / "center_0002/parameters.json").read_bytes()
    # 原图y114..126裁条仅作放大读数，原图未改动。统一x坐标标尺，不画算法点。
    sheet = np.full((75 + 15 * 66, 1180, 3), 245, dtype=np.uint8)
    cv2.putText(sheet, "Raw y114..126 strips; visual audit after seeing overlays; NOT blind truth",
                (8, 20), cv2.FONT_HERSHEY_SIMPLEX, .48, (0, 0, 0), 1)
    for x in range(0, 320, 20):
        cv2.putText(sheet, str(x), (215 + x * 3, 51), cv2.FONT_HERSHEY_SIMPLEX, .35, (0, 0, 0), 1)
    for pose, session, evidence_name, target_offset, target_heading, manual_left, manual_right in POSES:
        folder, evidence = SOURCE / session, EVIDENCE / evidence_name
        checked = verify(folder)
        if checked["frames"] != 3 or checked["pose_label"] != pose:
            raise RuntimeError("Unexpected pose/count: " + session)
        if (evidence / "parameters.json").read_bytes() != parameters:
            raise RuntimeError("Parameters changed: " + session)
        for path in sorted(folder.iterdir()):
            if path.is_file():
                manifest.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                                     sha256=sha256(path)))
        records = [json.loads(line) for line in (evidence / "frames.jsonl").read_text(encoding="utf-8").splitlines()]
        group = dict(pose=pose, session=session, verification=checked, valid=0, frames=[])
        for record in records:
            frame_id = record["frame_id"]
            path = folder / ("data_%04d.jpg" % frame_id)
            if record["source_sha256"] != sha256(path):
                raise RuntimeError("Replay/input hash mismatch: " + str(path))
            gray = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            index = len(metadata)
            strip = cv2.cvtColor(cv2.resize(gray[114:127], (960, 39), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR)
            for x in range(0, 320, 20):
                cv2.line(strip, (x * 3, 0), (x * 3, 38), (0, 150, 0), 1)
            top = 65 + index * 66
            sheet[top:top + 39, 220:1180] = strip
            cv2.putText(sheet, pose + " / " + str(frame_id), (5, top + 24),
                        cv2.FONT_HERSHEY_SIMPLEX, .40, (0, 0, 0), 1)
            metadata.append(dict(source=path.relative_to(ROOT).as_posix(), pose=pose,
                                 instructed_offset_cm_right_positive=target_offset,
                                 instructed_heading_deg_right_positive=target_heading,
                                 exact_displacement_measured=False, exact_heading_measured=False,
                                 mount_height_mm_approx=200, mount_angle_deg_approx=50,
                                 mount_angle_reference="not_confirmed", nearest_front_cm_approx=15,
                                 pose_source="operator_followed_instructions_and_script_label"))
            # 已逐张看过原图／叠加，粗略记录黑白内缘过渡位置，容许约2px读数带。
            # 未盲标、未精测；特别是灰度过渡处选黑侧端点或白侧起点会有约1px差别。
            manual.append(dict(source=path.relative_to(ROOT).as_posix(), y=120,
                               left_inner_x_approx=manual_left, right_inner_x_approx=manual_right,
                               reading_band_px=2, midpoint_x_approx=(manual_left + manual_right) / 2,
                               audit="posthoc_visual_review_not_independent_ground_truth"))
            group["valid"] += int(record["valid"])
            group["frames"].append(dict(frame_id=frame_id, deviation_px=record["deviation_px"],
                                        left_inner_x=next(p["x"] for p in record["left"] if p["y"] == 120),
                                        right_inner_x=next(p["x"] for p in record["right"] if p["y"] == 120),
                                        pair_y_range=record["reference_diagnostics"]["pair_y_range"]))
        groups.append(group)
    write_csv(OUTPUT / "source_manifest.csv", manifest)
    write_csv(OUTPUT / "metadata.csv", metadata)
    write_csv(OUTPUT / "manual_reference.csv", manual)
    if not cv2.imwrite(str(OUTPUT / "reference_strips.png"), sheet):
        raise RuntimeError("Cannot write reference strips")
    summary = dict(groups=groups, image_count=len(metadata), source_file_count=len(manifest),
                   valid=sum(g["valid"] for g in groups), frozen_code_hashes=frozen,
                   parameter_sha256=hashlib.sha256(parameters).hexdigest(),
                   scope="15 static frames only; posthoc visual audit is not independent accuracy ground truth")
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"images": len(metadata), "source_files": len(manifest), "valid": summary["valid"],
                      "output": str(OUTPUT), "frozen_parameters": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
