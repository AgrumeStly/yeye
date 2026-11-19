# 当前状态与任务

更新：2026-11-19。依据：仓库任务、已归档迁移检查与首弯接续，以及主控本日的新总管指派、ORG-03验收通过、本地提交规则确认和新项目架构上传要求。维护：本对话总管，身份见协作标准；本轮仅核对记录并维护管理文件，未操作设备或验证整车。

## 当前判断

- 当前工程主线：S2首弯。一次直道80RPM／2秒已由主控确认；完整自主首弯和整圈尚未通过。
- 首弯最后记录：11月18日运行858ms、LINK2／源年龄200ms停车，未进弯；不是前次2861ms的PATH3。先查日志保存及处理／发送间隔，不放宽保护或先增转向。
- 配对版本：STM32 0x02120012／v5、视觉release_r6_final。最后归档为视觉已停止、故障锁定；这是历史记录，不能当本轮实时状态。
- 先读[I-04完整接续](../testing/2026-11-18_right_angle/resume_20261119.md)。恢复需主控转交；KEY／RST由主控操作，一次双轮悬空后一次上道。保留已跑通映射，不再逐轮识别。
- SpeedMatch闭环、视觉采集／离线识别和真实UART已有后续证据，旧“闭环未实现／视觉未归档”不再作为全局现状。HardwareBench老目标边界不等于独立试跑目标边界。
- 语音、全车越线后自动停车、完整圈及报告终稿未取得完整验收；结构尺寸／重量、其它设备同步等缺口仍须总管按原证据核对，不能由源码推定。
- 迁移时本地分支codex/current-version-20261025，HEAD 62b4f288b27c4e3fa9f6d213c07be186e502f43c，保留共享未提交／未跟踪成果。远端及板上未重新核验。

## 下一步与管理边界

主控已指定本对话为新总管，并于2026-11-19明确“org-03验收通过”。总管已核对[ORG-03架构交付](tasks/ORG-03-TASK-ARCHITECTURE.md)及归档检查，登记该管理架构成果已验收；该结论不扩大到车辆能力或其它S0任务。

唯一下一步：主控将[新项目架构上传任务](tasks/TASK-20261119-01-architecture-upload.md)转交一个执行对话。本次文档架构上传授权已明确，任务范围及同名目标分支已定义，尚未执行上传；当前控制／视觉实现及其它共享成果保留在本地，不夹带提交。上传结果交回后由主控验收、总管更新状态。

S2工程主线仍是[I-04-RIGHT-ANGLE原任务](tasks/I-04-RIGHT-ANGLE.md)，接续定义已准备，尚未重新转交或开工；先排查日志保存与LINK2／源年龄200ms的处理／发送间隔。架构上传不恢复I-04实现或设备授权。

阶段退出条件见[路线图](roadmap.md)。任务详细状态与结果以各文件当前区为准；下表只是同一事实的全局索引，不另维护第二张待办表。“待核实”不表示从零开始；“已验收”均有具体范围，不能外推整车。

## 全部任务索引与旧称映射

仅说I-03／I-04有歧义：I-03-HARDWARE-HANDOFF为旧硬件资料，I-03-STRAIGHT-ASSIST为直道；I-04-HARDWARE-WIRING为旧接线签核，I-04-RIGHT-ANGLE为首弯。必须使用完整标识或路径。

| 唯一标识 | 阶段 | 状态（范围见任务） | 任务路径 |
| --- | --- | --- | --- |
| C-02B-PWM-R4 | S1 | 已验收 | [记录](tasks/C-02B-PWM-R4.md) |
| C-02C | S1 | 待核实 | [记录](tasks/C-02C.md) |
| C-02D | S1 | 待核实 | [记录](tasks/C-02D.md) |
| C-02E | S1 | 待主控验收 | [记录](tasks/C-02E.md) |
| C-02F | S1 | 已验收 | [记录](tasks/C-02F.md) |
| C-02G | S3 | 待主控验收 | [记录](tasks/C-02G.md) |
| C-OLED-01 | S1 | 已验收 | [记录](tasks/C-OLED-01.md) |
| G-03 | S0 | 待核实 | [记录](tasks/G-03.md) |
| G-04 | S0 | 待核实 | [记录](tasks/G-04.md) |
| G-05 | S0 | 待核实 | [记录](tasks/G-05.md) |
| G-06 | S0 | 待核实 | [记录](tasks/G-06.md) |
| G-07 | S0 | 待核实 | [记录](tasks/G-07.md) |
| H-03 | S1 | 待核实 | [记录](tasks/H-03.md) |
| I-02-LOW-SPEED-LAP | S2 | 进行中 | [记录](tasks/I-02-LOW-SPEED-LAP.md) |
| I-03-STRAIGHT-ASSIST | S2 | 已验收 | [记录](tasks/I-03-STRAIGHT-ASSIST.md) |
| I-04-RIGHT-ANGLE | S2 | 进行中 | [记录](tasks/I-04-RIGHT-ANGLE.md) |
| ORG-01 | S0 | 已关闭 | [记录](tasks/ORG-01.md) |
| ORG-02 | S1 | 待主控验收 | [记录](tasks/ORG-02.md) |
| REVIEW-20261107 | S0 | 待核实 | [记录](tasks/REVIEW-20261107.md) |
| V-01 | S1 | 待核实 | [记录](tasks/V-01.md) |
| V-02 | S1 | 待主控验收 | [记录](tasks/V-02.md) |
| V-03 | S1 | 待主控验收 | [记录](tasks/V-03.md) |
| V-04 | S1 | 待主控验收 | [记录](tasks/V-04.md) |
| V-05 | S1 | 待主控验收 | [记录](tasks/V-05.md) |
| V-06 | S2 | 待主控验收 | [记录](tasks/V-06.md) |
| V-07 | S4 | 待主控验收 | [记录](tasks/V-07.md) |
| V-08 | S1 | 待主控验收 | [记录](tasks/V-08.md) |
| C-02B-R2 | S1 | 待核实 | [记录](../control/docs/motor_bench_r2_task.md) |
| C-02B-R3 | S1 | 待核实 | [记录](../control/docs/motor_bench_r3_task.md) |
| I-03-HARDWARE-HANDOFF | S1 | 待核实 | [记录](../hardware_preparation/i03_handoff.md) |
| I-05-MOTOR-POWER-DIAGNOSIS | S1 | 待核实 | [记录](../hardware_preparation/i05_motor_power_diagnosis_task.md) |
| ORG-03-TASK-ARCHITECTURE | S0 | 已验收 | [记录](tasks/ORG-03-TASK-ARCHITECTURE.md) |
| TASK-20261119-01-architecture-upload | S0 | 未开始 | [记录](tasks/TASK-20261119-01-architecture-upload.md) |

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
