# 主控基础工程验证记录

## 2026-10-25：MotorPwm人工验收回报

主控在收到新MotorPwm下载、无动力演练、A/B分别500ms测试及断动力收尾流程后回报：“全部符合预期”。据此记录A/B分别PWM起转、约500ms自动停转与阶段灯态符合本轮流程，C-02B-PWM-R4软件及人工验收完成。证据为主控文字回报，未另附Watch版本读回、仪器计时、波形或录像；不把约500ms描述写成精密测量，也不据此确认AB同时运行、编码器或闭环。详见[现场原始回报与结果](../../testing/2026-10-25_motor_pwm/acceptance_record.md)、[任务](../../project_planning/tasks/C-02B-PWM-R4.md)。本轮仅回写文档，未改代码或重新构建；全局摘要由00据文件更新。

## 2026-10-25：按主控要求重写PWM

主控确认AB直接驱动均正常，随后要求删除旧PWM代码重写。已替换motor_bench_main.c与motor_bench_pwm.c，更新接口，新增独立motor_pwm.uvprojx／MotorPwm。新单次版本0x020B0004：1kHz、50%、500ms，只有选中桥IN1切AF，IN2始终GPIO低；MOE使能失败立即撤驱动并锁存故障32。纯按键状态机、Direct A/B与SPL依赖保持现有接口。

Keil5／ARMCC5.06u5：独立MotorPwm与原MotorBench均0错误0警告，Code4908／RO424／RW64／ZI1288；独立BIN5396字节，SHA256为ea10fb83a5497c40c346ee6005073562dade79b013fcc8c6a5f6ec4d49d65a33，两入口BIN一致。MotorContinuous仍20kHz／30%持续A，版本升级0x020B1002，构建0错误0警告，Code4864／RO424／RW64／ZI1288，BIN哈希1002748e7755bf9ec762bfdee29f389e51b48ca411abb669a4ac510003783374。

电脑模型：新PWM168项／9场景，启动154项／10场景，按键73项；持续115项／7场景与启动154项；Direct A/B各52593项／9场景及Direct启动154项通过。测试更新了新频率/占空比、仅IN1切AF和版本的预期，并增加真实SysTick下完整A/B/AB独立人工触发、500ms边界、终态锁定；MOE拒绝使能场景改为验证立即故障停止。其他停止、回绕与启动失败场景保留。

工程和本机uvoptx已核对独立目标、源码引用、CMSIS-DAP/SWD及Flash配置。新工程准备时XML空字段格式导致Keil退出15，规范化空字段后实际构建通过。全部是软件检查，未由代理下载、访问调试器或运行马达；新PWM起转、外部波形与电流仍待主控。操作、任务与持久化日志分别见[MotorPwm](motor_pwm.md)、[C-02B-PWM-R4](../../project_planning/tasks/C-02B-PWM-R4.md)、[本次证据](../../testing/2026-10-25_motor_pwm/acceptance_record.md)。

## 2026-10-25：笔记本Keil下载配置

维护：主控／01。依据：主控要求继续调整Keil5设置，使工程具备手动下载配置；本轮未执行Flash Download、目标复位或运行。

开工发现主控已生成motor_direct.uvoptx、界面文件和DebugConfig，并将独立工程UpdateFlashBeforeDebugging改为1。独立工程实际本机Debug驱动仍为UL2CM3，未选CMSIS-DAP。修改前将两工程及现有独立uvoptx备份到control/build/keil_laptop_settings_backup_20261025_133141，保留已有DebugConfig。

- 修正独立motor_direct.uvoptx并新建六目标yeye_control.uvoptx。除LogicDemo保留模拟器外，板级目标选BIN/CMSIS_AGDI.dll；CMSIS_AGDI注册项设置SWD、1MHz（本机驱动频率表索引-S3）、自动选择已接入的DAPLink。
- Flash设置为STM32F4xx_512.FLM，起点0x08000000，范围0x80000，算法RAM起点0x20000000、大小0x1000；选擦除／编程／校验，不选下载后复位运行。Flash使用Debug Driver；各目标关闭Update Target before Debugging，实际下载由主控在Keil手动点击Flash → Download。
- 预置MotorDirect版本、fault、ms、watchdog_stage、状态机和GPIO诊断六项Watch，MotorBench／MotorContinuous使用各自变量；启用Periodic Window Update，关闭Run to main及Trace／Event Recorder自动恢复。未改现有dbgconf寄存器值、应用代码、保护参数和编译选项。
- 已静态检查两份XML、六目标覆盖、CMSIS-DAP DLL与Flash算法路径及Watch变量对应源码；此前本机六目标及独立Direct均已编译通过，本轮配置不改变编译内容。尝试打开Keil核对界面，实际窗口标题确认载入独立工程，但当前自动化未能读取Options对话框，因此不将界面设置或SWD通信写成已实测通过。

