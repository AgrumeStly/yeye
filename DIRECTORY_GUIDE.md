# 项目目录与文件用途说明

核对日期：2026-10-14（北京时间）。依据主控台式机 `D:\Projects\yeye` 的实际文件编写。

本文供主控、视觉、硬件共同阅读，集中解释各层级的文件夹、文件用途和维护方式。正式文件逐项说明；大量重复的编译产物、预览图和工具包内部文件按名称或类型归类。

这是本地目录快照，包含尚未上传的文件和被 Git 忽略的本机文件，因此 GitHub 或主控笔记本不一定具有全部内容。新增、移动或删除正式文件后，应同步维护本文。

## 1. 从根目录理解整个项目

```text
yeye/
├── DIRECTORY_GUIDE.md               当前这份完整目录说明
├── README.md                       项目首页与主要资料入口
├── AGENTS.md                       Codex 在本项目中的工作规则
├── .gitignore                      整个仓库的忽略规则
├── .gitattributes                  文件换行、二进制等 Git 属性
├── skills-lock.json                技能安装来源与版本校验记录
├── .agent/
│   └── skill/                      项目技能的正式内容
├── .agents/
│   └── skills/                     Codex 发现项目技能的入口
├── .git/                           Git 版本历史与仓库内部数据
├── competition/                    官方比赛资料
├── project_planning/
│   └── source/                     规划与协作教程的生成脚本
├── hardware_preparation/
│   ├── source/                     硬件文档生成器及清单数据
│   └── archive/                    已被替代的硬件方案
├── control/
│   ├── docs/                       主控使用方法与技术约定
│   ├── firmware/
│   │   ├── src/                    主控应用代码
│   │   ├── include/                主控接口与配置头文件
│   │   ├── startup/                芯片启动代码
│   │   ├── vendor/
│   │   │   ├── cmsis/              Cortex-M4 内核支持头文件
│   │   │   ├── stm32/              STM32 设备定义头文件
│   │   │   └── stdperiph/
│   │   │       ├── inc/            标准外设库接口头文件
│   │   │       └── src/            标准外设库驱动实现
│   │   ├── DebugConfig/            Keil 本机调试配置
│   │   └── build/                  单片机编译输出与日志
│   ├── tests/                      电脑端主控逻辑测试代码
│   ├── tools/                      日常编译、测试与配置工具
│   └── build/                      电脑端测试输出及模拟协议包
├── vision/
│   ├── reference_code/             尚未形成车载工程的 C 参考代码
│   ├── references/                 视觉算法参考文档
│   └── data/                       视觉输入样本
├── testing/                        整车联调和测试证据
├── report/                         报告、答辩与最终提交材料
└── tmp/
    ├── pdfs/
    │   └── references/             文档制作使用的参考图片
    ├── screenshots/                页面截图
    ├── board_tools/
    │   ├── dfu_util/               USB DFU 下载工具及其分发文件
    │   └── st_driver/              STM32 Bootloader 驱动文件
    └── skill_install_backup/       技能安装调整前的备份
```

| 根目录文件 | 用途 | 阅读或维护方式 |
| --- | --- | --- |
| `DIRECTORY_GUIDE.md` | 所有层级的用途索引，解释正式内容与本机文件 | 三人查找文件时先看本文；目录变化后更新 |
| `README.md` | 项目首页，提供规划、教程及比赛资料入口 | 三人快速了解项目；完整细节以对应文件为准 |
| `AGENTS.md` | 规定角色称呼、文件位置、技能使用、中文注释和上传授权 | Codex 执行项目任务前遵守；项目规则变更时维护 |
| `.gitignore` | 指定临时目录、编译输出、本机配置等不默认纳入 Git | 主控维护；它不会自动移除已经被 Git 跟踪的文件 |
| `.gitattributes` | 统一文本换行，并标识 PDF、表格、图片等二进制文件 | 主控维护；用于减少跨电脑的无意义差异 |
| `skills-lock.json` | 保存技能来源、路径与哈希，帮助追溯安装内容 | 工具配置记录；当前被根目录忽略规则排除 |

## 2. competition/：比赛以什么要求验收

该目录保存主办方资料。正式规则与后续通知属于此处，团队排期和建议属于 `project_planning/`。

