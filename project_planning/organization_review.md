# 文件与对话体系审查、迁移与证据

> 本文保留ORG-01整理时的审查范围和检查结果。主控随后明确授权ORG-02物理目录分层，现行工程位置与新增构建证据以[ORG-02](tasks/ORG-02.md)为准；下方历史阅读清单中已迁移文件的链接目标已适配新路径。

日期：2026-10-25（北京时间）。任务：ORG-01。维护：本轮体系整理交付，00接续。
依据：本地正式文档、内容源、配置、现有项目对话，以及主控本轮两项选择。本文保存本次审查，不作为第二份当前状态页。

## 为什么采用这套体系

现有业务目录已经符合比赛要求、模块实现、实测和报告的流向；四个长期对话也对应真实职责。主要问题在于文档角色混杂、当前状态和历史混写，以及跨对话结果没有及时回到统一入口。按聊天重新分工程目录会复制协议与硬件资料，并破坏Keil和生成器的相对引用。

本轮保留业务目录与四对话，补齐三条连接：角色对应写入范围；任务文件对应具体工作及结果；当前状态链接实际证据。主控既可向00提出全局需求，也可向01／02直接提出清晰模块任务。聊天更换后读任务文件恢复，项目事实不依赖某个聊天记忆。

03是按需服务职责，当前不需要额外增加常驻审查、学习、报告、视觉或硬件聊天。专题工作有明确独立产出时可临时拆出；主控的学习讲解通常跟随01，现场指导跟随02。三位成员的实现责任保持不变。

