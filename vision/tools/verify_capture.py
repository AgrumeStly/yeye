"""电脑端检查新采集会话：完整JSON、逐文件SHA-256、灰度尺寸及实际可解码性。"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def verify(folder):
    """只读原始会话；不修补日志，不接受未完成会话或与日志不一致的图片集合。"""
    folder = Path(folder)
    meta = json.loads((folder / "session.json").read_text(encoding="utf-8"))
    rows = [json.loads(s) for s in (folder / "frames.jsonl").read_text(encoding="utf-8").splitlines()]
    if meta.get("schema") != 1 or meta.get("state") != "complete":
        raise ValueError("会话未完整结束，保留原件并检查session.json")
    count = meta["requested_count"]
    if type(count) is not int or not 1 <= count <= 600 or len(rows) != count or meta["saved_count"] != count:
        raise ValueError("会话图片数量与日志不一致")
    expected = {"data_%04d.jpg" % i for i in range(1, count + 1)}
    if {p.name for p in folder.glob("*.jpg")} != expected:
        raise ValueError("JPEG集合存在缺失、重复或未完成的pending文件")
    for i, row in enumerate(rows, 1):
        name = "data_%04d.jpg" % i
        if row.get("frame_id") != i or row.get("file") != name or row.get("pose_label") != meta["pose_label"]:
            raise ValueError("帧编号／文件名／姿态标签异常")
        data = (folder / name).read_bytes()
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("文件校验不一致：" + name)
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None or image.shape != (240, 320) or image.dtype != np.uint8:
            raise ValueError("实际图片不是320×240灰度图：" + name)
        if (row["width"], row["height"], row["pixel_format"]) != (320, 240, "grayscale"):
            raise ValueError("帧配置异常：" + name)
        if i > 1 and row["elapsed_ms"] - rows[i-2]["elapsed_ms"] < meta["interval_ms"]:
            raise ValueError("相邻帧软件时序异常：" + name)
    if (meta["width"], meta["height"], meta["pixel_format"]) != (320, 240, "grayscale"):
        raise ValueError("会话配置与实际图片不一致")
    return dict(passed=True, folder=str(folder.resolve()), frames=count, pose_label=meta["pose_label"],
                actual_grayscale_size=[320, 240], cleanup_errors=meta.get("cleanup_errors", []),
                scope="file integrity and image format only; not pose truth or board acceptance")


def main():
    """命令行只报告检查结论；异常返回非零，让损坏文件不能被当作成功采样。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.folder), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