| 文件 | 用途 | 主要阅读角色 |
| --- | --- | --- |
| `README.md` | 说明比赛资料的存放范围 | 三人 |
| `比赛文档.pdf` | 保存原始比赛要求、评分、赛道和赛程信息 | 三人；规划或验收时核对原文与后续通知 |

## 3. project_planning/：任务、进度和协作方法

| 文件 | 用途 | 内容维护入口 |
| --- | --- | --- |
| `README.md` | 本目录的导航与文档更新说明 | 导航变化时更新 |
| `project_plan.pdf` | 可阅读、打印的执行计划，含分工、里程碑、截止日期及验收要求 | 对应生成器 |
| `project_plan.md` | 规划书的文字版，方便搜索和查看差异 | 与生成器保持一致，避免重新生成后丢失修改 |
| `team_work_outline.pdf` | 主控、视觉、硬件的职责及阶段分工概览 | 对应生成器 |
| `github_collaboration_guide.pdf` | 21 页 GitHub Desktop 入门手册，含分支、提交、同步、PR 与冲突处理 | 对应 Markdown 正文 |
| `github_collaboration_guide.md` | GitHub 手册的可编辑内容源 | 先修改正文，再生成 PDF |

### source/：这些 PDF 如何生成

| 文件 | 用途 |
| --- | --- |
| `generate_project_plan.py` | 生成 `project_plan.pdf` 和 `project_plan.md`；规划内容由脚本组织 |
| `generate_team_outline.py` | 生成 `team_work_outline.pdf`，包含分工文字与排版 |
| `generate_github_guide.py` | 读取 `github_collaboration_guide.md`，生成带分页、示意图、书签与链接的 PDF |

这里的 `source/` 是文档生成器，单片机程序位于 `control/firmware/src/`。修改文档时先确认各文档的内容源，重新生成后检查正文、页码和排版。

规划和教程保存的是制定时的安排与设置，不能代替最新状态。例如仓库目前已公开，GitHub 教程中仍存在先前的私有仓库说明；主控工程的最新实现与实测进度应查看 `control/README.md` 和测试记录。

## 4. hardware_preparation/：采购、供电、接线和实物记录

硬件负责实物、供电与装配资料；主控和视觉共同核对相关接口。采购记录说明购买安排，测试记录说明实际验证结果，两者不能互相替代。

| 文件 | 用途 |
| --- | --- |
| `README.md` | 硬件资料导航、历史方案与采购状态说明 |
| `hardware_modules_overview.pdf` | 按视觉、控制、通信、驱动、机械、供电等模块整理准备项 |
| `hardware_purchase_list.pdf` | 既有详细采购方案，含型号、数量、预算与说明；实际到货以订单和验收为准 |
| `purchase_list_control.pdf` | 主控负责采购的清单 |
| `purchase_list_vision.pdf` | 视觉负责采购的清单 |
| `purchase_list_hardware.pdf` | 硬件负责采购的清单，含接线与紧固件准备 |
| `control_bringup_plan.md` | 主控硬件到齐后的实施顺序：核物、下载、串口、电机、编码器、闭环及视觉联调 |
| `board_self_test_record.md` | 2026-10-14 天空星主控板首次测试的实际结果，含下载、读回校验和用户灯表现；未测功能明确列出 |

### source/：硬件文档的内容源

| 文件 | 用途 |
| --- | --- |
| `generate_modules_overview.py` | 生成模块级准备清单 PDF |
| `generate_purchase_list.py` | 生成详细采购方案 PDF |
| `purchase_bom.json` | 详细采购方案的数据，含器件、数量、规格和估算费用 |
| `generate_team_purchase_lists.py` | 生成主控、视觉、硬件各自的采购清单 PDF |
| `team_purchase_allocation.json` | 保存各项器件数量与采购角色分配，供清单生成器使用 |

### archive/：已被替代的方案

| 文件 | 用途 |
| --- | --- |
| `hardware_list_600CNY_preliminary.pdf` | 早期预算方案，用于追溯历史，不作为当前实物接线依据 |
| `generate_600CNY_preliminary.py` | 对应早期预算方案的生成器 |
| `hardware_list_697CNY_superseded.pdf` | 被替代的另一版硬件方案 |
| `generate_697CNY_superseded.py` | 对应被替代方案的生成器 |
| `layout_draft_697CNY.tex` | 该历史方案的 LaTeX 排版草稿 |

