# 主控开发：STM32 SPL分层工程

更新：2026-10-25（北京时间，ORG-02）。维护：主控／01。
既有STM32F407VET6、SPL V1.3.0、Keil5与六个目标继续使用；本轮只迁目录和引用，应用代码字节及运行行为保留。

## 打开哪个工程

2026-10-29当前安装变化：左右轮已互换，主控新命名物理A=当前左、B=当前右；旧前进旋转方向现为对应新轮侧后退。**物理A/B不等于驱动MOTOR-A/B或软件a/b**，当前关系及参数沿用统一查[wheel_mapping.md](../hardware_preparation/wheel_mapping.md)。[C-02C](../project_planning/tasks/C-02C.md)与[EncoderBench教程](docs/encoder_bench.md)中的10月25日标定保留为原安装历史，[原始记录](../testing/2026-10-25_encoder/acceptance_record.md)不改写。当前通道及实测方向尚待对应，未写固件；[C-02D](../project_planning/tasks/C-02D.md)已修订输入但本轮不启动实施。原EncoderBench零输出与MotorPwm桥级转停证据保留，不宣称新安装极性已验收。

2026-10-25最新电机工作：主控确认AB直接驱动均正常后，要求删除旧PWM实现重写。现已替换PWM入口与驱动，当前实测入口为 [MotorPwm独立工程](MDK-ARM/motor_pwm.uvprojx)，目标 **MotorPwm**、版本0x020B0004、1kHz／50%／500ms；先A正常再B。按[新PWM步骤](docs/motor_pwm.md)操作，[任务与检查](../project_planning/tasks/C-02B-PWM-R4.md)。共用驱动的MotorContinuous升0x020B1002，仍20kHz／30%持续A；本页后文ORG-02数值为迁移时证据。

本轮结果：主控回报“全部符合预期”，A/B分别PWM起转、自动停转及对应灯态人工验收完成。[现场记录](../testing/2026-10-25_motor_pwm/acceptance_record.md)保留回报与测量边界；本项任务完成。

| 场景 | 入口 |
| --- | --- |
| 双编码器只读手转／整圈标定 | [MDK-ARM/encoder_bench.uvprojx](MDK-ARM/encoder_bench.uvprojx)，只有EncoderBench；[操作](docs/encoder_bench.md) |
| 已通过的PWM分步测试／复现基线 | [MDK-ARM/motor_pwm.uvprojx](MDK-ARM/motor_pwm.uvprojx)，只有MotorPwm；[操作与结果](docs/motor_pwm.md) |
| Direct A诊断对照 | [MDK-ARM/motor_direct.uvprojx](MDK-ARM/motor_direct.uvprojx)，只有MotorDirect；[人工步骤](docs/motor_direct.md) |
| 查看全部六目标／继续开发 | [MDK-ARM/yeye_control.uvprojx](MDK-ARM/yeye_control.uvprojx) |
| 无硬件学习 | 多目标工程选择LogicDemo；[Keil说明](docs/keil_quickstart.md)、[SPL说明](docs/standard_library.md) |
| 看分层和各文件归属 | [整车架构](../docs/architecture.md)、[API索引](../docs/interfaces.md) |
| 查已验证范围 | [validation.md](docs/validation.md)、[整车状态](../project_planning/project_status.md)、[ORG-02](../project_planning/tasks/ORG-02.md) |

主控在Keil用Project → Open Project打开上述新路径。原control/firmware中的正式工程已迁走，该目录只保留历史本机缓存；不再打开旧UART临时工程。没有创建CubeMX配置或.ioc文件。

## 文件按层放置

