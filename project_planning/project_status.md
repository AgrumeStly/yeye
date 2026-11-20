# 当前状态与任务

更新：2026-11-20。依据：主控当前进度统一验收、I-03／I-04最新实证，以及“整理指导AI文档并上传、其余由队友和dsh处理”的明确交接要求。维护：总管；本轮只整理管理文档与已存在版本归档发布，不修改运行实现、不执行功能测试／构建／硬件操作。

## 当前判断

- 主控已统一验收当前实际交付的资料、软件、现场结果及进度，范围见[本次验收记录](evidence/2026-11-19_current_acceptance/acceptance.md)，相关任务与索引已同步。当前工程主线仍为S2首弯，完整自主首弯和整圈尚未完成。
- 直道已推进到0x02120003双轮启动适配；主控确认悬空／地面“正常”，最后一次2000ms／LIMIT11及零硬件／UART错误有实读证据。现有交付已验收，不新增触边、距离、摆动或重复性量化。
- 首弯最新为R8：/data迁移及188项离线检查后已部署复测，一次双轮1000ms通过，一次地面499ms／LINK2／源年龄200ms停车；完整日志关联到同步日志78ms叠加下一帧77ms处理，新包晚到4..7ms，修复尚未实施。R7的2041ms PATH3及11月18日858ms LINK是不同历史轮次。
- 首弯当前配对为STM32 0x02120012／v5、视觉release_r8_entry。当前阶段软件、存储／现场交付及诊断已验收；最后归档视觉已停止、主板LINK锁故障，仅为收工历史，不能当实时状态。
- 最新工程接续见[R8现场记录](../testing/2026-11-18_right_angle/r8_field_record.md)及[I-04当前区](tasks/I-04-RIGHT-ANGLE.md)。后续恢复按主控新指派，KEY／RST由主控操作，一次双轮悬空后一次上道；不重新逐轮识别，不因本次发布自动安排试跑。
- SpeedMatch闭环、视觉采集／离线识别和真实UART已有后续证据，旧“闭环未实现／视觉未归档”不再作为全局现状。HardwareBench老目标边界不等于独立试跑目标边界。
- 语音、全车越线后自动停车、完整圈及报告终稿尚未形成完整实证；结构尺寸／重量等历史缺证仍按原证据核对，不以本次当前进度验收补造测量或未实施能力。
- 主控现已明确语音接续交给队友电脑上的本地dsh，沿用现有K230麦克风和扬声器。AI阅读入口为[AI_HANDOFF.md](../AI_HANDOFF.md)和[语音交接](voice_handoff.md)；本次只整理文档并上传，队友本机环境、方案、实现及验证由视觉与dsh继续。当前研发目标拒绝远程START，STATUS无实际动作回执，交接已列明，未改接口。
- 当前本地分支codex/current-version-20261025，HEAD 82e237ed3e127b0bebc1846d932f7e9b3c28b05e；相对本地远端跟踪引用领先5次成果提交，另有共享未提交原位源码及未跟踪依赖。GitHub元数据核对默认分支仍为main，本轮总管未推送或更新main。
- 上次[74a45ef架构上传](tasks/TASK-20261119-01-architecture-upload.md)已由主控本次统一验收；其67份文件仅为当次文档范围。现授权通过新发布任务整理完整原位实现与依赖到main，解决此前仅有patch／快照、默认clone仍是旧版的问题。

## 下一步与管理边界

主控已指定本对话为新总管，并于2026-11-19明确“org-03验收通过”。总管已核对[ORG-03架构交付](tasks/ORG-03-TASK-ARCHITECTURE.md)及归档检查，登记该管理架构成果已验收；该结论不扩大到车辆能力或其它S0任务。

唯一下一步：[完整当前版本发布到main](tasks/TASK-20261119-02-current-version-main.md)按主控本次直接指派进行中，纳入指导dsh接续语音的两份文档。本次完整版本归档、上传、main同步及普通clone核对已获授权；本对话完成文档与发布，其余开发工作交给队友与dsh，不再安排本机语音实现任务。

S2工程后续继续[I-04-RIGHT-ANGLE原任务](tasks/I-04-RIGHT-ANGLE.md)的同步日志阻塞修复；当前发布不修改算法、放宽保护或恢复设备动作，不重复索取已确认阶段成果的验收。

阶段退出条件见[路线图](roadmap.md)。任务详细状态与结果以各文件当前区为准；下表只是同一事实的全局索引，不另维护第二张待办表。“待核实”不表示从零开始；“已验收”均有具体范围，不能外推整车。

## 全部任务索引与旧称映射

仅说I-03／I-04有歧义：I-03-HARDWARE-HANDOFF为旧硬件资料，I-03-STRAIGHT-ASSIST为直道；I-04-HARDWARE-WIRING为旧接线签核，I-04-RIGHT-ANGLE为首弯。必须使用完整标识或路径。

