# 项目目录与内容源

更新：2026-10-25（北京时间）。维护：00，模块负责人提供变更。
用途：说明文件放哪里、该读哪个入口；当前完成情况只维护在[状态页](project_planning/project_status.md)。整理前逐文件快照已[归档](project_planning/archive/2026-10-25_directory_guide_snapshot.md)。

## 1. 目录按业务划分

```text
yeye/
├── README.md                       主控和团队日常入口
├── AGENTS.md                       Codex长期规则
├── DIRECTORY_GUIDE.md              本目录和内容源说明
├── docs/                           架构、引脚、硬件、接口、任务、测试主题入口
├── competition/                    官方规则、通知、报名凭据
├── project_planning/
│   ├── README.md                   管理资料导航
│   ├── collaboration_standard.md   职责登记、事实源、交接规则
│   ├── project_status.md           全项目当前摘要和任务索引
│   ├── agent_initialization_prompts.md  四个对话的完整接续文本
│   ├── version_handoff.md          Git和实际设备版本记录
│   ├── organization_review.md      本次审查、迁移与检查范围
│   ├── tasks/                     多轮/跨对话任务与结果，同一任务一份
│   ├── source/                    规划和教程生成器
│   └── archive/                   历史状态流水、目录快照
├── hardware_preparation/           采购历史、实际接线、供电与装配资料
│   ├── source/                    硬件文档生成源及派生JSON
│   ├── evidence/                  原始照片、厂商资料与来源索引
│   └── archive/                   被替代硬件方案及其生成器
├── control/
│   ├── README.md                  主控工程与能力入口
│   ├── Core/                      各目标入口、SPL配置、启动汇编
│   ├── App/                       车辆与诊断状态逻辑
│   ├── Drivers_Custom/            自编Board／Motor／Communication
│   ├── Drivers/                   原版CMSIS、STM32定义和SPL
│   ├── Algorithms/                后续纯算法；目前只有范围说明
│   ├── Tests/Host/                电脑模型、逻辑测试和fakes
│   ├── MDK-ARM/                   Keil工程和本机调试配置
│   ├── docs/                      操作说明、协议、资源、软件验证
│   ├── firmware/                  旧本机产物／日志，非当前工程入口
│   ├── tools/                     日常编译/检查/调试配置工具
│   └── build/                     电脑输出；firmware子目录存新ARM构建
├── vision/
│   ├── README.md                  视觉和语音交付入口
│   ├── PORTING_REVIEW.md           历史移植审查
│   ├── reference_code/             C参考，非正式CanMV车载工程
│   ├── references/                 算法PDF资料
│   └── data/                      离线样本
├── testing/                       按日期归档的现场证据及结果
├── report/                        报告、答辩与最终提交物
├── .agent/skill/                   项目技能正式源
├── .agents/skills/                 本机技能发现入口，被Git忽略
└── tmp/                           被忽略的制作过程、缓存及历史原始附件
```

视觉正式程序需要时建立`vision/src/`和`vision/audio/`；报告需要时建立`source/`、`assets/`、`release/`、`archive/`。这些是放置约定，不表示目录或成果已经存在。新目录用英文名称，业务说明使用中文。

## 2. 同一项信息只维护一处

| 内容 | 写入位置 | 其它地方怎样引用 |
| --- | --- | --- |
| 跨模块任务目标、边界和详细结果 | 新任务放`project_planning/tasks/<ID>.md`；已有任务记录可沿用原位置 | 状态页一行摘要，Prompt给路径 |
| 当前全局状态和优先级 | `project_planning/project_status.md` | 首页和目录只给链接 |
| MCU协议／软件资源／实物接线 | 原`protocol_v1_draft.md`／`pin_plan.md`／`wiring.md` | 协作标准链接，不抄参数 |
| 应用源码与测试源码 | `control/Core/`、`App/`、`Drivers_Custom/`、`Tests/Host/` | 技术页解释实现与限制；纯算法后续放Algorithms |
| 软件构建、模型验证摘要 | `control/docs/validation.md` | 详细本轮日志／哈希按任务链接 |
| 实物过程、测量、失败和复测 | `testing/YYYY-MM-DD_topic/` | 任务单和报告引用原证据 |
| 硬件原始资料和首次板级记录 | 已有`hardware_preparation/evidence/`及板级记录 | 沿用路径，不因新分类强制搬迁 |
| 采购模型、预算和分配历史 | 硬件PDF及其源 | 实际采用情况查接线/清点，不重写采购日期 |
| 报告和提交包 | `report/` | 源码仍在模块，测试仍在testing |
| 可重建输出 | `build/`、`tmp/` | 需要复现时注明生成命令和环境 |
| 唯一原图、Flash备份、原始实测日志 | 既有位置先保留，交接中明确另存方式 | 不凭所在目录将其视为可删缓存 |

