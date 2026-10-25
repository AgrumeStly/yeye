# ORG-02：STM32主控物理目录分层

日期：2026-10-25（北京时间）。主状态：待验收（本地迁移与电脑检查完成，Keil人工使用体验待主控）。
执行：本轮体系整理对话；后续主控开发由01维护，00接收全局结果。

## 本轮要求与确认

主控在ORG-01后给出Core／App／Drivers_Custom／Algorithms／Tests／MDK-ARM及docs示例，要求实际重新组织文件夹。主控随后明确选择：“推荐：control内分层，保留整车模块边界”。

因此本轮授权包含主控工程的物理迁移及必要路径适配，替代ORG-01仅改管理资料时的工程原位限制；没有授权更换SPL／Keil、改变固件行为、上传远端、跨聊天发送或操作板卡。项目目录仍为D:/Projects/yeye，没有重命名工作区或建立第二份工程。

## 交付与分层

- [docs/README.md](../../docs/README.md)：根文档主题入口。
- [architecture.md](../../docs/architecture.md)：完整结构、六目标与层级职责。
- [pinmap.md](../../docs/pinmap.md)、[hardware.md](../../docs/hardware.md)、[interfaces.md](../../docs/interfaces.md)、[tasks.md](../../docs/tasks.md)、[test-log.md](../../docs/test-log.md)：统一查找，不复制另一份协议或全局状态。
- [control/README.md](../../control/README.md)：当前唯一主控工程入口和目录。
- [MDK-ARM/yeye_control.uvprojx](../../control/MDK-ARM/yeye_control.uvprojx)：原六目标。
- [MDK-ARM/motor_direct.uvprojx](../../control/MDK-ARM/motor_direct.uvprojx)：原单目标独立入口。

Core放入口／SPL配置／启动，App放车辆与诊断逻辑，Drivers_Custom放Board／Motor／Communication，Drivers保留CMSIS／STM32定义／SPL，Tests/Host放原电脑测试，Algorithms当前只存范围说明。保留car.c、board.c等原文件名和函数；没有制造PID、Encoder、Sensor、tracking或CubeMX.ioc。

本轮不是应用行为重构：应用C／H／启动汇编原字节保留；4份电脑测试只更新6处直接包含真实.c的相对路径；fake目录内部引用和优先搜索次序保留。两个工程的非路径编译设置、宏、逐文件IncludeInBuild和六目标入口隔离不变。

## 迁移、保存与边界

迁移前保存当前dirty工作区181份非忽略文件及本机调试配置、旧BIN和目标构建基线，未使用reset／stash／强推或覆盖其它工作。本机两个uvoptx、uvguix与DebugConfig随工程迁移，原CMSIS-DAP／Flash／Watch设置保留。

新ARM输出在control/build/firmware；原control/firmware/build和旧UART临时工程保留作历史本机产物。新旧Direct入口仍共享同一新输出目录，不能并行构建。旧firmware只留下缓存与迁移说明，没有复制第二份应用源码。

协议／引脚规格、硬件接线、testing原图和原始读数路径未移动；所有文档显式指向已迁移文件的链接已重定向。历史任务中的原路径标签、版本与失败结果保留，通过下表定位新文件。ORG-01的归档内容原有链接仅作本轮迁移适配，不把历史测试日期改写为本轮结果。

控制脚本、Git忽略／厂家换行属性、SPL来源清单project_path同步更新。厂商archive_path和SHA256原值保留。standard_library与Drivers README中原“TIM/IWDG仅MotorBench”的旧文字同步校正为实际三个诊断目标，未改库依赖或初始化。

## 完整文件映射（68项，含本机调试文件）

