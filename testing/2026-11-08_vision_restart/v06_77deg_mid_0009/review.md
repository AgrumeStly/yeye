# V-06：拟弯中摆位／单边可见组

日期：2026-11-08。主控现场摆位，本对话采集、检查与记录；任务V-06，仍进行中。

## 姿态与证据范围

主控在“内外尖角连线中点附近、车头朝入弯与出弯方向中间、保持相机安装、电机动力断开”的指导后反馈摆好。仅有操作反馈，未独立测量实际车身中心、朝向、净距或完整车体投影。前向图像也不能单独验证几何中点或整车位于车道内，因此本组记为拟弯中摆位，不记为精确弯中真值。

[预览](../v06_77deg_mid_preview_01.jpg)由现有COM10连接取得，frameId=7420、receivedAt=1794130716816、ageMs=1、8070字节。画面可辨一条由左下至右上的斜黑带，左上存在场地印字，未同时看到出口两侧边界，单凭图像不确定该斜带的道路左右角色。将该姿态作为单边可见及干扰场景保留，不为制造有效输出先改摆位或参考行。

## 正式采集与复现

临时停止预览，将PREVIEW_ONLY切False，保持POSE=center、FRAME_COUNT=3、REFERENCE_FRONT_CM=[]及相机参数；center仅为通用操作标签，具体场景以本记录为准。运行文本见[源码快照](../v06_77deg_mid_capture_source.py)，[正式终端](../v06_77deg_mid_terminal.json)确认v03_center_0009、3条[SAVED]、[DONE]，正常结束。

原件：[v03_center_0009](../../../vision/data/captures/final_mount_20261108/v03_center_0009/)，3张JPEG分别11439／11431／11434字节，另有完整JSON／JSONL，共5文件。校验通过，单通道320×240灰度、图片哈希与日志一致、session complete、cleanup_errors=[]，详见[verification.json](verification.json)及含原件哈希的[evidence.json](evidence.json)。冻结R1、回放器、校验器源码哈希和参数哈希与前两组／V-03相同。

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_center_0009
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_center_0009 --output vision/build/final_mount_20261108/v06_77deg_mid_0009_r1 --headless
vision/.venv/Scripts/python.exe testing/2026-11-08_vision_restart/summarize_v06_entry.py --session v03_center_0009 --name v06_77deg_mid_0009 --distance-note intended_midturn_operator_report_position_and_heading_unmeasured --scene intended_77deg_midturn_single_visible_boundary_pose_unverified
```

首次运行均退出0；归档器拒绝覆盖，复核直接读归档。归档器增加可选scene说明，默认仍保留首组入口场景，未改写首／第二组已存证据。完整派生物在vision/build/final_mount_20261108/v06_77deg_mid_0009_r1/，被Git忽略；关键结果／叠加另存本目录。

## 检查结果

逐张看过3张原图及3张叠加。3张均valid=false、quality=0.1667，centerline=[]、deviation_px=null、deviation_normalized=null；原因均为insufficient_pair_support、reference_row_not_bracketed、low_pair_quality。视频实际解码3帧，10fps仅人为播放速度。

[首张叠加](overlays/data_0001.png)及[逐帧数据](frames.jsonl)显示两类候选：

- 一条斜黑带的上下轮廓被记作visible_ribbons，side=unassigned、road_side_ambiguous=true；两条轮廓属于同一条带，不是道路双边。
- y70／75处的短暂双边候选，左点约(120,70)／(110,75)落在画面印字，右点约(284,70)／(277,75)落在斜黑带。它是场地图案与边界的错误配对，只有2行，最终被支持数、参考行与质量检查拒绝。不能把内部left_state/right_state=visible理解为真实道路双边，也不能因最终无效就宣称不存在误检。

本组最终没有输出虚构控制中线，支持现有无效输出在这一姿态下的保守表现；尚不能证明其他印字／场外线均被拒绝。当前为单边可见加印字干扰的一次摆位3张重复，不是纯净单边对照、全失线覆盖、动态性能或自动过弯验收。

## 当前下一步

主控保持电机动力断开、相机固定，在整车投影仍留在白色路面内的前提下，尽量保持当前车身中心位置，手动继续向右转动车身，直到车头与离开77°弯的出口直道平行，并朝离开弯道的方向。先核对出口朝向预览，必要的车身位置修正以实物边界为准；不声称本次旋转为拟采用的行驶动作或最优转向角。

当前本地脚本已恢复PREVIEW_ONLY=True，临时运行并开启预览，尚未保存出口原图。未改相机、R1、STM32、UART、协议或全局摘要，未发送运动命令、写自启动脚本或上传。HEAD仍a0733a8685db4c2b497539303bfe87fe1c1ebfe5，分支codex/current-version-20261025，共享修改保留。

得分关联：比赛第三部分、图1与评分表基本功能60分的可靠完赛、触边扣分与完全出界失败风险。本组保留单边和场地印字误配证据，支撑后续弯道识别／不可信路径处理和报告论证，没有实测加分结论。