后续正式接线图、照片和装配记录仍放本目录，按需要增加英文子目录。历史文件保留版本依据，当前工作优先阅读最新实物记录。

## 5. control/：主控代码、工程、说明和测试

主控维护该目录；视觉阅读协议和编码示例，硬件阅读引脚与板级测试说明。现有工程可以演示通信与状态机，并已有独立板级自检；电机 PWM、编码器及速度闭环等整车功能尚未完整实现。

| 文件 | 用途 |
| --- | --- |
| `README.md` | 当前主控状态、Keil 工程入口、已完成范围与后续接入边界 |
| `stm数据手册.pdf` | STM 相关参考资料；具体器件和引脚信息应核对正文是否适用于实物 |
| `.gitignore` | 补充忽略 Keil 本机调试状态、构建日志和临时 UART 检查工程等文件 |
| `.gitattributes` | 为第三方源码保留原有格式，并标记库代码，减少无关格式变动 |

### 5.1 docs/：先理解操作和约定

| 文件 | 解决的问题 | 主要阅读角色 |
| --- | --- | --- |
| `keil_quickstart.md` | Keil 环境、目标选择、编译与调试操作 | 主控 |
| `standard_library.md` | SPL 标准外设库的组成与代码阅读方法 | 主控；硬件参考 |
| `protocol_v1_draft.md` | 视觉到主控的 20 字节包布局、单位、符号、序号、CRC 和异常处理 | 主控、视觉；硬件核对电平 |
| `state_machine.md` | 待机、运行、停止、故障之间的转换，以及当前控制边界 | 主控、视觉 |
| `pin_plan.md` | UART、编码器、驱动及 SWD 的资源候选；未确认项不能直接当正式接线表 | 主控、硬件 |
| `validation.md` | 已执行的软件检查及对应结果、验证范围 | 三人 |
| `board_self_test.md` | BoardSelfTest 编译、双闪含义、USB DFU 下载及复测方法 | 主控、硬件 |

### 5.2 firmware/：Keil 单片机工程

| 文件或名称模式 | 用途 | 维护方式 |
| --- | --- | --- |
| `yeye_control.uvprojx` | 正式 Keil 工程：保存目标、芯片、文件分组、宏、包含路径和编译选项 | 主控维护；换电脑打开此文件 |
| `yeye_control.uvoptx` | Keil 本机调试选项，可由 `tools/setup_debug.ps1` 初始化 | 通常不入库；已有本机设置不直接覆盖 |
| `yeye_control.uvguix.*` | 各电脑用户的 Keil 窗口布局等界面状态 | 本机文件，通常不入库 |
| `yeye_uart_check.uvprojx` | `check_uart_build.ps1` 生成的 UART 开启编译检查工程 | 临时验证用；日常仍打开正式工程 |
| `yeye_uart_check.uvoptx`、`yeye_uart_check.uvguix.*` | 临时检查工程对应的本机调试与界面状态 | 通常不入库 |

一个工程内有不同编译目标，并非所有入口文件同时作为 `main()` 编译：

| 工程目标 | 入口文件 | 用途 |
| --- | --- | --- |
| `LogicDemo` | `src/logic_demo.c` | 不操作真实外设，模拟协议包与状态转换，适合无硬件学习 |
| `HardwareBench` | `src/main.c` | 板上主循环框架，接收字节、解析通信并定时更新状态；默认 UART 关闭，电机请求仍是调试变量 |
| `BoardSelfTest` | `src/board_self_test.c` | 独立点灯和基础自检目标，已有首次实物运行记录 |

#### src/：项目编写的应用代码

| 文件 | 用途 | 与其他文件的关系 |
| --- | --- | --- |
| `main.c` | HardwareBench 主入口：初始化，读取串口，解析包，约每 5 ms 调度状态机并交付左右请求 | 调用 `board.c`、`protocol.c`、`car.c` |
| `board.c` | 板级适配：时钟、SysTick、UART 接收及错误处理、左右请求输出接口 | 对上提供 `board.h`；底层调用 SPL 与 CMSIS |
| `protocol.c` | 20 字节包编码、CRC16、字段校验、逐字节滑窗解析和错误包恢复 | 实现 `protocol.h` 中的接口；解析通过才交给状态机 |
| `car.c` | 启停与故障状态机，检查路径有效性、序号和超时，计算演示用左右请求 | 使用解析后的协议数据；当前不是完整速度 PID 或电机驱动 |
| `logic_demo.c` | 向解析器注入模拟包，检查启动、停止、坏包和超时，用调试变量展示结果 | LogicDemo 独立入口；不依赖实际串口和电机 |
| `board_self_test.c` | PB2 用户灯双闪、16 MHz 软件配置值检查、128 字节专用 RAM 区域自检 | BoardSelfTest 独立入口；使用板级初始化与滴答 |

