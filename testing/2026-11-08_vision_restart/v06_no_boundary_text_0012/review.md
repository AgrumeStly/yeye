# V-06：无可信车道、汉字／图案干扰组

日期：2026-11-08。主控现场摆位，本对话采集、检查与记录。依据主控补充“实际赛道中央有很多汉字”，将原先干净空白地面对照建议改为保留实际文字／图案，先检查无可信道路双边时的误识别；未要求清除场地文字或改变相机。

## 场景与采集

主控按“车头朝向有汉字的地面，使两侧真实赛道边界不在预览内，保持安装及电机动力断开”指导后反馈摆好。[预览](../v06_no_boundary_text_preview_01.jpg)的主观察区y65..215包含文字和大幅几何图案，未见可信车道双边；画面最上沿仍有远处细线／接缝，角色未独立核实，不称为全图绝无黑线的干净空白对照。主要干扰也不只有汉字，包括长条及折线图案笔画。

预览frameId=4913、receivedAt=1794131490852、ageMs=1、10774字节，[元数据](../v06_no_boundary_text_preview_meta.json)另存。停止预览后，仅切PREVIEW_ONLY=False，POSE=center、FRAME_COUNT=3、REFERENCE_FRONT_CM=[]和相机参数保持。center是工具通用标签，不表示此区域实际存在道路中心。运行文本见[源码快照](../v06_no_boundary_text_capture_source.py)，[正式终端](../v06_no_boundary_text_terminal.json)确认v03_center_0012、3条[SAVED]及[DONE]，正常结束。

完整[原件会话](../../../vision/data/captures/final_mount_20261108/v03_center_0012/)共5文件，3张JPEG为15139／15165／15188字节。文件校验通过，320×240单通道灰度、图片哈希与日志相同、会话complete、cleanup_errors=[]，见[verification.json](verification.json)、含原件5文件哈希及冻结版本的[evidence.json](evidence.json)。

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_center_0012
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_center_0012 --output vision/build/final_mount_20261108/v06_no_boundary_text_0012_r1 --headless
vision/.venv/Scripts/python.exe testing/2026-11-08_vision_restart/summarize_v06_entry.py --session v03_center_0012 --name v06_no_boundary_text_0012 --distance-note text_graphics_region_no_credible_lane_operator_report_position_unmeasured --scene no_credible_lane_text_and_logo_clutter_not_clean_blank_floor
```

首次均退出0；归档器拒绝覆盖，复核直接读归档。R1、回放器、校验器源码及参数哈希与V-03／前5组相同。完整派生物在vision/build/final_mount_20261108/v06_no_boundary_text_0012_r1/，被Git忽略；关键结果另存本目录。

## 结果及其限制

3张原图、3张叠加逐张查看。3张均valid=false、quality=0.25，centerline=[]、deviation_px=null、deviation_normalized=null；理由为insufficient_pair_support、pair_not_widening_toward_camera、reference_row_not_bracketed、low_pair_quality。视频实际解码3帧，10fps为人为播放速度。见[首张叠加](overlays/data_0001.png)、[逐帧JSONL](frames.jsonl)、[统计](summary.json)。

内部仍将图案部分提取为visible_ribbons（角色未定条带），并将图案笔画配成y205／210／215的短路径，左点x55、右点约x291..292；支持不足且宽度增长为-0.1，未跨参考行，最终被拒绝。这是存在错误候选但没有有效假道路输出，不能说算法已经识别出汉字语义或彻底消除印字误检。

该结果支持本姿态下的无可信路径输出符合预期，不保证其他字形、朝向、距离、光照或图案都能被拒绝；同一摆位3张是重复图，不能计算无路径场景误报率。该组也不替代干净空白地面对照、所有全失线条件、实时序列失线处理或主控停车保护验收。

## 本轮结束状态

V-06首轮6组18张静态采样已保存／下载／校验／冻结回放，汇总见[首轮报告](../v06_round1_review.md)。当前采集程序自然结束，板上script_running=false，IDE预览已停止。本地capture_canmv.py恢复PREVIEW_ONLY=True供下次核对，未再次执行、未保存新组。主控暂不需要继续移动小车。

未改相机安装、ROI、参考行、R1、STM32、UART或协议，未发送运动命令、写自启动脚本、上传或更新00全局摘要。比赛关联为第三部分和评分表基本功能60分的可靠完赛、触边扣分与出界失败风险：保留图案误配及无效输出证据，支撑后续路径可信度处理和报告论证，没有实测得分收益。
