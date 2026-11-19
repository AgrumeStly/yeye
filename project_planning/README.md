# 项目管理入口

2026-11-19；总管维护管理文件，执行对话维护任务结果，主控人工验收。

| 主控要做什么 | 入口 |
| --- | --- |
| 看做到哪、当前阻塞及全部任务 | [当前状态](project_status.md) |
| 看各阶段成果及退出条件 | [阶段路线图](roadmap.md) |
| 新建总管或执行对话 | [启动提示词](agent_initialization_prompts.md) |
| 定义、交付、验收或接续任务 | [统一任务格式](tasks/README.md) |
| 查角色和更新责任 | [协作标准](collaboration_standard.md) |
| 验收本次重构 | [ORG-03](tasks/ORG-03-TASK-ARCHITECTURE.md) |
| 查设备与历史版本 | [版本交接](version_handoff.md)；历史上传授权不续期 |

日常流程：总管定义 → 主控转交 → 执行记录 → 主控验收 → 反馈总管 → 下一任务。任务中断与退回沿用原ID。

## 历史规划与生成资料

[原计划](project_plan.md)及PDF是历史目标，不是当前进度；其内容源为source/generate_project_plan.py，不只修改派生MD。三人分工PDF源为source/generate_team_outline.py。GitHub教程正文及PDF为历史人工教程，不授权自动上传；其生成器读取正文。原审查见[organization_review](organization_review.md)，旧状态及协作来源在[archive](archive/)。本轮不重生成这些PDF。
