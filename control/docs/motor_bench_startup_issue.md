# C-02B-R1：MotorBench看门狗初始化阻塞

状态：R1应用层修复与电脑验证完成；板级复验待主控，尚未认定实物症状已排除。日期：2026-10-20（北京时间）。00记录与分配，01负责固件修复；主控现场复验，电池XT30保持拔开。

## 现场证据

- 主控提供[Keil下载输出](../../testing/2026-10-20_motor_bench/keil_download_report.txt)：MotorBench编译0错误0警告，Programming Done、Verify OK、Application running；下载结束20:36:59。
- 主控持续观察：主板红灯常亮、绿灯不闪，g_motor_bench_ms恒为0。
- [主控停机截图](../../testing/2026-10-20_motor_bench/watchdog_wait_halt.png)已按原始字节复制，SHA256为e7b98d1a3238ef4681131928febc5a637dae83219d045e7ac9cbb68f2e203e2c。
- 截图PC=0x08000332，位于IWDG_GetFlagStatus()，源码显示IWDG_SR标志读取；R1=1，对应PVU检查，R2=1。LR=0x080011E7；故障原版链接映射watchdog_init位于0x080011B6起、长72字节，与返回地址相符；不再用这些旧地址定位R1新产物。
- Watch显示g_motor_bench_ms=0、g_motor_bench_fault=0、state=0、raw_candidate=0、SystemCoreClock=0x00F42400（16000000）。界面显示暂停时累计约207.68秒。

截图与调用顺序表明本次停机位置在watchdog_init()的PVU/RVU等待路径，尚未到其后的SysTick_Config；不能把state=0或raw=0解释为程序已完成运行。本次已足以进入固件修复，不能继续重复下载原版或要求重新识别硬件。

## 源码问题与官方依据

修复前[motor_bench_main.c](../Core/Src/motor_bench_main.c)的watchdog_init依次执行：开启LSI并等待就绪→配置PR/RLR→无限等待PVU/RVU清除→Reload→Enable。IWDG尚未Enable时就先等待更新，且等待没有退出条件；主控截图正命中此路径，导致后续SysTick及用户灯逻辑无法启动。此段保留故障原版事实，新实现见下方执行记录。

