# 双电机端口接线自查与代码复核

状态：v1.0，源码／工程／电脑检查完成，主控已反馈现场人工自查一致，电气与起转验收未通过。日期：2026-10-24（北京时间）。维护：主控／01；接线证据由主控／02归档。

本表响应主控“重新检查代码、梳理各端口接线表”的要求，是当前方案的便查副本。资源定义仍以[pin_plan.md](../control/docs/pin_plan.md)为准，逐线功能以[wiring.md](wiring.md)为准。沿用天空星STM32F407VET6青春版、AT8236 Standard／YB-MNT03-V1.0、MD310Z20_7.4V，不重新选型号。

**本轮自查全程驱动OFF、XT30动力电池拔开、DAPLink USB及主板Type-C断开。不按KEY、不试转、不重新下载。** 前一步测电阻时，A电机两根动力线已要求脱离驱动；先按本表核对位置，不能把这一临时状态误记成正常运行接线。主控可断电逐项复核／复原并记录，完成后仍不接动力。

## 1. 代码复核结论与范围

本次重新读取真实应用、SPL GPIO／TIM实现及宏、Keil各目标文件清单，查看ST复用表第65／66／68页、天空星排针／调试口原图、已归档驱动与主板照片；完整Rebuild MotorContinuous并检查其反汇编。**未发现本次四路PWM的端口、AF、定时器通道、CCR或主输出使能存在明确写错／遗漏。此结论不等于固件不存在其他问题，也不等于板外波形或电机通过。**

| 核对项 | 当前代码实际内容 | 结论／边界 |
| --- | --- | --- |
| 真正入口 | Keil MotorContinuous编入motor_bench_main.c、motor_bench.c、motor_bench_pwm.c和原厂RCC／GPIO／TIM／IWDG；不编入board.c、main.c、USART驱动 | 旧board_apply_requests只存请求，不是当前电机输出路径；只检查board.h／board.c会漏掉真实入口 |
| 目标宏／版本 | MotorContinuous独有MOTOR_CONTINUOUS_A_TARGET=1，同时MOTOR_BENCH_TARGET=1、BOARD_UART_ENABLE=0；运行版本0x020B1001 | 原MotorBench是0x020B0003、500ms A→B→AB；两目标不可混同。主控后续已确认当前持续版Watch版本／fault／ms符合期望，未另附原始截图 |
| GPIO时钟与脚位 | 开GPIOE时钟；MOTOR_PINS为PE9／PE11／PE13／PE14，掩码0x6A00；推挽、下拉 | 不配置PE8／PE10／PE12；运行时将同一四脚切换AF模式 |
| 复用 | GPIO_PinAFConfig(GPIOE, PinSource9／11／13／14, GPIO_AF_TIM1)，原厂宏GPIO_AF_TIM1=1 | ST DS8626表9对应TIM1_CH1／2／3／4，未套F103重映射或CHxN |
| 定时器与频率 | APB2 TIM1时钟开启；实际RCC必须为HSI／总线均16MHz，否则fault锁定；PSC0、ARR799、向上计数、PWM1高有效 | 16MHz÷800=20kHz；不是直接套168MHz参数 |
| 四通道输出 | OC1–OC4均OutputState_Enable，CH1–CH3互补输出禁用；CCxE应为1，极性正常；BDTR初始Break禁用 | E08／E10／E12是CH1N／2N／3N，不能作为已启用普通通道替代脚 |
| A运行比较值 | CCR1=240、CCR2=0、CCR3=0、CCR4=0 | 240÷800=30%；仅PE9有PWM，其余三根低。MotorContinuous不会自动运行B或AB |
| 输出打开顺序 | 关闭MOE时写四CCR→UG使预装载更新→GPIO改AF→TIM_CtrlPWMOutputs(TIM1, ENABLE) | 没有漏开高级定时器MOE；反汇编也含这些真实SPL调用 |
| 初始化／停止 | 先GPIO主动低；初始化MOE关闭、CCR0。停止撤MOE、CCR清零、UG、四脚改GPIO低 | 00滑行／休眠，不是主动刹车；复位最初GPIO高阻窗口仍需板外实测 |
| 人工控制 | PA0输入下拉读KEY（WKUP）；PB2控制用户绿灯。长按达标再松开才运行；再按KEY停止锁定；R1看门狗保留 | 灯常亮也可能是按住后的ARMED，必须已松开才是RUNNING；灯态不能证明引脚实际波形 |
| 编码器 | PC6／PC7、PB6／PB7资源分别留给TIM3／TIM4，当前未初始化或读取 | 编码器没有读数不会阻塞本开环目标；本轮不能声称其AF2／计数已在板上启用 |
| 资源隔离 | TIM1四PWM；TIM5仅启动等待内部时基；TIM3／4保留编码器；USART2 PA2／3、SWD PA13／14均不占用 | 本轮未发现计数器／端口冲突，保留R1及原四目标 |

