# C-02B-R2：受限30%起转诊断

## 当前摘要

唯一标识：`C-02B-R2`；阶段：S1；状态：**待核实**；整理：2026-11-19。
负责角色：主控；硬件／视觉协作沿用主控最新指派。执行对话：未重新指派；旧身份见历史。
结果／限制：30%软件交付，后续实测A无动作；不以后来PWM成功改写本版失败。
唯一下一步：只用于历史定位，不重新安排旧单轮试跑。

## 任务定义

成果：C-02B-R2：受限30%起转诊断。原范围、依赖、交付路径及量化标准见历史区；不自动取消遗留要求。原执行版本／环境／量化验收要求在历史区；恢复前由总管提升仍适用的缺口至本区，不能直接执行旧Prompt。
比赛关联：第三部分、图1、表1；支撑基本功能60分的可靠完圈、少触边及缩时，并保留报告20分的可引用证据，不宣称新增实测得分。
授权：本轮仅重构文档；原实现／设备／上传授权不续期。新执行按[协作规则](../../project_planning/collaboration_standard.md)及主控转交的当前范围。
- 事实来源：[证据／规格1](../../testing/2026-10-21_motor_bench/no_rotation_record.md)；[证据／规格2](pin_plan.md)；[证据／规格3](../../hardware_preparation/dual_motor_wiring_guide.md)；[证据／规格4](../Drivers_Custom/Motor/motor_bench_pwm.c)

## 执行结果

原实现、检查日期、版本、方法、实物反馈及未完成项保留于历史区／证据；本轮仅统一记录，未重跑原测试。完成层次限于摘要，不把软件或部分通过当整车验收。

## 主控验收

尚无覆盖原任务全部范围的主控明确验收；旧对话审核不替代主控。 后续填：日期／主控原话／通过或退回／接受范围／证据。退回继续本任务。

## 接续信息

迁移工作区D:/projects/projectsyeye，分支codex/current-version-20261025，HEAD 62b4f288b27c4e3fa9f6d213c07be186e502f43c；有共享未提交／未跟踪成果，不是原任务执行快照。
已有检查按适用源码、配置、输入和环境复用；只恢复摘要的唯一下一步。保护共享修改，先核对实际版本／设备占用。旧逐轮测试与固定聊天Prompt不作为当前指令；当前双轮流程按AGENTS。

## 历史记录（原文保留，仅作来源）

原日期、失败、授权和相对链接完整保留；下方“当前／下一步”只适用于原版本，不覆盖上方摘要。

<!-- ORIGINAL_TASK_BEGIN -->
# C-02B-R2：受限30%起转诊断

状态：01已完成固定30%版本、编译与电脑验证；待主控纯Keil下载及一次A实测，本轮未自动操作板卡。日期：2026-10-21（北京时间）。00分配与验收，01实现，主控手动试转；硬件负责后续实际电气测量。

## 背景与依据

主控已确认接线无问题，不再重复索要照片或既定型号。当前程序可正常待机、识别KEY并从A软件阶段进入待B，但电机没有转动；现场没有万用表。原始反馈见[无转动记录](../../testing/2026-10-21_motor_bench/no_rotation_record.md)，接法查[引脚表](pin_plan.md)和[接线指南](../../hardware_preparation/dual_motor_wiring_guide.md)。主板由DAPLink单源5V供电，驱动使用独立2S电池，信号共地，主板Type-C及两板间5V/3V3保持断开。

原参数为20kHz／15%／500ms。15%可能不足实际起转，但没有电气测量，不能当作已确认根因。本任务仅改变占空比这一试转变量，用一次受限的30%短脉冲观察；不以此证明电池、驱动或PWM已经正常。

## 转交01的要求

1. 读AGENTS、默认技能、协作标准、状态表、本文件、MotorBench说明及R1修复记录。保留R1启动顺序、限时等待、粘性故障与现有工作区成果，不切分支。
2. 先核对当前TIM1四路端口、AF、MOE、CCR及输出方向与既定接线一致；从现有代码证据核对，不把电脑检查当实测波形。发现其它确切问题时如实报告。
3. 将MOTOR_BENCH_DUTY_PERMILLE从150改为300，即30%，周期保持800，实际有效CCR应为240。20kHz、500ms、长按KEY到常亮后松开、A→B→AB逐步人工触发、停止和终态锁定均保持不变。
4. 禁止上电自动运行、自动爬升、延长脉冲或加入100%直驱；不删除看门狗或重写已验证的启动逻辑。初始化和故障仍必须零驱动。
5. 更新版本标识，例如revision=0x020B0002，和涉及参数的中文注释、当前操作文档及验证记录。旧15%失败记录保留为历史，不批量改写旧数据。
6. 编译受影响目标，运行适用的已有检查；核对30%参数、CCR计算及停止路径。无需为宏值另写只镜像实现的测试，不将原纯逻辑测试当作电机起转验证。保存新AXF／HEX／BIN与实际哈希。
7. 给出纯Keil5重建、Download至Verify OK、退出调试、无动力断电重启及确认版本／待机的方法，不要求主控用终端。

