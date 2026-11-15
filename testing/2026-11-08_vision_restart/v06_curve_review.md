# V-06：77°弯前预览检查

日期：2026-11-08。现场摆位：主控；预览读取、检查与记录：本对话。任务：[V-06](../../project_planning/tasks/V-06.md)。

## 场景与摆位依据

主控选择先检查比赛图1顶部约77°锐角弯，随后反馈已按指导摆好。指导位置为顺时针进入该弯的左侧斜直道中央，车头沿入口直道朝向顶角；这只是静态采样基准，不锁定最终走中线策略。预览起始距离建议约40cm，未取得独立量距证据，不记为实测值。

本次摆位距离的入口参照定义：经过行进方向右侧内边界尖角、垂直于入口直道的地面横线；距离沿入口直道方向量至经过车头最前沿地面投影的平行横线。无需在场地增加实物标记。77°为比赛图示场景标签，本次未从透视图像测量实际场地角度。

## 实际操作与原始证据

工具缓存报告COM10已连接且ready，K230D Lushanpi Lite 128M，固件K230D-v1.8-0-gc2d1f5cc994c206d0032aaf6aaf09332f3dc3c4c。初次读取无预览帧，板上script_running=false。核对本机CanMV示例与sensor接口后，临时运行现有vision/src/capture_canmv.py同一文本：POSE=center、PREVIEW_ONLY=True、REFERENCE_FRONT_CM=[]，再启用IDE预览；末次状态script_running=true，保留预览供后续摆位检查。

本次终端新增段含[START] capture-canmv-2 pose=center、find sensor gc2093_csi2、[READY] warming up; keep vehicle still；没有新[SESSION]／[SAVED]。终端缓存还包含前序标定的保存和主动中断记录，不将历史内容算作本次运行结果。

保存[预览帧](v06_77deg_entry_preview_01.jpg)：frameId=124，receivedAt=1794129716407，保存时ageMs=2，8561字节，SHA-256为b2b186edfab5fb59310b40db159dfdec34ab0f21e1cc02413549f57193faebf2。电脑OpenCV成功解码为320×240、3通道；脚本配置灰度，IDE预览JPEG的3通道封装不作为正式单通道采集会话验收。本文件是预览证据，不能代替后续板上原图及日志／哈希会话。

## 画面检查与结论

- 左侧外边界由左下方向约(x108,y49)延伸，再向画面右侧展开。
- 右侧内边界由右下方向约(x239,y115)延伸，在尖角附近转向画面右方；内弯尖角已进入视野。
- 近处入口双边及向右转出的部分道路可辨；出口远段延伸到画面右侧之外，不能声称整个出口均可见。
- 画面边界呈连续黑带；仅验证当前练习场景，不能代替官方5cm色块边界及实际间隙测试。

此摆位可作为第一组弯前正式采样位置，暂不要求移动相机或车辆。尚未保存本场景正式3张原图／会话、未执行冻结R1弯道回放；不据目视道路可辨推定算法有效、转向时机正确或整车可通过。

## 一个下一步与得分关联

主控保持当前车位与相机安装、电机动力断开；下一步在同一位置保存3张正式原图，并独立记录77°右弯前场景，下载完整会话后检查文件和冻结R1输出，再确定后续距离／弯中摆位。当前仍仅预览，未切换保存模式。

依据比赛第三部分、图1及评分表，本项支撑基本功能60分的提前识别转向，减少迟转造成的触边扣分／完全出界失败风险；验证证据为预览可见范围、后续原图与有效性／误配记录，没有实测加分结论。

本次未修改采集代码、相机安装、R1、STM32、UART或协议，未建立新TF卡会话、写main.py／boot.py、上传或改全局摘要。分支codex/current-version-20261025，HEAD a0733a8685db4c2b497539303bfe87fe1c1ebfe5，共享修改保留。

## 同日接续：首组正式3张与冻结R1检查

主控询问继续步骤后，在同一摆位停止预览，临时将PREVIEW_ONLY改False，POSE=center、FRAME_COUNT=3、REFERENCE_FRONT_CM=[]保持；未改变安装、算法或控制。运行文本见[采集源码快照](v06_77deg_entry_capture_source.py)。停止上一预览产生的IDE interrupt属于主动停止，正式采集段另存[终端记录](v06_77deg_entry_terminal.json)。正式段3条[SAVED]及[DONE] /sdcard/captures/v03_center_0007 saved=3，正常结束。

完整原件：[v03_center_0007](../../vision/data/captures/final_mount_20261108/v03_center_0007/)，5个文件，3张JPEG分别12304／12242／12286字节。板上会话名中的center为姿态标签；本记录明确其为77°弯前，不与之前的直道／标定组混用。verify_capture.py退出0，state=complete、3张均320×240单通道灰度且哈希一致、cleanup_errors=[]。

冻结R1源码、回放器、校验器哈希与V-03 static_summary/summary.json逐一相同，parameters.json哈希同为d34144aff88631d1a5d549483f13b5880e197011863e4b3e054150b29bac7afc。回放退出0，3有效／0无效，视频实际解码3帧；10fps只是人为播放速度。命令：

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_center_0007
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_center_0007 --output vision/build/final_mount_20261108/v06_77deg_entry_0007_r1 --headless
vision/.venv/Scripts/python.exe testing/2026-11-08_vision_restart/summarize_v06_entry.py
```

末条用于首次归档，拒绝覆盖已有证据，复核可直接读[归档结果](v06_77deg_entry_0007/evidence.json)、[文件校验](v06_77deg_entry_0007/verification.json)、[逐帧结果](v06_77deg_entry_0007/frames.jsonl)、[统计](v06_77deg_entry_0007/summary.json)及[叠加图](v06_77deg_entry_0007/overlays/data_0001.png)。全部3张叠加已查看，3张原图也逐张查看。完整派生目录vision/build/final_mount_20261108/v06_77deg_entry_0007_r1/被Git忽略；关键结果已另存本证据目录。

3张quality均0.9091，y120偏差dx均-5.333px、归一化-33；这是图像偏差，不解释为横向厘米或自动转向命令。双边支持行为y110、125、130至215，y120值由已有支持插值。目视这些点主要对应入口直道内缘，中线近乎竖直；内侧尖角及出口远段并未形成一条向右转出的路径。外边界转角约y49，位于当前ROI顶行y65以外，且出口延伸到画面右侧之外。**有效双边只说明这一帧有入口近场配对，不证明提前识别了右转、给出了可行转弯路径或可直接驱动车辆。** 后续还需按不同弯前距离、弯中和出口采样检查；本组是一次摆位的3张重复图，不是3个独立工况。

当前下一步：主控沿入口直道方向将整车向前移约10cm，横向保持居中、车头方向不变、相机不动、电机动力仍断开。若首组实际按40cm摆位，新位置约30cm；两者均须以现场实际量距为准，不能由标称值相减冒充实测。先预览检查尖角与出口如何变化，再决定保存；不让主控提前手转车头制造已入弯场景。

本地脚本已恢复PREVIEW_ONLY=True，并临时运行开启IDE预览，供主控下一摆位检查；此后没有保存新原图。首组正式源码快照保留False便于追溯。未发送START、写自启动脚本、改R1／STM32／UART、上传或更新00全局摘要。