本项目选择同一checkout顺序写入。需要并行开发时再安排独立worktree、基线、工具和合回检查；拆成多个本地聊天本身没有文件隔离。能力依据：[OpenAI Docs：环境](https://learn.chatgpt.com/docs/environments/modes)、[Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)、[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。职责、任务格式与文件名属于项目约定。

## 本轮实际迁移与改动

| 范围 | 处理 | 结果边界 |
| --- | --- | --- |
| 根README、目录与规划README | 重写为场景入口、业务目录和内容源索引 | 当前事实不再复制进静态目录清单 |
| AGENTS与协作标准 | 保留SPL／Keil／中文注释／角色／授权约束；明确身份登记、直接模块任务与单一写入 | 现有00继续负责全局，本对话只交付ORG-01 |
| 初始化Prompt | 提供四段完整职责更新文本与接续方法 | 未自动创建、改名、归档或发送聊天 |
| 当前状态 | 摘出有效事实、依赖、当前任务和原日期；校正I-04/I-05旧下一步及G-02摘要 | 不新增实测、不重新承诺工期 |
| 长状态流水、完整目录快照 | 保存至archive，显式相对链接随位置调整 | 原事实／失败／授权日期保留；归档不代表现行步骤 |
| tasks/README与ORG-01 | 目标、边界、结果、证据与完整交接在同一任务文件 | 状态页仍是唯一全局任务索引 |
| control／hardware／testing README | 区分当前操作、历史方法、已测结果与待填模板 | 技术规格、工程及现场记录正文未改 |
| version_handoff | 保存03的G-02历史完成回报及本地独立核对 | 本轮无远端实时复核，笔记本待确认 |

归档映射：

- 整理前project_planning/project_status.md → [archive/2026-10-25_project_status_snapshot.md](archive/2026-10-25_project_status_snapshot.md)。
- 整理前DIRECTORY_GUIDE.md → [archive/2026-10-25_directory_guide_snapshot.md](archive/2026-10-25_directory_guide_snapshot.md)。

原路径保留当前导航文件。工程、模块规格、PDF／生成器、原图与测试记录未搬动。技能内容和Git忽略规则未修改。

## 组织改善、技术缺陷和环境问题分别处理

### 本轮已经落实的组织改善

- 修正共享文件“当前对话就是00”的隐式身份；登记四个实际对话及本轮临时范围。
- 状态页从原长篇流水改为当前摘要，历史完整保留。
- 把已存在的R1绿灯恢复、R3快照、持续版测量与Direct交付串到当前入口，减少重新问型号／重复旧步骤。
- G-02从旧“进行中”修正为已有完成证据。来源为03历史最终回报及本地提交；未把回报当成主控认可或当前远端检查。
- 任务文件承担交接，清晰模块任务无需每一步绕回00；00仍统一处理跨模块影响与最终核对。

### 已发现、尚未在本轮修复的技术文档缺陷

| 问题 | 当前采用口径／建议修复负责人 |
| --- | --- |
| motor_bench／R3任务页仍含“尚无实板快照” | 以testing的R3原图为已有证据；01后续标明交付当时状态与现行结果链接 |
| R1修复页仍写板级待复验 | 绿灯恢复已有用户回报，完整变量／独立上电仍缺；01区分两层结论 |
| dual_motor_wiring_guide混有DAPLink／USB供电与UC2操作 | 硬件README已标历史冲突，02后续整理现行方法，保持wiring规格源 |
| control_bringup_plan含未到货、PWM未实现和PA0/PA1旧候选 | 推进顺序作历史参考；实际资源查pin_plan，01／02同步技术说明 |
| I-05正文保留R2边界，后续又有R3／Continuous／Direct | 按具体版本和当次任务阅读，02后续拆清阶段；历史限制不自动变永久规定 |
| motor_wiring_self_check第4节缺表头和供电行、标题有多余字符 | 02按既有权威资料修复格式，不能补造电气结果 |
| standard_library／vendor部分“TIM/IWDG仅MotorBench”表述落后 | 实际三个电机目标均有相关依赖；01按工程配置更新文字，不删必要库 |
| Git教程含私有、无工程、收工必Push及另建interfaces.md建议 | 当前授权看AGENTS，协议仍用现有protocol文件；03按单独文档任务修订源并重生成PDF |
| team_work_outline PDF规则路径落后于生成源 | 下次内容更新一并生成并检查，当前不为轻微路径重复重排PDF |
| 原D-01～D-10含采购精简、电池品牌、旧口径与排期差距 | 完整原问题在状态快照；由对应硬件／视觉／主控负责人依据真实交付处理 |

这些项是审查发现，不等于已派发执行或已获新技术改动授权。现行入口已注明边界；依赖未解决冲突的现场动作先由负责角色校正。

### 环境与交接问题

- setup_debug.ps1／debug_options.xml仅覆盖两个旧目标，换电脑不能据此认定六目标调试配置完整；后续由01单独修工具与复现说明，本轮未改。
- 原始Flash备份／实测日志有部分仅在被忽略tmp，构建日志和固件在build；03交接区分可重建产物与不可重建原证据。本轮未清理或迁移。
- .agents技能发现入口被忽略，不保证换电脑自动具备；正式技能仍在.agent/skill，AGENTS直接指向它。
- 本地Git存在所有者保护，沿用单命令safe.directory参数，没有修改全局配置。

## 阅读范围与方法

整理前正式文档清单来自Git已跟踪及未忽略的本地未跟踪文件，包含未提交成果：52份Markdown、17份PDF共96页；另外完整读取8份文档生成器、2份BOM／分配JSON、1份历史TeX、4份TXT、SPL发布说明HTML、库来源清单，以及9份主控PowerShell／调试模板和技能元数据。两个正式Keil工程按目标、宏、文件排除及相对路径检查。

主代理读全局／规划／导航／视觉审查，资料调查子任务分别完整读硬件与PDF、主控与测试、规划PDF与生成源。项目grilling技能明确要求事实调查使用子代理；这些是本轮调查，不是向现有用户聊天自动派任务。

PDF全部正文已读；比赛、厂商器件／接线资料、视觉和天空星图文资料补充渲染查看。天空星13页全部扫描，视觉末两页源码截图已视觉阅读；没有未读PDF页。采购／规划PDF完整提取阅读，未重新对全部96页进行出版排版验收。许可仅检查来源与保留关系，没有作法律结论。

业务文档不包括Git对象、第三方库逐行实现、编译缓存、下载工具包内部文档与全部历史网页缓存；这些按用途识别，不声称全量源码审查。原图证据按索引和已有结果读取，没有重新逐张鉴定全部照片，也没有重测算法／器件。

另读本机偏好上下文、tmp/README及历史PR正文草稿，用于辨别学习习惯和临时资料；它们不提升为新的项目全局要求。读取00／01／02／03近期状态和用户／最终回报，保留跨聊天证据不等同主控验收的边界。

以下逐文件清单在本次整理前建立；归档快照及本轮新增文件不计入52份基数。

### 整理前Markdown（52份，全部正文阅读）

| 原路径 | 阅读范围 |
| --- | --- |
| [.agent/skill/grill-me/SKILL.md](../.agent/skill/grill-me/SKILL.md) | 全文；整理前内容 |
| [.agent/skill/grilling/SKILL.md](../.agent/skill/grilling/SKILL.md) | 全文；整理前内容 |
| [AGENTS.md](../AGENTS.md) | 全文；整理前内容 |
| [DIRECTORY_GUIDE.md](../DIRECTORY_GUIDE.md) | 全文；整理前内容 |
| [README.md](../README.md) | 全文；整理前内容 |
| [competition/README.md](../competition/README.md) | 全文；整理前内容 |
| [control/README.md](../control/README.md) | 全文；整理前内容 |
| [control/docs/board_self_test.md](../control/docs/board_self_test.md) | 全文；整理前内容 |
| [control/docs/evidence/2026-10-18_c02a/README.md](../control/docs/evidence/2026-10-18_c02a/README.md) | 全文；整理前内容 |
| [control/docs/keil_quickstart.md](../control/docs/keil_quickstart.md) | 全文；整理前内容 |
| [control/docs/motor_bench.md](../control/docs/motor_bench.md) | 全文；整理前内容 |
| [control/docs/motor_bench_r2_task.md](../control/docs/motor_bench_r2_task.md) | 全文；整理前内容 |
| [control/docs/motor_bench_r3_task.md](../control/docs/motor_bench_r3_task.md) | 全文；整理前内容 |
| [control/docs/motor_bench_startup_issue.md](../control/docs/motor_bench_startup_issue.md) | 全文；整理前内容 |
| [control/docs/motor_continuous.md](../control/docs/motor_continuous.md) | 全文；整理前内容 |
| [control/docs/motor_direct.md](../control/docs/motor_direct.md) | 全文；整理前内容 |
| [control/docs/pin_plan.md](../control/docs/pin_plan.md) | 全文；整理前内容 |
| [control/docs/protocol_v1_draft.md](../control/docs/protocol_v1_draft.md) | 全文；整理前内容 |
| [control/docs/standard_library.md](../control/docs/standard_library.md) | 全文；整理前内容 |
| [control/docs/state_machine.md](../control/docs/state_machine.md) | 全文；整理前内容 |
| [control/docs/validation.md](../control/docs/validation.md) | 全文；整理前内容 |
| [control/firmware/vendor/README.md](../control/Drivers/README.md) | 全文；整理前内容 |
| [hardware_preparation/README.md](../hardware_preparation/README.md) | 全文；整理前内容 |
| [hardware_preparation/board_self_test_record.md](../hardware_preparation/board_self_test_record.md) | 全文；整理前内容 |
| [hardware_preparation/charger_replacement.md](../hardware_preparation/charger_replacement.md) | 全文；整理前内容 |
| [hardware_preparation/control_bringup_plan.md](../hardware_preparation/control_bringup_plan.md) | 全文；整理前内容 |
| [hardware_preparation/dual_motor_wiring_guide.md](../hardware_preparation/dual_motor_wiring_guide.md) | 全文；整理前内容 |
| [hardware_preparation/evidence/2026-10-18_i03/README.md](../hardware_preparation/evidence/2026-10-18_i03/README.md) | 全文；整理前内容 |
| [hardware_preparation/i03_handoff.md](../hardware_preparation/i03_handoff.md) | 全文；整理前内容 |
| [hardware_preparation/i05_measurement_guide.md](../hardware_preparation/i05_measurement_guide.md) | 全文；整理前内容 |
| [hardware_preparation/i05_motor_power_diagnosis_task.md](../hardware_preparation/i05_motor_power_diagnosis_task.md) | 全文；整理前内容 |
| [hardware_preparation/motor_dc_check.md](../hardware_preparation/motor_dc_check.md) | 全文；整理前内容 |
| [hardware_preparation/motor_scope_check.md](../hardware_preparation/motor_scope_check.md) | 全文；整理前内容 |
| [hardware_preparation/motor_wiring_self_check.md](../hardware_preparation/motor_wiring_self_check.md) | 全文；整理前内容 |
| [hardware_preparation/wiring.md](../hardware_preparation/wiring.md) | 全文；整理前内容 |
| [project_planning/README.md](../project_planning/README.md) | 全文；整理前内容 |
| [project_planning/agent_initialization_prompts.md](../project_planning/agent_initialization_prompts.md) | 全文；整理前内容 |
| [project_planning/collaboration_standard.md](../project_planning/collaboration_standard.md) | 全文；整理前内容 |
| [project_planning/github_collaboration_guide.md](../project_planning/github_collaboration_guide.md) | 全文；整理前内容 |
| [project_planning/project_plan.md](../project_planning/project_plan.md) | 全文；整理前内容 |
| [project_planning/project_status.md](../project_planning/project_status.md) | 全文；整理前内容 |
| [project_planning/version_handoff.md](../project_planning/version_handoff.md) | 全文；整理前内容 |
| [report/README.md](../report/README.md) | 全文；整理前内容 |
| [testing/2026-10-20_motor_bench/acceptance_record.md](../testing/2026-10-20_motor_bench/acceptance_record.md) | 全文；整理前内容 |
| [testing/2026-10-21_motor_bench/i05_measurement_results.md](../testing/2026-10-21_motor_bench/i05_measurement_results.md) | 全文；整理前内容 |
| [testing/2026-10-21_motor_bench/no_rotation_record.md](../testing/2026-10-21_motor_bench/no_rotation_record.md) | 全文；整理前内容 |
| [testing/2026-10-21_motor_bench/r3_watch/README.md](../testing/2026-10-21_motor_bench/r3_watch/README.md) | 全文；整理前内容 |
| [testing/2026-10-24_motor_continuous/scope_results.md](../testing/2026-10-24_motor_continuous/scope_results.md) | 全文；整理前内容 |
| [testing/2026-10-24_motor_continuous/watch/README.md](../testing/2026-10-24_motor_continuous/watch/README.md) | 全文；整理前内容 |
| [testing/README.md](../testing/README.md) | 全文；整理前内容 |
| [vision/PORTING_REVIEW.md](../vision/PORTING_REVIEW.md) | 全文；整理前内容 |
| [vision/README.md](../vision/README.md) | 全文；整理前内容 |

### PDF（17份，96页）

| 原路径 | 页数 | 阅读方法 |
| --- | --- | --- |
| [competition/比赛文档.pdf](../competition/比赛文档.pdf) | 6 | 全文提取＋图文／源码页逐页渲染查看 |
| [control/firmware/vendor/stdperiph/LICENSE.pdf](../control/Drivers/stdperiph/LICENSE.pdf) | 3 | 全文提取阅读；未重新作逐页排版验收 |
| [control/stm数据手册.pdf](../control/stm数据手册.pdf) | 13 | 全部扫描页渲染查看，非芯片完整数据手册 |
| [hardware_preparation/archive/hardware_list_600CNY_preliminary.pdf](../hardware_preparation/archive/hardware_list_600CNY_preliminary.pdf) | 2 | 全文提取阅读；未重新作逐页排版验收 |
| [hardware_preparation/archive/hardware_list_697CNY_superseded.pdf](../hardware_preparation/archive/hardware_list_697CNY_superseded.pdf) | 1 | 全文提取阅读；未重新作逐页排版验收 |
| [hardware_preparation/evidence/2026-10-18_i03/at8236_datasheet.pdf](../hardware_preparation/evidence/2026-10-18_i03/at8236_datasheet.pdf) | 10 | 全文提取＋图文／源码页逐页渲染查看 |
| [hardware_preparation/evidence/2026-10-18_i03/vendor_driver_introduction.pdf](../hardware_preparation/evidence/2026-10-18_i03/vendor_driver_introduction.pdf) | 1 | 全文提取＋图文／源码页逐页渲染查看 |
| [hardware_preparation/evidence/2026-10-18_i03/vendor_driver_stm32.pdf](../hardware_preparation/evidence/2026-10-18_i03/vendor_driver_stm32.pdf) | 3 | 全文提取＋图文／源码页逐页渲染查看 |
| [hardware_preparation/hardware_modules_overview.pdf](../hardware_preparation/hardware_modules_overview.pdf) | 2 | 全文提取阅读；未重新作逐页排版验收 |
| [hardware_preparation/hardware_purchase_list.pdf](../hardware_preparation/hardware_purchase_list.pdf) | 7 | 全文提取阅读；未重新作逐页排版验收 |
| [hardware_preparation/purchase_list_control.pdf](../hardware_preparation/purchase_list_control.pdf) | 1 | 全文提取阅读；未重新作逐页排版验收 |
| [hardware_preparation/purchase_list_hardware.pdf](../hardware_preparation/purchase_list_hardware.pdf) | 2 | 全文提取阅读；未重新作逐页排版验收 |
| [hardware_preparation/purchase_list_vision.pdf](../hardware_preparation/purchase_list_vision.pdf) | 1 | 全文提取阅读；未重新作逐页排版验收 |
| [project_planning/github_collaboration_guide.pdf](../project_planning/github_collaboration_guide.pdf) | 21 | 全文提取阅读；未重新作逐页排版验收 |
| [project_planning/project_plan.pdf](../project_planning/project_plan.pdf) | 6 | 全文提取阅读；未重新作逐页排版验收 |
| [project_planning/team_work_outline.pdf](../project_planning/team_work_outline.pdf) | 2 | 全文提取阅读；未重新作逐页排版验收 |
| [vision/references/智能车图像处理辅助文档V2.0.pdf](../vision/references/智能车图像处理辅助文档V2.0.pdf) | 15 | 全文提取＋图文／源码页逐页渲染查看 |

### 内容源和配套文本

| 原路径 | 阅读范围 |
| --- | --- |
| [.agent/skill/grill-me/agents/openai.yaml](../.agent/skill/grill-me/agents/openai.yaml) | 全文；配置／来源／内容关系核对 |
| [.agent/skill/grilling/agents/openai.yaml](../.agent/skill/grilling/agents/openai.yaml) | 全文；配置／来源／内容关系核对 |
| `.agents/skills/grill-me/SKILL.md` | 全文；配置／来源／内容关系核对 |
| `.agents/skills/grill-me/agents/openai.yaml` | 全文；配置／来源／内容关系核对 |
| `.agents/skills/grilling/SKILL.md` | 全文；配置／来源／内容关系核对 |
| `.agents/skills/grilling/agents/openai.yaml` | 全文；配置／来源／内容关系核对 |
| [.gitattributes](../.gitattributes) | 全文；配置／来源／内容关系核对 |
| [.gitignore](../.gitignore) | 全文；配置／来源／内容关系核对 |
| [control/firmware/motor_direct.uvprojx](../control/MDK-ARM/motor_direct.uvprojx) | 目标／宏／相对路径结构检查 |
| [control/firmware/startup/LICENSE.txt](../control/Core/Startup/LICENSE.txt) | 全文；配置／来源／内容关系核对 |
| [control/firmware/vendor/cmsis/LICENSE.txt](../control/Drivers/cmsis/LICENSE.txt) | 全文；配置／来源／内容关系核对 |
| [control/firmware/vendor/stdperiph/Release_Notes.html](../control/Drivers/stdperiph/Release_Notes.html) | 全文；配置／来源／内容关系核对 |
| [control/firmware/vendor/stdperiph/source_manifest.json](../control/Drivers/stdperiph/source_manifest.json) | 全文；配置／来源／内容关系核对 |
| [control/firmware/vendor/stm32/LICENSE.txt](../control/Drivers/stm32/LICENSE.txt) | 全文；配置／来源／内容关系核对 |
| [control/firmware/yeye_control.uvprojx](../control/MDK-ARM/yeye_control.uvprojx) | 目标／宏／相对路径结构检查 |
| [control/tools/build_keil.ps1](../control/tools/build_keil.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/check_uart_build.ps1](../control/tools/check_uart_build.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/debug_options.xml](../control/tools/debug_options.xml) | 全文；配置／来源／内容关系核对 |
| [control/tools/run_host_tests.ps1](../control/tools/run_host_tests.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/run_motor_bench_pwm_diag_tests.ps1](../control/tools/run_motor_bench_pwm_diag_tests.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/run_motor_bench_startup_tests.ps1](../control/tools/run_motor_bench_startup_tests.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/run_motor_bench_tests.ps1](../control/tools/run_motor_bench_tests.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/run_motor_continuous_tests.ps1](../control/tools/run_motor_continuous_tests.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/run_motor_direct_tests.ps1](../control/tools/run_motor_direct_tests.ps1) | 全文；配置／来源／内容关系核对 |
| [control/tools/setup_debug.ps1](../control/tools/setup_debug.ps1) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/archive/generate_600CNY_preliminary.py](../hardware_preparation/archive/generate_600CNY_preliminary.py) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/archive/generate_697CNY_superseded.py](../hardware_preparation/archive/generate_697CNY_superseded.py) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/archive/layout_draft_697CNY.tex](../hardware_preparation/archive/layout_draft_697CNY.tex) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/source/generate_modules_overview.py](../hardware_preparation/source/generate_modules_overview.py) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/source/generate_purchase_list.py](../hardware_preparation/source/generate_purchase_list.py) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/source/generate_team_purchase_lists.py](../hardware_preparation/source/generate_team_purchase_lists.py) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/source/purchase_bom.json](../hardware_preparation/source/purchase_bom.json) | 全文；配置／来源／内容关系核对 |
| [hardware_preparation/source/team_purchase_allocation.json](../hardware_preparation/source/team_purchase_allocation.json) | 全文；配置／来源／内容关系核对 |
| [project_planning/source/generate_github_guide.py](../project_planning/source/generate_github_guide.py) | 全文；配置／来源／内容关系核对 |
| [project_planning/source/generate_project_plan.py](../project_planning/source/generate_project_plan.py) | 全文；配置／来源／内容关系核对 |
| [project_planning/source/generate_team_outline.py](../project_planning/source/generate_team_outline.py) | 全文；配置／来源／内容关系核对 |
| [testing/2026-10-20_motor_bench/keil_download_report.txt](../testing/2026-10-20_motor_bench/keil_download_report.txt) | 全文；配置／来源／内容关系核对 |

