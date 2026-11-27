# DeepSeek 项目开发交接

2026-11-27 更新。主控把最新进度交给队友和本地 DeepSeek／dsh，接续 STM32、K230 循迹与语音、联调、证据和报告。开发助手在队友电脑上读写仓库，车上使用 K230 本地关键词模型。主控负责车辆操作、实车验收和远端发布授权，硬件负责实际电气取证。

## 在队友电脑开始

```powershell
git clone https://github.com/AgrumeStly/yeye.git
cd yeye
git status --short --branch
git rev-parse HEAD
```

在这个目录启动能访问工作区的本地 DeepSeek／dsh，复制本页最后一节的提示词。已有仓库的队友先检查本地修改，再从默认 `main` 更新。工作目录、Keil 编译器、Python 环境、COM 号及板上版本按队友现场核对。

1. 读取 [AGENTS.md](AGENTS.md)、[项目技能](.agent/skill/grill-me/SKILL.md)和[协作标准](project_planning/collaboration_standard.md)。
2. 读取[当前状态](project_planning/project_status.md)及[I-04-RIGHT-ANGLE 当前摘要和执行结果](project_planning/tasks/I-04-RIGHT-ANGLE.md)。历史区保留当时的版本和授权。
3. 查看[比赛 PDF](competition/比赛文档.pdf)第三部分、图 1 和表 1，可搜索[转写](competition/比赛文档.md)。工程入口见[架构](docs/architecture.md)、[STM32](control/README.md)、[视觉](vision/README.md)及[协议](control/docs/protocol_v1_draft.md)。
4. 按下表选当前任务所需的实现、配对包和证据。板上语音资源的来历见[语音历史交接](project_planning/voice_handoff.md)。

## 当前工程状态

| 范围 | 已有成果与待验 |
| --- | --- |
| 独立语音直道 | StraightVoice `0x02120004`。主控听到开机应答，排查取景后反馈 Go 表现“符合预期”。起步后车辆量化证据待补。见[直道任务](project_planning/tasks/TASK-20261124-02-straight-voice.md)。 |
| 首个直角弯 | RightAngleVoice `0x02120015`／K230 v9。主控确认完整通过首弯，停后绿灯快闪，故障码和触边数据待核。见 [v9 实车参数及配对包](testing/2026-11-18_right_angle/voice_v9_pass_baseline/parameters.md)。 |
| 起点直道、直角及钝角联合版 | 当前开发基线为 JointAngleVoice `0x02120019`／K230 v12 路径接收修订，电脑检查及 STM32 构建有记录，K230 写入后逐字节读回一致。此回执记载配套 STM32 尚未下载。两弯连续通过待验。见[配对说明](control/docs/joint_angle_voice.md)和[交接配对包](testing/2026-11-25_joint_angle_voice/v12_timing_fix_release/README.md)。 |
| 优先处理的实车故障 | 较早的 v12 兼容修订在起步 301 ms 时触发左轮无反馈，软件请求在、左轮原始计数为零，隔离动力手转能计数。带载驱动输出仍待硬件取证。见[冻结记录](testing/2026-11-25_joint_angle_voice/v12_left_no_feedback_swd.json)及[硬件定位任务](hardware_preparation/i05_motor_power_diagnosis_task.md)。 |
| 比赛验收缺口 | 顺时针完整一圈的用时与触边、冲线自动停车、语音接管后 3 秒停稳、应答清晰度与自选口令完整演示仍待取证，报告终稿待完成。见[比赛规则](competition/比赛文档.pdf)和[报告目录](report/README.md)。 |

联合版复用 K230 上的模型和 WAV，项目配对包内含本项目的“收到”音频。准备新板时按配对包的资源清单核对。项目工作区的登录凭据、驱动、虚拟环境和 IDE 用户设置由各自电脑管理。

开发先沿用 `I-04-RIGHT-ANGLE`。从现有冻结和日志梳理左轮故障与路径误停各自的证据，保留 KEY（WKUP）急停、路径超龄、失线和轮速保护。硬件取得同趟带载对照后，按首个异常点收敛修复；主控再对配对版本做 Go 上道验收，记录两轮反馈、两弯、用时、触边、停车码和语音应答。按表 1 优先解决影响完圈的故障，再推进剩余赛段和完整语音验收。

## 可直接复制给 DeepSeek

```text
当前目录是从 GitHub 获取的椰椰智能小车仓库。作为本地开发执行助手，接续 STM32、K230 循迹与语音、联调和报告相关开发。
先实际读取 AI_HANDOFF.md，再按其中顺序读 AGENTS.md、比赛规则、协作标准、当前状态和 I-04-RIGHT-ANGLE 的当前区。运行 git status 和 git rev-parse HEAD，报告实际路径、分支、完整提交号，以及最新工作版本、已验结果和待验事项。没有本地文件权限时先说明缺项。
先沿 I-04-RIGHT-ANGLE 核对 v12 的配对文件、停车冻结及左轮带载证据缺口，按已授权范围继续源码、离线验证和任务记录。v9 实车过首弯、v12 软件检查与 v12 实车待验分别记录。保留急停和故障保护，现场动作由主控和硬件执行。
每项改动关联比赛评分项及验证证据。主应用使用详细中文注释，保留共享修改，完成可交付改动后按完整任务 ID 本地提交。实车通过以主控反馈为准，上传按主控当次授权办理。
```