| 唯一标识 | 阶段 | 状态（范围见任务） | 任务路径 |
| --- | --- | --- | --- |
| C-02B-PWM-R4 | S1 | 已验收 | [记录](tasks/C-02B-PWM-R4.md) |
| C-02C | S1 | 待核实 | [记录](tasks/C-02C.md) |
| C-02D | S1 | 待核实 | [记录](tasks/C-02D.md) |
| C-02E | S1 | 已验收（现有软件交付） | [记录](tasks/C-02E.md) |
| C-02F | S1 | 已验收 | [记录](tasks/C-02F.md) |
| C-02G | S3 | 已验收（现有软件／模型） | [记录](tasks/C-02G.md) |
| C-OLED-01 | S1 | 已验收 | [记录](tasks/C-OLED-01.md) |
| G-03 | S0 | 待核实 | [记录](tasks/G-03.md) |
| G-04 | S0 | 待核实 | [记录](tasks/G-04.md) |
| G-05 | S0 | 待核实 | [记录](tasks/G-05.md) |
| G-06 | S0 | 待核实 | [记录](tasks/G-06.md) |
| G-07 | S0 | 待核实 | [记录](tasks/G-07.md) |
| H-03 | S1 | 待核实 | [记录](tasks/H-03.md) |
| I-02-LOW-SPEED-LAP | S2 | 进行中 | [记录](tasks/I-02-LOW-SPEED-LAP.md) |
| I-03-STRAIGHT-ASSIST | S2 | 已验收（02基线及03当前交付） | [记录](tasks/I-03-STRAIGHT-ASSIST.md) |
| I-04-RIGHT-ANGLE | S2 | 进行中（R8当前阶段交付已验收） | [记录](tasks/I-04-RIGHT-ANGLE.md) |
| ORG-01 | S0 | 已关闭 | [记录](tasks/ORG-01.md) |
| ORG-02 | S1 | 已验收（现有分层／迁移交付） | [记录](tasks/ORG-02.md) |
| REVIEW-20261107 | S0 | 待核实 | [记录](tasks/REVIEW-20261107.md) |
| V-01 | S1 | 待核实 | [记录](tasks/V-01.md) |
| V-02 | S1 | 已验收（现有电脑离线交付） | [记录](tasks/V-02.md) |
| V-03 | S1 | 已验收（现有静态分析） | [记录](tasks/V-03.md) |
| V-04 | S1 | 已验收（现有采集／保存交付） | [记录](tasks/V-04.md) |
| V-05 | S1 | 已验收（现有纵向参照） | [记录](tasks/V-05.md) |
| V-06 | S2 | 已验收（现有电脑候选／回放） | [记录](tasks/V-06.md) |
| V-07 | S4 | 已验收（现有终点观测／回放） | [记录](tasks/V-07.md) |
| V-08 | S1 | 已验收（现有诊断／准备） | [记录](tasks/V-08.md) |
| C-02B-R2 | S1 | 待核实 | [记录](../control/docs/motor_bench_r2_task.md) |
| C-02B-R3 | S1 | 待核实 | [记录](../control/docs/motor_bench_r3_task.md) |
| I-03-HARDWARE-HANDOFF | S1 | 待核实 | [记录](../hardware_preparation/i03_handoff.md) |
| I-05-MOTOR-POWER-DIAGNOSIS | S1 | 待核实 | [记录](../hardware_preparation/i05_motor_power_diagnosis_task.md) |
| ORG-03-TASK-ARCHITECTURE | S0 | 已验收 | [记录](tasks/ORG-03-TASK-ARCHITECTURE.md) |
| TASK-20261119-01-architecture-upload | S0 | 已验收 | [记录](tasks/TASK-20261119-01-architecture-upload.md) |
| TASK-20261119-02-current-version-main | S0 | 进行中 | [记录](tasks/TASK-20261119-02-current-version-main.md) |

## 旧全局登记、无独立任务单的缺口

以下保留旧登记，不虚构开工／完成。原定义与证据在[迁移前状态](archive/2026-11-19_project_status.md)，恢复前总管先界定当前缺口再建成果任务，禁止直接执行旧操作。

| 旧登记／当前完整标识 | 当前处理 |
| --- | --- |
| P-01 | 报名已由主控确认，见[报名记录](../competition/registration_status.md)；原整体协调计划非当前完成判据 |
| H-01／H-02 | 实物清点、接线签核须按当前车型证据核对，待核实；采购到齐不等于全电气验收 |
| C-01 | HardwareBench老框架验收待核实，不得阻塞独立RightAngle候选 |
| I-01 | 原20字节冻结／固定包范围待核实；当前v5实车链路不能不加区分地代替其原定义 |
| C-02／C-02B | 原父项，按各具体任务记录核对，不再独立派一份重复驱动工作 |
| C-02A | 引脚资源历史已采用，实物与当前映射另查权威文件，不新建副本 |
| C-02B-R1 | 旧启动修复和绿灯恢复记录保留，完整自主启动范围待核实 |
| I-04-HARDWARE-WIRING | 旧接线／供电签核，待核实；与I-04-RIGHT-ANGLE不同 |
| MotorDirect／持续A | 起转成功与旧失败分别保留；不是当前首弯下一步 |
| G-01／G-02 | 历史同步见[版本交接](version_handoff.md)，本轮不联网复核、不续用上传授权 |

全部旧任务已统一格式，历史正文及旧授权仍保留在各自历史区。[迁移记录](tasks/ORG-03-TASK-ARCHITECTURE.md)说明覆盖范围和检查边界。
