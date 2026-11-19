# 直道双轮启动适配版

2026-11-19；任务 [I-03-STRAIGHT-ASSIST](../../project_planning/tasks/I-03-STRAIGHT-ASSIST.md)。主控要求重试昨日最终直道，并明确“适配双轮启动”。本版 **0x02120003**；原StraightAssist／02工程与产物保留。

| 项目 | 入口／预期 |
| --- | --- |
| Keil5工程／目标 | [straight_dual_start.uvprojx](../MDK-ARM/straight_dual_start.uvprojx)／StraightDualStart |
| 产物 | `control/build/firmware/straight_dual_start/straight_dual_start.axf`、`.hex`、`.bin` |
| 首次KEY | 已验证轮位映射；两轮悬空60RPM／1000ms，不依赖视觉，不重新识别左右 |
| 悬空通过 | `g_corner_startup.completed=1`、`stage=2`、`bench_ms=1000`，两轮PWM0 |
| 随后KEY上道 | 原80RPM／2000ms、50%上限、原PI／滤波／差速补偿，当前有效v3双边直道 |
| 视觉原件 | [昨日R2 straight_drive.py](../../testing/2026-11-18_straight_assist/vision_bundle_r2/straight_drive.py) |
| 本轮证据 | [record.md](../../testing/2026-11-19_straight_dual_start/record.md) |

主控沿用 [当前实证轮位映射](../../hardware_preparation/wheel_mapping.md)。KEY是实物KEY键，对应PA0／WKUP；RST是另一复位键。原逐轮校准流程仅属02版历史，不用于本轮。

1. 主控支稳双轮悬空，在Keil5 **Project → Open Project** 打开上述工程，选 **StraightDualStart**。构建已通过0错误0警告，**Flash → Download** 人工下载，关闭Keil，暂不按KEY。
2. 代理只读核对Flash／版本03、毫秒递增、故障0、PWM0；若下载后RAM未初始化，主控保持悬空按RST一次，再核对。不自动复位／暂停／恢复CPU或发START。
3. 主控首次长按KEY约1～2秒再松开，两轮同时前进1秒并停。代理读取完整1000ms及两轮正反馈、completed=1。KEY／STOP中断、无反馈、反向、超速、硬件错误不得放行上道。复位会清除双轮资格。
4. 代理运行昨日R2视觉，保持后台及相机供电。主控放在顺时针直道中央、车头沿道路摆正；确认STM32真实收包增长、当前双边有效及源年龄小于200ms后，第二次KEY进行80RPM／2秒直跑。保留KEY立即撤驱动、失线／超时／反馈异常和看门狗保护。试跑线束留松弛与停车滑行空间。
5. 停后保持供电、不复位、不重复试跑，保存冻结环和视觉日志；记录直行、摆动、触边、偏移及停因。正常应为LIMIT11／2000ms。软件或悬空通过不等于地面或完整圈通过。

只读核对，每次另建输出目录。现场1MHz两次No ACK后100kHz成功，默认频率仍1MHz：

```powershell
vision/.venv/Scripts/python.exe control/tools/lap_swd_capture.py --profile straight-dual --frequency 100000 --output testing/2026-11-19_straight_dual_start/new_capture
```

确认映射及零输出后，沿用原视觉启动工具（不改main.py、不发START，输入窗口600秒；calibrated标志不代替双轮资格）：

```powershell
vision/.venv/Scripts/python.exe vision/tools/run_straight_live.py --port COM10 --confirmed-calibrated --output testing/2026-11-19_straight_dual_start/new_live
```

比赛关联：第三部分、图1、表1的基本功能60分；复核稳定直道以降低错映射／错版本、触边及出界风险，为缩短整圈用时提供基线。实际记录可支撑报告20分。60RPM／1秒、80RPM／2秒为队内验证条件，不是官方评分标准，不宣称单段得分或整圈成功。
