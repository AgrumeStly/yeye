# 主控开发：到货前基础工程

配置日期：2026-10-12。目标为已购的立创天空星 STM32F407VET6 青春版。采用STM32F4标准外设库（SPL），已建立Keil5工程、通信解析、状态机、电脑模拟测试和操作说明。

**主控从这里开始：** 双击 `firmware/yeye_control.uvprojx`，选择 `LogicDemo`，按 F7 编译。无硬件演示见 [Keil操作说明](docs/keil_quickstart.md)。

| 位置 | 内容 | 主责 |
| --- | --- | --- |
| `firmware/yeye_control.uvprojx` | Keil工程，含LogicDemo、HardwareBench两个目标 | 主控 |
| `firmware/src/car.c` | 启动、停止、路径失效与通信超时状态机 | 主控 |
| `firmware/src/protocol.c` | 定长结果包、CRC、流式接收解析 | 主控；视觉按协议发送 |
| `firmware/src/board.c` | HSI时钟、滴答、待启用UART、调试输出变量 | 主控；硬件复核引脚 |
| `docs/` | 操作说明、协议草案、状态图、引脚候选、验证记录 | 三人共同阅读 |
| `tests/` | 主控C代码的电脑端自动测试 | 主控 |
| `tools/` | 编译、测试、调试初始化和Python编码示例 | 主控；视觉参考编码示例 |

主控学习标准库入口：[标准库代码说明](docs/standard_library.md)，按时钟→GPIO→USART→NVIC顺序阅读board.c。

## 当前完成范围

- 台式机Keil5.24a / ARM Compiler 5.06 update 5，已补充官方STM32F4xx_DFP 2.17.1。
- FLASH `0x08000000 / 512 KiB`，普通SRAM `0x20000000 / 128 KiB`。64 KiB CCM尚未分配。
- 工程依赖随代码保存，路径均相对工程目录。LogicDemo不访问外设寄存器。
- 外设配置调用RCC_*、GPIO_Init、USART_Init、NVIC_Init；内核滴答、中断屏蔽与FPU启动使用CMSIS。
- HardwareBench使用内部HSI 16MHz、1ms滴答、约5ms一次主循环调度，不依赖外部晶振。

**当前不是整车运行程序。** 电机输出只是 `left_request/right_request` 调试值；UART默认关闭，未配置电机PWM、编码器、速度PID、自动完成一圈停车或语音应答。这些功能到货后按实物与接线继续接入。协议参数为草案，尚待视觉共同确认。

## 收工与换电脑

主控保存代码、验证后提交任务分支并推送；笔记本Clone/Pull相同分支。build目录和IDE本机状态不入库。笔记本安装Keil、对应编译器与芯片包后，执行 `tools/setup_debug.ps1` 再打开工程；已有本机调试设置不会被覆盖。

硬件接线资料放 `../hardware_preparation/`；视觉侧实现放 `../vision/`；整车测试结果放 `../testing/`。
