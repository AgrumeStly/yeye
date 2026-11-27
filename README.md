# 椰椰智能小车项目

实际工作区：`D:/projects/projectsyeye`。协作：一个总管规划，执行对话按可验收成果工作，主控亲自验收后反馈总管。

| 日常问题 | 入口 |
| --- | --- |
| 现在做到哪，下一步是什么 | [当前状态与全部任务](project_planning/project_status.md) |
| 队友用 DeepSeek 接续整车开发 | [AI 接续入口与提示词](AI_HANDOFF.md) |
| 各阶段要交付什么 | [阶段路线图](project_planning/roadmap.md) |
| 新建总管／执行对话、反馈验收 | [启动与反馈提示词](project_planning/agent_initialization_prompts.md) |
| 一项任务怎样定义、完成和中断接续 | [任务格式](project_planning/tasks/README.md) |
| 本次重构结果与检查 | [ORG-03](project_planning/tasks/ORG-03-TASK-ARCHITECTURE.md) |
| 文件放哪、事实以哪里为准 | [目录与内容源](DIRECTORY_GUIDE.md) |

当前工程主线为起点直道、左侧直角和钝角联合过弯。主控已确认 v9 完成首个直角弯。最新联合版为 STM32 `0x02120019`／K230 v12 路径接收修订，两弯连续通过和整圈待验。左轮带载无反馈的诊断从任务当前区接续。 [当前任务](project_planning/tasks/I-04-RIGHT-ANGLE.md)

## 模块入口

[官方规则](competition/README.md) · [主控工程](control/README.md) · [视觉与语音](vision/README.md) · [硬件与接线](hardware_preparation/README.md) · [实测证据](testing/README.md) · [报告](report/README.md) · [跨模块主题](docs/README.md)

工程、SPL、协议与原始证据保持原路径。总管只写管理文件，不执行代码／测试／设备动作。旧00／01／02／03为历史来源，主控已于2026-11-19指定新总管，登记见[协作标准](project_planning/collaboration_standard.md)；本轮没有替主控创建聊天。

执行任务完成可交付改动及适用检查后默认按明确范围做本地Git提交；上传当前改动需主控本次明确要求。共享checkout写入、Keil保存／构建、分支与硬件动作串行。被忽略的build／tmp可能有唯一原始日志或Flash备份，不据目录名删除。换设备按[版本交接](project_planning/version_handoff.md)核对本地未同步及工具环境。

队友从 GitHub 获取默认 `main` 后，在仓库根目录把 [AI_HANDOFF.md](AI_HANDOFF.md) 交给能访问该目录的本地 DeepSeek／dsh。当前配对包、源码和现场证据见[版本交接](project_planning/version_handoff.md)。队友按接续说明核对本机工具、语音资源和实际设备版本。