源码入口：[GPIO／PWM初始化及输出](../control/Drivers_Custom/Motor/motor_bench_pwm.c)、[按键／灯／看门狗及SysTick](../control/Core/Src/motor_bench_main.c)、[人工状态机](../control/App/Diagnostics/motor_bench.c)、[参数](../control/Drivers_Custom/Motor/motor_bench_pwm.h)、[Keil工程](../control/MDK-ARM/yeye_control.uvprojx)。

## 2. 天空星与驱动之间的九根线

下表按驱动照片方向：**驱动开关及顶部Vin在上，元件面朝向观察者**。左下四针控制口自上而下是AIN2、AIN1、BIN2、BIN1；不是AIN1、AIN2、BIN1、BIN2。左上八针信号口自上而下是E2A、E2B、E1A、E1B、ADC、5V、GND、3V3。

P1／P2／H1针号来自官方原理图，只作辅助；不是MCU封装脚号，也不能直接用图纸左右推算翻到背面的列位。天空星按**板背完整丝印E09／E11等**找金属针，不能只沿同一列往下插。

| 线号 | 驱动信号／位置 | 天空星端口／板背丝印 | 原理图引出 | AF／资源 | 当前MotorContinuous用途 | 主控自查 |
| --- | --- | --- | --- | --- | --- | --- |
| C-02 | AIN2，左下第1针 | PE11／E11 | P1.17 | AF1／TIM1_CH2 | A运行时保持低 | 待填 |
| C-01 | AIN1，左下第2针 | PE9／E09 | P1.15 | AF1／TIM1_CH1 | A运行时30%／20kHz | 待填 |
| C-04 | BIN2，左下第3针 | PE14／E14 | P1.22 | AF1／TIM1_CH4 | 当前持续A目标保持低 | 待填 |
| C-03 | BIN1，左下第4针 | PE13／E13 | P1.19 | AF1／TIM1_CH3 | 当前持续A目标保持低 | 待填 |
| C-07 | E2A，左上第1针 | PB6／B06 | P2.23 | 预留AF2／TIM4_CH1 | B编码器A相，当前不读取 | 待填 |
| C-08 | E2B，左上第2针 | PB7／B07 | P2.22 | 预留AF2／TIM4_CH2 | B编码器B相，当前不读取 | 待填 |
| C-05 | E1A，左上第3针 | PC6／C06 | P2.35 | 预留AF2／TIM3_CH1 | A编码器A相，当前不读取 | 待填 |
| C-06 | E1B，左上第4针 | PC7／C07 | P2.36 | 预留AF2／TIM3_CH2 | A编码器B相，当前不读取 | 待填 |
| C-09 | GND，左上第7针 | 天空星GND | 如H1.4／H1.6的GND；沿用既有共地点 | 公共地，无AF | 两板信号参考地 | 待填 |

**这九根线不包含驱动5V或3V3。驱动5V／3V3均不连接天空星的电源输出。ADC本次不接；PA0保留KEY，不作为编码器。**

天空星相邻标签特别检查：

| 正确脚 | 同一行容易混淆的标签 | 检查重点 |
| --- | --- | --- |
| E09 | E08 | E08为TIM1_CH1N，本程序禁用该互补输出 |
| E11 | E10 | E10为TIM1_CH2N，本程序禁用该互补输出 |
| E13 | E12 | E12为TIM1_CH3N，本程序禁用该互补输出 |
| E14 | E15 | E14换到另一列；E15不是TIM1_CH4 |
| C06 | C07 | 同一行两列，按字样分清 |
| B06 | B05 | B06与B07不在同一行，不能把相邻B05当B07 |
| B07 | B08 | 按完整丝印，不按靠近或连续序号猜列 |

