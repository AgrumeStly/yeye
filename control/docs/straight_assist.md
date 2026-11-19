# 独立直道：已验收基线与历史操作

2026-11-19。一次80RPM／2秒结果已确认，详见[任务当前区](../../project_planning/tasks/I-03-STRAIGHT-ASSIST.md)。本页原固件的左右分别配对步骤只说明历史行为，不能改称支持双轮流程；当前试跑使用[首弯候选](right_angle_racing.md)的一次双轮悬空后一次上道。若需重新使用旧直道目标，由总管先定义兼容当前流程的具体任务，不直接照旧步骤测试。本轮未改固件。

## 历史记录

# 直道测试：编码器稳速与视觉微调

2026-11-18。负责：主控。当前固件 **0x02120002**，视觉R2；一次80RPM／2秒地面直行已确认正常LIMIT，主控反馈无明显摇摆。任务[I-03](../../project_planning/tasks/I-03-STRAIGHT-ASSIST.md)，[本次实测范围](../../testing/2026-11-18_straight_assist/ground_03_capture/review.json)，原I-02及本轮前两次失败保留。重复性／提速／完整圈另验。

最新视觉采用[vision_bundle_r2/straight_drive.py](../../testing/2026-11-18_straight_assist/vision_bundle_r2/straight_drive.py)。首个地面116ms因旧半段斜率门误拒绝当前双边而停车；视觉R2修正后，第二次563ms因左轮明显超调／右偏导致双边支持不足停车。固件02增加编码器差速补偿、PI候选Kp6／Ki8与更快轮速滤波后，第三次正常跑满2秒；末帧反馈82.83／84.86RPM、PWM28.2%／27.5%，UART及硬件错误0。当前板上02已验，不需重复下载／复位再验同一次；80RPM／2秒／50%上限保持。旧vision_bundle_final保留为视觉R1历史。

## 程序入口

| 用途 | 文件／预期 |
| --- | --- |
| STM32 Keil5工程 | [straight_assist.uvprojx](../MDK-ARM/straight_assist.uvprojx)，唯一目标 **StraightAssist** |
| 构建产物 | `control/build/firmware/straight_assist/straight_assist.axf`、`.hex`、`.bin` |
| K230无动力预览单文件 | [straight_preview.py](../../testing/2026-11-18_straight_assist/vision_bundle_r2/straight_preview.py)，ALLOW_DRIVE=False，发无效v3路径，显示原图 |
| K230直道许可单文件 | [straight_drive.py](../../testing/2026-11-18_straight_assist/vision_bundle_r2/straight_drive.py)，ALLOW_DRIVE=True，不传IDE图像，不发START |
| 固件版本 | `g_speed_revision=0x02120002`；`g_speed_fault=0` |
| 默认配置 | `g_lap_config.straight_rpm=80` RPM、`run_ms=2000` ms、`min_feedforward=200` 千分比 |
| 配置范围 | 巡航40..100RPM；单次500..3000ms；前馈0..300千分比，均只在停止时改、下次KEY锁定 |
| 正常结束 | `g_lap_last.reason=LAP_LIMIT(11)`、`elapsed_ms=2000`；撤PWM后滑行，停稳距离须实测 |

不选旧StraightTest、SpeedSprint、LowSpeedLap或Track，不用旧v2视觉搭配。新程序为直道段验证，不处理整圈、弯道或终点。

## 控制行为

视觉每帧检查当前双边白走廊，拟合直线，组合近处位置与道路方向代理量；拒绝明显折角、过大偏移、单边、历史和过期画面。沿用既有近似投影计算代理量，不称完整地面标定。至少3帧／80ms一致才可启动；丢线立即撤许可。

STM32每20ms读取真实编码器，两轮分别PI稳速。共同轮速从40RPM以100RPM/s爬升到巡航；视觉误差经80ms低通、0.08进入／0.04退出滞回，最大±12%差速，比例变化率不超过0.6/s。小幅左右噪声不会反复大幅拉低内轮；最低正目标35.2RPM。固件02直道PI候选Kp=6、Ki=8，轮速低通alpha=1/2；随后按`(实测左-实测右)-(目标左-目标右)`直接补偿PWM，增益4千分比/RPM、幅度最多正负100千分比。左轮实际偏快时减左加右，保留视觉有意安排的目标差速，不强制同速转弯。抗饱和、起步限时、50%上限不变。旧01的Kp2／Ki12与alpha1/4属于历史；新参数仍待地面验证。轮径、侧滑仍可能造成偏移，视觉持续监督。

保留两次人工单轮500ms／50%配对、KEY立即撤驱动、300ms无反馈、原始反向<-5RPM／超速>600RPM、编码器时序／UART错误／溢出／源年龄监督、TIM5启动超时及IWDG。停止／故障清积分和直道滤波；恢复画面不自动重启。PWM=50%而RPM仍明显低于目标时属于饱和线索，先保存证据，不以提高软件上限掩盖带载问题。

## 现场顺序

1. **主控先关闭驱动动力、支稳两只驱动轮悬空**，保留现有已核对接线。沿用车载供电及CMSIS-DAP；DAP仅SWDIO／SWCLK／GND，不接供电或NRST。KEY为实物KEY键，对应PA0／WKUP；RST为另一复位键。
2. 主控Keil5选择 **Project → Open Project** 打开上述新工程，目标选 **StraightAssist**；**Project → Rebuild all target files**，应0错误0警告；**Flash → Download** 人工下载。保持悬空，不按KEY。若要查看Watch，用 **Debug → Start/Stop Debug Session** 后Run，核对版本／配置／故障0；运动时不暂停、单步或加断点。最终退出调试后若状态丢失，按新上电校准，不沿用旧RAM。
   - 本轮实读已发现“Flash完全正确、下载后应用RAM尚未初始化”的情况。此时保持悬空，退出并关闭Keil后由主控按实物RST一次，再读版本／毫秒递增／零PWM；非法RAM不当故障，不按KEY绕过，也不重复烧录掩盖。代理只读工具不会自行复位或恢复CPU。
