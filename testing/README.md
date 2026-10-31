# 联调、现场证据与验收

更新：2026-10-30（北京时间，补同型号新板烧录及电机旋转反馈）。归档：主控／02，视觉、硬件提供各自证据。
本目录已有下载、板内观察、电压与电机台架诊断记录；尚无整车跑圈或故障停车验收结果。全局结论查[项目状态](../project_planning/project_status.md)。

## 现有记录

| 目录 | 已归档范围 | 边界 |
| --- | --- | --- |
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