#### include/：对外接口、类型和配置

`.h` 定义可供其他代码使用的接口和数据类型，`.c` 实现具体行为。修改协议或函数时，需要同步相关头文件和说明。

| 文件 | 用途 |
| --- | --- |
| `board.h` | 板级函数声明、UART 启用开关和可观察的调试变量 |
| `car.h` | 车辆状态、停车原因、状态结构、超时阈值及状态机函数声明 |
| `protocol.h` | 包类型、标志、命令、字段结构、解析器结构及协议函数声明 |
| `stm32f4xx_conf.h` | SPL 配置入口，集中包含当前使用的外设模块并配置参数断言 |

#### startup/：进入 C 程序之前的启动过程

| 文件 | 用途 |
| --- | --- |
| `startup_stm32f407xx.s` | STM32F407 汇编启动文件，提供中断向量及复位入口，衔接系统初始化与 C 运行环境 |
| `LICENSE.txt` | 随启动代码保存的第三方许可说明 |

#### vendor/：工程携带的第三方依赖

这些文件让工程能够使用标准内核定义和外设驱动。应用逻辑优先在 `src/`、`include/` 中修改；库文件按其版本与来源维护，许可文件随库保留。

| 文件 | 用途 |
| --- | --- |
| `vendor/README.md` | 记录 CMSIS、设备头文件、SPL 与启动代码的来源、固定版本及许可位置 |
| `vendor/cmsis/core_cm4.h` | Cortex-M4 内核寄存器和内核操作接口，如 SysTick、NVIC |
| `vendor/cmsis/cmsis_compiler.h` | 按编译器选择对应的 CMSIS 适配头文件 |
| `vendor/cmsis/cmsis_armcc.h` | ARM Compiler 5 的关键字与内核操作适配 |
| `vendor/cmsis/cmsis_armclang.h` | ArmClang 编译器适配 |
| `vendor/cmsis/cmsis_gcc.h` | GCC 编译器适配 |
| `vendor/cmsis/LICENSE.txt` | CMSIS 的第三方许可 |
| `vendor/stm32/stm32f4xx.h` | STM32F4 设备、寄存器、位定义和中断编号，供外设库与应用使用 |
| `vendor/stm32/system_stm32f4xx.h` | 系统初始化和时钟变量、更新函数的声明；本工程实际初始化实现需结合 `board.c` 等入口阅读 |
| `vendor/stm32/LICENSE.txt` | 设备头文件随附的许可说明 |
| `vendor/stdperiph/source_manifest.json` | 当前引入的标准库文件来源与哈希记录，便于核对原始依赖 |
| `vendor/stdperiph/Release_Notes.html` | 标准外设库版本发布说明 |
| `vendor/stdperiph/LICENSE.pdf` | 标准外设库许可 |

`vendor/stdperiph/inc/` 与 `vendor/stdperiph/src/` 按模块对应：

| 头文件 | 实现文件 | 用途 |
| --- | --- | --- |
| `stm32f4xx_rcc.h` | `stm32f4xx_rcc.c` | 系统与外设时钟配置、使能和复位接口 |
| `stm32f4xx_gpio.h` | `stm32f4xx_gpio.c` | GPIO 模式、输入输出和复用功能配置 |
| `stm32f4xx_usart.h` | `stm32f4xx_usart.c` | 串口参数、收发、状态标志和中断接口 |
| `misc.h` | `misc.c` | NVIC 中断配置等辅助接口 |

#### DebugConfig/：Keil 保存的本机配置

