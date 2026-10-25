# 引脚与外设资源入口

日期：2026-10-25（北京时间）。资源设计：主控／01；实物核对：硬件／02。

- **软件资源规格**：[control/docs/pin_plan.md](../control/docs/pin_plan.md)，维护GPIO、复用功能、定时器、UART和SWD分配。
- **实际针脚与线束**：[hardware_preparation/wiring.md](../hardware_preparation/wiring.md)，维护对端接口、电平、供电／共地和实物签核。
- **原图依据**：[主板原理图索引](../control/docs/evidence/2026-10-18_c02a/README.md)与[驱动／电机证据](../hardware_preparation/evidence/2026-10-18_i03/README.md)。

本文件作为入口，不复制第二份完整引脚表。软件资源约定与实物导通／电气验收分别维护；旧PA0／PA1编码器候选已失效，当前按pin_plan核对。目录迁移没有改变任何端口、定时器或初始化行为。
