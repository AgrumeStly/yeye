# C-02B-R3：保留瞬时输出证据，先做无动力诊断

日期：2026-10-21。状态：01实现、编译及电脑验证完成，R3实板快照待主控；未自动操作板卡。01实现与电脑验证，主控按纯Keil图形步骤采集实物数据，00判断下一步，02／硬件继续I-05实际供电测量。

## 当前目标与事实

主控要求“现在不管电池，让马达转起来”，指先不继续充电器选型，恢复电机调试；不代表可以绕过停止保护或忽略驱动的必要供电。UC2仍停用。主控已确认既定型号、接线、电池冷却和外观条件；无需重问型号或全套接线照片。

本轮R2下载Verify OK、主板绿灯正常，按30%／500ms首次A指导后“完全没动，也没声音”。主控刚补充上次AT8236驱动板自身电源指示灯亮；灯亮不代替Vin电压或带载能力测量。现场没有万用表。板内Watch版本、本次输出寄存器与实际PWM均未取得。

00只读核对现有PWM实现及SysTick调用，未发现可确证的软件配置错误，不能据代码正确宣称管脚／电机正常。AT8236手册第5页允许PWM／0快衰减控制，当前20kHz在芯片资料频率范围内，30%高电平名义15us；第6页有休眠／唤醒条件，不能未经证据把休眠当根因。禁止再把“加占空比”作为默认排错。

依据：[R2交付](motor_bench_r2_task.md)、[无转动记录](../../testing/2026-10-21_motor_bench/no_rotation_record.md)、[接线与厂家资料索引](../../hardware_preparation/wiring.md)、[I-05](../../hardware_preparation/i05_motor_power_diagnosis_task.md)。芯片原厂内容快照见[AT8236手册](../../hardware_preparation/evidence/2026-10-18_i03/at8236_datasheet.pdf)。

## 01授权范围

先读AGENTS、默认技能、协作标准、状态及当前main／PWM／状态机。仅在MotorBench应用中增加小范围只读诊断数据及必要版本／文档、适用验证，不更改当前四路分配、20kHz／30%／500ms、按键人工A→B→AB、停止逻辑、看门狗或R1限时等待。版本使用0x020B0003等明确新值。

目标：0.5秒运行太短，试转后寄存器已归零，无法靠事后Watch确认运行窗口。增加保留到复位的诊断快照，让主控不接动力电池也能判断程序是否真正走过PWM启动路径。

1. 记录版本、启动请求次数／实际输出启用次数、最后mask、开始及结束ms、结束原因，并给出字段含义与期望。不能把每1ms相同mask的重复调用当成多次启用；禁止为观察延长输出。
2. 在真实PWM启用完成后，读取实际TIM1的CR1、PSC、ARR、CCER、BDTR、CCR1–4，及GPIOE的MODER、AFRH等关键端口寄存器，保存为最后一次活动快照。不要将宏计算值或期望常量伪装成寄存器读数，不在后续停止时覆盖活动快照。
3. 分别保留停止后快照／标记，证明程序执行了关闭MOE、清CCR和GPIO低的停止路径。未发生输出启用时valid标记保持无效，不用全0冒充成功快照。采集位置及先后顺序须准确，避免只记录关闭MOE之前的中间状态。
4. 若能够无阻塞地从GPIO输入读数获得有限的管脚数字证据，可提出额外采集；没有可靠采样依据则不增加长轮询、不写成测得20kHz／真实电压。寄存器快照本身仍不证明外接控制线或驱动输出正常。
5. 诊断数据只保存／读取，不允许Watch强改输出、状态或fault；不添加串口输出，不改官方库，代码补充面向初学者的中文注释。不要在SysTick内打印、延时或循环等待调试器。
6. 如实际复核发现另一个确切缺陷，先给证据及与本症状的关联，再做必要修复；不得顺手重写整个驱动。任何需要更改功率、时长、控制方式或引脚的方案另返回00说明。

## 检查与交付

编译MotorBench、运行受影响的已有检查，新增验证仅针对诊断采集的有效性、保留语义和停止路径等有意义行为，不为字段赋值编写镜像测试。电脑模型不能复现电机实物不转，不把模型通过记为问题解决。给出新AXF／HEX／BIN及哈希，保留R2历史。

纯Keil操作：驱动OFF、动力电池XT30拔开、UC2断开；只用DAPLink供主板，下载新MotorBench到Verify OK。保持动力断开，主控进入Keil、F5运行、按原KEY动作触发一次A，等500ms结束后，使用Periodic Window Update读取保留快照，无需在输出窗口暂停或打断点。明确Watch字段与可复制列表，最终给一张少量字段的判定表。无可靠运行中读数时不得偷偷改用接电池调试。结束退出调试。

此轮主控不连接动力电池、不进行真实起转复测。回报无动力快照后，00区分请求未发出、输出未启用／配置错误、寄存器看似正常三类边界，再决定01修复或02／硬件测实际输入／输出。I-05借仪表仍可继续；没有外部波形／电压时不得保证已经定位。

