# 模块API与跨板协议入口

2026-10-29安装变更：主控已换左右轮并重新命名物理A左／B右，旧前进转向在新位置成为后退；当前资源到物理轮的对应及参数沿用统一见[当前轮位](../hardware_preparation/wheel_mapping.md)。新物理A/B不等同驱动插口MOTOR-A/B或编码器软件a/b；原始软件通道不随命名自动改动，当前实际配对待核。本次不改固件／引脚，不把旧安装的手转或桥级转停证据外推为新安装动力通过。


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
| [encoder_hw.h](../control/Drivers_Custom/Encoder/encoder_hw.h) | encoder_hw_init、encoder_hw_read | SPL TIM3／TIM4初始化及实际CNT读取；两路非同时锁存，不自动输出电机 |
| [encoder_counter.h](../control/Algorithms/Encoder/encoder_counter.h) | encoder_counter_init、encoder_counter_update | 16位有符号增量、64位累计、实际dt及counts/s；无CPR／RPM，异常窗口与连续性标志须处理 |
| [encoder_bench.h](../control/App/Diagnostics/encoder_bench.h) | encoder_bench_init、encoder_bench_sample | 10ms手转诊断与Watch发布；原始a/b保留硬件符号，不自动解释车辆前进 |

C-02C新增上述编码器Interface；已有接口保持原语义。诊断入口保留SysTick、IWDG、TIM5限时等待等原保护，不能因为目录中出现Algorithms而把这些硬件监督搬成纯算法。

## 视觉与主控之间

唯一跨板结果包规格仍为[protocol_v1_draft.md](../control/docs/protocol_v1_draft.md)，当前尚为草案。该文件负责字节布局、端序、CRC、序号、有效性、单位、更新和超时约定，未来动作反馈也在同一入口扩展。

本页是所有模块接口的导航和职责说明，没有另定义一个“最终协议”。视觉代码变更须共同确认兼容性；修改内部C接口时由01同步调用者、相关电脑测试和本页索引。

## 计划中的运动Module与视觉调用

[C-02D](../project_planning/tasks/C-02D.md)拟提供左右目标RPM、停止、状态反馈与非阻塞周期执行；尚未实现，当前没有可供调用的motion.h，不能把这些名字当作现成函数。反馈／轮速控制、PWM及保护由STM32内部封装，目标单位不是占空比。

视觉侧继续通过既有20字节协议发送路径、START和STOP，不能跨板直接调用C函数。START的新鲜有效路径条件与STOP优先保留；STATUS目前没有状态回包。台架闭环及协议接收分别验收后，再由02连接真实运动；旧car演示左右request不能未经换算当RPM／PWM。