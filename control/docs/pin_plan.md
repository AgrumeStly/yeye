# C-02A 主控电机与编码器引脚资源方案

> 2026-10-29轮位／命名更新：MCU端口和本页AF表未改，但物理轮已互换，主控新A=左、新B=右。物理新A/B不能与驱动AIN/BIN、MOTOR-A/B或软件a/b混同；当前轮组／通道／方向及旧CPR参考沿用统一见[wheel_mapping.md](../../hardware_preparation/wheel_mapping.md)。以下10月25日及更早的左右或未标定措辞保留其历史阶段含义。


2026-10-25实施补充：C-02C已按原PC6/7 TIM3 AF2、PB6/7 TIM4 AF2增加[独立EncoderBench采集](encoder_bench.md)，不改八线映射。TIM3／TIM4各自独占16位CNT，采样用SysTick，TIM5仍只负责启动等待；本入口四电机脚为GPIO低、不启用TIM1，原MotorPwm资源及验收保持。下文“编码器未实现”等为C-02A历史设计时结论，当前软件与待实物标定范围以C-02C为准。

状态：v0.2，资源设计完成，00于2026-10-20采用并同步接线表；实物接线未冻结。设计日期：2026-10-18（北京时间）。维护：主控／01；状态回填：00；接线归档：主控／02；现场位置与导通复核：硬件。

适用器件沿用主控2026-10-18确认的采购型号：天空星STM32F407VET6青春版、AT8236 Standard／YB-MNT03-V1.0、MD310Z20_7.4V。型号确认不重复询问；本方案不表示接线、电压或运行已通过验收。

任务依据：[I-03接线草案v0.2](../../hardware_preparation/wiring.md)、[I-03交接](../../hardware_preparation/i03_handoff.md)、现有[board.h](../Drivers_Custom/Board/board.h)／[board.c](../Drivers_Custom/Board/board.c)，以及第6节资料。本次只更新文档，没有改动固件、烧录、上电或电机测试。

## 1. 资源决定与旧候选修正

- 四路桥输入采用 **TIM1_CH1–CH4，PE9／PE11／PE13／PE14，AF1**。四路独立比较值，共用TIM1计数器、预分频和周期；可分别调占空比，不能各设一个PWM频率。
- A桥编码器采用 **TIM3_CH1／CH2，PC6／PC7，AF2**；B桥编码器采用 **TIM4_CH1／CH2，PB6／PB7，AF2**。两只编码器各占一个独立16位计数器，不把TIM3／TIM4剩余通道再分给独立时基PWM。
- **取消旧版PA0／PA1、TIM2编码器候选**：PA0是板载用户／唤醒按键WKUP网络，保留按键，避免按键电路影响编码器。PA1、TIM2本次不使用；也不改用会占SWO的PA15／PB3组合。
- 保留USART2 PA2／PA3、SWD PA13／PA14、SWO PB3、USART1 PA9／PA10、PB2用户灯／BOOT1、PA0按键、BOOT0／NRST、晶振、USB及TF／SPI FLASH板载网络。
- MA／MB指驱动A／B桥，**尚不指定左／右轮**。先固定桥与编码器的配对，安装轮侧、前进与计数符号由02／硬件记录，再由01标定。

以上是01选定的资源方案，02可据此补接线草案。硬件现场复核与签核完成后，才能将“原理图引出”改为“实物已核对”。

## 2. 交给02的八线映射

P1／P2针号取自官方“双路80PIN排针”图：两组各40针、共80针。`P1.15`表示原理图连接器P1第15脚，**不是MCU封装脚号**。板背丝印E09、C06、B06等分别表示PE9、PC6、PB6。AF使用F407复用选择，不沿用F103重映射配置。

| wiring线号 | AT8236侧信号／位置 | 方向（主控侧） | MCU端口 | AF | 定时器通道 | 官方排针针号 | 板背标识／同一行相邻标签 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C-01 | AIN1，控制排针自上第2 | 输出 | PE9 | AF1 | TIM1_CH1 | P1.15 | E09，与E08同一行 |
| C-02 | AIN2，控制排针自上第1 | 输出 | PE11 | AF1 | TIM1_CH2 | P1.17 | E11，与E10同一行 |
| C-03 | BIN1，控制排针自上第4 | 输出 | PE13 | AF1 | TIM1_CH3 | P1.19 | E13，与E12同一行 |
| C-04 | BIN2，控制排针自上第3 | 输出 | PE14 | AF1 | TIM1_CH4 | P1.22 | E14，与E15同一行；注意换列 |
| C-05 | E1A，信号排针自上第3 | 输入 | PC6 | AF2 | TIM3_CH1／TI1 | P2.35 | C06，与C07同一行 |
| C-06 | E1B，信号排针自上第4 | 输入 | PC7 | AF2 | TIM3_CH2／TI2 | P2.36 | C07，与C06同一行 |
| C-07 | E2A，信号排针自上第1 | 输入 | PB6 | AF2 | TIM4_CH1／TI1 | P2.23 | B06，与B05同一行 |
| C-08 | E2B，信号排针自上第2 | 输入 | PB7 | AF2 | TIM4_CH2／TI2 | P2.22 | B07，与B08同一行；不与B06同一行 |