## 本轮验证

2026-10-25已执行本地静态检查：

- 57份现有正式Markdown按UTF-8读取，无替换字符、未闭合代码围栏或正文冲突标记；代码示例中的冲突演示不当成真实冲突。
- 567个显式本地Markdown链接、1个Markdown标题锚点均存在；检查覆盖新入口和归档快照。没有验证全部外部网页可用性、PDF内部链接或截图内容。
- 两份归档正文逐字比对整理前备份，除新归档说明及显式相对链接适配外，原内容保持一致。
- 整理前171份非忽略文件的SHA256对比：本轮只改变11份原有说明文件，新增5份Markdown；其余160份文件哈希不变，包含既有固件、工具、Keil工程、PDF、生成源和原始证据。共享目录原有修改没有被覆盖或并入本轮成果说明。
- `git diff --check`通过；仍为main、HEAD 82640aba4cf7aa4f30db14b486aef852936118fe，未切分支、提交或推送。Git仅提示既有validation.md／uvprojx在后续Git写入时可能转换换行，不是本轮修改其内容。

核对脚本与原始结果保存在本机被忽略的tmp/organization_audit/；本段为可随项目保存的结果摘要。验证只针对文档体系，未复跑固件、PDF生成或板卡试验；主控日常使用体验仍待反馈。
