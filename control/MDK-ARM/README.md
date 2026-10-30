# MDK-ARM：Keil工程与本机调试

2026-10-25从firmware目录迁移；维护：主控／01。

- [yeye_control.uvprojx](yeye_control.uvprojx)：六个原目标，宏、设备、编译参数和逐文件启用／排除保持不变。
- [motor_direct.uvprojx](motor_direct.uvprojx)：只有MotorDirect的独立入口，仍共享同一源码与输出。
- [encoder_bench.uvprojx](encoder_bench.uvprojx)：只有EncoderBench，只手转读取双编码器，不链接电机启动代码；[操作与供电](../docs/encoder_bench.md)。原六目标及motor_pwm／Direct A/B工程未编辑。
- [motor_pwm.uvprojx](motor_pwm.uvprojx)：已通过A/B分别起转／停转的MotorPwm复现入口；本轮不做新的动力测试。
- [motor_direct_b.uvprojx](motor_direct_b.uvprojx)：保留MotorDirectB独立入口，不用于本轮编码器手转采集。
- 本机两个.uvoptx和DebugConfig已随工程迁移，CMSIS-DAP、Flash算法与Watch设置保留；这些被Git忽略，换电脑仍需分别核对。
- .uvguix界面状态随本机保存；正式构建产物改为control/build/firmware。旧firmware/build保留历史日志及产物。

主控在Keil使用Project → Open Project打开本目录工程，按任务选择目标，再Rebuild；下载属于后续明确的人工步骤，本轮只编译未烧录。

同一checkout的两个Direct入口共享输出，不并行构建。tools/setup_debug.ps1只在没有本机uvoptx时安装旧双目标默认模板，不能据此保证换电脑六目标设置完整；此原环境缺口未在迁移中扩大为行为变更。
