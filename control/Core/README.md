# Core：入口、SPL配置与启动

2026-10-25目录迁移；维护：主控／01。

- Inc/stm32f4xx_conf.h：选择SPL外设模块，保留原宏与断言。
- Src/main.c：HardwareBench主循环。
- Src/logic_demo.c：LogicDemo无硬件演示。
- Src/board_self_test.c：独立板级自检。
- Src/motor_bench_main.c：MotorBench／MotorContinuous入口、滴答和监督。
- Src/motor_direct_main.c：MotorDirect入口与原保护。
- Src/encoder_bench_main.c：C-02C只手转入口，四电机输入低、R1／IWDG、1ms滴答和10ms编码器采样；独立encoder_bench工程，不加入原六目标。
- Startup：F407启动汇编与原许可。

原六目标入口由[MDK-ARM工程](../MDK-ARM/yeye_control.uvprojx)逐目标显式选择，编码器使用[EncoderBench独立工程](../MDK-ARM/encoder_bench.uvprojx)；不要全部编入同一个目标。板级函数在Drivers_Custom/Board，状态逻辑在App。没有CubeMX生成来源或.ioc配置。