| 整理前路径 | 现行路径 |
| --- | --- |
| `control/firmware/DebugConfig/Bench_STM32F407VETx.dbgconf` | `control/MDK-ARM/DebugConfig/Bench_STM32F407VETx.dbgconf` |
| `control/firmware/DebugConfig/BoardSelfTest_STM32F407VETx.dbgconf` | `control/MDK-ARM/DebugConfig/BoardSelfTest_STM32F407VETx.dbgconf` |
| `control/firmware/DebugConfig/HardwareBench_STM32F407VETx.dbgconf` | `control/MDK-ARM/DebugConfig/HardwareBench_STM32F407VETx.dbgconf` |
| `control/firmware/DebugConfig/LogicDemo_STM32F407VETx.dbgconf` | `control/MDK-ARM/DebugConfig/LogicDemo_STM32F407VETx.dbgconf` |
| `control/firmware/DebugConfig/MotorBench_STM32F407VETx.dbgconf` | `control/MDK-ARM/DebugConfig/MotorBench_STM32F407VETx.dbgconf` |
| `control/firmware/DebugConfig/MotorContinuous_STM32F407VETx.dbgconf` | `control/MDK-ARM/DebugConfig/MotorContinuous_STM32F407VETx.dbgconf` |
| `control/firmware/DebugConfig/MotorDirect_STM32F407VETx.dbgconf` | `control/MDK-ARM/DebugConfig/MotorDirect_STM32F407VETx.dbgconf` |
| `control/firmware/EventRecorderStub.scvd` | [control/MDK-ARM/EventRecorderStub.scvd](../../control/MDK-ARM/EventRecorderStub.scvd) |
| `control/firmware/include/board.h` | [control/Drivers_Custom/Board/board.h](../../control/Drivers_Custom/Board/board.h) |
| `control/firmware/include/car.h` | [control/App/Car/car.h](../../control/App/Car/car.h) |
| `control/firmware/include/motor_bench.h` | [control/App/Diagnostics/motor_bench.h](../../control/App/Diagnostics/motor_bench.h) |
| `control/firmware/include/motor_bench_pwm.h` | [control/Drivers_Custom/Motor/motor_bench_pwm.h](../../control/Drivers_Custom/Motor/motor_bench_pwm.h) |
| `control/firmware/include/motor_direct_gpio.h` | [control/Drivers_Custom/Motor/motor_direct_gpio.h](../../control/Drivers_Custom/Motor/motor_direct_gpio.h) |
| `control/firmware/include/protocol.h` | [control/Drivers_Custom/Communication/protocol.h](../../control/Drivers_Custom/Communication/protocol.h) |
| `control/firmware/include/stm32f4xx_conf.h` | [control/Core/Inc/stm32f4xx_conf.h](../../control/Core/Inc/stm32f4xx_conf.h) |
| `control/firmware/motor_direct.uvguix.ShiduanTian` | `control/MDK-ARM/motor_direct.uvguix.ShiduanTian` |
| `control/firmware/motor_direct.uvoptx` | `control/MDK-ARM/motor_direct.uvoptx` |
| `control/firmware/motor_direct.uvprojx` | [control/MDK-ARM/motor_direct.uvprojx](../../control/MDK-ARM/motor_direct.uvprojx) |
| `control/firmware/src/board.c` | [control/Drivers_Custom/Board/board.c](../../control/Drivers_Custom/Board/board.c) |
| `control/firmware/src/board_self_test.c` | [control/Core/Src/board_self_test.c](../../control/Core/Src/board_self_test.c) |
| `control/firmware/src/car.c` | [control/App/Car/car.c](../../control/App/Car/car.c) |
| `control/firmware/src/logic_demo.c` | [control/Core/Src/logic_demo.c](../../control/Core/Src/logic_demo.c) |
| `control/firmware/src/main.c` | [control/Core/Src/main.c](../../control/Core/Src/main.c) |
| `control/firmware/src/motor_bench.c` | [control/App/Diagnostics/motor_bench.c](../../control/App/Diagnostics/motor_bench.c) |
| `control/firmware/src/motor_bench_main.c` | [control/Core/Src/motor_bench_main.c](../../control/Core/Src/motor_bench_main.c) |
| `control/firmware/src/motor_bench_pwm.c` | [control/Drivers_Custom/Motor/motor_bench_pwm.c](../../control/Drivers_Custom/Motor/motor_bench_pwm.c) |
| `control/firmware/src/motor_direct_gpio.c` | [control/Drivers_Custom/Motor/motor_direct_gpio.c](../../control/Drivers_Custom/Motor/motor_direct_gpio.c) |
| `control/firmware/src/motor_direct_main.c` | [control/Core/Src/motor_direct_main.c](../../control/Core/Src/motor_direct_main.c) |
| `control/firmware/src/protocol.c` | [control/Drivers_Custom/Communication/protocol.c](../../control/Drivers_Custom/Communication/protocol.c) |
| `control/firmware/startup/LICENSE.txt` | [control/Core/Startup/LICENSE.txt](../../control/Core/Startup/LICENSE.txt) |
| `control/firmware/startup/startup_stm32f407xx.s` | [control/Core/Startup/startup_stm32f407xx.s](../../control/Core/Startup/startup_stm32f407xx.s) |
| `control/firmware/vendor/README.md` | [control/Drivers/README.md](../../control/Drivers/README.md) |
| `control/firmware/vendor/cmsis/LICENSE.txt` | [control/Drivers/cmsis/LICENSE.txt](../../control/Drivers/cmsis/LICENSE.txt) |
| `control/firmware/vendor/cmsis/cmsis_armcc.h` | [control/Drivers/cmsis/cmsis_armcc.h](../../control/Drivers/cmsis/cmsis_armcc.h) |
| `control/firmware/vendor/cmsis/cmsis_armclang.h` | [control/Drivers/cmsis/cmsis_armclang.h](../../control/Drivers/cmsis/cmsis_armclang.h) |
| `control/firmware/vendor/cmsis/cmsis_compiler.h` | [control/Drivers/cmsis/cmsis_compiler.h](../../control/Drivers/cmsis/cmsis_compiler.h) |
| `control/firmware/vendor/cmsis/cmsis_gcc.h` | [control/Drivers/cmsis/cmsis_gcc.h](../../control/Drivers/cmsis/cmsis_gcc.h) |
| `control/firmware/vendor/cmsis/core_cm4.h` | [control/Drivers/cmsis/core_cm4.h](../../control/Drivers/cmsis/core_cm4.h) |
| `control/firmware/vendor/stdperiph/LICENSE.pdf` | [control/Drivers/stdperiph/LICENSE.pdf](../../control/Drivers/stdperiph/LICENSE.pdf) |
| `control/firmware/vendor/stdperiph/Release_Notes.html` | [control/Drivers/stdperiph/Release_Notes.html](../../control/Drivers/stdperiph/Release_Notes.html) |
| `control/firmware/vendor/stdperiph/inc/misc.h` | [control/Drivers/stdperiph/inc/misc.h](../../control/Drivers/stdperiph/inc/misc.h) |
| `control/firmware/vendor/stdperiph/inc/stm32f4xx_gpio.h` | [control/Drivers/stdperiph/inc/stm32f4xx_gpio.h](../../control/Drivers/stdperiph/inc/stm32f4xx_gpio.h) |
| `control/firmware/vendor/stdperiph/inc/stm32f4xx_iwdg.h` | [control/Drivers/stdperiph/inc/stm32f4xx_iwdg.h](../../control/Drivers/stdperiph/inc/stm32f4xx_iwdg.h) |
| `control/firmware/vendor/stdperiph/inc/stm32f4xx_rcc.h` | [control/Drivers/stdperiph/inc/stm32f4xx_rcc.h](../../control/Drivers/stdperiph/inc/stm32f4xx_rcc.h) |
| `control/firmware/vendor/stdperiph/inc/stm32f4xx_tim.h` | [control/Drivers/stdperiph/inc/stm32f4xx_tim.h](../../control/Drivers/stdperiph/inc/stm32f4xx_tim.h) |
| `control/firmware/vendor/stdperiph/inc/stm32f4xx_usart.h` | [control/Drivers/stdperiph/inc/stm32f4xx_usart.h](../../control/Drivers/stdperiph/inc/stm32f4xx_usart.h) |
| `control/firmware/vendor/stdperiph/source_manifest.json` | [control/Drivers/stdperiph/source_manifest.json](../../control/Drivers/stdperiph/source_manifest.json) |
| `control/firmware/vendor/stdperiph/src/misc.c` | [control/Drivers/stdperiph/src/misc.c](../../control/Drivers/stdperiph/src/misc.c) |
| `control/firmware/vendor/stdperiph/src/stm32f4xx_gpio.c` | [control/Drivers/stdperiph/src/stm32f4xx_gpio.c](../../control/Drivers/stdperiph/src/stm32f4xx_gpio.c) |
| `control/firmware/vendor/stdperiph/src/stm32f4xx_iwdg.c` | [control/Drivers/stdperiph/src/stm32f4xx_iwdg.c](../../control/Drivers/stdperiph/src/stm32f4xx_iwdg.c) |
| `control/firmware/vendor/stdperiph/src/stm32f4xx_rcc.c` | [control/Drivers/stdperiph/src/stm32f4xx_rcc.c](../../control/Drivers/stdperiph/src/stm32f4xx_rcc.c) |
| `control/firmware/vendor/stdperiph/src/stm32f4xx_tim.c` | [control/Drivers/stdperiph/src/stm32f4xx_tim.c](../../control/Drivers/stdperiph/src/stm32f4xx_tim.c) |
| `control/firmware/vendor/stdperiph/src/stm32f4xx_usart.c` | [control/Drivers/stdperiph/src/stm32f4xx_usart.c](../../control/Drivers/stdperiph/src/stm32f4xx_usart.c) |
| `control/firmware/vendor/stm32/LICENSE.txt` | [control/Drivers/stm32/LICENSE.txt](../../control/Drivers/stm32/LICENSE.txt) |
| `control/firmware/vendor/stm32/stm32f4xx.h` | [control/Drivers/stm32/stm32f4xx.h](../../control/Drivers/stm32/stm32f4xx.h) |
| `control/firmware/vendor/stm32/system_stm32f4xx.h` | [control/Drivers/stm32/system_stm32f4xx.h](../../control/Drivers/stm32/system_stm32f4xx.h) |
| `control/firmware/yeye_control.uvguix.ShiduanTian` | `control/MDK-ARM/yeye_control.uvguix.ShiduanTian` |
| `control/firmware/yeye_control.uvoptx` | `control/MDK-ARM/yeye_control.uvoptx` |
| `control/firmware/yeye_control.uvprojx` | [control/MDK-ARM/yeye_control.uvprojx](../../control/MDK-ARM/yeye_control.uvprojx) |
| `control/tests/fakes/motor_bench_pwm/stm32f4xx.h` | [control/Tests/Host/fakes/motor_bench_pwm/stm32f4xx.h](../../control/Tests/Host/fakes/motor_bench_pwm/stm32f4xx.h) |
| `control/tests/fakes/motor_bench_startup/stm32f4xx.h` | [control/Tests/Host/fakes/motor_bench_startup/stm32f4xx.h](../../control/Tests/Host/fakes/motor_bench_startup/stm32f4xx.h) |
| `control/tests/fakes/motor_direct/stm32f4xx.h` | [control/Tests/Host/fakes/motor_direct/stm32f4xx.h](../../control/Tests/Host/fakes/motor_direct/stm32f4xx.h) |
| `control/tests/test_control.c` | [control/Tests/Host/test_control.c](../../control/Tests/Host/test_control.c) |
| `control/tests/test_motor_bench.c` | [control/Tests/Host/test_motor_bench.c](../../control/Tests/Host/test_motor_bench.c) |
| `control/tests/test_motor_bench_pwm_diag.c` | [control/Tests/Host/test_motor_bench_pwm_diag.c](../../control/Tests/Host/test_motor_bench_pwm_diag.c) |
| `control/tests/test_motor_bench_startup.c` | [control/Tests/Host/test_motor_bench_startup.c](../../control/Tests/Host/test_motor_bench_startup.c) |
| `control/tests/test_motor_direct.c` | [control/Tests/Host/test_motor_direct.c](../../control/Tests/Host/test_motor_direct.c) |
| `control/tests/test_motor_direct_startup.c` | [control/Tests/Host/test_motor_direct_startup.c](../../control/Tests/Host/test_motor_direct_startup.c) |

