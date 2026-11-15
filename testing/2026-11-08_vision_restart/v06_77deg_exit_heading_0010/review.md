# V-06：出口朝向静态组

日期：2026-11-08。主控现场摆位，本对话采集、检查和记录；任务V-06进行中。

## 场景与采集

主控在“尽量保持车身中心，手动继续右转，直至车头与出口直道平行且朝离开77°弯方向”的指导后反馈摆好。实际位置、朝向角及完整车体边界余量未独立测量，不记为精确弯中位置或实际自动转向动作；本组标为出口朝向。

现有COM10连接取得[新预览](../v06_77deg_exit_heading_preview_01.jpg)，frameId=4629、ageMs=1、9215字节，[预览元数据](../v06_77deg_exit_heading_preview_meta.json)另存。画面恢复左右两条向远方收敛的道路边界，图像远端含转折／印字；不据此前向图像推定车体已完整驶离弯道。

临时停止预览，仅将PREVIEW_ONLY切False，POSE=center、FRAME_COUNT=3、REFERENCE_FRONT_CM=[]及相机参数保持。运行文本见[源码快照](../v06_77deg_exit_heading_capture_source.py)，[正式终端](../v06_77deg_exit_heading_terminal.json)确认v03_center_0010、3条[SAVED]及[DONE]，正常结束；前序预览主动停止另作历史，不混为本组失败。

原件：[v03_center_0010](../../../vision/data/captures/final_mount_20261108/v03_center_0010/)，共5文件，3张JPEG为13045／13127／13108字节。校验通过，全部320×240单通道灰度、图片哈希与日志一致、会话complete、cleanup_errors=[]。见[verification.json](verification.json)及保存原件5文件哈希的[evidence.json](evidence.json)。

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_center_0010
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_center_0010 --output vision/build/final_mount_20261108/v06_77deg_exit_heading_0010_r1 --headless
vision/.venv/Scripts/python.exe testing/2026-11-08_vision_restart/summarize_v06_entry.py --session v03_center_0010 --name v06_77deg_exit_heading_0010 --distance-note exit_heading_operator_report_position_and_angle_unmeasured --scene intended_77deg_exit_heading_dual_boundaries_visible_static_pose
```

首次运行均退出0，归档器拒绝覆盖。冻结R1、回放器、校验器及参数哈希与前3组／V-03一致。完整派生物在vision/build/final_mount_20261108/v06_77deg_exit_heading_0010_r1/，被Git忽略；关键JSON／参数／叠加已归档本目录。

## 检查结果与适用范围

逐张查看3张原图和3张叠加。3张均valid=true、quality=1.0，双边支持y65..215共31行且含y120；y120偏差均-1.0px，归一化-6。quality是启发式评分，像素偏差不换算横向厘米或主控转向量。叠加的左右点与当前可见道路内缘相符，未在本组看到印字代替参考行道路边缘。见[首张叠加](overlays/data_0001.png)、[逐帧结果](frames.jsonl)及[统计](summary.json)。视频实际解码3帧，10fps仅人为播放速度。

截至本组的四种静态摆位如下；每组是一次摆位的3张重复，采样次序不能当作连续运动或动态恢复时间：

| 场景／会话 | 有效张数 | 关键边界 |
| --- | --- | --- |
| 较远弯前／0007 | 3/3 | 入口近场双边有效，未形成右转路径 |
| 向前10cm／0008 | 0/3 | 参考行缺右边界，双边配对仅y170..215 |
| 拟弯中／0009 | 0/3 | 单条斜带，印字与斜带短暂错配后被拒绝 |
| 出口朝向／0010 | 3/3 | 参考行与ROI双边恢复，近乎竖直中线 |

当前同安装在出口朝向能恢复道路双边，支持后续重点检查观察方向及锐角过渡的表示／规划；不能用当前静态有效证明车辆会自主从0007转到0010。入弯与转向过渡仍有有效性／路径缺口，出弯纵向位置及全失线场景尚待补充。未改变ROI、参考行、算法或相机来制造恢复。

## 一个下一步

主控继续断开电机动力，保持车头沿出口直道的朝向，手动将整车沿出口向前移约30cm、保持道路居中，相机安装不变；先检查出弯位置预览，距离为队内采样建议，以实际量距／反馈为准。当前本地capture_canmv.py已恢复PREVIEW_ONLY=True，临时运行并启用IDE预览，尚未保存出弯位置原图。

比赛关联：第三部分、图1及评分表基本功能60分的顺时针完赛、触边扣分与完全出界失败风险；本组与前组对照用于识别锐角过渡缺口和出弯恢复条件，支持报告论证，没有实测得分收益。未发送运动命令、写自启动脚本、改STM32／UART／协议、上传或更新00全局摘要；共享修改保留。
