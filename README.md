# 椰椰智能小车项目

实际工作区：`D:/projects/projectsyeye`。协作：一个总管规划，执行对话按可验收成果工作，主控亲自验收后反馈总管。

| 日常问题 | 入口 |
| --- | --- |
| 现在做到哪，下一步是什么 | [当前状态与全部任务](project_planning/project_status.md) |
| 队友用本地dsh继续语音开发 | [AI接续入口](AI_HANDOFF.md) → [K230语音交接](project_planning/voice_handoff.md) |
| 各阶段要交付什么 | [阶段路线图](project_planning/roadmap.md) |
| 新建总管／执行对话、反馈验收 | [启动与反馈提示词](project_planning/agent_initialization_prompts.md) |
| 一项任务怎样定义、完成和中断接续 | [任务格式](project_planning/tasks/README.md) |
| 本次重构结果与检查 | [ORG-03](project_planning/tasks/ORG-03-TASK-ARCHITECTURE.md) |
| 文件放哪、事实以哪里为准 | [目录与内容源](DIRECTORY_GUIDE.md) |

当前工程主线为首弯；独立直道一次80RPM／2秒已确认，完整自主过弯及整圈待验。首弯最后故障为LINK超龄，具体版本与恢复步骤查任务记录，不执行旧对话的过期操作。

## 模块入口

[官方规则](competition/README.md) · [主控工程](control/README.md) · [视觉与语音](vision/README.md) · [硬件与接线](hardware_preparation/README.md) · [实测证据](testing/README.md) · [报告](report/README.md) · [跨模块主题](docs/README.md)

工程、SPL、协议与原始证据保持原路径。总管只写管理文件，不执行代码／测试／设备动作。旧00／01／02／03为历史来源，主控已于2026-11-19指定新总管，登记见[协作标准](project_planning/collaboration_standard.md)；本轮没有替主控创建聊天。

执行任务完成可交付改动及适用检查后默认按明确范围做本地Git提交；上传当前改动需主控本次明确要求。共享checkout写入、Keil保存／构建、分支与硬件动作串行。被忽略的build／tmp可能有唯一原始日志或Flash备份，不据目录名删除。换设备按[版本交接](project_planning/version_handoff.md)核对本地未同步及工具环境。

当前完整版本与默认main发布情况见[发布任务](project_planning/tasks/TASK-20261119-02-current-version-main.md)及[版本交接](project_planning/version_handoff.md)。队友从仓库根目录的[AI_HANDOFF.md](AI_HANDOFF.md)交给本地dsh接续；本机环境、语音方案、实现和验证在队友电脑继续处理。工具安装、模型获取及板上文件状态以交接说明和实际设备为准，不随Git自动恢复。
