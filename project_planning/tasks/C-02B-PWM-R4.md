# C-02B-PWM-R4：删除旧PWM实现并重写起转测试

日期：2026-10-25（北京时间）。状态：完成，软件交付与主控A/B分步PWM起转、自动停转人工验收完成。责任：主控／01实现与本地检查；主控操作Keil及马达，02接收现场证据；00按文件顺序汇总。

依据：主控本轮确认AB直接通电均能旋转，要求开始PWM测试，随后明确“不要看之前的代码，之前的代码驱动不起来，你删掉重新写”。属于清晰模块任务，无新增跨对话消息或远端授权。

## 已确认事实与边界

AB在Direct阶段各自能转，沿用已确认硬件与接线；[Direct现场证据](../../testing/2026-10-25_motor_direct/acceptance_record.md)。旧PWM未转为历史事实，新软件检查不算旧根因定位或新实物通过。

## 范围与交付

- 删除并重写 `control/Core/Src/motor_bench_main.c` 与 `control/Drivers_Custom/Motor/motor_bench_pwm.c`，更新接口头；保持SPL、时钟核对、启动限时、1ms监督及IWDG。
- 新测试1kHz／50%／每次500ms，仅IN1切PWM、IN2普通GPIO低；A/B按键分别触发。纯按键状态机与Direct共用，本轮不改其行为。
- 独立 [motor_pwm.uvprojx](../../control/MDK-ARM/motor_pwm.uvprojx)，目标MotorPwm，版本0x020B0004；[Keil步骤](../../control/docs/motor_pwm.md)与[现场记录](../../testing/2026-10-25_motor_pwm/acceptance_record.md)。
- 原六目标保留，MotorBench采用新单次PWM。共用驱动的MotorContinuous仍20kHz／30%、人工持续A及停止锁定，版本升0x020B1002；Direct A/B源码与工程不因本轮改变。

## 执行顺序与验收

1. 重写、构建、电脑模型检查、保存软件证据。
2. 主控在MotorPwm下载，动力断开演练；再RST回A阶段。
3. 悬空A单次起转/自动撤驱动正常后继续B；B结束OFF并拔XT30，不触发AB。
4. 任一步不转或异常即停止，保存版本、动作及灯态；必要时无动力读取保留帧。实物通过须主控回报，未提供的项目不补填。

## 本次授权

本地代码重写与检查、准备PWM测试，实物由主控手动执行。无远端上传、跨聊天消息、代理自动下载/复位/通电。共享checkout写入与构建顺序执行；当前Keil窗口在MotorDirectB，未关闭或保存该窗口。旧实现仅在Git忽略的 `control/build/pwm_rewrite_backup_20261025/` 留本地恢复副本，不再作为新PWM源码。

## 执行结果

- 2026-10-25：独立MotorPwm、原MotorBench、MotorContinuous均0错误0警告。PWM适配器返回失败时同滴答撤驱动并锁存故障32。
- 新PWM168项／9场景，启动154项／10场景，按键73项；持续115项／7场景及启动154项；Direct A/B各52593项／9场景及Direct启动154项通过。BIN哈希与日志见[模块说明](../../control/docs/motor_pwm.md)、[软件证据](../../testing/2026-10-25_motor_pwm/software/)。
- 独立工程及本机uvoptx已核对XML、CMSIS-DAP配置；uvoptx不由Git同步。准备工程时XML空字段被格式化为换行空白，导致Keil退出15；规范化空字段后已实际构建通过，没有进入板卡测试。
- 实物：主控随后回报“全部符合预期”，确认本轮下载/演练、A/B分别PWM起转与约500ms自动停转、阶段灯态和断动力收尾符合完整流程，人工验收完成；原始文字与细分结果见[现场记录](../../testing/2026-10-25_motor_pwm/acceptance_record.md)。未单独提供Watch版本、波形、仪器计时或录像，不补造相应读数。
- 本项结束，无需为本项新增测试。00可读取本任务及现场记录更新全局摘要；AB同时运行、编码器与闭环等后续范围另行安排。

## 接续位置

目录 `D:/projects/projectsyeye`；分支 `codex/current-version-20261025`；起始HEAD `0f033c6f67e5d4bef27b1c5afdd9d7014ac0456d`。开工已有Direct A/B、笔记本Keil及证据未提交改动，全部保留；本次也未提交、未上传。全局状态由00读取本任务与现场记录后更新。
