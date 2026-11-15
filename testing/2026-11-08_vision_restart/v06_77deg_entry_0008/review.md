# V-06：沿入口向前移约10cm后的第二组

日期：2026-11-08。现场摆位：主控；采集、检查与记录：本对话。主控在“沿入口直道向前移约10cm，保持横向居中、车头方向与相机安装”的指导后反馈摆好；仅为操作反馈，没有独立量距证据。若前组实距40cm，此组约30cm，但不以标称相减当实测。

## 采集与证据

沿用现有COM10连接、K230D-v1.8-0固件与capture-canmv-2。先取[新预览](../v06_77deg_entry_nearer_preview_01.jpg)，frameId=4276，ageMs=2，元数据见[预览记录](../v06_77deg_entry_nearer_preview_meta.json)。右侧内弯尖角由前组约y110附近移到约(x254,y143)，左侧外转角约(x103,y56)，出口继续向画外右侧延伸。坐标为非盲目视约读，不是精确几何标定。

停止预览后仅将PREVIEW_ONLY切False，POSE=center、FRAME_COUNT=3、REFERENCE_FRONT_CM=[]；保持安装及算法。运行文本见[源码快照](../v06_77deg_entry_nearer_capture_source.py)，[终端](../v06_77deg_entry_nearer_terminal.json)确认本组v03_center_0008，3条[SAVED]及[DONE]，正常结束。前序预览的主动停止不记为正式采集失败。

完整原件：[v03_center_0008](../../../vision/data/captures/final_mount_20261108/v03_center_0008/)，3张JPEG分别11998／12031／11980字节，另有session.json、frames.jsonl；verify_capture.py通过，3张均320×240单通道灰度、实际哈希与日志一致、会话complete、cleanup_errors=[]。原件5文件SHA-256见[evidence.json](evidence.json)，[校验结果](verification.json)独立保存。

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_center_0008
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_center_0008 --output vision/build/final_mount_20261108/v06_77deg_entry_0008_r1 --headless
vision/.venv/Scripts/python.exe testing/2026-11-08_vision_restart/summarize_v06_entry.py --session v03_center_0008 --name v06_77deg_entry_0008 --distance-note forward_10cm_from_first_pose_operator_report_no_independent_measurement
```

三条首次运行均退出0；归档器拒绝覆盖已存证据，复核直接读JSON／原图。归档器增加可选会话名、证据名和距离说明，默认仍对应首组，没有改写首组原件／归档。冻结R1、回放器、校验器的3个源码哈希以及参数哈希与V-03、前组相同；没有调整ROI、阈值或参考行。

## R1结果与图像检查

3张原图与3张叠加均已逐张查看。回放0有效／3无效，3张原因均reference_row_not_bracketed；双边配对仅y170..215共10行，quality=0.8333，centerline=[]、deviation_px=null、deviation_normalized=null。y120诊断只有左侧黑段x52..73，没有右侧黑段。输出见[逐帧JSONL](frames.jsonl)、[统计](summary.json)、[首张叠加](overlays/data_0001.png)。视频实际解码3帧，10fps仅人为播放速度；完整派生物在vision/build/final_mount_20261108/v06_77deg_entry_0008_r1/，build不自动跨设备同步，关键结果另存本目录。

与前组3张有效入口近场相比，本组内弯尖角落在y120下方；y120横向截线在当前视野内确实没有可用的右侧道路边界支持。不能向画外补边、把缺失侧当固定路宽补齐，或将本组无效解释为摄像头故障／采集失败。算法y170起有配对也不意味着更远处所有可见边缘都不存在；可见性与筛选结果须区分。

本组揭示固定参考行双边输出尚不能贯穿这段入弯过程，并不证明车应在本摆位才开始转向，也不证明调整参考行就能解决弯道规划。此处不放宽有效性条件、不把前组近乎竖直的中线延伸成右转路径。仅为两个静态摆位，不代表动态失线次数、完成率或算法准确率。

## 一个下一步

沿入口保持原朝向继续前移将重复出现参考行缺侧。下一步改采弯中姿态：主控电机动力断开，手动将整车放在该弯内外两个尖角连线中点附近的白色区域，车头朝赛道图右方，即入口与出口行进方向的中间朝向；整车投影留在白色路面内，相机安装保持。此为静止视野采样建议，不是拟定行驶轨迹或转向时机。若实物边界与图示位置不对应，先按实物预览核对，不强套纸面坐标。

当前本地capture_canmv.py已恢复PREVIEW_ONLY=True，并临时运行开启预览，POSE=center仅为待核对标签；未保存弯中原图。已保持R1／STM32／UART／相机安装，未发送运动命令、写自启动脚本、上传或更新00全局摘要。

比赛关联：第三部分、图1与评分表基本功能60分要求顺时针可靠完赛，触边扣分、完全出界失败。本组用真实缺侧证据防止错误补线和迟转／错误转向假设，支持后续弯道策略与报告论证，没有实测得分收益。