归档[主板背面照片](evidence/2026-10-18_i03/photo_03_controller.jpg)可辅助定位，上面的历史插线不代表当前现场接法。若实物朝向与照片不同，继续以端口丝印核对，不套照片左右。

## 3. 电机六芯线到驱动

A／B只表示驱动桥编号，尚未标定左／右轮或前进方向。电机端按PCB丝印M1、M2、G、V、A、B识别；**电机接口与驱动电机口的六个功能顺序不同，不能认为六芯线能插入就等于位置直通正确。**

| 电机端丝印 | A电机接MOTOR-A | B电机接MOTOR-B | 功能／注意 | 主控自查A／B |
| --- | --- | --- | --- | --- |
| M1 | AO1 | BO1 | 电机绕组动力端1；不是AIN1／BIN1控制针 | 待填／待填 |
| M2 | AO2 | BO2 | 电机绕组动力端2；不是GND | 待填／待填 |
| G | GND | GND | 编码器地 | 待填／待填 |
| V | 3V3 | 3V3 | 编码器供电，来自驱动电机口；不是电池正极，也不连天空星3V3 | 待填／待填 |
| B | E1B | E2B | 编码器B相 | 待填／待填 |
| A | E1A | E2A | 编码器A相 | 待填／待填 |

驱动右上MOTOR-A自上而下为AO1、AO2、GND、3V3、E1B、E1A；右下MOTOR-B为BO1、BO2、GND、3V3、E2B、E2A。依[驱动正面照片](evidence/2026-10-18_i03/photo_01_driver.jpg)的开关在上朝向辨认，以对应针的丝印为准。

已归档[电机照片](evidence/2026-10-18_i03/photo_02_motor.jpg)中从上到下是M2、V、A、B、G、M1，该束线对应蓝、红、绿、白、黑、黄。**颜色只对这张已识别照片有效，第二束或换线后不能照颜色认功能。**

## 4. 动力供电、DAPLink与板载资源i
 | 同上，不把AO2当电源负极 |
| DAPLink 5V0 | 天空星5V，H1.7 | 已采用的主板单源供电；不是H1.2的3V3 |
| DAPLink GND | 天空星GND，H1.4或H1.6 | 与第2节驱动公共地相通，沿用原已确认接法 |
| DAPLink DIO | SWDIO／PA13，H1.5 | 不是U1R／U1T |
| DAPLink CLK | SWCLK／PA14，H1.3 | 不是SWO |
| DAPLink RST | NRST，H1.9 | 不接BOOT0或KEY |
| DAPLink 3V3 | 不接 | 不与板上稳压输出并联 |
| 天空星Type-C | 不接 | DAPLink供电时保持空着 |
| 驱动左上5V／3V3及底部稳压排针 | 不连接天空星5V／3V3 | 电机口3V3给编码器是第3节既有支路，不因此取消 |
| 驱动底部蓝色Vout | 本车此阶段不使用 | 不是5V稳压输出，不接天空星 |
| UC2 | 不接电池或系统 | 沿用此前停用决定 |

KEY即PA0／WKUP板载用户按键，用户绿灯为PB2，均无需外接线。PA2／PA3为后续USART2 TX／RX预留，当前未启用；H1的U1R／U1T属于USART1，不是USART2。SWO PB3、USB PA11／12保持未被本目标占用。

## 5. 断电自查顺序与回报

1. 确认全部电源实际拔开，拍照或标记现状。先查C-01到C-04，逐根从驱动丝印追到天空星完整端口名，重点排除E08／E10／E12与E14列位。
2. 查C-09共地，再查C-05到C-08。编码器接对不表示已实现读取，但不应让信号误插到5V／3V3／ADC。
3. 从每只电机的M1／M2及G／V／A／B功能逐根追到驱动电机口，不把电机的A／B编码器线当AIN1／AIN2；A桥两根临时脱开的动力线按原标记核对后才能断电复原。
4. 查DAPLink五线与两路供电边界，不按接头外观、线色或图纸左右猜针脚。自查完成仍保持断电，不顺手接电池试转。
5. 回报本表差异：例如“AIN1实际到E08，表要求E09”或“九线与两束功能逐项一致”；没有完成的项保持待填。没有差异也不能自动将接线标为导通／波形验收通过。