3. K230先在CanMV中停止旧脚本，打开并运行 **straight_preview.py**。该文件自包含，无需复制模块；不覆盖`main.py`。先看新程序能输出`[STRAIGHT LOG]`、约每10帧一行状态，串口接收增长但两轮PWM0。预览画面还须在正常安装高度、直道居中／车头平行道路时核对；动力仍关闭。预览的`wire_valid=False`是预期，`reason=ready`才说明几何门通过；若不是ready，先保存原图和日志，不进行地面。
4. 停止预览，保持轮子悬空，CanMV打开并运行 **straight_drive.py**，预期`[STRAIGHT] ready ... valid True`。此时只建立路径许可；不因相机有效自动开车。日志在`/sdcard/straight_logs/run_XXXX.jsonl`，不覆盖历史。处理必须<=100ms、发送前年龄<150ms，实际连续周期应明显小于200ms；若超时／频繁无效，先处理视觉时序。
5. 主控打开动力，悬空长按KEY约1～2秒后松开：第一次只左轮前进500ms并停，第二次只右轮前进500ms并停，两次之间待停稳及准备灯。核对`g_speed_match.phase=2`、`g_lap.state=LAP_WAIT(1)`、fault／UART错误0。校准只识别当前编码器通道与符号；轮子实际朝车头须目视确认。若相机启动STOP使尚未完成的配对重置，以当前phase为准，不盲按第三次KEY。
6. 悬空可再按一次KEY验证双轮约2秒、编码器跟踪与无大幅差速；本次若只是为确认调用链，不据此放行地面。悬空运行中停止K230脚本应由v3 STOP撤驱动；断开视觉输入应在既有源年龄期限内撤PWM。故障后保存原因再复位并补必要两次配对，故障画面恢复不会自行启动。
7. 通过上述检查后，主控保持车载供电，把车置于**顺时针直道居中、车头平行道路、前方至少2米直道并留滑行空间**；两只电脑USB／调试线脱开，确认K230仍由车载供电运行。只拔电脑USB不能切断相机车载供电；也不能误复位K230启动旧main。新相机入口10分钟后会发STOP退出，超时应停稳后手动重新运行。`g_lap.state=LAP_WAIT`下正常双边绿灯每2秒约亮400ms，快闪为故障；保持当前ready后，主控只按一次KEY长按松开，试跑2秒，接近边界时KEY立即终止。
8. 停后先记录真实距离、明显左右摆动、最大横向偏移、触边及灯态。**保持车载电、不按RST／不重跑／不进入Debug**，保存冻结环和日志。正常应在2000ms以LIMIT结束；快闪应按真实reason处理，不能当正常限时。

首轮若主控希望更低速度，停止时先设60RPM／2000ms，保留记录；稳定后按60→80→100RPM逐档，不同时改速度、PI和视觉参数。80RPM是默认设定，不是实测车速或达标证明。研发试验人工KEY终止不能记作正式自主完圈。

## 停车取证与本地复现

本轮若主控希望由代理直接运行视觉、避免手动入口未执行导致KEY启动被拒，可在实读phase2／零输出后使用：

```powershell
vision/.venv/Scripts/python.exe vision/tools/run_straight_live.py --port COM10 --confirmed-calibrated --output testing/2026-11-18_straight_assist/new_live
```

该后端须持续保持，不能启动后立即关闭／另连CanMV；实际10分钟相机输入窗口与STM32每次2秒独立。它不发START、不写main.py，当前路径有效且KEY人工启动才会运动。KEY无动作时先看当前path_valid和received是否增长，不要求重复配对或反复按键。

主控完成停车后的三线连接且Keil关闭时，代理可使用下列**只读**命令（不自动下载、复位、暂停或启动）：

```powershell
vision/.venv/Scripts/python.exe control/tools/lap_swd_capture.py --profile straight --output testing/2026-11-18_straight_assist/ground_01_capture
```

必须先比对实际Flash与StraightAssist BIN，匹配后才按AXF解码RAM；输出目录必须新建。旧lap默认配置不变。冻结环保存最后32个20ms窗口，含原始增量、目标／实际RPM、PWM及PATH序号；相机逐帧日志用于对齐，不能用串口累计包数代替真实序号。每次运行另建记录，保留失败。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File control/tools/run_straight_assist_tests.ps1
vision/.venv/Scripts/python.exe control/tools/build_straight_assist.py
vision/.venv/Scripts/python.exe vision/tools/check_straight_assist.py --output testing/2026-11-18_straight_assist/new_check
```

本地证据见[record.md](../../testing/2026-11-18_straight_assist/record.md)。现有模型验证控制边界与保护，静态图验证指定样本方向，不能替代新程序的板上时序、带载反馈与直道不触边验收。

## 比赛关联

比赛第三部分、图1和表1要求顺时针自主完圈、5分钟内，用时越短基础功能得分越高；基本功能满分60，触黑边扣分、完全出界失败。直道抑摆用于降低触边／出界风险，稳定提速用于缩短整圈时间。验证同时记录用时、横向偏移、摆动、触边及成功次数；具体计分公式和单次触边扣分尚未明确，不编造得分收益。直道程序不能当正式整圈／额外功能已完成。
