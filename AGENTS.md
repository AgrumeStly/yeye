# Workspace preferences

- **比赛要求强制遵循 `competition/比赛文档.pdf`，可检索全文见 `competition/比赛文档.md`。** 制定需求、方案、接口、实现、测试、报告或验收标准前，必须读取相关比赛条款、赛道图和评分表；项目计划、历史约定及改进方案均须符合比赛文档。转写与原文冲突以 PDF 为准，正式补充通知须归档来源并明确替代条款；未明确的规则标记待核实，不自行补造。
- **一切改进的目的都是在符合比赛要求的前提下取得更高的比赛总分。** 每项改进必须说明对应比赛条款／评分项、预期得分收益或避免的扣分／失败风险，以及验证指标和证据；基础能力、可靠性、维护性及学习安排也须说明如何支撑比赛得分。结合完赛成功率、碰线扣分、用时、额外功能和报告评分确定优先级；不得以违背比赛要求换取速度或功能。不把队内目标、预测收益或软件检查当作官方规则或实测得分。
- Project skills are stored in `.agent/skill/`, with Codex discovery entries in `.agents/skills/`. For every project task, consult `.agent/skill/grill-me/SKILL.md` by default without requiring an explicit invocation. Use its interview workflow for material unresolved planning or design decisions; carry out clear, already-authorized work directly. Explicit `grilling` requests use `.agent/skill/grilling/SKILL.md`.
- 项目采用一个总管对话＋按可验收成果建立的执行对话，主控负责最终人工验收。总管可维护阶段路线图、任务定义、管理规则与全局摘要；不修改实现代码、执行测试、构建、烧录或操作硬件。执行对话维护实现、适用验证、任务结果及原始证据；不自行接管总管或宣布主控验收通过。
- 开始新任务时读取 `project_planning/collaboration_standard.md`、短状态 `project_planning/project_status.md` 和指定任务的当前摘要／定义／接续；后续只按任务读取相关规格和证据，规则未变时不每轮重读全部历史。任务格式见 `project_planning/tasks/README.md`。
- 交接流程：总管定义任务→主控转交→执行对话交付记录→主控明确验收→主控反馈总管→总管核对并安排下一项。软件通过仅能进入待主控验收，退回及中断换聊继续原任务ID；历史授权不自动续期。
- 新总管由主控手动新建并指定，身份登记见协作标准；旧00／01／02／03仅为历史对话来源，不要求常驻。本轮架构迁移执行者获授权更新全局管理文档，不因此成为新总管。成员责任按主控最新指派；已有记录显示主控承担视觉／语音，不能再把旧待视觉交付当作阻塞。
- 总管生成Prompt不代表已转交或已执行。默认由主控转交任务路径和验收反馈，不自动发送跨聊天消息。共享checkout默认一个执行对话写入；Keil保存、构建、切分支及硬件动作串行。工程、协议权威路径及原始证据保持原位。
- 检查按改动影响和任务结束条件选择。适用源码、配置、输入和相关环境一致时复用已有证据；新检查须说明新改动、失败或未解问题。满足任务预定验收后停止，不自动追加无依据复测。
- STM32 development uses `control/Core/`, `control/App/`, `control/Drivers_Custom/`, `control/Drivers/`, `control/Algorithms/`, `control/Tests/` and `control/MDK-ARM/`. Start from `docs/architecture.md` and `control/README.md`; preserve SPL and the six existing target behaviors. New mathematical algorithms belong in Algorithms, hardware adapters in Drivers_Custom, and application policy in App. Root `docs/` routes to existing specifications and evidence rather than duplicating parameter tables or the UART protocol.
- Save and verify changes locally by default. Push to GitHub or update remote pull requests only when 主控 explicitly requests uploading the current changes; past upload requests do not authorize automatic uploads in later tasks.
- 执行对话完成一个可交付改动及适用检查后，默认将明确属于本任务的改动做本地 Git 提交；本地提交属于已授权任务的交付步骤，无须逐次请求确认，主控明确要求暂不提交时除外。提交信息使用 `<完整任务ID>: <改动说明>`，交付报告给出分支、完整提交号、检查与待验状态及剩余未提交／未上传项。暂存前核对差异和已有暂存内容，按明确路径或改动块选择，不用全目录暂存夹带共享成果；同文件混有历史改动时只暂存本任务部分，无法安全分离时保留现场并报告范围与原因。提交不代表主控验收通过，不自动上传、合并、发布或改写历史。细则见 `project_planning/collaboration_standard.md` 的“Git 本地提交与版本交接”。
- Use English names for all new folders in this workspace. Keep existing folders English-named when reorganizing files.
- Store smart-car hardware preparation documents in `hardware_preparation/`, editable generators in `hardware_preparation/source/`, and superseded documents in `hardware_preparation/archive/`.
- In conversation and shared team documents, address members by role: 主控, 视觉, 硬件. Use explicit roles instead of first- or second-person pronouns, and identify the responsible role for role-specific steps.
- Write detailed Chinese comments in newly written or modified main application code so beginners can follow it. Document module and function purposes, parameters and units, return values, key processing steps and design reasons, boundary and error handling, and relevant hardware, interrupt, and timing constraints. Prioritize initialization, communication, state machines, and control algorithms; update comments whenever the corresponding code changes.

## 主控开发与人工验证（2026-10-23补充）

- 沿用已确认的 STM32 标准外设库（SPL）工程；改外设初始化前读取 `control/docs/standard_library.md`，保留该文档区分 SPL 外设与 CMSIS 内核支持的边界。不要仅为简化讲解迁移库或删除必要的时序/故障保护。
- 给主控的下载、调试指导优先采用当前工程的 Keil5 图形界面及已确认下载器，写清工程、目标、菜单和预期现象；确需更换链路时说明具体原因。代理自己的构建/检查仍可使用命令行。操作步骤使用实物丝印，例如 KEY，并在首次出现时注明它与 WKUP 的对应关系。

以上源自标准库和中文注释要求、Keil操作纠正及KEY称呼反馈；不改变既有职责、上传授权或技能启用状态。

## 主控试跑流程（2026-11-24更新）

- 接线及轮组沿用已归档实证时，主控要求本次及后续**跳过起始动力测试，摆车后直接口令 Go 上道跑动**。沿用已确认的编码器映射，取消默认双轮悬空及逐轮测试。
- 硬件接线或轮组安装实际改变、已有映射失效时，先说明具体变化和所需核实项；不能用双轮同时转动猜测左右映射，也不能静默恢复逐轮测试流程。KEY急停、失线／超时／反馈异常保护保留。
