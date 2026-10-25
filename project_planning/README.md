# 项目管理入口

更新：2026-10-25（北京时间）。维护：00项目总指挥。当前协作方式由主控在本轮确认，工程及技术证据路径沿用。

## 日常只需按问题找入口

| 文件 | 负责的信息 | 维护时机 |
| --- | --- | --- |
| [project_status.md](project_status.md) | 当前判断、有效任务、阻塞、近期节点 | 00核对新证据后更新摘要 |
| [collaboration_standard.md](collaboration_standard.md) | 对话登记、职责、权威来源、交接与写入规则 | 职责或协作方式变化时 |
| [agent_initialization_prompts.md](agent_initialization_prompts.md) | 给00／01／02／03的完整接续Prompt | 新开或恢复职责时 |
| [tasks/README.md](tasks/README.md) | 任务单、执行结果与回报模板 | 多轮或跨对话任务开始时 |
| [version_handoff.md](version_handoff.md) | 设备、Git版本、未同步项及操作证据 | 03实际检查或交接时 |
| [organization_review.md](organization_review.md) | 2026-10-25审查依据、阅读清单、迁移与遗留问题 | 本次体系整理的证据，按日期留存 |
| [ORG-02](tasks/ORG-02.md)／[根docs](../docs/README.md) | STM32分层目录迁移、架构与统一主题入口 | 新主控文件放置和恢复工程时 |

短小模块修改直接在模块文档留证；涉及多轮、跨对话、接口或验收的任务才建立 `tasks/<ID>.md`。不另建一套重复待办表。

## 原计划与阅读版

- [原规划文字版](project_plan.md)／[PDF](project_plan.pdf)：2026-10-11制定的目标与里程碑，完成情况查状态页。
- [三人分工大纲](team_work_outline.pdf)：历史职责概览，现行对话规则查协作标准。
- [GitHub教程PDF](github_collaboration_guide.pdf)／[正文](github_collaboration_guide.md)：2026-10-11人工操作教程；其中私有仓库、尚无工程、收工必Push、另建interfaces.md等为旧口径，日常以协作标准及当前任务授权为准。

| 内容源 | 生成产物 | 修改方法 |
| --- | --- | --- |
| `source/generate_project_plan.py` 内正文与表格 | `project_plan.md`、`project_plan.pdf` | 先改生成源，再生成并检查 |
| `source/generate_team_outline.py` | `team_work_outline.pdf` | 修改生成源 |
| `github_collaboration_guide.md` | 同名PDF | `source/generate_github_guide.py`读取Markdown |
| 协作规则、状态与任务Markdown本身 | 无强制PDF副本 | 直接维护、检查差异和链接 |

本轮没有重排计划或重生成PDF。修改计划须记录新预计日期、原因与主控确认，不能只覆盖原目标。

## 历史记录

[archive/](archive/)保留整理前的状态流水与目录快照。它们说明“当时发生过什么”，当前行动由状态页和具体任务确定。历史授权只适用于其原任务。

本次落地与给00的完整交接见[ORG-01](tasks/ORG-01.md)。