## 实际检查结果

### 源码与工程等价

- 38份应用／第三方C、H和启动汇编迁移后与本轮开工字节一致；原厂家清单16项SHA256逐项通过。原许可文件随来源保留。
- 两份Keil工程分别6目标和1目标；所有文件和IncludePath存在。除路径与构建状态字段外，设备／编译宏／优化／逐文件选项均与迁移前一致。
- 两份本机uvoptx除PathWithFileName／ListingPath外逐节点等价，保留CMSIS-DAP、Flash和Watch设置。
- 电脑测试4文件的6处真实.c包含路径适配后，去除这些路径文本的正文与开工一致；没有改测试断言、场景或硬件fake行为。

### 构建与电脑模型

迁移前：六个原Keil目标＋UART开启HardwareBench均0错误0警告。

迁移后：同六目标＋UART开启HardwareBench＋MotorDirect独立工程均0错误0警告。

原有六个电脑测试脚本全部通过，共八组测试程序：

| 程序／范围 | 实际结果 |
| --- | --- |
| 协议／车辆状态机 | 55项通过 |
| MotorBench纯逻辑 | 73项通过 |
| MotorBench真实入口启动 | 154项／10场景通过 |
| R3真实入口／PWM诊断 | 131项／8场景通过 |
| MotorContinuous诊断 | 113项／7场景通过 |
| MotorContinuous启动 | 154项／10场景通过 |
| MotorDirect GPIO集成 | 52593次边界断言／9场景通过；断言次数不代表独立场景数 |
| MotorDirect启动 | 154项／10场景通过 |

