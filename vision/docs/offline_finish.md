# 终点候选F1运行与状态

日期2026-11-08；维护视觉软件，现场责任主控。任务[V-07](../../project_planning/tasks/V-07.md)，事实与事件时间以[报告](../../testing/2026-11-08_vision_finish_f1/review.md)为准。

入口`FinishDetector.detect(gray, road, timestamp_ms, session_key)`：gray为320×240 uint8灰度；road为同帧冻结R1结果（含实测pair_samples／threshold）；时间必须是真实采集软件毫秒。依赖电脑OpenCV／NumPy／dataclasses，不直接在CanMV导入。`observe`为无时序空间候选，`update`单独管理时间状态；可单测起始已见线、断流与恢复。详见[src/offline_finish.py](../src/offline_finish.py)。

输出observation仅表示当前横向虚线形态，event一次性给finish_line_seen；gate_event给passed_image_y180_gate；passage_event给near_marker_then_unobserved。后者是近处检测后缺检，不能说整个图像已无虚线。whole_vehicle_crossed=None、automatic_stop=False。初始线抑制／1500ms清空武装／150ms确认／600ms缺检／1500ms合并复位／700ms采样断流复位均为开发参数，非比赛规则或停车参数。

```powershell
vision/.venv/Scripts/python.exe vision/tools/replay_finish.py --output vision/build/finish_new_run
vision/.venv/Scripts/python.exe vision/tools/validate_finish.py
```

回放以已保存C2同帧R1诊断为输入，每张原图哈希必须匹配，终点算法重新执行；输出拒绝覆盖。原始基线没有终点模块，本次不能声称准确率提升。当前两次同会话观察只支持研发，完整车尾越线与自动减速停车仍待车体／地面／运动证据；本次不生成STOP。
