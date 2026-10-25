# R3首次A保留快照：主控截图证据

日期：2026-10-21（北京时间）。三张截图由主控在本对话提供，00原样复制、读取并核对，未操作板卡／改固件／上传。按上一轮无动力采集步骤交回；截图本身不能独立证明电池已断开，未额外补造现场操作。

## 读数及判断

| 项目 | 原始读数 | 解释 |
| --- | --- | --- |
| request_count／enable_calls／enable_count／stop_count | 全部0x00000001 | 新A请求、执行启用、读回MOE启用、结束事件各一次，不是电机转数 |
| last_mask／active.mask／stopped.mask | 全部1 | 对应同一次A桥；停止帧mask是事件标签，不是仍在驱动 |
| start_ms／stop_ms | 0x0000BCE2／0x0000BED6 | 十进制48354／48854ms |
| elapsed_ms／stop_reason | 0x000001F4／1 | 实际滴答差500ms，正常超时结束 |
| active／stopped valid与run_id | 全部1 | 活动与停止帧配对且采集完成，valid本身不是硬件合格标记 |
| active.state／fault，stopped.state／fault | 4／0，0／0 | 运行时RUNNING，停止采集时WAIT_RELEASE，两个采集点无软件fault |
| TIM1 CR1／PSC／ARR（两帧） | 0x81／0／0x31F | CEN=1，PSC0、周期800；停止后计数器保持运行符合原设计 |
| TIM1 CCER（两帧） | 0x1111 | 四普通通道使能，高有效 |
| TIM1 CCMR1／CCMR2（两帧） | 0x6868／0x6868 | 四通道PWM1并启用预装载，与配置一致 |
| 活动BDTR／CCR1–4 | 0x8C00／(0xF0,0,0,0) | MOE=1，A通道比较值240，即名义30%配置 |
| 停止BDTR／CCR1–4 | 0x0C00／(0,0,0,0) | MOE=0，四CCR清零 |
| 活动GPIOE MODER／AFRH | 0x28880000／0x01101010 | PE9／11／13／14为AF模式，复用AF1 |
| 停止GPIOE MODER／ODR | 0x14440000／0 | 四脚GPIO输出，ODR为低 |
| 活动／停止GPIOE IDR | 0x27D／0x7D | PE9在活动采样时读高、停止采样时读低；仅单次数字样本，不证明20kHz／30%实际波形和幅值 |
| RCC AHB1ENR／APB2ENR（两帧） | 0x00100013／0x00000001 | GPIOE与TIM1时钟使能位均为1 |

本次板内请求、TIM1／GPIO配置与启用／500ms停止读回均符合预期，未发现应立即修改固件的证据。图中没有g_motor_bench_revision、连续两次ms或总体实时state，不填已独立核验版本／持续计时；结构与已交付R3一致。

实际MCU排针波形、连线到驱动输入、Vin／内部VM与带载能力、H桥输出及电机仍未测；不能写成“PWM实测正常”“固件完全无问题”或“驱动已损坏”。优先按[I-05步骤](../../../hardware_preparation/i05_measurement_guide.md)做M01–M03静态供电测量，保留R3，不继续加占空比或自动复测B／AB。

## 原图与SHA256

| 文件 | SHA256 |
| --- | --- |
| [01_summary.png](01_summary.png) | 946f24a475e2bb19726f137dc5bcf294d1699bd878871c107c6c41a56d3f2aba |
| [02_active.png](02_active.png) | 8ad43490f539bd34ff82f70923b2c3dcaa41edccf6f4e7b879a8d8e8588debc9 |
| [03_stopped.png](03_stopped.png) | bc2c5c2868e0c1b92c14ee865b2009b818d86f0c170c12390277ba60d32db1ac |