```text
control/
├── Core/
│   ├── Inc/stm32f4xx_conf.h
│   ├── Src/                 main.c和各独立目标入口（含EncoderBench）
│   └── Startup/             F407启动汇编及许可
├── App/
│   ├── Car/                 car.c / car.h
│   └── Diagnostics/         motor_bench.c / motor_bench.h
├── Drivers_Custom/
│   ├── Board/               board.c / board.h
│   ├── Motor/               motor_bench_pwm与motor_direct_gpio
│   ├── Communication/       protocol.c / protocol.h
│   └── Encoder/             TIM3／TIM4实际计数读取
├── Drivers/                 cmsis / stm32 / stdperiph
├── Algorithms/              Encoder增量／回绕／时间换算纯算法
├── Tests/Host/              原电脑测试和fakes
├── MDK-ARM/                 yeye_control与motor_direct工程
├── tools/                   现有编译、检查、调试配置脚本
├── docs/                    操作、协议、引脚、验证与历史交付
├── build/                   电脑输出；firmware/保存新ARM构建
└── firmware/                旧本机缓存与迁移说明
```

保留原文件名和函数名，便于接续学习材料。C-02C新增Drivers_Custom/Encoder硬件采集及Algorithms/Encoder计数换算；没有独立car_control／car_state、PID、Sensor或tracking实现，不能把目录存在算成功能完成。新应用代码仍按AGENTS写详细中文注释。

## 当前实现与证据

- 基础工程：HSI 16MHz，FLASH 0x08000000／512KiB，普通SRAM 0x20000000／128KiB，CCM未分配。Keil5.24a／ARMCC5.06u5／STM32F4xx_DFP2.17.1沿用。
- LogicDemo：协议与状态机演示。HardwareBench：1ms滴答、约5ms主循环，UART默认关闭；board_apply_requests仍更新调试请求，尚非整车运动适配。
- BoardSelfTest：已有2026-10-14双闪与DFU读回[记录](../hardware_preparation/board_self_test_record.md)，不替代UART、电机或整车测试。
- MotorPwm／MotorBench：当前重写版本0x020B0004，1kHz／50%／500ms；主控已确认A/B分别起转与自动停转，见[本次验收](../testing/2026-10-25_motor_pwm/acceptance_record.md)。原R3的30%／20kHz失败与[快照](../testing/2026-10-21_motor_bench/r3_watch/README.md)仅为历史，不混用旧参数。
- MotorContinuous：共用重写驱动后软件版本0x020B1002，仍20kHz／30%持续A；旧0x020B1001的[配对Watch](../testing/2026-10-24_motor_continuous/watch/README.md)及未转测量原位保留，未新增本目标的实物验收。
- MotorDirect A/B：独立入口与GPIO短时测试保留，已有[主控A/B分别起转反馈](../testing/2026-10-25_motor_direct/acceptance_record.md)，具体证据与未记录细项按原页；不能把未展示的Watch版本补为已读取。
- 编码器采集已在[C-02C](../project_planning/tasks/C-02C.md)完成本地软件交付：10ms、原始CNT、有符号增量／64位累计、counts/s与数据状态，实物手转与初版轮侧／方向／CPR交付已由00核对采用，参数仍待下一任务配置；速度PID、整圈停车及语音应答尚未实现。[协议](docs/protocol_v1_draft.md)仍为草案，视觉和硬件内部工作由对应角色负责。

迁移后六目标、UART开启分支和独立Direct构建均0错误0警告；现有六个电脑测试脚本通过。六目标BIN／HEX与迁移前逐字节一致。完整方法、日志与边界见[ORG-02](../project_planning/tasks/ORG-02.md)，本轮没有烧录或新实物验证。

## 输出和换电脑

新ARM输出在control/build/firmware，电脑测试输出在control/build。原firmware/build日志与旧产物保留原位供历史记录溯源；AXF含调试路径，迁移后哈希可能变化，不能与历史AXF混用。

当前本机两个uvoptx、uvguix和DebugConfig随工程迁移并保留原CMSIS-DAP设置；Git忽略这些本机文件。另一设备须核对本机编译器、芯片包、下载器和全部目标配置。tools/setup_debug.ps1只在没有已有uvoptx时装旧双目标模板，不能保证新设备六目标调试已齐。

默认本地保存验证，上传当前改动须主控明确要求。同一checkout的工程保存、构建、Git与板卡操作顺序进行。硬件资料在hardware_preparation、视觉在vision、实物证据在testing，路径保持原位。
