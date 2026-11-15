# 首次地面三秒短直道

状态：已实际执行一次地面试跑，出现停车后急闪，按未通过保存，具体停因待无复位取证。

## 主控实际反馈

### 最新取证补充与现场接续

0B第二次必要校准：主控对右轮500ms向前／自动停／左轮不动预期回复“正常”。[mcu0b_cal_right_01](mcu0b_cal_right_01/capture.json)实际phase2／error0、WAIT1／reason0、硬件及UART错误0、目标及PWM0、40RPM／3000ms／前馈200，取证环total0／frozen0且last_run.valid0；没有重复双轮悬空RUN。相机在当前悬空视角有双边及单边交替，steering-503→-594，不作地面稳定双边许可。DWT SysTick1781周期=111.3125us、提交1299=81.1875us、UART196=12.25us，仅校准／待机基线。下一步仅脱开DAP SWD三线，保持车载供电及悬空观察10秒周期灯；不按第三次KEY／RST，不进Keil Debug。随后另行摆直道，准备0B取证版一次针对性地面复测。

0B第一次必要校准：主控对左轮500ms向前／自动停／右轮不动预期回复“正常”。[mcu0b_cal_left_01](mcu0b_cal_left_01/capture.json)无复位实读phase1／READY1／error0、输出及故障0、UART错误0、接收递增、配置3000ms保持。当前悬空PATH仍无效，未启动双轮。下一步仅第二次KEY右轮500ms，不重做整套台架。

主控明确“已按”物理RST后，第三次无复位读取[mcu0b_baseline_03](mcu0b_baseline_03/capture.json)取得真实0B启动基线：Flash与1fc5ee49…33e4a28一致，revision0x0211000B、40RPM／3000ms／前馈200，g_lap CALIBRATION0／reason0，phase0／READY1／error0，目标及PWM0，硬件／UART错误0。ms21249→22361、接收383→405，CPU运行、看门狗started1／stage4；last_run.valid0，诊断环total0／frozen0。当前PATH无效且steering／bend0，符合不放行运动的条件，不能称双边通过。DWT counter_ready1／clock16MHz，SysTick1292周期=80.75us、motion_lock241=15.0625us、UART195=12.1875us，仅非RUN基线，不外推新增写环的中断时序。物理RST后应用初始化已恢复；前两次无效RAM保留，未以重下载替代。下一步仍悬空车载ON，仅第一KEY左轮500ms必要校准；不重做全台架，不启动双轮。

主控追加“正常”后再读[mcu0b_baseline_02](mcu0b_baseline_02/capture.json)：Flash仍完全一致，RAM版本／ms／state／phase与第一次相同，工具按新增初始化检查退出失败并保存原件；不记应用启动通过。该“正常”未明确写出RST动作，不补造已执行复位。下一步明确只指导一次物理RST（非KEY/WKUP），等待5秒，再读；不自动复位／暂停／下载，不进入校准。

主控按仅接不供电DAP电脑USB、Keil选LowSpeedLap／Flash→Download、暂不进Debug／按KEY的人工下载步骤反馈“正常”。[mcu0b_baseline_01](mcu0b_baseline_01/review.json)实际Flash与0B BIN完全一致；但RAM两次版本0x68016041、state74、phase1134586120，ms1229080643不递增，DWT时钟604016640与实际16MHz不符。拒绝作为初始化基线或真实故障，原始乱码／NaN保留；下载器算法残留可能，尚未证明。下一步仅主控RST一次建立应用启动基线，不重下载或按KEY。SWD工具补初始化不变量检查，后续无效RAM保存后退出失败，避免把Flash比对通过等同应用已运行；不加入自动reset／halt／resume。

主控对上述车载供电接新电池XT30／驱动ON、等待30秒、两轮悬空静止且两板灯正常的步骤反馈“正常”。两板电脑USB当时均不接。只记上电现象，v3实际相机／接收仍待实读。下载前重新核对当前LowSpeedLap短目标BIN与mcu_trace_build_02哈希均为1fc5ee49f6265499802fb6e5a3983542a4a60337a75fb8c05747d650433e4a28，Keil日志0错误0警告。下一步主控接仅SWD三线且不供电的DAP USB，GUI选LowSpeedLap手动Flash→Download；暂不进Debug、不按KEY。没有代理烧录或运动命令，下载尚待人工完成反馈。

取证及部署完成后，主控依次反馈“已悬空”“已断电”，再对全断电恢复K230车载5V0支路、UART T→A03／R→A02／G共地（V不接）、DAP仅SWDIO／SWCLK／GND且5V／3V3／NRST不接的步骤回复“接好”。当前两轮悬空、电脑USB全不接、驱动OFF／XT30断开；K230 main为已部署v3，STM32最后Flash仍09，0B仅本地构建。下一步只接XT30／驱动ON并等待两板上电、观察零运动，不按KEY／RST、不进入Keil；人工下载另一步安排。

