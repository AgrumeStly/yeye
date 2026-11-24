# 当前状态与任务

更新：2026-11-24。依据：主控要求完整阅读视觉与DeepSeek已放在视觉板上的成果并更新进度，本轮专项读取和资料更新见[TASK-20261124-01-vision-board-review](tasks/TASK-20261124-01-vision-board-review.md)。全局维护职责仍按协作标准；本次只读现有板上资料并更新记录，没有修改运行实现、启动应用测试、构建、刷写或试跑。CanMV连接／断开有软重启输出，不能将本次读取称作无扰动观察。

## 当前判断

- 主控已统一验收当前实际交付的资料、软件、现场结果及进度，范围见[本次验收记录](evidence/2026-11-19_current_acceptance/acceptance.md)，相关任务与索引已同步。当前工程主线仍为S2首弯，完整自主首弯和整圈尚未完成。
- 直道已推进到0x02120003双轮启动适配；主控确认悬空／地面“正常”，最后一次2000ms／LIMIT11及零硬件／UART错误有实读证据。现有交付已验收，不新增触边、距离、摆动或重复性量化。
- 首弯最新为R8：/data迁移及188项离线检查后已部署复测，一次双轮1000ms通过，一次地面499ms／LINK2／源年龄200ms停车；完整日志关联到同步日志78ms叠加下一帧77ms处理，新包晚到4..7ms，修复尚未实施。R7的2041ms PATH3及11月18日858ms LINK是不同历史轮次。
- 首弯最后已确认配对为STM32 0x02120012／v5、视觉release_r8_entry。当前阶段软件、存储／现场交付及诊断已验收；11月24日板上R7／R8与仓库归档逐字节一致，本批新增成果没有替换首弯程序或证明LINK问题已修复。本轮未读STM32 Flash，旧收工LINK锁故障不能当实时状态。
- 最新工程接续见[R8现场记录](../testing/2026-11-18_right_angle/r8_field_record.md)及[I-04当前区](tasks/I-04-RIGHT-ANGLE.md)。后续恢复按主控新指派，KEY／RST由主控操作，一次双轮悬空后一次上道；不重新逐轮识别，不因本次发布自动安排试跑。
- SpeedMatch闭环、视觉采集／离线识别和真实UART已有后续证据，旧“闭环未实现／视觉未归档”不再作为全局现状。HardwareBench老目标边界不等于独立试跑目标边界。
- 语音已推进到板上独立助手源码、关键词模型、四个回应WAV和部分历史识别日志；`events.log`记录“小南小南／Go／Stop”各一次，当前助手能封装v5 START／STOP。`uart_events.log`没有识别或UART事件，`session.wav`为0字节，没有新整车语音启动、接管后3秒停稳或清晰输出验收。全车越线自动停车、完整圈及报告终稿仍缺完整实证；尺寸／重量缺证不因本次阅读补齐。
- 视觉已在既有K230D Lite／128M、CanMV v1.8-0上放置`qoder_scripts`五份语音／图传／采集／UART工具，另有`/data/final_sampling_gc2093`三份采集脚本。主控最新表述确认视觉与DeepSeek已有成果；dsh／DeepSeek仍是开发助手，运行时是本地KPU关键词模型。责任仍由视觉接续语音、主控协调整车接口和验收。AI入口与[语音交接](voice_handoff.md)已更新为实读现状。
- 手机图传S3已有灰度车线标注、MJPEG与遥测源码，不发UART；目标12fps和源码所称328帧验证尚无对应报告。静态采集目录有20张原图／20张调试图、两张彩色参考照及CSV，本轮未目视图片；动态目录枚举超时、单独下载CSV含损坏字节，不能可靠计帧或认定新的标定／识别验证通过。详见[完整阅读报告](evidence/2026-11-24_vision_board_review/review.md)。
- 板上根目录本次没有`/sdcard/main.py`；语音入口为停用的`qoder_scripts/main_voice.py`，R8为独立文件。语音、图传、循迹尚未整合；阻塞录音／播放不能直接插入200ms路径链路。STM32仓库源码仍拒绝远程START，STATUS无回执，接口未改。本次读取后后端已断开，没有恢复应用；后续现场状态须按新指派核对。
- 完整当前版与AI语音交接主提交[15adcc5c1093a3162f27907457687c75e0fd8121](https://github.com/AgrumeStly/yeye/commit/15adcc5c1093a3162f27907457687c75e0fd8121)已同步到开发分支及默认main；补齐此前未提交原位源码与依赖，保留5次已有成果提交。普通clone自动选main且干净，614份非交付回填内容和553份现场原件核对通过；结果回填随后随正常提交同步main，最终号在发布回报中给出。
- 上次[74a45ef架构上传](tasks/TASK-20261119-01-architecture-upload.md)已验收，其文档范围作为历史保留。当前完整发布及未随库内容见[发布任务](tasks/TASK-20261119-02-current-version-main.md)；本机UI／用户路径配置、忽略环境和认证保留本地，未编辑运行源码或进行新功能验证。

## 下一步与管理边界

主控已指定本对话为新总管，并于2026-11-19明确“org-03验收通过”。总管已核对[ORG-03架构交付](tasks/ORG-03-TASK-ARCHITECTURE.md)及归档检查，登记该管理架构成果已验收；该结论不扩大到车辆能力或其它S0任务。

当前唯一下一步：主控核对[11月24日板上阅读成果](tasks/TASK-20261124-01-vision-board-review.md)中的已有实现与待核实范围，再指派后续语音接口／循迹并行任务。本轮不直接进入修改固件、恢复自启动或试跑。视觉已有板上成果，不再把“队友尚未取得仓库／先clone”当当前进度；11月20日[发布任务](tasks/TASK-20261119-02-current-version-main.md)及其待确认状态保留为独立历史交付，本轮未上传。

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
| TASK-20261119-02-current-version-main | S0 | 待主控验收 | [记录](tasks/TASK-20261119-02-current-version-main.md) |
| TASK-20261124-01-vision-board-review | S0／S4 | 待主控验收（板上成果阅读与进度记录） | [记录](tasks/TASK-20261124-01-vision-board-review.md) |

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