需要看板内版本时另按[MotorContinuous无动力Keil步骤](../control/docs/motor_continuous.md)执行，动力电池始终拔开；工程目标下拉应为MotorContinuous，不因本次复核要求重新下载。版本应为0x020B1001；原MotorBench为0x020B0003。主控后续对版本、fault及ms检查已反馈“完全符合期望”，此项按主控回报确认，不再重复要求核对；它独立于本地构建检查及后续外部PWM验收。

主控随后明确反馈“我也查了一遍接线没有任何问题”，记为本表人工自查一致；没有逐行新增仪表记录，不将“待填”自动全部改成电气验收通过。下一步不再重复整套接线检查，转当前板内版本／fault／滴答核对。工程当前启用了进入调试前更新Flash；只读核对前，主控需在Options for Target → Utilities取消Update Target before Debugging，再按[最新无动力版本核对步骤](../control/docs/motor_continuous.md)操作，避免覆盖原板内程序后才读版本。代理未更改此选项或操作板卡。

## 6. 本轮实际验证与依据

2026-10-24，MotorContinuous完整Rebuild：Keil5／ARMCC5.06u5，0错误0警告，Code5164／RO424／RW64／ZI1288。BIN5652字节、SHA256 `5cd07579b14e1e50e736e2ba0553f21197d6784a305febb6402c9050a55a1eef`，与复核前逐字节一致，版本未变。持续A模型113条／7场景、同宏启动模型154条／10场景、原R3诊断131条／8场景实际通过；SPL／寄存器边界仍为电脑模型，不能证明真实外部输出。

重新构建后的AXF397460字节，SHA256为`f00bcbe54952b157e8a74fe86c91454a29ac6faf5b255cd8f9716402f4a3ef9b`，容器哈希与旧AXF不同；HEX15957字节，SHA256仍为`366e915629db25e50be0f32ccd0f90a611bf5ea3c44859fe54c31de1f30f90d9`。不将AXF哈希变化误报为应用行为变化，也不将BIN相同泛化为所有产物字节相同。

反汇编核对真实AXF内GPIOE基址0x40021000、四次PinSource9／11／13／14和AF1调用，TIM1基址0x40010000、四CCR写入、UG、切AF及MOE启用路径；不是只读假头文件或把board.c当电机驱动。实际.map由当前工程ListingPath放在`control/firmware/build/motor_bench/motor_continuous.map`，AXF／HEX／BIN仍在独立`build/motor_continuous/`，以目标名和文件名区分。

本地忽略证据：`control/firmware/build/MotorContinuous_port_audit_rebuild.log`、`control/build/motor_port_audit_disassembly.txt`、`control/build/motor_port_audit_before.json`及`motor_port_audit_checks.json`，测试日志仍在`control/build/`。没有改固件、切分支、烧录、连接设备、接电池或上传。根因未确定，不宣称已解决。

资料依据：

- [ST DS8626表9](https://www.st.com/resource/en/datasheet/stm32f405rg.pdf)，本地已归档Rev12第65／66／68页图，确认PB6／7、PC6／7、PE9／11／13／14 AF及通道；[原理图证据索引](../control/docs/evidence/2026-10-18_c02a/README.md)保存官方天空星P1／P2、H1、KEY／LED图及来源哈希。
- [天空星P1／P2原图副本](../control/docs/evidence/2026-10-18_c02a/schematic_20240815_203023.png)、[H1原图副本](../control/docs/evidence/2026-10-18_c02a/schematic_20240815_044555.png)；资料针号与照片丝印已复核，不代替现场导通。
- [亚博官方STM32接线图副本](evidence/2026-10-18_i03/vendor_driver_stm32.pdf)、[AT8236厂家内容副本](evidence/2026-10-18_i03/at8236_datasheet.pdf)第5页真值表及[来源索引](evidence/2026-10-18_i03/README.md)；只沿用模块功能，不照搬F103端口。
- 主控本轮已报：AIN1约1V、AIN2为0V、运行AO1−AO2约0.07V、待机／运行Vin均7.54V；200Ω档表笔0.4Ω、电机回路23Ω。原始数值及局限见[持续测试现场记录](../control/docs/motor_continuous.md)，不能据平均值排除固件或判定驱动坏。
