# 整车文档入口

日期：2026-10-25（北京时间）。维护：00统筹，01／02及对应成员维护模块原文。
本目录提供按主题查找的入口；技术规格和实测记录继续在原维护位置更新，避免产生两份互相冲突的参数表。

| 入口 | 内容 |
| --- | --- |
| [architecture.md](architecture.md) | 整车数据流、STM32软件分层、目标与职责 |
| [pinmap.md](pinmap.md) | MCU资源与实物针脚资料入口 |
| [hardware.md](hardware.md) | 已确认型号、接线、供电和硬件版本入口 |
| [interfaces.md](interfaces.md) | C模块API索引、调用约束与跨板协议入口 |
| [tasks.md](tasks.md) | 当前任务、统一任务格式和新总管／执行接续入口 |
| [test-log.md](test-log.md) | 软件验证与实物测试入口及证据层次 |

当前工程任务以[全局状态](../project_planning/project_status.md)和首弯接续为准；旧MotorPwm为历史基础，不能据旧导航重启C-02D。工程分层与迁移来源见[ORG-02](../project_planning/tasks/ORG-02.md)。