现有 `LogicDemo_STM32F407VETx.dbgconf`、`HardwareBench_STM32F407VETx.dbgconf`、`BoardSelfTest_STM32F407VETx.dbgconf` 和 `Bench_STM32F407VETx.dbgconf` 均属于本机调试配置。文件名对应当前或历史目标，不意味着工程现在存在四个正式目标。该目录被忽略，迁移时按目标与下载器重新核对。

#### build/：单片机编译产物

`control/firmware/build/` 保存主控固件的输出，现有 `logic/`、`uart_check/`、`board_test/` 子目录分别保存逻辑演示、UART 编译检查和板级自检的产物。根部还保存 HardwareBench 等编译结果及部分历史产物。

| 文件或类型 | 用途 |
| --- | --- |
| `*.axf` | 包含程序和调试信息的链接结果，供 Keil 调试或下载使用 |
| `*.hex`、`*.bin` | 可用于相应下载工具的固件格式；必须确认对应目标、生成时间和程序版本 |
| `*.o` | 各源文件编译出的目标文件，等待链接 |
| `*.d`、`*.dep` | 构建依赖记录，帮助工具判断哪些文件需要重新编译 |
| `*.map` | 链接地址、段分布与内存占用报告 |
| `*.lst` | 汇编列表等编译辅助输出 |
| `*.sct` | 链接使用的存储区布局文件，当前输出目录中的文件由构建流程产生 |
| `*.lnp` | 链接器调用参数文件 |
| `*.htm`、`*.build_log.htm`、`keil_build.log` | 构建结果、内存信息或编译日志 |
| `logic/verify_sim.ini` | 自动验证 LogicDemo 时使用的模拟器命令文件 |
| `uart_check/uart_check.uvprojx` | 历史 UART 检查流程留下的临时工程副本 |
| `*.Bak` | 构建过程留下的备份文件 |

该目录通常不纳入 Git。日常修改源代码后重新编译；正式发布固件应与明确的源代码提交和参数绑定，单独归档，不能把旧输出误当最新版本。

### 5.3 tests/：电脑端逻辑检查

| 文件 | 用途 |
| --- | --- |
| `test_control.c` | 在电脑上检查 CRC、编码、流式解析、异常包、序号、启动条件及状态转换，无需连接单片机 |

电脑测试覆盖程序逻辑，实车供电、串口接线、电机行为与停车效果由实物测试验证。

### 5.4 tools/：可重复使用的主控辅助工具

| 文件 | 用途 | 使用角色 |
| --- | --- | --- |
| `build_keil.ps1` | 按所选目标调用 Keil 编译并检查日志；只编译，不烧录 | 主控 |
| `check_uart_build.ps1` | 生成临时检查工程，打开 UART 宏验证编译；原正式工程仍保持原配置 | 主控 |
| `run_host_tests.ps1` | 用电脑端 C 编译器构建并运行 `tests/test_control.c`，保存测试日志 | 主控 |
| `setup_debug.ps1` | 首次生成本机 Keil 调试设置；已有设置时保留 | 主控 |
| `debug_options.xml` | 上述脚本使用的可移植调试默认模板 | 主控 |
| `protocol_example.py` | Python 参考编码器，生成路径和命令的二进制包及十六进制文本；不自动发送串口 | 视觉、主控 |

### 5.5 build/：电脑端输出，与 firmware/build/ 区分

| 文件或目录 | 用途 |
| --- | --- |
| `test_control.exe` | 电脑运行的测试程序，不能烧录到 STM32 |
| `host_tests.log` | 电脑端测试的执行结果 |
| `protocol_samples/` | Python 编码器生成的模拟通信包目录 |
| `protocol_samples/path_valid.bin` | 有效路径包示例 |
| `protocol_samples/path_invalid.bin` | 无效路径包示例 |
| `protocol_samples/start.bin` | 启动命令包示例 |
| `protocol_samples/stop.bin` | 停止命令包示例 |
| `protocol_samples/status.bin` | 状态查询命令包示例；不表示已实现应答 |

同样是 `.bin`，这里的是串口数据样例，`firmware/build/board_test/board_self_test.bin` 才是板级自检固件；不能仅凭扩展名选择烧录文件。

## 6. vision/：视觉参考、样本与后续实现

