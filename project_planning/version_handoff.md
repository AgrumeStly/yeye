# 版本与设备交接记录

## 当前交付：整车开发交给队友与 DeepSeek（2026-11-27）

队友从 GitHub 默认 `main` 获取代码后，从 [AI_HANDOFF.md](../AI_HANDOFF.md) 开始。本轮范围见[发布任务](tasks/TASK-20261127-01-deepseek-handoff.md)。当前开发配对为 STM32 `0x02120019`／K230 v12 路径接收修订，配对文件、源码来源和板上资源见[归档](../testing/2026-11-25_joint_angle_voice/v12_timing_fix_release/README.md)。实车接续按 [I-04-RIGHT-ANGLE](tasks/I-04-RIGHT-ANGLE.md) 当前区。

## 历史交付：完整当前版本及AI语音交接已发布到main（2026-11-20）

当前版本主提交[`15adcc5c1093a3162f27907457687c75e0fd8121`](https://github.com/AgrumeStly/yeye/commit/15adcc5c1093a3162f27907457687c75e0fd8121)已普通atomic推送至main及原开发分支。已核对远端默认HEAD指向main且同号，并从GitHub运行不指定分支的普通clone：main、HEAD同号、工作区干净；614份非交付回填文件树与清单一致、553份现场原件字节哈希一致、26个AI交接本地链接可定位。当前任务、状态与收据随后随交付回填提交继续同步main，最终号在发布回报给出，避免自引用循环提交。

队友只需普通clone后从根目录[AI_HANDOFF.md](../AI_HANDOFF.md)交给本地dsh；细节见[voice_handoff](voice_handoff.md)。既有原位源码与历史未跟踪依赖已归档，本机UI／用户路径配置、环境及认证没有随传。本轮未修改运行实现、安装语音环境、运行功能测试／构建或操作板卡；后续方案、队友本机环境、语音实现和验证交队友与dsh。

核对入口：[实际清单](evidence/2026-11-19_current_version_main/file_manifest.json)、[静态检查](evidence/2026-11-19_current_version_main/static_checks.json)、[普通clone](evidence/2026-11-19_current_version_main/clone_verification.json)、[上传收据](evidence/2026-11-19_current_version_main/upload_receipt.json)。下方“尚未执行／进行中”均保留各自较早时点，不覆盖本段已完成发布事实。

2026-11-20主控明确本对话整理指导AI的文档并上传，后续本机环境、语音方案、实现和验证交队友与本地dsh。根目录[AI_HANDOFF.md](../AI_HANDOFF.md)及[语音交接](voice_handoff.md)已整理，沿用现有K230麦克风和扬声器；本次既有版本发布继续原任务ID，不新开语音开发任务。下述11月19日“待转交／尚未执行”为当时状态，实际本轮提交与远端核对结果完成后补充。

主控已明确“现在的进度我都已验收，整理后上传github，让别人clonegithub时直接是当前这个最新版”。总管已登记[当前进度验收](evidence/2026-11-19_current_acceptance/acceptance.md)，更新直道03、首弯R8及历史文档架构上传的接受范围，建立[TASK-20261119-02-current-version-main](tasks/TASK-20261119-02-current-version-main.md)。本次授权完整项目版本整理、提交、上传及为实现普通clone所需的main集成，不再局限文档范围；执行对话负责原位源码、未跟踪依赖、发布和证据清单及干净clone核对。

总管只读核对本地分支codex/current-version-20261025、HEAD 82e237ed3e127b0bebc1846d932f7e9b3c28b05e，有5次未推送成果提交及共享未提交源码／依赖；该领先关系依据本地跟踪引用，需执行时fetch核实。GitHub插件元数据确认默认分支为main。本次发布尚未执行，不把任务定义当成默认分支已更新。最近首弯为499ms LINK2，阶段交付已验收，完整首弯尚未完成，后续同步日志阻塞修复尚未实施；失败和未测能力随当前版如实保留。

## 历史交付：新项目架构上传（2026-11-19，已验收）

本段原始交付在较早时刻保持待验，现已由主控“现在的进度我都已验收”统一接受；以下记录保留当次文件范围及核对时点，不代表本次完整实现和main发布已经完成。

主控已转交[TASK-20261119-01-architecture-upload](tasks/TASK-20261119-01-architecture-upload.md)，明确本次架构提交、推送与远端核对授权。版本上传执行对话核对目录`D:/projects/projectsyeye`、分支`codex/current-version-20261025`、起始HEAD `62b4f288b27c4e3fa9f6d213c07be186e502f43c`及origin `https://github.com/AgrumeStly/yeye.git`；暂存区为空，无git进程／index.lock。实际fetch及ls-remote确认同名远端起始提交一致，领先／落后0／0。

架构主提交[`bdc38c6a465c2a07f6f191b563c29ed8f886e495`](https://github.com/AgrumeStly/yeye/commit/bdc38c6a465c2a07f6f191b563c29ed8f886e495)含65份文件，已普通推送；提交后实时ls-remote返回同一完整提交号。[实际命令收据](evidence/2026-11-19_architecture_upload/upload_receipt.json)及[保留核对](evidence/2026-11-19_architecture_upload/preservation.json)已归档。本段与任务的结果回填追加提交并推送，最终完整提交号及最终远端同号核对在执行对话最终回报给出，另存本地忽略路径tmp/architecture_upload_20261119/final_verification.json，避免自引用循环提交。

本次限定61份许可架构文件及本任务文字／JSON证据，含新协作标准3.2、本地Git规则、路线图、任务迁移、ORG-03验收和I-04 LINK2／200ms接续；首页补齐新总管已登记事实及上传边界。[实际清单](evidence/2026-11-19_architecture_upload/file_manifest.json)、[静态检查](evidence/2026-11-19_architecture_upload/static_checks.json)、[范围外591个文件哈希](evidence/2026-11-19_architecture_upload/initial_state.json)及[逐项依赖](evidence/2026-11-19_architecture_upload/local_dependencies.json)为核对入口。原五份迁移证据不改写，不跑固件／视觉／硬件测试。

这是文档架构上传，不能据此恢复完整最新实车环境：直道／首弯源码、算法／测试／工具、协议本地变更、Keil工程、wheel_mapping实跑映射、相机发布包、原始照片／日志、IDE／Obsidian设置等保留本地，不夹带上传。范围外591个起始内容差异文件哈希一致；另yeye_control.uvprojx是起始status已显示M而文本diff无差异的共享工程项，未编辑／暂存，单列保留，共592条状态记录。技术／历史链接在候选树中有69处缺失（42个目标），另31处目标存在旧版但本地修改未上传；部分历史目标本地也不存在，依赖JSON逐项标识。build／tmp、固件及本机配置继续单独保留。本任务当前区是执行结果入口；全局状态保留总管转交前快照，主控验收后由总管更新。仅完成资料及版本检查，未操作硬件；主控仍须明确验收上传成果，Git同号不代表车辆或其它设备通过。

总管于2026-11-19收到主控转交的最终执行回报，核对最终交付提交为[`74a45ef81f2165e4e53cf43bc45d349564bca42b`](https://github.com/AgrumeStly/yeye/commit/74a45ef81f2165e4e53cf43bc45d349564bca42b)，含架构主提交及结果回填共67份文件。最终核对文件记载实际ls-remote与该提交同号、暂存区为空、范围外内容保留；本轮总管只读核对本地HEAD一致，未重新联网或重跑原检查。本次尚未收到主控明确验收结论，任务及全局索引均登记待主控验收；本轮管理状态回填仅本地保存，不属于上述已上传提交。

## 历史接续：G-07当前版本上传（2026-11-15）

主控本轮要求“把当前版本更新到github”。来源设备 `JokeBearDesktop`，目录 `D:/projects/projectsyeye`，分支 `codex/current-version-20261025`，开始 HEAD 为 `a0733a8685db4c2b497539303bfe87fe1c1ebfe5`，Fetch 后与同名远端领先 0、落后 0。保存当前全部非忽略源码、照片、测试与现场证据及文档，沿用现有分支上传。范围、已重跑主控测试与其它设备接续方法见 [G-07](tasks/G-07.md)；最终提交及远端一致性以本轮实际命令和最终回报为证。

本轮未操作其它设备或板卡，未重新确认视觉、ARM 构建及整车验收；main、历史标签保持原位。原始失败与历史记录保留，全局技术摘要由 00 读取模块证据后维护。

## 历史接续：G-06笔记本上传至台式机（2026-10-31）

主控本轮要求“将所有内容更新github，方便台式上拉取”。实际来源设备为`JokeBearDesktop`，目录`D:/projects/projectsyeye`，分支`codex/current-version-20261025`，开始HEAD为`9520eeb481169f88146afe541b4d53617c7728eb`；Fetch后同名远端与本地领先0、落后0。本轮保存全部非忽略项目改动，含StraightTest、SpeedMatch、测试与工具、新板复测及相关文档，沿用现有分支上传。

台式机在实际仓库目录拉取同名分支；历史目录为`D:/Projects/yeye`，本轮未直接操作台式机。完整步骤、检查与本机设置差异见[G-06](tasks/G-06.md)。最终提交及上传一致性以本轮最终回报为证；main和历史正式标签继续保持原位。00可读取C-02E、C-02F及新板记录顺序汇总技术进展，本轮仅维护版本交接。

## 历史接续：G-05台式机上传至笔记本（2026-10-30）

本次主控已明确要求上传当前最新版本，以便笔记本继续开发。03在DESKTOP-0HLUQN7、D:\Projects\yeye核对当前分支codex/current-version-20261025；开工本地及联网核对的远端同名分支均为0b0343577895d8eb03a337165da6ce9c5e433519，main仍为82640aba4cf7aa4f30db14b486aef852936118fe。当前编码器实现／原手转证据、轮组换位、比赛与底板资料、任务和状态文档一并纳入本轮提交；已有修改保留。

本轮继续上传现有任务分支，不合并main、不发布、不移动formal-2026-10-25；该标签只表示历史正式快照，笔记本应拉取任务分支最新提交。完整步骤、当前轮位注意事项、检查结果及Codex接续Prompt见[G-05](tasks/G-05.md)，最终完整提交号与远端一致性以03最终回报为证。

台式机已实际检查；笔记本仅有先前来源记录D:\projects\projectsyeye、设备JokeBearDesktop，本轮未直接核对其当前目录、改动、HEAD、工具与串口，仍为待确认。用户级Codex认证／插件、本机Keil配置、build和tmp原始日志继续分开核实。00读取G-05更新全局摘要，上传或电脑检查不产生新实物／整车验收。

版本：v1.3。原记录日期：2026-10-18；2026-10-25补充G-03完整版本上传与Codex接续（北京时间）。维护角色：主控／03 GitHub与多设备同步。

## 2026-10-25台式机接收确认：G-04正式版本

主控在本对话确认笔记本马达测试已完成并上传GitHub，要求台式机拉取更新。03实际检查DESKTOP-0HLUQN7的D:\Projects\yeye：更新前工作区干净，当前分支codex/current-version-20261025，HEAD为0f033c6f67e5d4bef27b1c5afdd9d7014ac0456d；其它已显示的本项目对话均未在执行写入。

联网Fetch发现当前分支只落后1个提交，采用仅快进更新至0b0343577895d8eb03a337165da6ce9c5e433519，完整接收40个文件的变更。远端同名分支、台式机HEAD及formal-2026-10-25标签对应提交一致；main保持原位，没有合并、上传、发布或移动正式标签。笔记本设备名与目录沿用G-04上传记录，本轮没有直接操作笔记本环境。

本次接收包括Direct A/B、重写PWM、独立MotorPwm／MotorDirectB工程、C-02B-PWM-R4及两份10-25实物记录。主控对A/B分别PWM起转、自动停转与阶段灯态的验收，以testing/2026-10-25_motor_pwm/acceptance_record.md所载文字回报和边界为准；不补造板内版本读回或外部波形。编码器、闭环、反转、双马达同时运行及整车验收仍无本次结果。全局状态由00读取上述证据后顺序更新。

台式机重跑六个现有电脑测试脚本全部通过：协议55项、台架73项、启动154项／10场景、PWM168项／9场景、持续115项／7场景及启动154项、Direct A/B各52593次断言／9场景及启动154项；日志在被忽略的tmp/g04_desktop_receive。附加Keil重编译命令被自动审批拦截（blocked by policy，未提供具体原因），本轮未重编译，保留笔记本原构建证据。未烧录、连接板卡或驱动电机；台式机IDE交互、下载器和串口未另行实测。

首次Git直连失败，03读取已存在的系统代理127.0.0.1:7897及监听端口后，仅为本次Fetch／核对命令指定http.proxy；没有修改持久Git或系统网络配置。拉取完成时工作区干净，本段接收回填仅保存台式机本地，形成version_handoff.md的未提交修改；本轮未获上传新记录授权，不沿用笔记本上传授权。主控可让00读取本记录及G-04任务继续汇总。

## 当前接续：G-04正式版本与台式机更新（2026-10-25）

主控在笔记本明确要求上传当前全部内容，并确认当前版本为正式版本、符合预期。当前上传来源为 `D:/projects/projectsyeye`，设备 `JokeBearDesktop`，分支 `codex/current-version-20261025`，起始HEAD `0f033c6f67e5d4bef27b1c5afdd9d7014ac0456d`。本次包括Direct A/B、重写PWM、主控验收及软件证据。正式快照标签为 `formal-2026-10-25`；最终提交与远端核对以03执行回报为准。

台式机更新分支、Codex绑定本地目录、接续Prompt及后续上传方法见 [G-04](tasks/G-04.md)。本次沿用已存在的任务分支；未合并main或创建GitHub Release，不能只拉取默认main取得本次版本。台式机历史目录为 `D:/Projects/yeye`，尚未在本轮实际操作或核验，不能标为已同步。G-03及以下历史中的待实测结论按原日期保留；当前PWM人工验收以 [C-02B-PWM-R4](tasks/C-02B-PWM-R4.md) 和 [现场记录](../testing/2026-10-25_motor_pwm/acceptance_record.md) 为准。全局项目摘要由00读取证据后顺序更新。

## 历史接续：G-03完整版本上传（2026-10-25）

主控已在03明确要求上传当前全部版本并提供笔记本Clone后接续Codex的方法。详细范围、验证与可直接复制的步骤见[G-03](tasks/G-03.md)。本次来源分支为codex/current-version-20261025，包含固件、硬件／测试证据、ORG-01与ORG-02及本次可移植配置；本轮没有合并main或发布授权。Clone必须选择该任务分支，不能仅看默认main。

台式机DESKTOP-0HLUQN7、D:\Projects\yeye；开始时本地与联网核对的远端main均为82640aba4cf7aa4f30db14b486aef852936118fe，后续成果当时尚未提交。最终上传提交、远端同号结果和剩余本地项由03最终回报提供；不为写入自身提交号循环提交。项目技能正文和Codex发现入口随版本上传，用户级插件、认证、IDE、驱动与本机调试配置分别核实。

笔记本设备名、目录、分支、完整提交、Codex登录／项目绑定、IDE与串口仍为待确认；视觉／硬件电脑亦未核对。G-01／G-02为历史记录，后续设备接续优先采用G-03当前步骤。全局项目状态由00读取本任务后顺序更新。

依据：G-01、G-02任务授权、[协作标准](collaboration_standard.md)、[项目状态](project_status.md)及本次Git命令实测。记录仅确认实际检查到的设备与远端引用，不替代固件、驱动或整车验证。接续优先使用最新G-02步骤，G-01保留为历史记录。

## 2026-10-25补记：G-02已有完成回报与本地核对

ORG-01读取现有“03 GitHub与多设备同步”的G-02最终回报，记录：PR [#2](https://github.com/AgrumeStly/yeye/pull/2)当时已Merged，来源最终提交为`febd91aaee4f9a8800d166ed096d5b639398e4d2`，合并及当时本地／远端main均为`82640aba4cf7aa4f30db14b486aef852936118fe`。回报来源：对话`01a14d28-5be8-7d73-9967-2da2936a8edc`，轮次`01a14d48-4add-7b32-872e-676e10131190`。此处保存跨对话结果证据，不推定主控已验收。

本轮仅用本地Git独立核对：当前分支main、HEAD为上述82640aba完整提交；该提交标题为合并PR #2，上一提交为上述febd91aa。原状态页“G-02进行中”据此改为已取得完成证据。没有重新联网确认PR／远端，也没有拉取、提交、推送或合并。不能把本地跟踪引用当实时远端。

当前HEAD之后存在大量10-18以来固件、文档及本次组织资料的未提交修改，和G-02完成当时的干净工作区不同；HEAD不代表当前工作文件全部内容。笔记本及视觉／硬件电脑仍未实际检查，保持待确认。后续上传须另获主控对当前范围的明确要求，不能沿用旧G-02授权。

以下原G-02与G-01正文保留为当时步骤和范围；执行新交接先核对当前真实状态。

## G-02：协作文档合入main及台式机接续

### 授权、版本与执行边界

主控于2026-10-18明确授权“合并至main”，包括相关记录提交上传、创建或更新PR、普通merge commit合并及台式机本地main同步。不发布、不删除任务分支、不强推或丢弃修改。

| 对象 | 执行前已确认事实 | 接续及验证要求 |
| --- | --- | --- |
| 台式机 | DESKTOP-0HLUQN7；D:\Projects\yeye；当前codex/project-coordination；HEAD为2e16e84205e5fc44440092935a2fbfb01abfc0fe | 保留00状态表修改并提交上传，PR合并后切main并仅快进接续 |
| 远端来源分支 | codex/project-coordination位于2e16e84205e5fc44440092935a2fbfb01abfc0fe，与本地一致 | 追加本次状态与交接记录提交；合并时校验PR来源最终完整提交号 |
| 本地及远端main | 9c2db9bcedf01e40dcfddde3ee7dfcc3b618cb0f | PR合并后核对GitHub Merged状态、两侧main完整提交号及8份最终文档 |
| 工作区 | 仅project_status.md有00的G-01验收、G-02登记和授权修改，暂存区为空 | 保留该内容；仅提交相关记录，无关修改不得夹带 |
| 主控笔记本 | 未实际检查设备名、目录、分支、提交或环境 | 待确认，按下方main接续步骤核实 |
| 视觉、硬件电脑 | 未实际核对 | 待确认，本次不认定对应设备已同步 |

03开工时通过对话列表确认00、01、02及其它已显示的本项目对话空闲。远端main是来源分支祖先，尚无本分支到main的开放PR。8份Markdown内容已审阅；链接、编码、冲突标记及git diff --check检查作为本次适用验证，不重测固件。

本段在PR合并前随来源分支提交，记载的是执行前事实、授权与接续要求。G-02是否完成，以03最终回报的PR链接及Merged状态、来源最终提交、普通合并提交、本地与远端main完整提交号、文档核对和工作区状态为证；不为在正文写入自身最终提交号重复提交。最终回报前不将待执行事项当成已验证。

### 主控笔记本从main接续（待实际执行）

1. 主控记录笔记本设备名、实际工程目录和 `git remote -v`，确认origin为AgrumeStly/yeye；执行 `git status --short --branch`、`git branch --show-current`、`git rev-parse HEAD`。保留已有修改；不干净时先交03核对，不覆盖、不强推。
2. 确认该目录没有其它对话正在写入或操作分支，运行 `git fetch origin`。
3. 已有本地main时，运行 `git switch main`，再运行 `git pull --ff-only origin main`。没有本地main时，运行 `git switch --track -c main origin/main`。不能快进或存在分叉时保留现场交03处理。
4. 运行 `git rev-parse HEAD`、`git rev-parse origin/main`、`git ls-remote --heads origin main`，对照03最终回报的完整main提交；同时核对工作区状态与8份协作文档。远端若已有后续更新，先由03确认新增差异，不能仅凭分支名认定同版。
5. 主控将设备名、目录、完整提交和工作区状态带回03，再更新“待确认”。IDE、编译器、芯片支持包、驱动、串口、下载器与板卡配置另行核实；代码文件一致不能替代环境或实车验证。

尚未Clone的笔记本须Clone到新的空目录，再按上述步骤核对main；已有工程不得复制覆盖。本次保留codex/project-coordination任务分支，后续开发应按新任务安排使用分支。

## G-01：项目协作文档上传与笔记本接续准备

### 授权与范围

主控明确要求“现在与github同步”，授权提交并上传当前相关文档；不包含合并至main、创建发布或操作目标设备。03提交原定7份Markdown，并追加本文件与相关导航、状态记录。未修改业务代码，未创建PR，未强推、丢弃或覆盖已有修改。

原定文件：AGENTS.md、DIRECTORY_GUIDE.md、README.md、project_planning/README.md、project_planning/agent_initialization_prompts.md、project_planning/collaboration_standard.md、project_planning/project_status.md。新增文件：project_planning/version_handoff.md。

### 设备与版本

| 对象 | 实际核对结果 | 状态及边界 |
| --- | --- | --- |
| 本次执行设备 | DESKTOP-0HLUQN7；D:\Projects\yeye | 已检查此目录；本机IDE、驱动、串口和板卡配置未检查 |
| 开始时本地main | 9c2db9bcedf01e40dcfddde3ee7dfcc3b618cb0f；4个已跟踪文件修改、3个未跟踪文件；暂存区为空 | 7份文件全部保留并带入任务分支 |
| 任务分支 | codex/project-coordination，跟踪origin/codex/project-coordination | 文档已上传；本记录随随后记录提交交付，接续须核对最终交付提交 |
| 已核验的首批文档提交 | 7471643e2fad03666caf825b0654c8f0ee70d454 | 2026-10-18 12:13:38北京时间，推送成功，git ls-remote与本地HEAD一致 |
| 远端main | 9c2db9bcedf01e40dcfddde3ee7dfcc3b618cb0f | 首批上传后联网核对保持不变；本次无合并授权 |
| 主控笔记本 | 设备名、目录、分支、提交与本地改动均未实际核对 | 待确认，不能根据台式机上传成功标为已同步 |
| 视觉、硬件电脑 | 未实际核对 | 待确认；本任务不代表对应设备接续完成 |

远端地址：https://github.com/AgrumeStly/yeye.git。

首批文档提交之后另有执行记录提交，包含本文件、G-01结果和导航更新。G-01最终交付为2e16e84205e5fc44440092935a2fbfb01abfc0fe，03已完成推送与远端复核，00随后独立验收通过。不要将首批7471643误当作包含交接记录的最终版本，也不要以G-02后续记录提交替代G-01历史验收版本。

### 执行与验证证据

1. 重新读取AGENTS、默认grill-me技能、协作标准、状态表及03初始化职责，检查实际差异、暂存区和远端配置。
2. Fetch远端跟踪信息并通过git ls-remote核对main；执行前main与origin/main领先0、落后0，目标任务分支尚不存在。
3. 分支切换前，Codex对话列表中00、01、02及已显示的其它本项目对话均为空闲；未发现Git锁文件。再次核对7份文件SHA256与初始快照一致后创建任务分支。
4. 原定7份文档的41个本地Markdown链接存在性检查通过；暂存前后git diff --check通过。仅文档变化，未重跑固件测试。
5. 仅明确指定相关路径执行git add；首批提交推送后工作区干净。git ls-remote确认首批文档提交已在远端，main不变。
6. 回填G-01实际结果，建立本记录并更新导航；8份文档共48个本地Markdown链接、UTF-8解码、冲突标记及git diff --check检查通过。记录提交的精确提交号与最终远端核对结果由03在最终回报中提供。

### 未同步项与限制

- 首批核对时未发现无关改动；记录提交后的剩余工作区状态以03最终回报为准。
- Git忽略的本机工具、编译缓存、原始证据未在本任务中逐项清点或上传。必要原始录像和附件须按模块记录另行核对；本任务不能证明这些文件已在笔记本。
- IDE、编译器、芯片支持包、驱动、串口号及下载器配置按设备分别核实；文档同步不等于这些环境可用。
- 本次Git执行遇到目录所有者与执行账号不同的保护提示，采用单次命令参数 `git -c safe.directory=D:/Projects/yeye ...`；未修改全局safe.directory配置。目标设备若出现同类提示，先核对目录和归属。
- 未确认目标设备，尚未合并至main；不能按main拉取后认定已取得本次文档。

### G-01当时的笔记本接续步骤（历史；最新接续按G-02）

1. 主控在笔记本记录设备名与实际工程目录，确认远端地址；执行 `git status --short --branch`、`git branch --show-current`、`git rev-parse HEAD`，保留已有修改。工作区不干净或存在同名分支分叉时先交03核对，不覆盖、不强推。
2. 确认笔记本工程没有其它对话正在写入。运行 `git fetch origin`，检查 `git branch -vv`。
3. 本地尚无任务分支时，运行 `git switch --track -c codex/project-coordination origin/codex/project-coordination`。已有同名分支时，运行 `git switch codex/project-coordination`，确认上游正确后执行 `git pull --ff-only origin codex/project-coordination`。若不能快进，保留现场交03处理。
4. 运行 `git rev-parse HEAD`，与03最终回报的完整提交号逐字核对；运行 `git ls-remote --heads origin codex/project-coordination`，确认远端同号，再检查 `git status --short --branch`。远端若已有后续提交，先由03核对差异，不能直接认定同版。
5. 阅读本次协作规范与初始化职责；若继续主控开发，由01另行核验本机IDE及编译环境。驱动、串口和板卡验证分别记录，不能仅凭Git成功标记可烧录或整车已通过。
6. 主控将笔记本实际设备名、目录、分支、完整提交、工作区状态及环境检查结果带回03；03再更新本记录的“待确认”项。

首次Clone的笔记本须选择新的空目录，Clone后再按上述步骤切换任务分支；已有工程不得复制覆盖或重复Clone到原目录。
