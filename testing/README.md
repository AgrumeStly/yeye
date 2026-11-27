# 验证与现场证据入口

更新于 2026-11-27。原始失败和复测按日期、版本及条件保留。

- [联合过弯 v12 配对包](2026-11-25_joint_angle_voice/v12_timing_fix_release/README.md)及[较早 v12 兼容修订的左轮无反馈记录](2026-11-25_joint_angle_voice/v12_left_no_feedback_swd.json)。
- [v9 完整通过首弯基线](2026-11-18_right_angle/voice_v9_pass_baseline/parameters.md)。当次停后绿灯快闪，故障码待核。
- [首弯历史停机](2026-11-18_right_angle/resume_20261119.md)。858 ms LINK2，未进弯，含前次 PATH 差异、缺失触发帧和日志问题。
- [直道任务限定验收](../project_planning/tasks/I-03-STRAIGHT-ASSIST.md)：一次80RPM／2秒，不代表重复性或整圈。
- [首弯最终归档](2026-11-18_right_angle/release_r6_final/README.md)：版本配对来源，非通过证明。
- [统一任务及验收规则](../project_planning/tasks/README.md)：按改动选检查，已有适用证据复用；主控明确验收后总管更新状态。

## 历史证据导航（原文保留）

以下“最新／待验”限于原日期和版本，不能覆盖上方接续。

# 联调、现场证据与验收

2026-11-10接续：[新电池宿舍复测准备](2026-11-10_pre_field/record.md)：主控确认新电池安装、已充满、驱动供电正常且可悬空测试，端电压未测；09／0A重新构建与基线一致，控制／UART与台架入口检查通过，操作单及取证表已准备；新电池下动力／断源保护／一圈待验。

2026-11-10新增：[OLED点亮记录](2026-11-10_oled_bench/record.md)：独立工程零错误零警告、Keil下载／Flash比对、0x3C应答与持续写帧，主控确认画面完全清晰；当前板上为无动力OledBench，运动集成另验。

更新：2026-10-30（北京时间，补同型号新板烧录及电机旋转反馈）。归档：主控／02，视觉、硬件提供各自证据。
本目录已有下载、板内观察、电压与电机台架诊断记录；尚无整车跑圈或故障停车验收结果。全局结论查[项目状态](../project_planning/project_status.md)。

## 现有记录

- [2026-11-09低速一圈整合候选](2026-11-09_low_speed_lap/review.md)：独立STM32差速／v2通信、L1轻量视觉、构建与失效检查；真实板上／UART／动力与整圈均待验，不把交付当作能完圈。

- [2026-11-09视觉多帧／二维推荐路线T2](2026-11-09_vision_temporal_route_t2/review.md)：完整两圈预览、1394张回归、真实时间历史与节点、遮挡误差和失败版本；比赛目标一圈，板上／动力待验。

| 目录 | 已归档范围 | 边界 |
| --- | --- | --- |
| [2026-11-08_vision_recovery_c2](2026-11-08_vision_recovery_c2/review.md) | V-06独立C2／1394张回归、全关键段及新增输出复核 | 原R1/C1不变，单带弯中及完整过弯路径仍有缺口 |
| [2026-11-08_vision_finish_f1](2026-11-08_vision_finish_f1/review.md) | V-07独立终点模块、两次同会话事件、负例／时序检查 | 不证明车尾越线或自动停车，不称可靠率 |
| [2026-11-08_vision_board_prep](2026-11-08_vision_board_prep/review.md) | V-08诊断子集、20字节包、原生产C交叉检查及下一次无动力步骤 | 仅电脑软件，未操作板卡／UART／电机；完整移植及整车待验 |
| [2026-11-01_speed_sprint](2026-11-01_speed_sprint/acceptance_record.md) | 直线带载逐档提速的待填现场记录；软件检查见模块说明 | 尚无本版下载、地面转速、跑偏或停车结果，不把模板或悬空同速反馈当作地面通过 |
| [2026-10-30_new_board_flash](2026-10-30_new_board_flash/record.md) | 同型号新主板烧录EncoderBench 0x020C0001，编译零错误零警告，Keil Programming Done／Verify OK；后续电机复测主控回报“旋转正常” | 电机反馈未逐项确认轮侧／前进方向、AB并转、自动停转及MotorPwm版本；编码器与整车仍未验，原烧录日志仅对应EncoderBench |
| [2026-10-20_motor_bench](2026-10-20_motor_bench/acceptance_record.md) | 原版下载、启动故障与R1后绿灯恢复 | 自主启动完整变量／电机通过证据未齐 |
| [2026-10-21_motor_bench](2026-10-21_motor_bench/no_rotation_record.md) | 原PWM／R2无动作、[静态电压续报](2026-10-21_motor_bench/i05_measurement_results.md)、[R3快照](2026-10-21_motor_bench/r3_watch/README.md) | 目录日期是建档日期，续报保留实际日期；板内启停不证明外部波形／起转 |
| [2026-10-24_motor_continuous](2026-10-24_motor_continuous/watch/README.md) | 持续A启用／KEY停止配对Watch | 电机未转；[示波器结果表](2026-10-24_motor_continuous/scope_results.md)未填写，不算已测波形 |
| [2026-10-25_motor_direct](2026-10-25_motor_direct/acceptance_record.md) | 主控回报A通电起转、约500ms后停转，随后回报B也正常 | B的具体灯态／时长／下载读回未记录；原PWM失败及编码器、闭环、整车验证仍独立保留 |
| [2026-10-25_motor_pwm](2026-10-25_motor_pwm/acceptance_record.md) | 重写后1kHz／50%／500ms；软件检查通过，主控回报完整流程符合预期，A/B分别起转与自动停转人工验收完成 | 文字回报，无独立Watch/波形/精确计时；AB同时运行、编码器及闭环未验收 |

首次主板双闪另在[board_self_test_record.md](../hardware_preparation/board_self_test_record.md)，原路径保留。MotorDirect操作查[固件说明](../control/docs/motor_direct.md)及[B版说明](../control/docs/motor_direct_b.md)，不能把旧测试结果自动套给它。

## 新记录怎样保存

按需建立`YYYY-MM-DD_topic/`，保存一份记录、必要原始附件及索引。记录至少包含：

- 任务ID、实际测试日期、执行角色、操作人。
- 固件／脚本提交及未提交改动说明、Keil目标与revision、协议、接线版、参数。
- 环境、仪器、步骤、预期与实际结果、失败现象及停止条件。
- 原图／日志／录像位置、关键读数、测量参考点与单位。
- 验证到哪一层、仍未验证什么、后续修复与复测记录。

区分“电脑模型、编译、下载校验、板内变量、外部电气、机械动作、整车表现”。模板待填、已给指导、已有软件请求都不能填成实物通过；每次失败保留。

原图保持不变，必要时记录SHA256；注释图另存并链接原图。大录像可在共享存储，记录可获取位置与版本，Git忽略不表示已交接。

测试任务和依赖放`project_planning/tasks/`，技术方法放模块说明，报告引用这里的实测证据。全局状态只摘录关键结论，不复制完整现场流水。
