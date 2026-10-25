# 智能小车项目

项目目录：`D:/Projects/yeye`。团队角色：主控、视觉、硬件。资料按“比赛要求 → 计划与任务 → 模块实现 → 实测证据 → 报告交付”组织。

## 日常从这里开始

| 当前要做什么 | 入口 |
| --- | --- |
| 按架构、硬件、接口、任务、测试主题查资料 | [docs统一入口](docs/README.md) |
| 看现在做到哪、接下来做什么 | [当前状态与任务](project_planning/project_status.md) |
| 判断该找哪个Codex对话、怎样交接 | [协作标准与对话登记](project_planning/collaboration_standard.md) |
| 给现有对话更新职责或恢复上下文 | [完整接续Prompt](project_planning/agent_initialization_prompts.md) |
| 在笔记本Clone当前版本并接续Codex | [G-03上传与设备接续](project_planning/tasks/G-03.md) |
| 交付一项跨轮任务 | [任务文件与模板](project_planning/tasks/README.md) |
| 查文件放哪、以哪份为准 | [目录与内容源](DIRECTORY_GUIDE.md) |
| 看本次为什么这样整理、阅读和检查范围 | [体系审查与迁移记录](project_planning/organization_review.md) |

00负责全局安排与验收；01负责固件；02负责装配、测量与整车联调；03按需负责版本和设备交接。主控可直接向01／02提出清晰模块任务；范围、接口、排期与跨模块问题归00。执行结果保存到文件，00读取证据后更新全局判断。

## 按模块进入

- [比赛资料](competition/README.md)：官方规则与后续通知，原文件保留。
- [项目管理](project_planning/README.md)：当前状态、协作规则、任务与历史计划。
- [主控开发](control/README.md)：现有STM32F407／SPL／Keil工程、学习与操作说明。
- [硬件准备](hardware_preparation/README.md)：已确认型号、接线与测量入口；采购文件按历史资料阅读。
- [视觉与语音](vision/README.md)：已有参考、样本及视觉后续正式交付。
- [联调与测试](testing/README.md)：下载、板内观察、电压与整车结果的原始记录。
- [报告与答辩](report/README.md)：引用已留证成果，不承担当前技术状态维护。

目录按业务模块划分，不按聊天名称再复制一份工程。任务文件连接对话、代码与证据；聊天换新后从这些文件继续。

2026-10-25按主控确认完成STM32物理分层：Core／App／Drivers_Custom／Drivers／Algorithms／Tests／MDK-ARM位于control内。结构图见[architecture.md](docs/architecture.md)，原工程入口改为[control/MDK-ARM/yeye_control.uvprojx](control/MDK-ARM/yeye_control.uvprojx)，MotorDirect独立入口为[control/MDK-ARM/motor_direct.uvprojx](control/MDK-ARM/motor_direct.uvprojx)。继续沿用SPL，不生成CubeMX的.ioc。迁移与实际检查见[ORG-02](project_planning/tasks/ORG-02.md)。

## 本地保存与同步

远端：[AgrumeStly/yeye](https://github.com/AgrumeStly/yeye)。仓库访问范围以实际设置为准。

默认保存并验证本地改动；主控明确要求上传本轮改动后，由03按范围处理。推送、合并、发布分别核对授权。换电脑按[版本交接记录](project_planning/version_handoff.md)核对目录、分支、完整提交及未同步文件。

同一目录中的对话共享工作文件与Git分支，写入、Keil构建、IDE保存和硬件操作按顺序进行。需要并行开发时先安排独立worktree及合回路径；当前未提交改动、下载器配置、编译输出和原始附件须单独核对。

`tmp/` 和 `build/` 是本机工作区，其中可能存在唯一原始日志或Flash备份；清理前逐项检查。新目录使用英文名。
