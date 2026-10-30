# App：应用与诊断流程

2026-10-25目录迁移；维护：主控／01。

- Car/car.c、car.h：车辆启停／故障状态、路径时效与演示左右请求。
- Diagnostics/motor_bench.c、motor_bench.h：人工按键、诊断阶段、停止锁定和灯态的纯逻辑，供三种电机目标与电脑模型共用。
- Diagnostics/encoder_bench.c、encoder_bench.h：C-02C双路只读采样、独立计数器状态及Watch发布，未接入Car运动策略；不是纯算法，数学部分位于Algorithms/Encoder。

ORG-02当时只移动原文件；随后C-02C增加了上述实际编码器诊断，仍未实现PID或整车运动闭环。后续Car的策略与控制拆分由具体功能任务决定。接口见[模块API索引](../../docs/interfaces.md)，编码器当前接口以其模块头文件为准。
