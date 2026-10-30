# Drivers_Custom：主控自编适配

2026-10-25目录迁移；维护：主控／01。

- Board：保留原board.c/h，包含HSI、SysTick、UART及请求调试边界。本轮整体迁移，没有拆改中断或初始化。
- Motor：保留motor_bench_pwm.c/h与motor_direct_gpio.c/h，分别服务PWM／固定GPIO诊断，不等于整车闭环驱动。
- Communication：保留protocol.c/h字节包编码与流式解析；实际UART收字节仍在Board。
- Encoder/encoder_hw.c、encoder_hw.h：C-02C的TIM3 PC6/7、TIM4 PB6/7 AF2计数器初始化与真实CNT／数字输入读取，不配置TIM1／TIM5或UART，不做左右与符号标定。

Encoder已按C-02C实际实现；后续传感器按任务建立Sensor。纯数学算法放Algorithms，车辆策略放App。外部SPL源码在Drivers中维护来源与许可。
