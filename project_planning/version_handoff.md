# 版本与设备交接记录

版本：v1.1。日期：2026-10-18（北京时间）。维护角色：主控／03 GitHub与多设备同步。

依据：G-01、G-02任务授权、[协作标准](collaboration_standard.md)、[项目状态](project_status.md)及本次Git命令实测。记录仅确认实际检查到的设备与远端引用，不替代固件、驱动或整车验证。接续优先使用最新G-02步骤，G-01保留为历史记录。

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