ST官方F4 HAL参考[stm32f4xx_hal_iwdg.c](https://raw.githubusercontent.com/STMicroelectronics/stm32f4xx-hal-driver/master/Src/stm32f4xx_hal_iwdg.c)的HAL_IWDG_Init（2026-10-20读取）采用：先Start→允许写入→配置PR/RLR→有超时的状态等待→Reload。参照的是硬件顺序，不要求本项目改用HAL；本项目继续SPL。官方实现与现场共同指向本次启动顺序缺陷，修正是否排除板级症状仍须主控复验。

## 转交01的执行要求

任务ID：C-02B-R1。目录：D:/Projects/yeye。主控转交后执行；生成本文不表示已自动消息或开工。

先读AGENTS、默认grill-me、协作标准、project_status、本文件及motor_bench.md，再检查当前源码、原厂IWDG资料及实际工作区。保存已有未提交成果，不切分支或覆盖其它任务。

1. 修复应用层watchdog_init的启动／配置／状态等待顺序。保留SPL及原厂库，不通过修改IWDG_GetFlagStatus、伪造返回值、无条件跳过等待或删除看门狗掩盖问题。
2. LSI就绪及PVU/RVU等待必须有边界和明确失败处理。此时SysTick尚未启用，超时不得依赖恒为0的g_motor_bench_ms；处理启动期间已启用IWDG的复位时间约束、故障标志及退出路径，不能形成永久静默等待。
3. 保持电机四控制脚在初始化／错误路径为零驱动；保留15%／500ms、人工A/B/AB、自动停止及锁定语义。更新涉及代码的详细中文注释。
4. 验证本次初始化故障路径：有可测试的真实边界时补故障验证，覆盖状态位不清的退出／安全输出；电脑无法模拟的硬件语义明确写出。不能以既有73项纯状态机通过替代本次IWDG启动验证。
5. 编译受影响及需回归的目标，运行适用的现有检查，保存新构建产物、哈希和结果。核对原目标不受影响；不重复宣称旧BIN哈希为新版。
6. 给主控纯Keil5步骤：电池拔开、DAPLink五线供电／SWD，选择MotorBench、编译、Download至Verify OK、退出调试并断电重启验证待机。随后在无动力条件下观察g_motor_bench_ms持续增长、fault=0、释放WKUP后READY及用户灯每组闪1次。调试暂停可能影响看门狗，记录自主上电结果与调试结果的区别。

允许修改：相关应用代码、必要的正确层级验证、MotorBench说明与状态条目。默认本地保存；本次允许编码、编译和电脑验证，不自动访问板卡、烧录、接电池、运行电机或上传，不改Option Bytes。实物验收由主控手动回报。

回报00：修复原因、文件、初始化顺序与超时依据、验证结果、新产物及版本位置、主控操作步骤、仍待板级验证的项目。只有主控确认新版本能自主启动后，才继续C-02B动力试转。

## 01执行记录：C-02B-R1

2026-10-20，01已完成下列本地工作，没有访问调试器、下载或给驱动供电；已有现场截图、下载日志、Keil本机设置及其它成果保留。

### 修复与有界失败处理

应用顺序改为：先建立四脚低电平并初始化待机逻辑→验证TIM5启动时基→限时等LSI→**IWDG_Enable**→允许配置写入→PR=32／RLR=249→限时等PVU/RVU→Reload→启动SysTick。保留SPL，不引入HAL或修改厂家IWDG实现。

TIM5是32位计数器，当前HSI／HCLK／APB1均为16MHz且APB1不分频，PSC=15、ARR=0xFFFFFFFF，1计数为名义1us；不使用TIM5中断、GPIO或DMA。与TIM1 PWM、TIM3/4编码器资源独立，启动结束或失败均停止TIM5。启用后先检查计数确有递增，此检查最多1024次；正常等待按微秒差比较，每个LSI／PVU-RVU阶段独立最多10ms，支持计数回绕。若时基在等待中失效，100000次轮询作为额外有限保护，返回时基故障；此次数不是精确毫秒超时。

时间依据：[F407 RM0090 Rev22](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405415-stm32f407417-stm32f427437-and-stm32f429439-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)第21.4.4节／707页说明PVU/RVU硬件更新最多5个LSI周期。本版为固定F407选10ms余量，不照搬跨型号HAL的超时常量，也不用此时恒为0的g_motor_bench_ms。IWDG启动从复位计数0xFFF开始，配置完成前不提前Reload到较短249；按手册表107名义32kHz及初始/4为512ms预算，10ms更新窗口远短于该名义预算，LSI容差及实板时序仍待测。IWDG一旦启用无法由应用关闭，不能在超时后假装回到无看门狗状态。

故障位锁存：1=PWM时钟，2=启动时基，4=LSI超时，8=IWDG更新超时，16=SysTick配置；可按位组合。初始化失败返回main后保持ABORTED及零输出，不调用试转状态机；可用SysTick显示快闪并保持计数增长，不清故障，也不允许长按起转。LSI失败时看门狗尚未启动，不作假喂狗；看门狗已启动后更新超时，后续故障分支继续喂狗保留诊断，CPU／滴答停滞仍会由IWDG复位。异常处理仍先关PWM并四脚拉低。人工触发、15%／500ms及停止锁定逻辑未改动。

诊断字段：`g_motor_bench_revision=0x020B0001`标识R1实际应用执行；`g_motor_bench_watchdog_started=1`及`stage=4`表示启用、配置更新完成。stage=1为时基就绪、2为LSI就绪、3为已Enable但未确认更新完成。相关中文注释已写入应用源码。

### 针对本故障的电脑复现与验证

回归入口：`control/tools/run_motor_bench_startup_tests.ps1 -Compiler C:/software/mingw64/bin/gcc.exe`。测试直接包含真实motor_bench_main.c并运行main→watchdog_init→SysTick调用链，只在SPL／内核／PWM边界使用明确的电脑模型；模型不加入任何Keil目标。未启动IWDG时更新标志不清，保护预算使旧无限等待可以自动判失败。

修复前已实际运行一次，失败输出：

```text
FAIL startup: stuck at PVU before IWDG_Enable; ms=0, SysTick=0, output=0
```

修复后实际输出：

```text
PASS MotorBench startup: 154 checks in 10 hardware-model scenarios (real main/SysTick; no board access)
```

覆盖正常启动及计数回绕、LSI永久不就绪及回绕、PVU不清、RVU不清、两标志都不清、TIM5从未递增、中途停滞、时钟不符。断言超时在SysTick仍为0时退出，故障位正确锁存、实际main/SysTick故障分支反复保持停止、完整长按／松开也不放行；正常模型最终ms增长、fault=0、READY。它验证应用顺序、边界及失败决策，**不能模拟或证明F407时钟跨域电路、真实计时和GPIO电平**，不能替代主控实测。

原73项人工试转逻辑、55项协议检查仍通过。四个正式目标及UART开启分支最终均0错误0警告；官方SPL清单所有SHA256仍匹配，原截图SHA256未变。原始电脑输出位于被忽略的control/build/motor_bench_startup_red.log、motor_bench_startup_tests.log等；编译日志位于control/firmware/build/。详细结果同步[验证记录](validation.md)。

### 新产物版本与文件

本地目录`D:/Projects/yeye`，main，HEAD `82640aba4cf7aa4f30db14b486aef852936118fe`加未提交修改。Keil ARMCC5.06u5：Code4672、RO424、RW48、ZI1048。以下为本次构建字节哈希，重新构建后须按实际产物记录；AXF含调试信息，可能受路径／工具变化影响。

| 产物（control/firmware/build/motor_bench/） | 字节 | SHA256 |
| --- | --- | --- |
| motor_bench.axf，纯Keil Download使用 | 390824 | `6cd1aa9ab11d47d52c0c5baa17fa2a4d88eb55b02cf78a5c1e1bb3a78e11faaf` |
| motor_bench.hex | 14525 | `2b548e09651fc0f1137de6ef98e7579bf5772acea9c539fda15aa990f6cb037a` |
| motor_bench.bin，备选DFU使用 | 5144 | `9c165244e60585d5c9a9fbaf882dc4964a56c7c046a808ecfa37a66539c036dd` |

本轮实际修改：应用`control/Core/Src/motor_bench_main.c`；新增`control/Tests/Host/test_motor_bench_startup.c`、`control/Tests/Host/fakes/motor_bench_startup/stm32f4xx.h`及`control/tools/run_motor_bench_startup_tests.ps1`；更新本故障记录、motor_bench.md、validation.md、keil_quickstart.md、pin_plan.md、control/README.md及project_status.md关联项。官方库、原人工试转逻辑与PWM驱动未改。

纯Keil重下载、DAPLink五线及无动力独立启动步骤见[操作说明第11节](motor_bench.md)。本次不接电池、不长按试转。主控应先退出调试、真正断电重启观察每组1次绿灯，再以运行中Watch确认ms持续增长、fault=0、READY；暂停／断点可能改变看门狗行为，不能拿暂停时的静止数值验收。**当前没有R1实物复验结果，问题保持待现场验收。**
