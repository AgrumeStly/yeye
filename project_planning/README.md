# 项目规划

- [对话分工与标准文档](collaboration_standard.md)：长期对话的职责、旧对话衔接建议、标准文档入口、内容源和交接方式。
- [当前状态与任务](project_status.md)：当前进展、证据、近期任务与文档冲突的统一汇总。日常先看这一份，原规划保留目标与里程碑。
- [项目协作对话初始化Prompt](agent_initialization_prompts.md)：00项目总指挥、01主控固件开发、02整车联调与拼组、03GitHub与多设备同步的初始化文本及任务分配模板。主控向00汇报，00生成Prompt交由主控转发。
- [版本与设备交接记录](version_handoff.md)：03维护设备、目录、分支、提交、未同步项和接续步骤；笔记本未实际核对前保持待确认。

- [GitHub三人协作操作手册](github_collaboration_guide.pdf)：21页零基础教程，覆盖首次接入、每天开发、换电脑、PR、冲突、撤销和稳定版发布；第20页为日常速查。
- [教程可编辑正文](github_collaboration_guide.md)：教程内容源，`source/generate_github_guide.py`从它生成PDF。

- [项目规划书](project_plan.pdf)：按硬件、视觉、主控分工的执行计划。
- [规划文字版](project_plan.md)：便于阅读与修改。
- [三人分工大纲](team_work_outline.pdf)：角色职责及阶段概览。
- `source/generate_project_plan.py`：生成当前目录内的规划PDF和Markdown。
- `source/generate_team_outline.py`：生成当前目录内的分工大纲PDF。

规划书和分工大纲的内容源在对应生成脚本内；规划生成器会覆盖规划Markdown和PDF。GitHub教程以Markdown为内容源。对话标准和当前状态直接维护Markdown。具体生成方向见对话与文档标准，修改时先确认内容源。

后续进度表、会议决定与待办清单放在本目录；被替代的规划放 `archive/`（有需要时创建）。比赛官方资料见 `../competition/`。