### 固件内容对比

六目标均由本轮迁移前、迁移后实际构建的AXF导出BIN，和各自HEX逐字节比较；全部相同：

| 目标 | BIN字节 | BIN SHA256 |
| --- | --- | --- |
| LogicDemo | 2296 | 0930b637a613157c81948bf3f5a4e281714e8f5e21e7669617f4cd3df50f92eb |
| HardwareBench | 2572 | b35740085b044cdc52351fcaa9db925135473b7cb99c272867548e36f4a81ade |
| BoardSelfTest | 1868 | 36aabc410b125cbd84284875c1d5d7836a315b181b78d7a2ceda24faef07872e |
| MotorBench | 5696 | d09c4095c55eb34607d012c36611b239b6d24c00d2451497f925e812e994e0d8 |
| MotorContinuous | 5652 | 5cd07579b14e1e50e736e2ba0553f21197d6784a305febb6402c9050a55a1eef |
| MotorDirect | 4376 | 6377f00d7f9ff812a6d22ccd5c86217cd0b694092a8dce7cdc6eadb0b134fc9a |

AXF携带源码调试路径，迁移后其哈希变化，不将历史AXF哈希当作当前文件。BIN／HEX相同及源码等价是软件迁移证据，不代替实际烧录／硬件／整车结果。

