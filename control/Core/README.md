# Core：入口、SPL配置与启动

2026-10-25目录迁移；维护：主控／01。

- Inc/stm32f4xx_conf.h：选择SPL外设模块，保留原宏与断言。
- Src/main.c：HardwareBench主循环。
- Src/logic_demo.c：LogicDemo无硬件演示。
- Src/board_self_test.c：独立板级自检。
- Src/motor_bench_main.c：MotorBench／MotorContinuous入口、滴答和监督。
- Src/motor_direct_main.c：MotorDirect入口与原保护。
- Startup：F407启动汇编与原许可。

这些入口由[MDK-ARM工程](../MDK-ARM/yeye_control.uvprojx)逐目标显式选择；不要全部编入同一个目标。板级函数在Drivers_Custom/Board，状态逻辑在App。没有CubeMX生成来源或.ioc配置。