主控已确认隔离K230车载5V0和UART T/R，再只接K230电脑USB。实取原run_0009及另存USB的run_0010，补10秒禁止驱动预览，并完成STM32原始采样冻结环及相机逐帧时间／序号取证版的具体实现、检查、ARM构建；相机v3已真实备份／部署／完整读回，STM32未下载。详细版本、哈希、证据边界与下一步见[diagnostic_candidate.md](diagnostic_candidate.md)。当前K230USB供电／v3 main／后端关闭且running=false；驱动OFF／XT30断开、DAPUSB不接、车载5V0与UART T/R仍隔离，车辆最后在地面。下一步仅支稳悬空，再安排恢复接线及Keil人工下载短版0B。不把取证能力补全当反向根因已解决或地面通过。

故障原件保存后，主控按驱动OFF／拔XT30／拔DAP电脑USB且K230电脑USB仍不接的步骤回报“完成”。当前整车断电，RAM校准不再沿用；不得以此断电掩盖此前2044ms反向反馈失败。下一步在断电下隔离K2305V0车载支路和UART T/R，再独立USB取原编号日志；USB新启动日志另存，不冒充本次地面。

### 无复位取得的实际停因

[fault_capture_01/capture.json](fault_capture_01/capture.json)成功，无Reset／Halt／Resume请求、Flash未写且与09 BIN一致。两次读数一致：g_lap.state6 FAULT／reason5 LAP_REVERSE；g_lap_last.valid1，elapsed_ms **2044**，reason5；末次目标左6.7676706／右22.9803333RPM，滤波反馈左12.2855244／右28.0350704RPM，撤驱动前PWM172／298千分比，起步补偿样本各1。当前两目标／PWM均0，g_speed_fault0、UART总数及各错误分项0，CPU运行、接收21770→21789，当前相机新包为双边有效。

校准phase2仍在，内部state7／error11来自故障锁定，不是新一次校准失败。starts_rejected为1，具体拒绝发生时刻及按键次数尚不能由该累计值确定，不向主控补造操作。滤波轮速在故障中停止更新，其停车后仍非零不是车仍在转。

源码lap_motion_sample在任一归一化原始轮速<-5RPM时立即触发LAP_REVERSE；快照保存的是滤波轮速和上一控制目标，未保存本次触发的原始delta／轮侧。因此2044ms反向反馈锁定已确认，实际回退、机械回弹或编码器瞬态的根因仍待核；不能以正滤波值排除原始负采样，不放宽反向保护掩盖问题。无UART故障证据，不把此次归因通信。下一步先动力隔离再取本次K230相机日志，分析左右摇摆和目标变化，保留现有STM32故障原件。

主控原话：“前进了很短距离，速度较慢，无触边，左右摇摆，自动停车，停后绿灯急速闪烁”。记为短距离／慢速／左右摇摆／无触边／自行停止，无实测厘米数、运行毫秒数或独立视频。源码急闪对应LAP_FAULT；尚未读state／reason／g_lap_last，不指定无反馈、视觉、通信或供电原因，也不记正常3000ms LIMIT。是否完全出界未单独回报，不由无触边补造。

下一步保持车载供电和原RAM，不按KEY／RST、不进Keil、不Download，接回仅SWDIO／SWCLK／GND（DAP不供电、NRST不接），直接无复位读取当前故障及最后RUN。先保存停因再解决，不重复启动掩盖失败。停车快照解码已核对实际AXF DWARF40字节布局，离线检查见decoder_check.json，未因此操作板卡。

## 试跑前条件与安排（历史）

主控确认DAP脱开后周期闪正常，随后按最终赛道直道居中／车头顺时针／前方至少1米空直道／所有电脑线脱开／正常车高摆放、不按KEY或RST，观察10秒灯态反馈“符合前者”，即每2秒亮约0.4秒的当前双边待机灯。此为人工灯态确认，非连续逐帧视觉日志。

最近无复位实读见../swd_detach_01/cal_right_01/capture.json：LowSpeedLap09，0x02110009，40RPM／3000ms／前馈200，phase2／error0／WAIT，硬件与UART故障0，目标及PWM0。STM32 BIN SHA256为7f3f7b5e8c676e321e23f3c2c2b6a88cd0e3821c5b8f80af9f608cce3224e2f9。真实相机持续v2 main SHA256为838c5e9a4d14d42840c54526b1f3c4d4a848e93654de8bca5faf45f85fb2968f，R6检测器，无固定fixture／START。

供电为新电池→驱动板稳压5V并联两板；K230电脑USB和DAP调试三线均已脱开；驱动ON。本次脱DAP后STM32静态读数5.178V／3.315V，非动态示波验收。此前悬空真实相机三秒结论复用，不重做全台架。

下一项仅人工KEY长按1—2秒松开，观察一次地面最多3秒运动。记录起转、方向、偏左／偏右／基本直行、距离、触边／出界、自动或人工停止。明显偏离时人工KEY立即终止，保存失败；不追加第二次KEY、不复位或断电覆盖结果。停车后取g_lap_last及当前故障／PWM，未实读前不指定LIMIT或故障原因。

对应比赛第三部分项目要求／图1／评分表基本功能60分：本项为完圈前地面纠偏及保护验证，减少触边／出界风险；不是自主完圈、用时成绩或实际得分。完整顺时针一圈、弯道／锐角仍未验。
