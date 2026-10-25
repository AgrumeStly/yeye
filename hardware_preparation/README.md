# 硬件准备与现场资料入口

更新：2026-10-25（北京时间）。资料提供：硬件；接收与现场归档：主控／02。
本目录保存采购历史、实际接线、结构、供电、测量和维护。已确认按清单采购的型号继续沿用，当前状态查[项目状态](../project_planning/project_status.md)，原始采购日期不改写。

## 1. 当前接续先看这里

| 场景 | 入口与适用范围 |
| --- | --- |
| 当前电机诊断接续 | [MotorDirect](../control/docs/motor_direct.md)：GPIO单次A，独立Keil入口；代码与电脑验证完成，下载／演练／起转回报仍待主控 |
| 实际接线与软件资源 | [wiring.md](wiring.md)与[pin_plan.md](../control/docs/pin_plan.md)：分别维护实物连线和MCU资源；PA0/PA1旧编码器候选已失效 |
| 已测过哪些电压、出现什么现象 | [I-05测量结果](../testing/2026-10-21_motor_bench/i05_measurement_results.md)、[持续版Watch](../testing/2026-10-24_motor_continuous/watch/README.md)及其链接 |
| 首次板级双闪和下载读回 | [board_self_test_record.md](board_self_test_record.md)：2026-10-14记录，不代表电机、UART或整车验收 |
| 型号／照片／厂家资料的来源 | [I-03证据索引](evidence/2026-10-18_i03/README.md)、[原交接](i03_handoff.md) |

当前采用DAPLink单源5V供主板、独立2S供驱动的记录；具体接线按现行任务与规格核对。旧指南中“继续USB供主板”等属历史阶段，不能与DAPLink供电叠加。UC2已停用，旧采购/指南中的充电操作不作为当前入口。

实际逐项清点表尚未建立，后续由硬件记录采购角色、保管角色、到货与电气验收；主控已确认到齐，不因此重复追问既定型号。现有接线确认与完整电气签核分别记录。

## 2. 专项步骤与历史方案

下列页面保留原路径。只有当前任务明确采用的步骤才执行，不把多种方案串成一轮测试。

- [motor_dc_check.md](motor_dc_check.md)：隔离电机与实验室限流电源方案，仪器条件／实测待确认。
- [motor_scope_check.md](motor_scope_check.md)：无动力示波器方案；[scope_results](../testing/2026-10-24_motor_continuous/scope_results.md)尚为待填模板。
- [motor_wiring_self_check.md](motor_wiring_self_check.md)：断电接线自查；第4节表格格式待修，现行逐线规格查wiring。
- [i05_measurement_guide.md](i05_measurement_guide.md)、[原任务](i05_motor_power_diagnosis_task.md)：10-21分阶段测量边界，后来续报已有静态电压；不是“当前无实测”。
- [dual_motor_wiring_guide.md](dual_motor_wiring_guide.md)：首次装配指南，混有不同阶段供电与已停用UC2的历史内容；依赖这些冲突的动作须先由02校正，不直接照旧段落操作。
- [control_bringup_plan.md](control_bringup_plan.md)：历史推进顺序；其中未到货、PWM未实现和PA0/PA1端口为制定时起点，当前资源与状态看上述入口。
- [charger_replacement.md](charger_replacement.md)：替代充电器历史建议，不代表已采购、到货或验证。

本轮只整理导航和状态，以上技术正文待修项见[审查记录](../project_planning/organization_review.md)。

## 3. 采购历史和内容源

采购完成、型号确认和实际运行通过是不同事实。下列文件保留2026-10-10/11制定时的价格、预算与分配，不按“待选型”“未购买”重新描述当前项目。

| 历史文件 | 用途／维护源 |
| --- | --- |
| [hardware_purchase_list.pdf](hardware_purchase_list.pdf) | 详细采购方案；正文/BOM在`source/generate_purchase_list.py` |
| [purchase_list_control.pdf](purchase_list_control.pdf)、[purchase_list_vision.pdf](purchase_list_vision.pdf)、[purchase_list_hardware.pdf](purchase_list_hardware.pdf) | 三人采购分配；`generate_team_purchase_lists.py`读取BOM，分配在脚本 |
| [hardware_modules_overview.pdf](hardware_modules_overview.pdf) | 模块级准备概览；`source/generate_modules_overview.py` |
| `source/purchase_bom.json`、`source/team_purchase_allocation.json` | 生成产物，修改源后再生成 |
| [archive/](archive/) | 600／697元旧方案及生成器／TeX，只作溯源；部分脚本会写回根部旧文件，运行前核对 |

原方案部件估算625.8元、预留20元为历史预算，不是当前报价或已结算费用。实际采用器件与接线以wiring及后续清点为准，采购PDF中的16字节／80ms等旧通信建议以[协议入口](../control/docs/protocol_v1_draft.md)为准。

新文档放本目录、生成器放`source/`、被替代硬件文件放`archive/`；原始证据保留既有路径。比赛资料在[competition/](../competition/README.md)，团队安排在[project_planning/](../project_planning/README.md)。
