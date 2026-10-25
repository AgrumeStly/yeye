# 主控开发：STM32 SPL分层工程

更新：2026-10-25（北京时间，ORG-02）。维护：主控／01。
既有STM32F407VET6、SPL V1.3.0、Keil5与六个目标继续使用；本轮只迁目录和引用，应用代码字节及运行行为保留。

## 打开哪个工程

2026-10-25最新电机工作：主控确认AB直接驱动均正常后，要求删除旧PWM实现重写。现已替换PWM入口与驱动，当前实测入口为 [MotorPwm独立工程](MDK-ARM/motor_pwm.uvprojx)，目标 **MotorPwm**、版本0x020B0004、1kHz／50%／500ms；先A正常再B。按[新PWM步骤](docs/motor_pwm.md)操作，[任务与检查](../project_planning/tasks/C-02B-PWM-R4.md)。共用驱动的MotorContinuous升0x020B1002，仍20kHz／30%持续A；本页后文ORG-02数值为迁移时证据。

本轮结果：主控回报“全部符合预期”，A/B分别PWM起转、自动停转及对应灯态人工验收完成。[现场记录](../testing/2026-10-25_motor_pwm/acceptance_record.md)保留回报与测量边界；本项任务完成。

| 场景 | 入口 |
| --- | --- |
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
│   ├── Src/                 main.c和四个独立目标入口
│   └── Startup/             F407启动汇编及许可
├── App/
│   ├── Car/                 car.c / car.h
│   └── Diagnostics/         motor_bench.c / motor_bench.h
├── Drivers_Custom/
│   ├── Board/               board.c / board.h
│   ├── Motor/               motor_bench_pwm与motor_direct_gpio
│   └── Communication/       protocol.c / protocol.h
├── Drivers/                 cmsis / stm32 / stdperiph
├── Algorithms/              纯算法落点，当前仅范围说明
├── Tests/Host/              原电脑测试和fakes
├── MDK-ARM/                 yeye_control与motor_direct工程
├── tools/                   现有编译、检查、调试配置脚本
├── docs/                    操作、协议、引脚、验证与历史交付
├── build/                   电脑输出；firmware/保存新ARM构建
└── firmware/                旧本机缓存与迁移说明
```

保留原文件名和函数名，便于接续学习材料。没有独立car_control／car_state、PID、Encoder、Sensor或tracking实现；后续有实际任务再拆分或新增，不能把目录存在算成功能完成。新应用代码仍按AGENTS写详细中文注释。

## 当前实现与证据

- 基础工程：HSI 16MHz，FLASH 0x08000000／512KiB，普通SRAM 0x20000000／128KiB，CCM未分配。Keil5.24a／ARMCC5.06u5／STM32F4xx_DFP2.17.1沿用。
- LogicDemo：协议与状态机演示。HardwareBench：1ms滴答、约5ms主循环，UART默认关闭；board_apply_requests仍更新调试请求，尚非整车运动适配。
- BoardSelfTest：已有2026-10-14双闪与DFU读回[记录](../hardware_preparation/board_self_test_record.md)，不替代UART、电机或整车测试。
- MotorBench R3：0x020B0003，原30%／20kHz／500ms诊断；已有[R3板内快照](../testing/2026-10-21_motor_bench/r3_watch/README.md)，原起转未通过。
- MotorContinuous：0x020B1001，原持续A诊断；[配对Watch](../testing/2026-10-24_motor_continuous/watch/README.md)和人工测量已归档，电机仍未转。
- MotorDirect：0x020B2001，普通GPIO人工单次A500ms，原停止锁定、IWDG和TIM5保护保留；软件与独立入口完成，下载／无动力演练／起转回报仍待主控。
- 编码器采集、速度PID、整圈停车及语音应答尚未实现；[协议](docs/protocol_v1_draft.md)仍为草案。视觉和硬件内部工作由对应角色负责。

迁移后六目标、UART开启分支和独立Direct构建均0错误0警告；现有六个电脑测试脚本通过。六目标BIN／HEX与迁移前逐字节一致。完整方法、日志与边界见[ORG-02](../project_planning/tasks/ORG-02.md)，本轮没有烧录或新实物验证。

## 输出和换电脑

新ARM输出在control/build/firmware，电脑测试输出在control/build。原firmware/build日志与旧产物保留原位供历史记录溯源；AXF含调试路径，迁移后哈希可能变化，不能与历史AXF混用。

当前本机两个uvoptx、uvguix和DebugConfig随工程迁移并保留原CMSIS-DAP设置；Git忽略这些本机文件。另一设备须核对本机编译器、芯片包、下载器和全部目标配置。tools/setup_debug.ps1只在没有已有uvoptx时装旧双目标模板，不能保证新设备六目标调试已齐。

默认本地保存验证，上传当前改动须主控明确要求。同一checkout的工程保存、构建、Git与板卡操作顺序进行。硬件资料在hardware_preparation、视觉在vision、实物证据在testing，路径保持原位。