仅本地实现、文档和电脑检查；不自动连接板卡、烧录、接电池、驱动电机、发跨聊天消息、提交／上传或切分支。回报修改文件、版本、字段与期望、测试／构建、产物哈希、纯Keil步骤以及仍待现场的证据。

## 01执行记录与交付

2026-10-21，版本`g_motor_bench_revision=0x020B0003`。R1启动顺序、TIM5有界等待、IWDG和粘性故障保留；R2四路引脚、30%（300‰／CCR240）、名义20kHz（PSC0／ARR799）、500ms及人工A→B→AB／停止锁定不变。没有为观察延长窗口、改变驱动模式、增功率或加串口。

### 采集位置与保留语义

- PWM适配层新增`volatile g_motor_bench_pwm_diag`，244字节RAM。请求与实际启用各独立计数：request_count只计新的非零mask请求（非法非零请求也计），相同mask的1ms重复调用不累加；enable_calls在真正执行MOE启用调用返回后增加；enable_count只在随后实际BDTR读回MOE=1时增加，不能把它称为电机已转次数。
- 活动帧active在原先写CCR／UG、切GPIO AF、调用TIM_CtrlPWMOutputs(ENABLE)后采集；停止帧stopped在原先关闭MOE、清四CCR／UG、ODR清零和GPIO输出配置完成后采集。正常仅每轮启用／结束各读一次，不循环采样；活动帧不被重复idle／故障stop覆盖。初始化从未启用时两帧valid=0；valid最后写1只代表完整读回，即使MOE或CCR不符合期望也原样保存。
- 每份读取20个真实MMIO寄存器：TIM1 CR1／PSC／ARR／CNT／CCER／BDTR／CCMR1／CCMR2／CCR1–4、GPIOE MODER／AFRH／OTYPER／PUPDR／ODR／IDR、RCC AHB1ENR／APB2ENR。寄存器字段全部直接读外设，不写入期望常量。软件metadata包括采集ms、mask、state、fault与run_id，与寄存器字段分别注明；逐项读取不是同一硬件时刻的原子快照。
- start_ms／stop_ms为上下文实际毫秒值；elapsed_ms按无符号时间差计算并支持回绕，不把500常量填写进诊断。stop_count只计启用后完成的停止事件，stop_reason区分正常超时、KEY、fault、逻辑中止、mask切换、直接停止、CPU异常、非法mask；具体值见[操作说明第13节](motor_bench.md)。CPU异常仍先禁中断，有限次诊断上下文赋值后立即停止，硬件安全写入早于寄存器采集；未新增等待或打印。
- 每次启用都有run_id，新启用将stopped.valid清0，结束时配对同一次run_id；后一轮替换最后一组，复位／断电清零，不保证跨IWDG复位保留。新增上下文函数只写诊断RAM，不反向控制状态机。主控不得通过Watch写值强行通过。
- IDR只读一个瞬时数字值；未追加长轮询或固定1ms计数法，以免与20kHz同相混叠而误判。ODR在AF输出时可为0，单个IDR／ODR值不证明实际频率、电压、线束或驱动正常。

### 实际验证结果

| 检查 | 本轮实际结果与范围 |
| --- | --- |
| 新诊断集成回归 | 131条检查／8场景通过，直接运行真实main／SysTick／PWM与纯状态机，只有SPL／寄存器边界为电脑模型 |
| 覆盖的语义 | 完整KEY→A→500ms超时、活动数据在硬件读值变化与停机后保留、相同mask去重、KEY即停、粘性fault重复stop不覆盖、非法mask、后一次启用配对、ms回绕、从未启用时valid0 |
| 非期望读回 | 模型在MOE调用返回前扰动PSC／ARR／CCR／CCER／AFRH／IDR并使MOE不置位，诊断原样报告异常、enable_calls=1但enable_count=0；另模拟停止时MOE不清，stopped.valid=1仍如实报告MOE异常。证明测试能捕获“用期望值冒充”及“stop标记冒充停止成功”，不是宏值镜像测试 |
| 既有回归 | 启动154条／10场景、台架73项、协议55项全部通过；启动测试只增加诊断上下文边界替身及R3版本期望 |
| MotorBench编译 | Keil5.24a／ARMCC5.06u5，0错误0警告；Code5208、RO424、RW64、ZI1288字节。原三目标配置未变，本轮未重编译无关目标／UART分支，不重记为新验证 |
| 源码与ARM证据 | R1 SystemInit／时钟更新及startup_timer_init至watchdog_init段与开工副本逐字一致；原motor_bench.c／.h和Keil工程未变。新AXF反汇编capture含TIM1基址0x40010000、GPIOE基址0x40021000及RCC时钟寄存器的真实加载，valid置1位于读完之后；链接映射保留244字节诊断符号 |

实际输出：