| 文件或目录 | 用途 |
| --- | --- |
| `README.md` | 视觉目录导航与新增正式程序的存放约定 |
| `PORTING_REVIEW.md` | 原 C 示例的移植审查、问题清单、K230D 实现建议与验证范围 |
| `reference_code/` | 原始算法参考；当前不是可直接在 CanMV 运行的完整程序 |
| `reference_code/image.h` | 参考算法的类型、分辨率、数组及接口定义 |
| `reference_code/image.c` | 图像复制、阈值分割、二值化、追边、边界和显示等参考实现；采集与显示依赖原平台 |
| `reference_code/十字补线和最小二乘法.c` | 线性拟合、十字识别及补线参考片段，不代表比赛必做功能 |
| `references/` | 视觉算法辅助资料 |
| `references/智能车图像处理辅助文档V2.0.pdf` | 原参考代码的原理、移植要求和效果示例 |
| `data/` | 单模块离线输入样本，供算法验证和回放 |
| `data/图像.xlsx` | 现有 60×94 二值图像表格样例，不等同于实拍赛道数据 |

视觉新增正式程序可按约定放 `vision/src/`，语音程序放 `vision/audio/`；截至核对日期，这两个目录尚未创建。模型、样本与代码分别记录来源、用途和运行方法。

## 7. testing/ 与 report/：证据和最终表达

| 文件或目录 | 用途 | 主责 |
| --- | --- | --- |
| `testing/README.md` | 整车测试记录的存放与字段约定，建议按日期和轮次建立目录 | 三人；主控汇总 |
| `report/README.md` | 报告、插图、答辩和正式提交包的存放约定 | 三人；主控汇总 |

`testing/` 当前只有导航文件，后续跨模块联调、试跑与停车证据归档到此处。首次主控板自检记录已保存在 `hardware_preparation/board_self_test_record.md`，不能因 `testing/` 暂无记录就认为所有实物均未测试。

`report/` 当前尚无正式报告。后续可按需要新增 `source/`、`assets/`、`release/`、`archive/`，分别保存生成器、插图、最终提交包和旧稿；这些目录目前只是约定。

## 8. .agent/ 与 .agents/：项目技能内容和发现入口

这两个隐藏目录用于 Codex 工作流程，赛车程序不依赖它们运行。

| 层级 / 文件 | 用途 |
| --- | --- |
| `.agent/skill/` | 项目技能正式存放位置 |
| `.agent/skill/grill-me/SKILL.md` | 默认任务入口：先判断需求是否明确，重大未决方案按需访谈，清晰任务直接执行 |
| `.agent/skill/grill-me/agents/openai.yaml` | grill-me 的技能显示与调用元数据 |
| `.agent/skill/grilling/SKILL.md` | 明确要求 grilling 时使用的深入访谈工作流 |
| `.agent/skill/grilling/agents/openai.yaml` | grilling 的技能显示与调用元数据 |
| `.agents/skills/` | Codex 发现项目技能的入口目录，当前被根目录 Git 忽略规则排除 |
| `.agents/skills/grill-me/SKILL.md` | 指向正式 grill-me 技能内容的入口说明 |
| `.agents/skills/grill-me/agents/openai.yaml` | 对应发现入口的显示与调用元数据 |
| `.agents/skills/grilling/SKILL.md` | 指向正式 grilling 技能内容的入口说明 |
| `.agents/skills/grilling/agents/openai.yaml` | 对应发现入口的显示与调用元数据 |

技能正文以 `.agent/skill/` 为准，发现入口负责引导到正文。代码下载到另一台电脑后，被忽略的入口不保证随 Git 同步，应核对该电脑的技能配置。

## 9. .git/：Git 管理的版本历史

该隐藏目录让本地项目成为 Git 仓库。由 Git 和 GitHub Desktop 管理，三人日常通过提交、切分支、拉取等操作使用它，不手动编辑内部数据。

| 层级 / 文件 | 用途 |
| --- | --- |
| `HEAD` | 记录当前检出的分支或提交位置 |
| `config` | 本仓库的 Git 配置，包括远端连接信息等 |
| `index` | 暂存区数据，记录下一次提交准备包含的文件状态 |
| `COMMIT_EDITMSG` | 最近提交说明的编辑记录 |
| `FETCH_HEAD` | 最近 Fetch 获取的远端引用记录 |
| `description` | Git 仓库描述字段，不是项目业务说明 |
| `refs/` | 分支、标签和远端跟踪引用；内部名称由实际分支与标签决定 |
| `objects/` | 文件内容、目录树与提交对象；大量哈希文件由 Git 自动管理 |
| `logs/` | 引用变化日志，用于追踪分支与 HEAD 的移动 |
| `hooks/` | Git 操作钩子及示例脚本 |
| `info/` | 本仓库附加信息，例如本地排除配置 |