软件`src/`保存可运行实现，文档目录的`source/`保存生成器。数据样例`.bin`与固件`.bin`用途不同，必须结合目录和目标确认。

## 3. Keil工程与本机状态

| 路径／类型 | 用途 |
| --- | --- |
| [yeye_control.uvprojx](control/MDK-ARM/yeye_control.uvprojx) | 正式多目标工程；六目标为LogicDemo、HardwareBench、BoardSelfTest、MotorBench、MotorContinuous、MotorDirect |
| [motor_direct.uvprojx](control/MDK-ARM/motor_direct.uvprojx) | 仅MotorDirect的独立入口，复用同一源码与输出目录 |
| `control/Core/`、`App/`、`Drivers_Custom/` | 入口、应用与自编适配；新增修改按AGENTS写详细中文注释 |
| `control/Core/Startup/`、`control/Drivers/` | 芯片启动、CMSIS、STM32定义、SPL；保留固定版本、来源、许可和清单 |
| `control/build/firmware/` | 新ARM固件、链接与构建日志；旧firmware/build仅留历史产物 |
| `control/build/` | 电脑测试程序、日志和协议样例；电脑EXE不能烧录 |
| `*.uvoptx`、`*.uvguix.*`、`DebugConfig/` | 被忽略的本机调试和界面状态，换设备另核对 |
| `yeye_uart_check.uvprojx` | 工具生成的UART编译检查工程，非日常主入口 |

`LogicDemo`用于学习逻辑；`HardwareBench`仍有运动适配边界；`BoardSelfTest`只做板级自检；三个电机目标是诊断程序。具体操作和验证范围查[主控入口](control/README.md)，不能按目标名推定整车可运行。

ORG-02已同步迁移源码、Keil、工具、电脑测试和文档引用；[完整映射与验证](project_planning/tasks/ORG-02.md)为旧路径接续依据。资料生成器、规格与原始实测证据未搬动。正式内容变化后同步模块README；完整逐文件历史无需复制进每轮Prompt。

## 4. PDF和生成内容如何维护

| 实际内容源 | 输出 | 注意 |
| --- | --- | --- |
| `project_planning/source/generate_project_plan.py`内正文 | 规划MD和PDF | 不能只改生成MD |
| `project_planning/source/generate_team_outline.py` | 分工PDF | 源中路径和现有PDF有轻微历史差异，见审查记录 |
| `project_planning/github_collaboration_guide.md` | 同名PDF | `source/generate_github_guide.py`读取正文 |
| `hardware_preparation/source/generate_purchase_list.py`内BOM/正文 | 详细采购PDF、`purchase_bom.json` | JSON是生成产物 |
| `hardware_preparation/source/generate_team_purchase_lists.py`，读BOM | 三人采购PDF、`team_purchase_allocation.json` | 分配规则在脚本，JSON是产物 |
| `hardware_preparation/source/generate_modules_overview.py` | 模块概览PDF | 历史准备方案 |
| `hardware_preparation/archive/`内生成器与TeX | 旧方案 | 仅溯源；部分脚本会写回硬件根目录，运行前核对 |

修改PDF内容时先修改正确源，再重生成并检查正文和排版。本轮未修改这些生成源、PDF或原始赛事文件。

## 5. Git、技能与临时内容

`.git/`由Git维护；`.gitignore`排除本机状态、工具、原始录像与生成输出；`.gitattributes`管理文本换行和二进制属性。文件被忽略不说明可删除，也不说明另一设备已收到。

项目技能正文在`.agent/skill/`；`.agents/skills/`仅为本机发现入口，未保证经Git同步。接续先按AGENTS直接读取正式技能路径，避免维护两套正文。

`tmp/board_tools/`已有首次烧录前Flash备份与原始日志，`tmp/pdfs/references/`有历史制作素材；保持原位，清理前核对其它副本。本次调查与检查中间件在`tmp/organization_audit/`，正式结论已放项目管理目录。历史远端/烧录脚本只作溯源，运行前重新核对范围和当前授权。
