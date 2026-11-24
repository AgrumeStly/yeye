# ============================================================
# K230D 视觉识别 —— 已实测通过（9/9 正确，2-3ms/张）
#
# 用 VS Code 的 CanMV 运行：Ctrl+Shift+P -> "CanMV: 运行当前脚本"
#
# 为什么不用摄像头：
#   摄像头模块已损坏，本脚本改为读取 TF 卡上的图片文件。
#   摄像头修好后，只需把 load_image() 换成 sensor.snapshot()。
# ============================================================

import gc
import time
import math
import image
import nncase_runtime as nn
import ulab.numpy as np
from libs.AI2D import Ai2d

KMODEL = "/sdcard/examples/ai_test_kmodel/veg_cls.kmodel"
LABELS = ["spinach", "eggplant", "amaranth", "carrot", "tomato", "broccoli"]

# 测试图及官方标注（来自 examples/16-AI-Cube/SelfLearningApp.py）
SAMPLES = [
    ("/sdcard/examples/ai_test_utils/0.jpg", "spinach"),
    ("/sdcard/examples/ai_test_utils/1.jpg", "spinach"),
    ("/sdcard/examples/ai_test_utils/2.jpg", "spinach"),
    ("/sdcard/examples/ai_test_utils/3.jpg", "eggplant"),
    ("/sdcard/examples/ai_test_utils/4.jpg", "eggplant"),
    ("/sdcard/examples/ai_test_utils/5.jpg", "eggplant"),
    ("/sdcard/examples/ai_test_utils/6.jpg", "carrot"),
    ("/sdcard/examples/ai_test_utils/7.jpg", "carrot"),
    ("/sdcard/examples/ai_test_utils/8.jpg", "carrot"),
]


def load_chw(path):
    """JPEG 文件 -> (CHW 张量, 宽, 高)

    ★ 关键：模型要 NCHW 格式 (3,H,W)，
      直接喂 to_numpy_ref() 得到的 (H,W,3) 会让结果全错。
      实测：喂 HWC = 0/3 正确，喂 CHW = 9/9 正确。
    """
    img = image.Image(path)
    rgb = img.to_rgb888()
    w, h = rgb.width(), rgb.height()
    hwc = rgb.to_numpy_ref()
    chw = hwc.reshape((h * w, 3)).transpose().copy().reshape((3, h, w))
    del hwc, rgb, img
    gc.collect()
    return chw, w, h


def build_ai2d(w, h):
    """硬件 2D 加速器：缩放到模型输入 224x224"""
    a = Ai2d(0)
    a.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT, nn.ai2d_format.NCHW_FMT,
                     np.uint8, np.uint8)
    a.pad([0, 0, 0, 0, 0, 0, 0, 0], 0, [0, 0, 0])
    a.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
    a.build([1, 3, h, w], [1, 3, 224, 224])
    return a


def softmax(row):
    mx = float(row[0])
    for i in range(1, len(row)):
        if float(row[i]) > mx:
            mx = float(row[i])
    s = 0.0
    for i in range(len(row)):
        s += math.exp(float(row[i]) - mx)
    out = []
    for i in range(len(row)):
        out.append(math.exp(float(row[i]) - mx) / s)
    return out


def main():
    print("loading model ...")
    t0 = time.ticks_ms()
    kpu = nn.kpu()
    kpu.load_kmodel(KMODEL)
    print("model loaded in %d ms" % (time.ticks_ms() - t0))

    ok = 0
    total = 0

    for path, truth in SAMPLES:
        chw, w, h = load_chw(path)
        a = build_ai2d(w, h)
        tensor = a.run(chw)
        del chw, a
        gc.collect()

        kpu.set_input_tensor(0, tensor)
        t0 = time.ticks_ms()
        kpu.run()
        cost = time.ticks_ms() - t0

        result = kpu.get_output_tensor(0).to_numpy()
        probs = softmax(result[0])
        del result, tensor

        best = 0
        for i in range(len(probs)):
            if probs[i] > probs[best]:
                best = i

        total = total + 1
        hit = LABELS[best] == truth
        if hit:
            ok = ok + 1

        name = path.split("/")[-1]
        print("%-8s -> %-9s %6.2f%%  %s  (%d ms)"
              % (name, LABELS[best], probs[best] * 100,
                 "OK" if hit else "MISS", cost))

        gc.collect()

    print("--------------------------------")
    print("result: %d/%d correct" % (ok, total))

    kpu.__del__()
    nn.shrink_memory_pool()
    gc.collect()
    print("done, free memory: %d" % gc.mem_free())


main()