换电脑通过 Clone 获取项目历史，不通过覆盖 `.git/` 同步。删除该目录会破坏这份本地副本的版本管理信息。

## 10. tmp/：制作过程、工具缓存与本地原始证据

整个 `tmp/` 被 Git 忽略。多数文件可重新生成，但其中已有烧录前 Flash 备份和原始日志；清理前必须逐项确认来源与副本，不能把目录名称当作可全部删除的依据。

### 10.1 根部说明、文档检查与历史辅助脚本

| 文件 | 用途 |
| --- | --- |
| `README.md` | 临时目录的存放与清理约定 |
| `check_github_roles.py` | 检查 GitHub PDF 页数、正文称呼、书签、链接和文字边界，并生成检查拼图 |
| `revise_github_roles.py` | 历史称呼改写脚本，已对特定旧正文执行；日常应修改正式 Markdown 正文 |
| `check_control_files.py` | 主控文件、工程配置与相关结果的制作期检查 |
| `check_spl_change.py` | SPL 切换时的来源、工程和代码一致性检查 |
| `create_control_project.py` | 初次建立主控工程的制作脚本 |
| `fix_control_xml.py` | 制作过程中调整 Keil 工程 XML 的脚本 |
| `normalize_keil_schema.py` | 按 Keil XML 结构要求整理工程文件的制作脚本 |
| `configure_spl_project.py` | 将工程配置为 SPL 版本的制作脚本 |
| `create_board_test_target.py` | 向工程加入 BoardSelfTest 目标的制作脚本 |
| `prepare_f407.py` | F407 工程依赖与设备包准备脚本 |
| `fetch_f4_spl.py` | 获取标准库来源包的准备脚本 |
| `inspect_spl.py` | 检查来源包内容的辅助脚本 |
| `install_spl_subset.py` | 从来源包提取工程所需标准库文件，并记录来源与校验信息 |
| `run_keil_sim.py` | 自动验证 Keil 逻辑演示的制作期脚本 |
| `probe_flash_tools.py` | 查找 USB 下载工具来源的准备脚本 |
| `fetch_dfu_tools.py` | 获取并准备 DFU 下载工具文件 |
| `flash_board_test.py` | 首次板级测试的备份、写入、读回及比较流程；运行会涉及实物 Flash 操作 |
| `open_control_pr.py` | 历史创建主控 PR 的辅助脚本，涉及 GitHub 远端操作 |
| `update_control_pr.py` | 历史更新主控 PR 的辅助脚本，涉及 GitHub 远端操作 |
| `set_repository_public.py` | 将仓库改为公开并验证访问的历史脚本，涉及远端设置 |
| `control_pr_body.md` | 主控 PR 说明的制作期文字稿 |
| `spl_source.txt` | 本机选用的标准库来源包路径记录 |
| `Keil.STM32F4xx_DFP.1.0.8.pack` | 提取匹配 SPL 源码使用的设备包缓存 |
| `Keil.STM32F4xx_DFP.2.17.1.pack` | 当前 Keil 环境使用的设备包安装缓存 |
| `stm32_driver_catalog.html` | 查找 STM32 驱动时保存的网页资料 |

这些脚本记录项目建立过程，部分固定了本机路径，部分会修改工程、硬件或 GitHub。日常操作优先使用 `control/tools/` 与正式说明；重新使用历史脚本前核对其实际内容和适用阶段。远端上传仍以主控对当前改动的明确要求为准。

### 10.2 pdfs/：预览图与参考素材

| 文件或名称模式 | 用途 |
| --- | --- |
| `github_guide-01.png` 至 `github_guide-21.png` | GitHub 手册逐页渲染的检查图 |
| `github_contact_*.jpg` | 初版手册的多页排版拼图 |
| `github_roles_contact_*.jpg` | 角色称呼修订后的多页排版拼图 |
| `github_guide_final-21.png` | 手册末页的专门检查图 |
| `project_plan-*.png` | 项目规划书逐页预览 |
| `purchase-*.png` | 采购方案逐页预览 |
| `hardware_600_preview-*.png` | 历史预算方案预览 |
| `course-2.png`、`rules-4.png`、`赛道.png` | 比赛与赛道相关的制作期图片 |
| `vision_reference-05.png` | 视觉参考文档的页面检查图 |
| `references/` | 历史文档制作使用的参考图片；保留前核对原始来源，清理前确认其他副本 |