```text
PASS PWM retained diagnostics: 131 checks in 8 real-main/PWM model scenarios (no board access)
PASS MotorBench startup: 154 checks in 10 hardware-model scenarios (real main/SysTick; no board access)
PASS motor bench: 73 checks (manual sequence, debounce, stop, timeout, wrap, lockout)
PASS all 55 checks
```

模型没有STM32真实引脚、时钟同步、负载、电压或驱动器，不能复现并判定“实物不转”根因，也没有测量新增采集的板上执行耗时。采集只有固定20次寄存器读和有限次RAM操作，没有循环等待；500ms与停止触发逻辑的电脑验证保留，板上时序／波形仍待现场。

### 新产物与本地版本

目录`D:/Projects/yeye/control/firmware/build/motor_bench/`，Keil Download使用AXF；本轮构建如下，后续重建按实际文件核验：

| 文件 | 字节 | SHA256 |
| --- | --- | --- |
| motor_bench.axf | 397136 | `1034006289d9df1aa06b8f2d5a3a2bdb0fe387156d5aa8095cbb0dbea3334a9c` |
| motor_bench.hex | 16071 | `db15063d73f30c7852faac11980a9a20eefd6ce62e83acf9fdd1026a06eb7240` |
| motor_bench.bin | 5696 | `d09c4095c55eb34607d012c36611b239b6d24c00d2451497f925e812e994e0d8` |

2026-10-24重建说明：上表保留R3交付当时产物。新增独立MotorDirect及共享代码注释后的回归构建，当前目录AXF为397144字节、SHA256 `be30e42e98e6dd4a6003915c7db6df3716601f4ecdc40f81cf6c8327b357dfc6`；BIN／HEX与上表逐字节相同，R3版本／行为不变。重建前产物留存`control/build/motor_direct_baseline/`。AXF调试容器变化不等于电机执行代码变化，不据此要求重新下载旧目标。

版本位置仍`D:/Projects/yeye`、main、HEAD `82640aba4cf7aa4f30db14b486aef852936118fe`加本地未提交修改，已有成果保留。R2历史产物与开工源码副本在被忽略的`control/build/c02b_r3_baseline/`；R2交付文档与原失败记录未改。新日志为`control/build/motor_bench_pwm_diag_tests.log`及原154／73／55日志、`control/firmware/build/MotorBench_build.log`，反汇编为`control/build/c02b_r3_disassembly.txt`，均为本地忽略输出。

### 修改文件与主控下一步

本轮14份文件：应用`control/Drivers_Custom/Motor/motor_bench_pwm.h`、`control/Drivers_Custom/Motor/motor_bench_pwm.c`、`motor_bench_main.c`；已有验证`control/Tests/Host/test_motor_bench_startup.c`及`control/Tests/Host/fakes/motor_bench_startup/stm32f4xx.h`；新增`control/Tests/Host/test_motor_bench_pwm_diag.c`、`control/Tests/Host/fakes/motor_bench_pwm/stm32f4xx.h`、`control/tools/run_motor_bench_pwm_diag_tests.ps1`；文档本文件、`control/docs/motor_bench.md`、`validation.md`、`keil_quickstart.md`、`control/README.md`、`project_planning/project_status.md`。未修改官方库、Keil目标或原按键状态机。

主控按[当前纯Keil操作、Watch列表及判定表（第13节）](motor_bench.md)：动力电池拔开、驱动OFF、UC2断开→MotorBench重建／Download至新Verify OK→进入硬件调试并F5持续Run、Periodic Window Update→确认版本0x020B0003／ms增长／fault0／READY→只KEY长按松开一次A→500ms后保留截图，再退出调试。不要在输出窗口暂停，不改Watch值，不连接动力电池，也不继续B／AB。

一次正常A应请求／启用调用／MOE读回／停止各1次，两帧valid1且run_id1；活动MOE1、CCR(240,0,0,0)、四脚AF1，停止MOE0、CCR全0及GPIO低，elapsed500、reason1。细节及按位比较以第13节为准。实板字段若异常原样回报；若寄存器符合，也只能证明板内路径，外部供电／PWM／驱动输出仍须I-05仪表证据。当前未取得R3现场快照，未烧录、访问板卡、接电池、试转、切分支、提交或上传，不宣称电机问题解决。

最终本地核对：相对R3开工副本11份修改、3份新增，14份编写文件无行尾空白；6份更新文档的103个本地链接存在，git diff --check通过。16份官方来源哈希匹配，四个Keil目标保留且测试替身未入工程，R2历史及其余开工文件保持原字节；新AXF／HEX／BIN与交付表哈希一致，BIN向量SP=0x20000548、Reset=0x0800019D布局通过。摘要在被忽略的`control/build/c02b_r3_checks.json`。末次补充中文函数注释后已重新编译，BIN／HEX不变、AXF调试哈希按表更新；电脑测试对应的可执行逻辑未再改动。