两份uvoptx为本机忽略文件，不能通过Git默认同步。主控退出现有Keil后重新打开D:\projects\projectsyeye\control\MDK-ARM\motor_direct.uvprojx，以重新加载本机设置；旧窗口如询问保存，选择No避免覆盖新配置。动力电池拔开、驱动OFF时，Options for Target → Debug应为CMSIS-DAP Debugger；Settings核对SWD／1MHz，Utilities使用Debug Driver、关闭Update Target before Debugging；Flash Download页核对STM32F4xx 512KB／0x08000000、Program／Verify与不勾Reset and Run，再按既有MotorDirect说明手动下载。Programming Done／Verify OK尚无本轮回报；主控无需重复报告既定硬件型号。

## 2026-10-25：笔记本芯片包安装与编译验证

维护：主控／01。依据：主控明确要求在已接入DAPLink的笔记本安装项目缺少的芯片包、驱动等；不含烧录或电机操作授权。

- 设备名JOKEBEARDESKTOP，实际目录D:\projects\projectsyeye；分支codex/current-version-20261025，完整HEAD为0f033c6f67e5d4bef27b1c5afdd9d7014ac0456d。开工工作区干净。
- 复用D:\software\Keil5，TOOLS.INI标记5.24a；实际运行ARMCC版本查询，结果为5.06 update 5 build 528。Git 2.50.1、MinGW GCC 6.3.0已存在。
- 从Keil官方HTTPS地址下载并使用本机签名有效的UV4/PackUnzip.exe安装Keil.STM32F4xx_DFP 2.17.1。该包声明依赖ARM.CMSIS 5.6.0，因此同时安装5.6.0，原5.0.1保留。两个安装进程均退出0，安装至现有ARM/PACK目录，STM32F4xx_512.FLM存在。
- 下载地址分别为https://www.keil.com/pack/Keil.STM32F4xx_DFP.2.17.1.pack 与https://www.keil.com/pack/ARM.CMSIS.5.6.0.pack 。本次下载文件SHA256分别为C7E0F3595AA5EE4C2DA2C0DE79598B8A91FC5F4F77E16C3B39C674429FB0F4EB及15A139AAB106111F82BE486C5D0834C9AB77DAADF27391781FEE8185B1E85285；这些是本机留证值，不是另行取得的厂家校验值。安装包保留在用户临时目录。
- 已接入LC DAPLINK，USB VID_0D28/PID_0204。HID、WinUSB、USB串口、存储及复合接口均Status OK；驱动提供商Microsoft，IsSigned=True。串口为COM9。现有Keil包含CMSIS_AGDI.dll与CMSIS_DAP.dll，无需另装第三方USB驱动，也未替换当前驱动或升级DAPLink固件。
- 顺序构建yeye_control.uvprojx六目标以及motor_direct.uvprojx独立目标，全部0错误0警告。MotorBench、MotorContinuous、MotorDirect导出BIN的SHA256分别与ORG-02记录的d09c4095…、5cd07579…、6377f00d…一致。六目标源码文件引用检查无缺失。
- 本机PowerShell默认策略禁止执行.ps1；仅在获准的本次构建子进程使用-NoProfile -ExecutionPolicy Bypass运行原build_keil.ps1，并显式传入-KeilRoot D:\software\Keil5；未修改全局执行策略。独立工程使用Keil命令行构建。日志在control/build/firmware/*_build.log，独立入口日志为MotorDirect_standalone_laptop_build.log；均为Git忽略的本机输出。

本次没有重跑电脑模型或UART开启分支，没有打开调试会话、复位目标、烧录、驱动电机、上传或跨聊天发送。两个本机uvoptx及DebugConfig仍未配置，六目标人工Debug／Flash／Watch设置与实际下载链路仍待单独核对；不使用旧setup_debug.ps1双目标模板宣称六目标配置齐全。USB枚举及编译通过不代表板卡通信、MotorDirect起转或整车验收完成。全局状态仍由00按本模块证据顺序汇总。

## 2026-10-25：ORG-02物理分层与等价检查

按主控确认把Core、App、Drivers_Custom、Drivers、Algorithms、Tests、MDK-ARM放在control内。应用C／H和启动汇编只移动，4份电脑测试更新6处直接包含真实.c的路径；工程、工具、清单及文档引用同步。新Keil入口为[MDK-ARM/yeye_control.uvprojx](../MDK-ARM/yeye_control.uvprojx)，Direct独立入口为[同目录motor_direct.uvprojx](../MDK-ARM/motor_direct.uvprojx)，新ARM输出在control/build/firmware。

本轮迁移前六目标＋UART开启HardwareBench均0错误0警告；迁移后同六目标＋UART开启＋Direct独立工程均0错误0警告。现有六个电脑测试脚本共八组程序通过：协议55、台架73、启动154／10场景、R3诊断131／8场景、持续113／7场景及启动154、Direct52593次边界断言／9场景及启动154。断言数不等于独立场景数。

38份应用／第三方C、H及启动汇编原字节保留，来源清单16项哈希通过；两个正式工程除路径／构建状态外配置相同，两个本机uvoptx除源码／列表路径外等价，CMSIS-DAP设置保留。六目标迁移前后BIN和HEX逐字节一致，AXF包含不同调试路径不要求同哈希。完整映射、BIN哈希及检查见[ORG-02](../../project_planning/tasks/ORG-02.md)；本机日志在tmp/layering_audit。

本轮没有修改应用行为、烧录、访问板卡或上传；Keil人工打开新工程的体验、真实波形／起转／整车结果仍待主控。以下原构建和AXF哈希按原日期保留，旧control/firmware/build中的历史日志未清理。

## 2026-10-24：按主控要求复核电机端口与实际构建

重新阅读真实motor_bench_main／pwm／状态机、board.h／board.c、Keil XML及原厂SPL GPIO／TIM实现，查看ST表9及天空星P1／P2／H1官方原图与已归档照片。MotorContinuous未链接旧board.c；四脚PE9／11／13／14、AF1、CH1–4、PSC0／ARR799、A运行CCR240／0／0／0、UG→AF→MOE路径一致，未发现明确映射或使能遗漏。此为源码／构建复核，不构成“固件无缺陷”或实物波形通过。完整接线副本、逐项核对结论与边界见[接线自查及代码复核](../../hardware_preparation/motor_wiring_self_check.md)。

本轮实际完整Rebuild MotorContinuous，ARMCC5.06u5，0错误0警告，Code5164／RO424／RW64／ZI1288；BIN5652字节及SHA256 `5cd07579b14e1e50e736e2ba0553f21197d6784a305febb6402c9050a55a1eef`与开工一致，版本仍0x020B1001。真实AXF反汇编含GPIOE／TIM1及四AF和启用调用。持续模型113条／7场景、持续宏启动154条／10场景、原R3诊断131条／8场景全部重新执行通过；未重跑无变化的协议、原台架纯逻辑或其他Keil目标。日志为`control/firmware/build/MotorContinuous_port_audit_rebuild.log`及既有测试日志，反汇编／哈希与最终检查在`control/build/motor_port_audit_*`。本轮只改文档，没有修改应用或官方库，没有烧录、访问板卡、接电池或上传。

## 2026-10-24：独立MotorContinuous持续A桥

主控本轮直接要求“让马达一直转”。新增Keil目标MotorContinuous及目标专用宏，仅A桥固定30%／20kHz人工启动后持续，不再500ms自动停止；KEY立即停止并锁定、上电零输出、R1与R3保护保留。实现、完整产物哈希和纯Keil步骤见[持续A桥说明](motor_continuous.md)。此变更来自本轮新需求，不记为R3缺陷修复或实物起转通过。

实测电脑结果：新目标真实main／SysTick／PWM模型113条／7场景通过（模拟120秒、回绕、KEY／fault停止及锁定、非法阶段），持续宏下R1启动154项／10场景通过；原诊断131项、台架73项、协议55项通过。MotorContinuous 0错误0警告，Code5164／RO424／RW64／ZI1288，BIN5652字节、SHA256 `5cd07579b14e1e50e736e2ba0553f21197d6784a305febb6402c9050a55a1eef`。MotorBench重新编译0错误0警告，BIN与R3开工文件逐字节相同；原四目标配置与本机调试项结构一致，新目标复制已验证DAPLink设置，无模拟器替换。原三目标应用源码未改，本轮未重编译无关目标或UART分支。

日志在`control/build/motor_continuous_tests.log`、`motor_continuous_startup_tests.log`及`control/firmware/build/MotorContinuous_build.log`；既有回归日志为本次重新执行结果。全部是电脑验证，没有访问板卡、烧录、接电池或运行电机；真实起转及KEY电气停止仍待主控，不能以模型模拟120秒代替实测。

软件验证日期：2026-10-12，北京时间。本记录对应标准外设库（SPL）版本，当时没有板卡或电机接入。2026-10-14 已新增实物基础测试，见下文及 [板级测试记录](../../hardware_preparation/board_self_test_record.md)。

| 项目 | 方法 | 结果 |
| --- | --- | --- |
| Keil LogicDemo | Keil5.24a / ARMCC5.06u5实际编译链接 | 0错误、0警告；Code1860、RO424、RW12、ZI1108字节 |
| Keil HardwareBench | 同环境实际编译链接，含SPL RCC/GPIO/USART/misc模块 | 0错误、0警告；Code2112、RO424、RW36、ZI1108字节 |
| 链接布局 | 核对Keil生成scatter文件 | FLASH0x08000000/0x80000，SRAM0x20000000/0x20000 |
| UART开启分支 | check_uart_build.ps1临时工程，BOARD_UART_ENABLE=1，完整编译链接 | 0错误、0警告；Code3428、RO424、RW44、ZI1364字节；串口未做板上验证 |
| PC通信与状态机 | GCC，C99，Wall/Wextra/Wconversion/Werror/pedantic | 55项检查全部通过 |
| Python编码示例 | 输出直道、无效路径、START、STOP、STATUS的20字节包 | 生成成功；直道固定字节向量与C编码器匹配 |
| Keil模拟器运行 | 命令行自动调试尝试 | 未取得日志；窗口检查工具不可用，模拟器执行待主控按说明人工确认 |
| 实物基础测试（2026-10-14） | BoardSelfTest经USB DFU烧录并读回校验，主控观察LED | 1868字节一致；正常双闪；不包含电机控制 |

## 电脑端实际输出

```text
PASS parser: CRC, split/concatenated frames, noise, corruption, truncation, format/range checks
PASS state: explicit start/stop, demands, duplicate/old frames, timeout, no auto-restart, invalid path, delayed processing, transport error, counter wrap/reboot
PASS end-to-end: wire bytes -> parser -> state; corrupted updates cannot keep vehicle running
PASS all 55 checks
```

覆盖：CRC标准向量与固定包、负数解码、分包/连包/噪声、截断恢复、字段越界、无路径拒绝启动、转向演示输出、重复帧不续命、200ms边界、晚到数据不能掩盖超时、恢复数据不自动启动、STOP优先和延迟START、低质量路径、处理耗时、接收故障、序号及毫秒计数回绕、板卡重启后序号基线重建。

不将电脑逻辑检查或基础双闪测试当成实车性能：HSI误差、实际帧率、UART引脚/电平、SWD连接、电机方向、编码器、PID、真实制动距离、一圈判定与语音链路仍待接线后验证。

原始可重建输出在control/build和control/firmware/build，Git忽略。主控修改通信或状态机后重新执行tools/run_host_tests.ps1和两个Keil目标编译，记录新的验证结果。

标准库版本固定为V1.3.0，来自Keil官方分发包1.0.8；本机用于器件识别/下载的DFP仍为2.17.1。SPL源文件、匹配头文件和许可证已随工程保存，原始来源与SHA256见Drivers/stdperiph/source_manifest.json。

## 2026-10-20 C-02B：独立双电机台架的电脑验证

负责角色／对话：主控／01。版本起点：main，82640aba4cf7aa4f30db14b486aef852936118fe；本任务为本地未提交修改，保留原有接线／规划文档改动。操作说明与参数见[motor_bench.md](motor_bench.md)。本次**没有烧录、连接电池或运行电机**，不将下表写为板级通过。

| 项目 | 方法 | 实际结果／范围 |
| --- | --- | --- |
| MotorBench编译链接 | Keil5.24a／ARMCC5.06u5，独立目标 | 0错误0警告；Code4216、RO424、RW32、ZI1048字节 |
| 既有三目标回归 | LogicDemo、HardwareBench、BoardSelfTest分别实际编译 | 均0错误0警告；三目标大小与既有记录相同 |
| UART开启分支 | check_uart_build.ps1，仅编译临时工程HardwareBench | 0错误0警告；Code3428、RO424、RW44、ZI1364字节；原UART仍默认关闭 |
| 既有协议／状态机 | run_host_tests.ps1，GCC严格告警 | PASS all 55 checks |
| 新台架纯逻辑 | run_motor_bench_tests.ps1，GCC C99，Wall／Wextra／Wconversion／Werror／pedantic | 73项通过；同一motor_bench.c用于板端与电脑测试 |
| Keil目标隔离 | 对比HEAD原三目标XML的已有配置／文件选项；剔除新增显式排除条目后结构一致；核对台架链接响应文件 | 原配置保留，新增电机／TIM／IWDG文件在原目标显式排除。台架仅链接新入口／逻辑／PWM、启动、RCC／GPIO／misc／TIM／IWDG，不链接原board.c、main.c、协议或UART |
| SPL来源 | 对本地Keil.STM32F4xx_DFP.1.0.8.pack核SHA256，提取TIM／IWDG四文件并核manifest | 来源包与原清单一致，文件保持厂家原字节；未替换本机2.17.1设备包 |
| BIN准备 | fromelf --bin；检查向量SP落在SRAM、复位地址在Flash且为Thumb | 4672字节，地址布局检查通过；不代表板上执行通过 |
| 下载工具条件 | 检查历史DFU写入／读回日志、当前文件存在性及dfu-util --version | 0.11可运行；本次未执行-l、读Flash或写Flash，当前USB枚举／WinUSB连接状态由主控现场核实 |
| 最终文档／差异 | 本地链接、下载示例PowerShell语法解析、Git空白检查、原应用源差异 | 78个本地链接存在；4段PowerShell示例只解析未执行；git diff --check通过；原board.c／main.c／car.c／protocol.c／board_self_test.c及board.h无修改 |

新台架测试实际输出：

```text
PASS motor bench: 73 checks (manual sequence, debounce, stop, timeout, wrap, lockout)
```

覆盖上电按住不转、松键门槛、按键抖动／短按不启动、不能用松键消抖时间补足长按、A→B→AB需各次人工触发、500ms边界、按键原始电平立即停止并锁定、持续长按卡键锁定、复位不续跑、第三步终态不循环、毫秒计数回绕、晚调度停止、异常状态／编号归零。电脑测试不访问PWM硬件或编码器，不覆盖真实电气输出。

首次编译曾因新目标缺少显式排除旧入口而出现多main链接错误；已修正Keil跨目标文件清单与IncludeInBuild，新旧目标最终编译均通过。最终工程XML仅做缩进／换行整理，配置结构复核；不将失败构建当交付版本。

BIN SHA256：`8593c996b152dc3a7f67515dbe66b3bfa323acaf81d42222c2bbe95d3749b8a4`。原始可重建日志位于`control/build/host_tests.log`、`control/build/motor_bench_tests.log`、`control/firmware/build/MotorBench_build.log`及各目标命名日志；UART日志在`control/firmware/build/uart_check/keil_build.log`。这些被Git忽略，换电脑重新构建。

待现场验证：断电导通与供电电压、实际复位窗口无驱动、20kHz／15%波形、A/B轮侧与方向、低占空比能否起转、500ms撤输出、运行中按键停止、IWDG实际行为、滑行停稳时间及三步不循环。未初始化编码器、未实现闭环或整车驱动适配，板级／台架结果尚未归档。

## 2026-10-20 C-02B-R1：启动阻塞修复的电脑验证

主控现场已确认原版下载Verify OK，但停机截图显示PVU=1、执行停在watchdog_init调用的IWDG_GetFlagStatus、毫秒为0。上述C-02B编译与逻辑测试没有覆盖硬件启动链路，不能据此认定原版已正常运行。原始证据、依据及R1完整文件清单见[故障交接与修复记录](motor_bench_startup_issue.md)。本轮由01只做应用层修复、编译与电脑验证，**未烧录、访问板卡、接电池或试转，实物症状是否排除仍待主控确认**。

修复顺序为TIM5时基检查→LSI限时就绪→IWDG_Enable→解锁／配置PR、RLR→限时等待PVU／RVU→Reload。每段等待用独立TIM5的名义1MHz计数限时10ms，不用尚未启动的SysTick；TIM5计数不动还有有限轮询保护。初始化错误粘性锁存、保持ABORTED及零驱动，不能通过按键重新启动。保留IWDG、20kHz／15%／500ms与原触发和锁定语义，TIM1／3／4资源不变；官方库未改动。

| 项目 | 实际检查与结果 | 范围／限制 |
| --- | --- | --- |
| 修复前回归复现 | 新测试先运行原main，实际失败：stuck at PVU before IWDG_Enable; ms=0, SysTick=0, output=0 | 模型强制未Enable时更新标志不清，用测试轮询预算捕获永久等待；与现场路径相符，模型不是实板 |
| 修复后启动检查 | `run_motor_bench_startup_tests.ps1`：154条断言／10场景全部通过，实际调用main、watchdog_init和SysTick_Handler | 正常／计数回绕、LSI卡住及回绕、PVU卡住、RVU卡住、两标志卡住及回绕、TIM5从不计数、等待中TIM5停计数、错误时钟；验证SysTick启动前完成或有限退出、IWDG先启动、故障不能触发与零输出 |
| 原台架／通信回归 | `run_motor_bench_tests.ps1` 73项、`run_host_tests.ps1` 55项全部通过 | 原人工序列、停止锁定和通信逻辑保留；电脑不测电气输出 |
| MotorBench编译链接 | Keil5.24a／ARMCC5.06u5：0错误0警告，Code4672、RO424、RW48、ZI1048字节 | 使用原SPL工程和独立目标，没有把测试替身加入Keil |
| 既有三目标与UART分支 | LogicDemo、HardwareBench、BoardSelfTest及临时UART开启分支均0错误0警告，大小与原记录一致 | 未修改原入口／board／通信源文件，不增加UART依赖 |
| 官方库及证据完整性 | source_manifest.json所列官方文件SHA256全部匹配；原停机截图SHA256仍为e7b98d1a3238ef4681131928febc5a637dae83219d045e7ac9cbb68f2e203e2c | R1没有修改官方库；保留原故障证据 |

实际红／绿输出：

```text
FAIL startup: stuck at PVU before IWDG_Enable; ms=0, SysTick=0, output=0
PASS MotorBench startup: 154 checks in 10 hardware-model scenarios (real main/SysTick; no board access)
PASS motor bench: 73 checks (manual sequence, debounce, stop, timeout, wrap, lockout)
PASS all 55 checks
```

本次新BIN为**5144字节**，SHA256为`9c165244e60585d5c9a9fbaf882dc4964a56c7c046a808ecfa37a66539c036dd`；原版4672字节／8593c996…仅作为故障历史。新AXF、HEX、BIN均在`control/firmware/build/motor_bench/`，各文件完整哈希见[修复记录产物表](motor_bench_startup_issue.md)。Watch版本值为`g_motor_bench_revision=0x020B0001`。当前版本仍为main、HEAD `82640aba4cf7aa4f30db14b486aef852936118fe`加本地未提交修改，保留已有工作区成果，未切分支、提交或上传。

最终文档／产物核对：7份更新文档的89个本地链接存在，11份本轮编写文件无行尾空白，git diff --check通过；16个官方来源文件哈希匹配，四个Keil目标保留且未包含测试替身；新AXF／HEX／BIN实际大小及哈希与交付表一致，原现场截图未改动。原board.c／board.h／main.c／car.c／protocol.c／board_self_test.c无Git差异。

日志在`control/build/motor_bench_startup_red.log`、`motor_bench_startup_tests.log`、`motor_bench_tests.log`、`host_tests.log`与各Keil目标构建日志，均是Git忽略的本地产物。复现新启动检查可运行`powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/run_motor_bench_startup_tests.ps1 -Compiler C:/software/mingw64/bin/gcc.exe`，GCC运行依赖目录需在PATH中；此命令只编译运行电脑模型，不访问板卡。正常使用不要求主控打开终端。

待主控按[纯Keil复验步骤](motor_bench.md)重新编译、下载并保留新Verify日志，退出调试后真正断电重启，电池始终拔开。实物验收必须取得：毫秒持续增长、fault=0、松键后READY、PB2用户灯每组闪1次；自主启动视频与运行中Watch分别留证。模型不能验证实际PVU／RVU同步、LSI／TIM5频率、看门狗复位时长、复位高阻窗口或真实引脚低电平，台架及实车仍未通过。

## 2026-10-21 C-02B-R2：固定30%起转诊断的电脑验证

主控已回报绿灯正常，KEY长按松开后进入每组2闪待B，但电机未转；确认接线正确、现场无万用表。保留[原15%不转记录](../../testing/2026-10-21_motor_bench/no_rotation_record.md)，不将低占空比认定为已证实根因。R2只把固定输出从150‰改为300‰并更新版本，保留20kHz／500ms、A→B→AB人工序列及全部R1启动／停止保护。完整端口、使能链路、修改清单与产物表见[R2交付记录](motor_bench_r2_task.md)。

| 项目 | 本轮实际结果／边界 |
| --- | --- |
| PWM源码核对 | PE9／PE11／PE13／PE14分别TIM1_CH1–4、AF1，PWM1高有效、普通通道CCxE开启；初始化MOE关闭，触发时写CCR并UG→切AF→开MOE；停止关MOE、CCR归0、四脚GPIO主动低。未发现确切配置不一致，不等于实物波形通过 |
| 固定参数／ARM产物 | HSI／APB2名义16MHz、PSC=0、ARR=799，20kHz；CCR=800×300／1000=240。新AXF反汇编在motor_bench_pwm_apply的0x08000E50为MOVS r5,#0xF0，按mask传给Compare1／3，Compare2／4为0；500ms原逻辑未改 |
| MotorBench编译 | Keil5.24a／ARMCC5.06u5，0错误0警告；Code4672、RO424、RW48、ZI1048。仅重编译受影响目标；原三目标与UART分支本轮未重编译，沿用R1记录并核对源码／工程配置未变 |
| 启动回归 | `run_motor_bench_startup_tests.ps1`：154条断言／10场景通过，仅更新版本期望为0x020B0002；不能模拟真实电气起转 |
| 原逻辑回归 | `run_motor_bench_tests.ps1` 73项、`run_host_tests.ps1` 55项全部通过；无新增宏值镜像测试 |
| R1与停止保护保留 | 开工副本对比main仅改版本赋值及同行注释；watchdog_init、TIM5超时、SysTick故障、异常停止不变，motor_bench.c／motor_bench.h不变，PWM停止／初始化／apply可执行源码不变 |
| BIN与向量 | 新旧R1／R2均5144字节，仅偏移0xDA4的01→02、0xE50的78→F0变化，对应版本与120→240比较值；SP=0x20000448、Reset=0x0800019D布局通过 |

本轮实际输出：

```text
PASS MotorBench startup: 154 checks in 10 hardware-model scenarios (real main/SysTick; no board access)
PASS motor bench: 73 checks (manual sequence, debounce, stop, timeout, wrap, lockout)
PASS all 55 checks
```

新版本字段`g_motor_bench_revision=0x020B0002`。R2 BIN SHA256：`99b03ae743aa1021aeb5cb49192f2b24771e30d0872a577b17b3b29bbbd1d967`，完整AXF／HEX哈希见[R2产物表](motor_bench_r2_task.md)。R1的9c165244…为15%历史产物；两版大小相同，不能仅凭大小确认30%。编译／电脑日志路径沿用上一节，本轮覆盖为R2实际输出；开工R1产物和源码副本在被忽略的`control/build/c02b_r2_baseline/`，反汇编在`control/build/c02b_r2_disassembly.txt`。

本轮只保存本地未提交修改，没有访问板卡、烧录、接电池、试转或上传。主控按[纯Keil步骤第12节](motor_bench.md)下载、无动力确认版本及待机、退出调试后，首轮只触发A一次。真实30%／20kHz波形、供电、起转、500ms撤输出和机械停稳仍待现场；仍不转／仅抖动即关驱动拔电池，不继续B／AB、不重复触发或再加功率，后续由硬件借仪表补测。电脑验证不能替代这些实物项目。

最终范围及文档检查：相对R2开工副本只变更11份预定文件，7份更新文档的104个本地链接存在，行尾空白及git diff --check通过；16份官方来源哈希匹配，新AXF／HEX／BIN大小与交付哈希一致。原Keil工程及其余已记录文件保持原字节。核对摘要为本地忽略输出`control/build/c02b_r2_checks.json`。

## 2026-10-21 C-02B-R3：保留实际输出寄存器的诊断验证

现场R2 Verify OK、绿灯正常、驱动电源灯亮但A完全无动作／无声音的反馈见[原记录](../../testing/2026-10-21_motor_bench/no_rotation_record.md)，不视为电气定位完成。R3保持30%／20kHz／500ms、原端口、R1及人工停止保护，只增加事件时的只读诊断。应用与字段语义、完整产物哈希见[R3交付](motor_bench_r3_task.md)，纯Keil无动力采集和判定表见[操作说明第13节](motor_bench.md)。

| 检查 | 本轮实际结果／限制 |
| --- | --- |
| 新诊断集成回归 | `run_motor_bench_pwm_diag_tests.ps1`实际通过131项／8场景：真实main、SysTick、状态机及PWM实现，SPL／寄存器边界为模型。覆盖KEY→A→500ms、活动与停止分开保留、重复mask去重、KEY／fault／非法mask停止、下一轮配对、ms回绕及未启用valid0 |
| 真实读回语义 | 故意扰动模型的PSC／ARR／CCR／CCER／AFRH／IDR、使MOE不置位，活动帧原样记录差异且启用调用数1／MOE读回数0；另使停止MOE不清，停止帧如实显示异常。能区分完整采集与配置符合，未用期望常量代替寄存器 |
| 原回归 | 启动154项／10场景、台架73项、协议55项全部通过。已有启动测试加上下文空替身和新版本期望，测试假头增加TIM重复计数字段；不影响官方库 |
| MotorBench编译 | Keil5.24a／ARMCC5.06u5，0错误0警告，Code5208、RO424、RW64、ZI1288字节。原三目标与UART分支无变化，本轮未重编译，不扩大本轮编译范围 |
| 原行为／实际加载 | 开工副本与R1时钟、TIM5／watchdog_init段逐字一致；纯状态机及Keil项目未变。capture反汇编读取0x40010000的TIM1、0x40021000的GPIOE和RCC时钟寄存器，读完再写valid1；映射表保留244字节volatile诊断结构 |

实际输出：

```text
PASS PWM retained diagnostics: 131 checks in 8 real-main/PWM model scenarios (no board access)
PASS MotorBench startup: 154 checks in 10 hardware-model scenarios (real main/SysTick; no board access)
PASS motor bench: 73 checks (manual sequence, debounce, stop, timeout, wrap, lockout)
PASS all 55 checks
```

R3版本0x020B0003，BIN5696字节，SHA256：`d09c4095c55eb34607d012c36611b239b6d24c00d2451497f925e812e994e0d8`；AXF397136字节、HEX16071字节，完整SHA256见R3交付表。新日志在`control/build/motor_bench_pwm_diag_tests.log`及原回归日志、`control/firmware/build/MotorBench_build.log`，R2输入与产物保留于`control/build/c02b_r3_baseline/`，反汇编在`control/build/c02b_r3_disassembly.txt`；均是本地忽略输出。

没有板卡访问、烧录、接电池或试转。本轮主控只在动力电池拔开、驱动OFF、UC2断开时用Keil F5持续运行，KEY一次A结束后取快照，不在500ms窗口暂停。当前尚无R3实板数据；模型无法判定实际TIM/GPIO输出、电压、真实频率、额外采集的板上耗时或不转根因。即使实板快照配置符合，也只能证明板内路径，后续外部供电／输入／输出仍由I-05补仪表证据。

最终核对：R3范围为11份修改和3份新增，14份编写文件无行尾空白，6份文档103个本地链接存在，git diff --check通过；16个官方来源哈希匹配，原Keil工程四目标、R2历史及其余开工记录保持原字节，测试替身不进Keil。新产物大小／哈希匹配，BIN向量SP=0x20000548、Reset=0x0800019D布局通过；摘要`control/build/c02b_r3_checks.json`。末次补充中文函数注释后重新编译通过，仅AXF调试哈希变化，已更新交付表；不重复运行未改变逻辑的已通过检查。

## 2026-10-24 MotorDirect：固定GPIO单次500ms的电脑验证

主控暂时无法去实验室，要求不用PWM快速检查电机是否能转。新增独立MotorDirect，版本0x020B2001；保留原九线，SPL普通GPIO使PE9高、PE11／13／14低，只A人工一次500ms后COMPLETE锁定，再按KEY可提前停止并锁定。不启动TIM1，不设置AF或CCR；保留R1的TIM5启动时基、IWDG和故障零输出。固定电平相当于满导通，强于原30%PWM；仍经过驱动板，不转不能独立判定电机坏。完整操作、文件及哈希见[MotorDirect说明](motor_direct.md)。

| 检查 | 实际结果／范围 |
| --- | --- |
| 新GPIO集成 | `run_motor_direct_tests.ps1`第一组：9个真实main／SysTick／GPIO场景通过，52593次断言含循环SPL边界检查，不代表独立场景数。验证499／500ms、只A、KEY／故障／非法阶段与非法请求、锁定不续跑、毫秒回绕、长按松开门槛、读回扰动及错误时钟拒绝置高；替身禁止AF、APB2时钟和非PE9电机脚置高 |
| 新入口R1启动 | 同脚本第二组154项／10场景通过：使用实际新入口，覆盖正常、LSI／PVU／RVU卡住、TIM5异常、错误时钟及回绕；不依赖未启动SysTick超时 |
| 原回归 | MotorContinuous模型113项／7场景及启动154项／10场景，R3保留诊断131项／8场景，原台架73项通过。通信源未变，协议55项沿用历史记录、本轮未重跑 |
| Keil构建 | LogicDemo、HardwareBench、BoardSelfTest、MotorBench、MotorContinuous、MotorDirect六目标均0错误0警告。Direct Code3888／RO424／RW64／ZI1184字节；无板卡访问 |
| 隔离／兼容 | 初次旧目标回归发现Keil隐式共享新文件，已在原五目标显式排除两份新入口／GPIO源，修复后全部通过。除这两项排除外原五目标配置与开工相同；本机五份调试配置保持相同。新目标排除旧main／PWM且自动调试下载关闭，手动Flash Download保留 |
| 代码／产物证据 | 六段R1初始化函数归一化对比相同；真实Direct AXF反汇编包含GPIO置位／复位，无AF／PWM输出比较／CCR／MOE调用。16份官方来源哈希匹配，原MotorBench及MotorContinuous BIN／HEX逐字节相同；AXF调试容器重建变化已分别注明 |

Direct BIN4376字节，SHA256 `6377f00d7f9ff812a6d22ccd5c86217cd0b694092a8dce7cdc6eadb0b134fc9a`。AXF384656字节，SHA256 `125e0bf676c3f160cf76418db79c719463e5a9a078ffc3d61571622fa60db288`；HEX12365字节，SHA256 `a6e5c5ff52b64597de72fbc3bc3c321a25a9f2c931f04d6b8c01a0e82b7b4fff`。路径为`control/firmware/build/motor_direct/`，纯Keil选MotorDirect后手动下载AXF，不要求主控使用终端。

开工工程及旧产物留存`control/build/motor_direct_baseline/`；新测试、启动日志位于`control/build/motor_direct*_tests.log`，六目标日志位于`control/firmware/build/`，反汇编／最终检查摘要为`control/build/motor_direct_disassembly.txt`、`motor_direct_checks.json`；均为本地忽略输出。原持续版Watch三图及历史不转反馈继续保留，不将本次模型视为根因复现或实物修复。

待主控：电池拔开纯Keil下载Verify、独立重启、无动力一次KEY确认500ms后慢闪锁定；通过后先断动力复位，悬空固定、退出调试，只一次A短时动作，再OFF拔电池。仍不转／仅抖动停止试验，不继续B／AB或延长；编码器／电流／温度／真实排针电平／输出电压／机械停稳未验证。仅本地保存，没有切分支、提交、上传、自动烧录、接电池或试转。

2026-10-24工程入口修复：主控反馈没有MotorDirect，实际磁盘工程只有五目标、Keil路径正确；覆盖来源未确定。已保留现场工程／uvoptx至control/build/motor_direct_entry_repair，恢复多目标工程，并新增[单目标独立入口](../MDK-ARM/motor_direct.uvprojx)，沿用同一源码、宏、输出和已验证CMSIS-DAP配置。独立入口实际编译0错误0警告，Code3888／RO424／RW64／ZI1184。源码未变、BIN／HEX哈希未变；当前AXF调试哈希更新为142e7ccb7c3bc37dab12c979e391ab7fa3ae398c47e308a8549523a26f2c5d11，原125e0bf6…为前次构建历史。以入口修复前快照核对原五目标配置保留；没有重新运行未受影响的固件模型，没有烧录、操作板卡或上传。