### 文档与原有工作保护

72份正式Markdown的UTF-8、代码围栏、正文冲突标记及702个显式本地链接／1个标题锚点检查通过；外部网页与PDF内部链接不在本次静态检查范围。工程和脚本没有继续指向已移走的旧应用源码。

181份开工非忽略文件逐项找到原位或映射后位置，131份内容哈希不变，其余变化限于路径适配、文档与工具配置。原有Obsidian配置、全部实物图片／读数、业务PDF与文档生成器得到保留。没有用Git旧HEAD覆盖未提交成果。

git diff --check通过，仍为main、HEAD 82640aba4cf7aa4f30db14b486aef852936118fe。检查脚本对源码字节、XML、测试包含路径和内容保护分别核对；主控人工打开新工程的体验仍待回报。

本机基线、映射、构建／测试日志和检查JSON在被忽略的tmp/layering_audit；以上为可随项目保存的摘要。没有自动上板、连接下载器、触发电机或上传GitHub。

## 仍需后续确认

- 主控在Keil手动打开新MDK-ARM路径后的目标／Watch与编辑体验，尚未回报；本轮只有命令行编译和本机配置等价检查。
- MotorDirect下载／无动力演练／起转仍待主控，不因迁移构建通过填写实物通过。
- setup_debug.ps1的旧双目标模板未扩展到六目标；当前本机配置已保留，换电脑仍须单独验证。
- 现有技术资料的其它历史问题仍按organization_review清单维护；本轮不顺带改供电、引脚或试验参数。

## 本地版本与完整交接Prompt

分支main，完整HEAD 82640aba4cf7aa4f30db14b486aef852936118fe；仍有原有及本轮未提交修改。没有切分支、提交、推送、合并或发布。

```text
接收ORG-02：主控已确认把Core/App/Drivers_Custom/Drivers/Algorithms/Tests/MDK-ARM分层放在control内，保留整车业务模块。项目D:/Projects/yeye，原有00继续总指挥，01继续固件开发。

先读取AGENTS.md、project_planning/collaboration_standard.md、project_planning/project_status.md、project_planning/tasks/ORG-02.md、docs/architecture.md、docs/interfaces.md和control/README.md。

现行工程为control/MDK-ARM/yeye_control.uvprojx，MotorDirect独立入口为同目录motor_direct.uvprojx。原六目标、SPL/ARMCC5、引脚/版本/运行保护均未变；源码和工具路径已迁移，旧firmware只留历史缓存。新输出在control/build/firmware，电脑测试在Tests/Host。没有CubeMX.ioc，PID/Encoder/Sensor尚无新实现，不能按目录认为功能完成。

本轮实际验证：六目标迁移前后及UART开启编译通过，Direct独立工程通过，现有六个测试脚本/八组程序通过；六目标BIN/HEX逐字节一致；本机uvoptx除路径外保持原配置。完整映射和检查边界在ORG-02。命令行构建没有验证Keil人工体验或实物，不要求主控重复报既定型号。

保留main、HEAD 82640aba4cf7aa4f30db14b486aef852936118fe之外全部原有与本轮未提交修改。旧ORG-01只改管理资料的路径限制由本轮明确目录迁移授权扩展；协议/引脚/接线和原始测试证据仍用原路径。

本次接续只采用新布局、核对任务文件，并按主控后续明确任务继续。00更新全局判断，01之后在新路径开发；不要重新复制旧firmware/src、旧工程或创建假HAL/CubeMX配置。MotorDirect真实起转仍未验收。

默认本地保存验证，本条不授权上传、合并、发布、跨聊天发送或板卡操作。需要转交由00生成包含新路径和当前约束的完整Prompt，不要求主控拼接旧版提示。
```