## 现场操作与验收

先只做电机A：主控确认电池与开关处于正确供电状态、退出Keil调试、轮子悬空、线束远离轴；KEY一次长按松开，观察30%／500ms是否能起转、是否按期撤去驱动，记录声音、轻微抖动、方向及停稳。若仍完全不转／只抖动，停止并关驱动拔电池，不继续B或AB、不再加占空比或重复连续堵转。

A正常才继续B；B也正常并停稳后才测双电机。未起转时由硬件借仪表补测供电及实际输入／输出，或由01按进一步证据定位，不继续用加功率替代测量。灯推进不等于实际起转。

本次授权范围：01应用参数及必要版本／文档更新、编译与电脑验证，仅本地保存；不自动连接板卡、烧录、接电池、触发电机或上传，不自动跨聊天发消息。物理步骤由主控手动执行。

回报00：修改文件、30%／500ms／20kHz参数核对、版本标识、编译与检查结果、新产物哈希、纯Keil操作及首轮A判定条件。真实起转仍待主控回报，不预先填通过。

## 01执行与交付记录

执行日期：2026-10-21（北京时间）。本次只修改占空比、版本字段与对应注释／文档，更新原启动测试的版本期望；不引入其它控制行为。主控接线正确的确认继续采用，旧15%不转记录保留，不能用本轮电脑结果确认真实起转根因。

### PWM源码核对结果

核对应用[motor_bench_pwm.c](../Drivers_Custom/Motor/motor_bench_pwm.c)、[参数头文件](../Drivers_Custom/Motor/motor_bench_pwm.h)、[主入口](../Core/Src/motor_bench_main.c)及本地未修改的官方SPL TIM／GPIO实现；AF与接线依据沿用[pin_plan.md及其官方资料](pin_plan.md)。未发现端口、AF、通道、输出使能或CCR计算与既定方案不一致的确切源码问题；此结论不等于板上PWM测量通过。

| 对端 | MCU／复用 | TIM1资源 | R2请求时的CCR |
| --- | --- | --- | --- |
| AIN1 | PE9／AF1 | CH1 | A或AB：240；否则0 |
| AIN2 | PE11／AF1 | CH2 | 始终0 |
| BIN1 | PE13／AF1 | CH3 | B或AB：240；否则0 |
| BIN2 | PE14／AF1 | CH4 | 始终0 |

- 当前HSI、HCLK、PCLK1、PCLK2名义均16MHz，APB2不分频，TIM1 PSC=0、ARR=799，因此频率16MHz／800=20kHz。R2宏为300‰，实际有效CCR=800×300／1000=240，PWM1高有效；相对R1的120只改变固定占空比。
- GPIOE时钟与TIM1时钟均开启；四通道普通CHx的CCxE由TIM_OCxInit的OutputState_Enable设置，互补CHxN不启用。GPIO_PinAFConfig为PE9／11／13／14设置GPIO_AF_TIM1（本地官方定义0x01）。TIM_Cmd开启计数器，不代表MOE已开放。
- 初始化先四脚GPIO低、CCR全0、MOE关闭；人工触发非零mask后先停止、关闭MOE，写CCR及UG同步更新，切四脚AF，最后TIM_CtrlPWMOutputs(ENABLE)设置MOE。A／B／AB的CCR1–4分别为(240,0,0,0)、(0,0,240,0)、(240,0,240,0)；没有改变正反向或轮侧标定。
- stop取消MOE、四CCR清零并UG，ODR写0后四脚改主动低GPIO。500ms、原始按键立即停止、卡键／终态锁定、上电松键门槛以及R1独立TIM5超时、IWDG和粘性故障零输出均保留。编码器TIM3／4未启用，USART2／SWD资源不变。

### 实际电脑验证与产物

