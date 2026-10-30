# 引脚与外设资源入口

2026-10-29安装变更：主控已换左右轮并重新命名物理A左／B右，旧前进转向在新位置成为后退；当前资源到物理轮的对应及参数沿用统一见[当前轮位](../hardware_preparation/wheel_mapping.md)。新物理A/B不等同驱动插口MOTOR-A/B或编码器软件a/b；原始软件通道不随命名自动改动，当前实际配对待核。本次不改固件／引脚，不把旧安装的手转或桥级转停证据外推为新安装动力通过。


日期：2026-10-25（北京时间）。资源设计：主控／01；实物核对：硬件／02。

- **软件资源规格**：[control/docs/pin_plan.md](../control/docs/pin_plan.md)，维护GPIO、复用功能、定时器、UART和SWD分配。
- **实际针脚与线束**：[hardware_preparation/wiring.md](../hardware_preparation/wiring.md)，维护对端接口、电平、供电／共地和实物签核。
- **原图依据**：[主板原理图索引](../control/docs/evidence/2026-10-18_c02a/README.md)与[驱动／电机证据](../hardware_preparation/evidence/2026-10-18_i03/README.md)。

本文件作为入口，不复制第二份完整引脚表。软件资源约定与实物导通／电气验收分别维护；旧PA0／PA1编码器候选已失效，当前按pin_plan核对。目录迁移没有改变任何端口、定时器或初始化行为。