AT8236位置方向沿用I-03照片P1：开关在上方，控制排针在左下，编码器信号排针在左上；该方向不是厂家连接器Pin1定义。电机口E1A／E1B、E2A／E2B经驱动转接后进入上表，板内及六芯线实际导通仍由硬件核对。

八线按3.3V逻辑域设计，并按wiring的C-09共地。亚博MD310Z20官方资料给出编码器3.3–5V供电、AB霍尔增量输出及上拉整形，本方案选3.3V供电域；不能将允许5V供电理解为已测3.3V脉冲，也不能把驱动3V3与主控3V3稳压输出并联。实际电压、输出类型细节与供电路径归H-02后续核对。

## 3. 保留接口及冲突检查

| 检查项 | 资源／官方原理图引出 | 本方案结果与限制 |
| --- | --- | --- |
| PWM与编码器 | TIM1：四PWM；TIM3：E1；TIM4：E2 | 三个CNT独立，无时基冲突。TIM3／TIM4整体给编码器，CH3／CH4也不另作周期PWM；采样周期另用调度时基 |
| C-02B-R1启动等待 | TIM5内部计数器，APB1名义16MHz、PSC=15，1MHz／1us每计数 | 不配置GPIO／AF、无中断／DMA；只用于LSI与IWDG初始化限时等待，退出初始化即停计数。与TIM1／3／4及SysTick独立；后续使用TIM5须重新检查初始化阶段占用。依据S2第18章及[启动修复记录](motor_bench_startup_issue.md) |
| 视觉USART2 | PA2／TX／AF7：P1.1（A02）；PA3／RX／AF7：P1.6（A03） | 不变；这两脚不启用TIM2_CH3／CH4。BOARD_UART_ENABLE仍为0；驱动ADC本次不接，禁止套用F103教程ADC→PA2 |
| SWD与复位 | PA13／AF0／SWDIO：H1.5；PA14／AF0／SWCLK：H1.3；NRST：H1.9 | 保留；H1.4、H1.6为GND。实际插合方向与下载器另一端待现场核对 |
| SWO与USART1 | PB3／AF0／SWO：H1.1；PA10／USART1_RX：H1.8；PA9／USART1_TX：H1.10 | 均保留；照片U1R／U1T不是USART2或SWD |
| 调试口电源 | H1.2：3V3；H1.7：PIN_IN_+5V | 只记录引出，不授权供电；下载器侧VTref／电源输出性质须按具体说明核对 |
| 用户灯与启动 | PB2／BOOT1、PA0／WKUP、BOOT0、NRST | 均保留；不用拆改按键／启动电路释放PA0 |
| USB与晶振 | USB FS PA11／PA12；HSE PH0／PH1；LSE PC14／PC15 | 不占用；保留USB引脚不表示当前HSI工程实现了USB应用 |
| TF卡 | PC8–PC12、PD2（SDIO），PD3（检测） | 不占用。PC6／PC7可复用SDIO_D6／D7，但板载TF是4位接口，不连接这两根8位扩展线；TIM3不把PC8／PC9初始化成AF2 |
| SPI FLASH | SPI1 PA4–PA7，青春版FLASH默认未贴 | 不占用，不依赖拆0Ω排阻；因此不选PA6／PA7／PB0／PB1的TIM3四PWM示例 |
| 其它互斥AF | PE9／11／13／14的FSMC；PC6／7的TIM8、USART6、DCMI等；PB6／7的I2C1、USART1备选等 | 当前工程未启用，无现有功能冲突；后续不能在同脚同时启用这些AF。PB6／PB7不再接I2C外设；F407不承担视觉采集 |
| 现有代码 | board.c的HSI、SysTick、可选PA2／PA3 UART；BoardSelfTest的PB2；C-02B独立MotorBench | 原三个目标不接新驱动。MotorBench单独配置TIM1四控制脚、PA0按键及PB2灯，TIM／IWDG模块仅加入该目标；四编码器端口仍未初始化或读取 |