| 项目 | 本轮结果与边界 |
| --- | --- |
| MotorBench编译 | Keil5.24a／ARMCC5.06u5：0错误0警告；Code4672、RO424、RW48、ZI1048。只重新编译受影响MotorBench，原三目标配置／源码未改，不重记为本轮已重编译 |
| R1启动模型 | 154条断言／10场景通过；真实main／SysTick调用链，版本期望更新为0x020B0002。仅电脑模型，不能证明板上更新时序／电气输出 |
| 原人工序列与协议 | 台架73项、协议55项通过；覆盖人工A→B→AB、500ms、按键停止及锁定等逻辑，不能证明电机起转 |
| R1保护差异 | 与开工本地副本逐字比较，main文件仅版本赋值／同行注释变化；watchdog_init、TIM5等待、SysTick故障与异常处理原样保留；纯逻辑及PWM停止代码不变 |
| ARM产物核对 | 从新AXF反汇编：motor_bench_pwm_apply在0x08000E50加载0xF0（240），分别按mask传入TIM_SetCompare1／3，Compare2／4传0。向量SP=0x20000448、Reset=0x0800019D落在对应SRAM／Flash范围 |
| 与R1的BIN比较 | 均5144字节，仅偏移0xDA4的01→02（版本）与0xE50的78→F0（比较值120→240）两字节变化；不把这项电脑字节检查写成真实PWM通过 |

实际输出：

```text
PASS MotorBench startup: 154 checks in 10 hardware-model scenarios (real main/SysTick; no board access)
PASS motor bench: 73 checks (manual sequence, debounce, stop, timeout, wrap, lockout)
PASS all 55 checks
motor_bench.axf - 0 Error(s), 0 Warning(s).
```

本轮产物位于`D:/Projects/yeye/control/firmware/build/motor_bench/`；Keil直接Download使用AXF。版本字段`g_motor_bench_revision=0x020B0002`，与R1的0x020B0001不同；编译大小相同，不以大小代替版本确认。

| 文件 | 字节 | SHA256 |
| --- | --- | --- |
| motor_bench.axf | 390828 | `f59095cd629bcf1f6015d568e198afa065abe808dc64752aedcfb317bac34149` |
| motor_bench.hex | 14525 | `eac6ad355f432601ab6a97c09f88cb64af89ebb4e58bc4cbe7d5d37053889b22` |
| motor_bench.bin | 5144 | `99b03ae743aa1021aeb5cb49192f2b24771e30d0872a577b17b3b29bbbd1d967` |

源码／文档、产物及开工副本保存在本地；版本仍为main、HEAD `82640aba4cf7aa4f30db14b486aef852936118fe`加未提交修改。产物、日志、`control/build/c02b_r2_baseline/`开工副本和`control/build/c02b_r2_disassembly.txt`反汇编被Git忽略，换电脑须重新构建并核验。最终编译日志在`control/firmware/build/MotorBench_build.log`，电脑日志在`control/build/motor_bench_startup_tests.log`、`motor_bench_tests.log`和`host_tests.log`。

### 修改文件、现场操作与待测

本轮修改11份文件：

- 应用3份：`control/Drivers_Custom/Motor/motor_bench_pwm.h`、`control/Drivers_Custom/Motor/motor_bench_pwm.c`、`control/Core/Src/motor_bench_main.c`。
- 原测试1份：`control/Tests/Host/test_motor_bench_startup.c`，只更新版本期望，没有为宏值新增镜像测试。
- 文档7份：本文件、`control/docs/motor_bench.md`、`control/docs/validation.md`、`control/docs/keil_quickstart.md`、`control/docs/pin_plan.md`、`control/README.md`、`project_planning/project_status.md`。

纯Keil逐步操作已更新至[MotorBench第12节](motor_bench.md)：动力电池拔开→MotorBench重建→Download及新Verify日志→无动力Watch确认0x020B0002／ms增长／fault0／READY→退出调试、独立断电重启观察每组1次待机灯→确认动力ON且轮子悬空后KEY长按松开，只触发A一次。若A完全不转或只抖动，关驱动并拔XT30，不继续B／AB、不反复触发或再加功率；返回真实现象并由硬件借仪表补测。程序保留后续B／AB，但首轮先回报A结果。

当前待现场：R2下载与板内版本、独立待机、实际30%／20kHz波形、A起转与500ms撤输出、机械停稳及声音／抖动／方向；B／AB和故障停止的物理效果仍待后续条件满足后验收。无仪表的项目保持未测。01未访问板卡、烧录、接电池、试转、切分支、上传或发跨聊天消息，不预先填写起转通过。

最终本地核对：相对开工副本恰好上述11份文件变化，其余已记录文件保持原字节；7份文档共104个本地链接存在，11份文件无行尾空白，git diff --check通过。16份官方来源文件SHA256匹配，新产物大小／哈希与表一致；核对摘要保存在被忽略的`control/build/c02b_r2_checks.json`。未据此扩大板级验证结论。
