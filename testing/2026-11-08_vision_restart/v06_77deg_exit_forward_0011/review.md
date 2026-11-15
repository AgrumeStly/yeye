# V-06：沿出口前移后的静态组

日期：2026-11-08。主控现场摆位，本对话采集、检查与记录；V-06仍进行中。

## 场景与原件

主控按“保持出口朝向、沿出口手动前移约30cm、保持道路居中和相机安装、电机动力断开”指导后反馈摆好；实际位移／朝向／完整车身投影未独立测量。不把指导值记成实测距离，不把此组称为自动出弯。

现有COM10连接取得[预览](../v06_77deg_exit_forward_preview_01.jpg)，frameId=2281、receivedAt=1794131192500、ageMs=0、9253字节，见[预览元数据](../v06_77deg_exit_forward_preview_meta.json)。左右道路边界均可见，随后停止预览，仅切PREVIEW_ONLY=False，POSE=center、FRAME_COUNT=3、REFERENCE_FRONT_CM=[]及相机参数保持。见[运行源码快照](../v06_77deg_exit_forward_capture_source.py)、[正式终端](../v06_77deg_exit_forward_terminal.json)。

正式v03_center_0011正常保存3张并[DONE]。完整[原件会话](../../../vision/data/captures/final_mount_20261108/v03_center_0011/)含5文件，3张JPEG分别12962／13010／12936字节。电脑校验全部通过，320×240单通道灰度、实际哈希与日志相同、session complete、cleanup_errors=[]。证据见[文件校验](verification.json)、[原件5文件哈希及冻结源码／参数](evidence.json)。

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_center_0011
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_center_0011 --output vision/build/final_mount_20261108/v06_77deg_exit_forward_0011_r1 --headless
vision/.venv/Scripts/python.exe testing/2026-11-08_vision_restart/summarize_v06_entry.py --session v03_center_0011 --name v06_77deg_exit_forward_0011 --distance-note forward_about_30cm_along_exit_operator_report_unmeasured --scene 77deg_exit_forward_static_dual_boundaries
```

首次执行均退出0；归档器拒绝覆盖，复核读已存原件／JSON。冻结R1、回放器、校验器3个源码哈希及参数哈希与V-03和前4组完全相同。完整派生物留vision/build/final_mount_20261108/v06_77deg_exit_forward_0011_r1/，build被Git忽略；关键结果已归档本目录。

## 检查结果

3张原图、3张叠加均逐张看过。3张valid=true、quality=1.0，双边支持y65..215的31行；y120偏差均0px、归一化0。叠加左右点与参考行及近场可见道路内缘相符，未在本组看到印字代替道路边缘。见[首张叠加](overlays/data_0001.png)、[逐帧JSONL](frames.jsonl)与[统计](summary.json)。视频实际解码3帧，10fps只是人为播放速度；quality不是正确概率，像素零偏差也不证明物理车体精确居中。

截至目前5组15张均文件完整，冻结R1在0007弯前、0010出口朝向、0011出口前移组各3张有效；0008近弯和0009拟弯中各3张无效。每组是同一摆位重复3张，不汇总成识别准确率，不当作连续运动、动态恢复时间或完赛成功率。现有证据支持出口直道姿态下双边恢复，同时保留入弯参考行缺侧和弯中印字错配的限制；没有完成自动转弯路径衔接。

## 一个下一步与边界

补本轮静态全失线场景：主控保持电机动力断开和相机安装，手动将整车挪到没有黑色边界、文字／图案的浅色平整地面，使当前预览观察区内两侧赛道线均不出现，先检查实际画面后再保存3张。该场景用于检查无可信路径时是否清空中线／偏差，不能以遮挡镜头替代真实地面缺线，也不由静态输出推定主控停车保护已经验收。

当前本地脚本已恢复PREVIEW_ONLY=True，临时运行并开启预览，尚未保存全失线原图。POSE=center仍为现有工具通用标签，不表示空白区域存在道路中心；下一组场景另记证据。未改相机、R1、STM32、UART、协议或00全局摘要，未驱动电机、写自启动脚本或上传，共享修改保留。

比赛关联：第三部分、图1及评分表基本功能60分的可靠完赛／触边扣分／完全出界失败风险。本组支撑出弯视野与后续路径恢复设计，下一组避免无赛道时仍输出虚构中线；原始证据支持报告论证，没有实测得分收益。