核对对象是天空星青春版**核心板**，没有套用“筑基学习板”底板上的屏幕、以太网、电机与传感器占用。板背照片只辅助定位，不替代官方AF与原理图。

## 4. 四PWM可行性与后续实现边界

使用TIM1普通CH1–CH4，不用CH1N／CH2N／CH3N互补输出。A桥CH1／CH2、B桥CH3／CH4，每桥可选择`PWM/0`或`0/PWM`调制两个方向。四PWM方案不需借用编码器定时器，也避免2PWM＋2GPIO方案的反相占空比语义。AT8236的`00`为滑行／休眠，`11`为刹车；厂家正／反向不等于已标定的车辆前进方向。

现board.c使用HSI 16MHz，RCC_DeInit后AHB／APB1／APB2分频均为1，因此TIM1（APB2）及TIM3／TIM4（APB1）的内部定时器时钟均为16MHz名义值；编码器CNT按外部相位边沿变化，并非每个内部时钟都加1。更改PLL／APB分频时须按RM0090重新计算，不按168MHz直接套参数。

本次只确定管脚与计数资源，**不冻结PWM频率／限幅、编码器采样周期、停车模式／时长、台架超时**。I-03交接中的这些实现项进入后续C-02；前置约束如下：

2026-10-20 C-02B已实现独立台架首轮参数：20kHz、15%、500ms，00滑行，WKUP人工触发及停止，IWDG监督；见[操作说明](motor_bench.md)。只用于本轮台架，未通过实测，不将其视为整车冻结参数；下方约束仍适用于后续整车实现。

2026-10-21 C-02B-R2：主控回报原15%触发A后未转、绿灯正常；当前固定改为30%（PSC=0、ARR=799、有效CCR=240），20kHz、500ms和原人工序列／停止保护保留。源码复核PE9／11／13／14的TIM1 AF1、CCxE、MOE及CCR一致，未发现确切映射错误；未测真实波形，不改变接线、轮侧或方向。TIM3／4编码器、TIM5启动时基、USART2／SWD资源不变。首轮只试A一次，失败即断动力，不继续加功率；见[R2记录](motor_bench_r2_task.md)与[当前操作说明第12节](motor_bench.md)。

2026-10-24按主控要求重新核对MotorContinuous：实际编入独立motor_bench_main／pwm／状态机及原厂SPL，不编入board.c；源码、真实AXF反汇编与ST表9均为PE9／11／13／14的TIM1_CH1–4 AF1，A运行CCR为240／0／0／0，UG后切AF并开启MOE。未发现明确端口／使能遗漏，但仍不能排除固件其他问题或证明外部PWM。完整Rebuild及电脑回归通过、BIN与原0x020B1001版本一致；[断电接线自查表](../../hardware_preparation/motor_wiring_self_check.md)列出全部信号／供电与相邻CHxN易混脚。编码器仍只是资源预留、未启用读取；原MotorBench时限与资源不变。

同日主控要求在无法去实验室时先不用PWM：新增独立[MotorDirect](motor_direct.md)，同一PE9／11／13／14在本目标改为普通GPIO输出，不选AF、不启动TIM1；人工A阶段仅PE9高，500ms结束四脚低并锁定，B始终低。该目标不改变物理接线或旧目标AF1资源；TIM5仍只用于R1启动等待，TIM3／4和USART2／SWD保留。固定10是比原30%更强的满导通诊断，代码／电脑验证通过但现场起转未测，不用“不转”单独判电机坏。

1. 定义PWM频率、PSC／ARR、有效极性和CCR范围；TIM1需处理MOE、空闲态与更新顺序。初始化先建立四输入低电平，再允许输出；预装载更新与换向应避免非预期输入组合。
2. 复位时所选PE端口不是主动低输出，芯片级下拉不能替代板级默认态验证。STOP／FAULT须明确实现00滑行或11刹车；左右请求归零不等于轮子停稳。换向先撤去驱动，等待按实测确定的条件后再换向。
3. TIM3／TIM4编码器读取需处理16位回绕、有符号增量、滤波与采样间隔；厂家13线、1:20不能直接当作已测车轮每圈计数，须结合解码倍频与实际输出轴转圈校准。
4. 先登记MA／MB↔轮侧，后续手转轮校准A/B及符号，再在获授权悬空台架中单轮低输出短时验证前进。台架要有主动退出和自动停止条件；本次不执行。

