# 低速试跑：K230D与STM32三线通信

日期2026-11-09；主控负责实物接线与验证；本地资料完成，实物待反馈。依据[I-02](../project_planning/tasks/I-02-LOW-SPEED-LAP.md)、[STM32唯一资源表](../control/docs/pin_plan.md)及[立创官方UART教程](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/basic/uart.html)第6.2／7／8节（本日查阅）。

主控确认相机与原电机／编码器接线保持，视觉板尚未接主板。本页只增加通信三线，不改变原供电／电机线。使用K230D两个侧按键之间、丝印**2**的GH1.25-4P串口座，按实物T/R/G/V识别，不按线色或照片左右猜针号。

| K230D丝印／功能 | 接STM32实物丝印／端口 |
| --- | --- |
| T，GPIO11／UART2_TXD | A03，PA3／USART2_RX |
| R，GPIO12／UART2_RXD | A02，PA2／USART2_TX |
| G，公共地 | 已确认GND |
| V，5V | **不接，线头单独绝缘** |

先断电再插线，保持两板各自已有供电方式，不并接两路电源输出；通信信号采用3.3V逻辑，共地、TX/RX交叉。串口0为系统控制台，本轮不用；缓存IO3/4是UART1示例，不是此座。没有合适GH转接线时，先核实可用线材，不能把裸线强塞座子或换猜另一组GPIO。

配置：FPIOA GPIO11→UART2_TXD，GPIO12→UART2_RXD，UART2 115200／8数据／无校验／1停止。新LowSpeedLap使用STM32 USART2 A02/A03；旧HardwareBench是否启用不代表新目标状态。

接好后电机动力保持物理断开。先按[试跑说明](../control/docs/low_speed_lap.md)检查板上诊断／真实收包，保存所运行版本、完整终端和Keil Watch；软件封包通过不能代替这一步。此接线支撑基本功能60分所需闭环与断流停车，降低失控／出界风险，不声称接线本身加分或已通信成功。
