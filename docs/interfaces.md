# 模块API与跨板协议入口

日期：2026-10-25（北京时间）。维护：01负责C接口；主控与视觉共同确认跨板协议，硬件复核电平。
依据：本轮迁移后真实头文件。函数声明与类型以头文件为准；本页记录层级、调用责任与边界，不另复制一套字节包规格。

## STM32内部C模块

| 模块／真实头文件 | 主要API | 调用约束与结果 |
| --- | --- | --- |
| [board.h](../control/Drivers_Custom/Board/board.h) | board_init、board_millis、board_uart_read、board_uart_fault、board_apply_requests | 主框架使用；时间为uint32毫秒。UART默认关闭；左右request为演示归一化请求，不是m/s、编码器闭环或真实PWM输出 |
| [protocol.h](../control/Drivers_Custom/Communication/protocol.h) | protocol_crc16、protocol_encode、protocol_parser_init、protocol_push | 字节包编解码；push每次输入一个字节，只在完整验证帧时返回1。字段单位及错误处理见协议原文 |
| [car.h](../control/App/Car/car.h) | car_init、car_receive、car_tick、car_transport_fault、car_state_name | 车辆状态和左右请求；now为本机uint32毫秒，串口故障通过transport_fault进入故障状态；尚无实际轮速反馈 |
| [motor_bench.h](../control/App/Diagnostics/motor_bench.h) | motor_bench_init、motor_bench_tick、motor_bench_led | 纯诊断逻辑；tick按1ms监督，原始KEY电平输入；mask是A/B桥编号，不等于左右轮；LED不是转动反馈 |
| [motor_bench_pwm.h](../control/Drivers_Custom/Motor/motor_bench_pwm.h) | motor_bench_pwm_* | 仅PWM诊断目标使用；初始化／启停及保留快照。快照是MMIO读数，不能证明外部PWM或车轮停稳 |
| [motor_direct_gpio.h](../control/Drivers_Custom/Motor/motor_direct_gpio.h) | init、apply、stop、diag_context，均带motor_direct_gpio前缀 | 独立GPIO诊断：apply仅接受0停止或1仅A，其它请求拒绝并停止；逻辑电平通过AT8236驱动，GPIO不直接供电机电流 |

本轮没有修改任何应用函数签名、枚举、单位或运行逻辑。诊断入口保留SysTick、IWDG、TIM5限时等待等原保护，不能因为目录中出现Algorithms而把这些硬件监督搬成纯算法。

## 视觉与主控之间

唯一跨板结果包规格仍为[protocol_v1_draft.md](../control/docs/protocol_v1_draft.md)，当前尚为草案。该文件负责字节布局、端序、CRC、序号、有效性、单位、更新和超时约定，未来动作反馈也在同一入口扩展。

本页是所有模块接口的导航和职责说明，没有另定义一个“最终协议”。视觉代码变更须共同确认兼容性；修改内部C接口时由01同步调用者、相关电脑测试和本页索引。