## 5. 02／硬件现场需核对的具体位置

| 位置 | 资料已确定 | 现场仍需证据 |
| --- | --- | --- |
| P1电机控制 | P1.15／17／19／22为E09／E11／E13／E14 | 确认丝印对应的实际金属针与列位；尤其E14换列，不能沿E09一列顺接。拍清插接面／定位基准，断电核对线两端 |
| P2编码器 | P2.35／36为C06／C07；P2.23／22为B06／B07 | C06／C07靠近排针末端；B06／B07在相邻两行不同列。分别确认实际针位、无其它已插外设占用；不猜内／外列 |
| USART2与H1 | PA2／PA3及SWDIO／SWCLK官方针号已明确 | P1顶部A02／REF相邻点、A03实际列位；H1正反插方向，实际SWD线与下载器另一端功能、电源端性质 |
| AT8236两组排针与六芯线 | AIN2／AIN1／BIN2／BIN1排列；E2A／E2B／E1A／E1B为信号排针前四位 | C-01–C-08逐根导通、无错位／对电源短路；MA／MB轮侧、插合朝向及六芯线／板内转接继续按I-03核对 |
| 逻辑供电与回路 | 设计采用3.3V编码器域及公共地 | 断电核对供电路径与不并联稳压输出；实际电压／脉冲幅度留给另行授权的测量任务 |

官方P1／P2／H1编号不是实物验收结论。P3是板背照片，不能将原理图“左边／右边”直接当照片左右，或将照片位置号当厂家Pin1。若某个端点不符，只补核该处及PCB差异，不重新识别已确认的整套型号。

00于2026-10-20已将wiring.md的C-01–C-08同步为第2节映射（wiring v0.3），明确C-05／C-06替代PA0／PA1，并建立[首次接线指南](../../hardware_preparation/dual_motor_wiring_guide.md)。旧版接线草案及历史步骤中的PA0／PA1接法失效；本次回填不代签实物验收。接线冻结仍依赖实际装配与核对。

## 6. 资料依据与检查范围

| 编号 | 来源 | 本次核对范围 |
| --- | --- | --- |
| S1 | [ST DS8626 Rev 12](https://www.st.com/resource/en/datasheet/stm32f405rg.pdf) | LQFP100封装、Table 7／9；第64页PA2／PA3与SWD、第65页PB6／PB7、第66页PC6／PC7、第68页PE9／11／13／14。提取并查看相关AF表页图 |
| S2 | [ST RM0090 Rev 22](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405415-stm32f407417-stm32f427437-and-stm32f429439-advanced-armbased-32bit-mcus-stmicroelectronics.pdf) | F405／407 RCC第7章217–218页时钟树与APB规则；TIM1第17章；TIM2–5第18章及18.3.12编码器接口。计数资源分别保留 |
| S3 | [立创天空星官方原理图](https://wiki.lckfb.com/zh-hans/tkx/hardware/schematic.html) | 双路排针、调试口、按键／LED、TF与FLASH原图；[原图副本及SHA256索引](evidence/2026-10-18_c02a/README.md)。针号取自原图，不由照片猜测 |
| S4 | [立创用户按键教程](https://wiki.lckfb.com/zh-hans/tkx/tkx-stm32f407vxt6/beginner/key-principle.html) | PA0／WKUP板载按键，取消旧编码器候选的依据 |
| S5 | [亚博MD310Z20官方电机资料](https://www.yahboom.net/public/upload/upload-html/1744700910/Motor%20introduction%20and%20usage.html) | AB霍尔编码器、3.3–5V供电、上拉整形；标称参数不作实测结论 |
| S6 | [亚博双路驱动官方STM32教程](https://raw.githubusercontent.com/YahboomTechnology/2-Channel-Motor-Driver-Module/main/2.For%20STM32/stm32f103c8t6.pdf)；[I-03厂家资料索引](../../hardware_preparation/evidence/2026-10-18_i03/README.md) | 查看第1页接线图，沿用AIN／BIN及E1／E2信号名，不照搬F103针脚。AT8236真值表核对I-03所存原厂内容第5页，其第三方托管性质保持注明 |

2026-10-18资料检查：八个端口无重复，AF／通道与官方表一致，三个CNT无共享冲突，P1／P2针号与官方图一致，保留接口与应用源码已核对。文档链接、差异与固件未改动检查随任务回报；没有功能代码变化，不编译或重跑55项电脑测试。实物导通、波形、计数、板级与实车运行全部待后续任务。