PDF 正式成果位于业务目录；预览图用于检查，不能替代对应正式文档。

### 10.3 screenshots/ 与 skill_install_backup/

| 文件 | 用途 |
| --- | --- |
| `screenshots/github_repository.jpg` | GitHub 仓库页面的历史截图，不反映实时状态 |
| `skill_install_backup/grill-me.SKILL.md` | 调整技能前的 grill-me 内容备份 |
| `skill_install_backup/grilling.SKILL.md` | 调整技能前的 grilling 内容备份 |

### 10.4 board_tools/：DFU 下载工具与首次烧录证据

| 文件或层级 | 用途 |
| --- | --- |
| `dfu-util-0.11-binaries.tar.xz` | dfu-util 工具分发压缩包 |
| `dfu_util/dfu-util-0.11-binaries/` | 工具包解压后的文件及随包资料 |
| 上述目录中的 `win32/`、`win64/` | 对应 Windows 位数的可执行工具与配套文件；本次使用 win64 工具 |
| `st_driver/Driver/` | 下载的 ST Bootloader 驱动和签名等配套文件，内部内容以官方包为准 |
| `install_st_dfu.ps1` | 本次安装 DFU 驱动的辅助脚本，涉及电脑驱动配置 |
| `driver_install.log` | 驱动安装原始日志 |
| `driver_install_exit.txt` | 驱动安装进程的退出结果 |
| `flash_before_test.bin` | 本次测试写入前读取的 512 KiB Flash 备份；需要保留，不能用新备份覆盖 |
| `flash_backup.log` | 烧录前备份的操作日志 |
| `flash_write.log` | 自检固件写入操作日志 |
| `flash_readback.bin` | 写入后读取的固件内容，用于逐字节比较 |
| `flash_verify.log` | 固件读回过程的日志 |
| `flash_result.json` | 写入与读回的结果汇总和校验数据 |

三人共享阅读的结果已整理在 `hardware_preparation/board_self_test_record.md`。本目录中的原始备份和日志没有通过 Git 自动同步；主控需要在换电脑或清理前另行保留必要副本。

## 11. 三人查找与维护文件的顺序

| 角色 / 任务 | 优先入口 | 成果位置 |
| --- | --- | --- |
| 主控学习和编译 | `control/README.md` → `control/docs/keil_quickstart.md` | 代码放 `control/firmware/`，说明放 `control/docs/` |
| 主控与视觉对接 | `control/docs/protocol_v1_draft.md` → `control/tools/protocol_example.py` | 协议修改同步代码、说明和测试 |
| 视觉实现算法 | `vision/README.md` → `vision/PORTING_REVIEW.md` | 正式程序按约定新增 `vision/src/`；输入样本放 `vision/data/` |
| 硬件验收与接线 | `hardware_preparation/README.md` → 当前实施计划与实测记录 | 供电、装配、接线和单板验收放 `hardware_preparation/` |
| 三人整车联调 | `testing/README.md` | 实测日志、参数、照片与录像索引放 `testing/` |
| 三人排期与分工 | `project_planning/README.md` | 任务、会议决定与进度放 `project_planning/` |
| 三人报告与答辩 | `report/README.md` | 正式报告与最终包放 `report/`，引用已保存的测试证据 |

文件后缀速查：`.md` 是文字说明，`.pdf` 是阅读或打印版，`.py` 是 Python 工具或生成器，`.ps1` 是 PowerShell 工具，`.json` 是结构化数据，`.c/.h` 是 C 实现与接口，`.s` 是汇编，`.uvprojx` 是 Keil 工程。相同后缀可能有不同用途，尤其 `.bin` 需要结合所在目录判断。

新增文件夹使用英文名称。正式文件按业务类别保存；编译输出和预览图留在生成目录；硬件旧方案放 `hardware_preparation/archive/`。本地修改默认先保存并验证，上传当前改动须由主控明确提出。
