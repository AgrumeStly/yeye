# 整车文档入口

日期：2026-10-25（北京时间）。维护：00统筹，01／02及对应成员维护模块原文。
本目录提供按主题查找的入口；技术规格和实测记录继续在原维护位置更新，避免产生两份互相冲突的参数表。

| 入口 | 内容 |
| --- | --- |
| [architecture.md](architecture.md) | 整车数据流、STM32软件分层、目标与职责 |
| [pinmap.md](pinmap.md) | MCU资源与实物针脚资料入口 |
| [hardware.md](hardware.md) | 已确认型号、接线、供电和硬件版本入口 |
| [interfaces.md](interfaces.md) | C模块API索引、调用约束与跨板协议入口 |
| [tasks.md](tasks.md) | 当前任务、完整任务单和四对话接续入口 |
| [test-log.md](test-log.md) | 软件验证与实物测试入口及证据层次 |

当前已通过的A/B分步PWM基线为[MotorPwm独立入口](../control/MDK-ARM/motor_pwm.uvprojx)；后续开发从[多目标Keil工程](../control/MDK-ARM/yeye_control.uvprojx)与[C-02D运动接口任务](../project_planning/tasks/C-02D.md)接续，Direct独立入口保留为对照。目录迁移范围及验证见[ORG-02](../project_planning/tasks/ORG-02.md)，人工验收见[本次PWM记录](../testing/2026-10-25_motor_pwm/acceptance_record.md)。
