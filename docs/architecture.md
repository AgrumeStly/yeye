# 系统架构与软件分层

日期：2026-10-25（北京时间）。维护：00协调架构，01维护STM32，视觉／硬件各维护对应实现。
依据：当前源码、六目标Keil配置、[模块状态](../project_planning/project_status.md)及主控确认的目录分层。以下区分现有实现与后续模块。

## 整车数据流

```mermaid
flowchart LR
    Camera[GC2093相机] --> Vision[K230D视觉与语音]
    Vision -->|UART结果包／命令| Protocol[STM32协议解析]
    Protocol --> State[车辆状态与控制请求]
    State --> Motion[运动驱动与闭环：待实现整合]
    Motion --> Driver[AT8236与双电机]
    Encoder[编码器：待读取与标定] --> Motion
```

该图描述系统连接方向，不代表完整链路已经验收。视觉正式脚本尚未在本仓库归档；HardwareBench的左右请求仍是演示值，编码器／PID未实现。当前电机诊断使用独立目标，不经过整车状态机。

## 仓库与主控工程的两层结构

```text
yeye/
├── AGENTS.md                     所有对话共同规则
├── README.md
├── docs/                         整车主题文档入口
├── control/                      STM32主控，01负责
│   ├── Core/
│   │   ├── Inc/stm32f4xx_conf.h  SPL模块配置
│   │   ├── Src/                  main及各独立目标入口
│   │   └── Startup/              F407启动汇编及许可
│   ├── App/
│   │   ├── Car/                  car.c/h：车辆状态与演示请求
│   │   └── Diagnostics/          motor_bench.c/h：纯诊断状态机
│   ├── Drivers_Custom/
│   │   ├── Board/                board.c/h：时钟、滴答、UART与板级适配
│   │   ├── Motor/                PWM台架／GPIO诊断驱动
│   │   └── Communication/        protocol.c/h：字节包编解码
│   ├── Drivers/                  原版CMSIS、STM32定义与SPL
│   ├── Algorithms/               纯算法落点；当前只有范围说明
│   ├── Tests/Host/               电脑测试及fake硬件边界
│   ├── MDK-ARM/                  多目标／独立Direct工程和本机调试配置
│   ├── tools/                    现有构建／测试脚本
│   ├── docs/                     主控技术规范与历史交付
│   └── build/                    本机编译输出，Git忽略
├── vision/                       视觉与语音，由视觉负责
├── hardware_preparation/         硬件、供电与装配资料
├── testing/                      带版本与日期的现场证据
├── project_planning/             协作、状态、任务和规划历史
├── competition/                  原始赛事文件
└── report/                       报告与最终提交
```

仓库路径仍为D:/Projects/yeye，没有改名或生成另一份工程。原control/firmware仅保留历史本机缓存与迁移说明；唯一可编辑源码和正式工程已迁到上述位置。

## 分层边界

| 层 | 负责什么 | 当前边界 |
| --- | --- | --- |
| Core | 选择入口、初始化、调度和中断衔接 | 保留原入口与保护流程，不改变六目标行为 |
| App | 车辆与诊断流程，使用模块接口推进状态 | car.c尚不构成速度闭环；诊断逻辑与整车逻辑独立 |
| Drivers_Custom | 主控自行实现的板级、通信、电机适配 | board.c内部UART本轮整体保留，未来有明确任务再拆分 |
| Drivers | 外部芯片／内核库 | 仅迁路径，厂家源码字节与来源哈希保留 |
| Algorithms | 与外设寄存器无关、可独立测试的数学算法 | PID、tracking尚未实现，不创建假实现或空API |
| Tests | 电脑验证真实逻辑与硬件边界模型 | 不验证真实电压、波形、电机或整车表现 |
| MDK-ARM | 设备、宏、目标排除、编译与调试配置 | SPL／ARMCC5沿用，CubeMX的.ioc不适用于当前来源 |

后续新增编码器或传感器驱动时放Drivers_Custom/Encoder或Sensor；纯PID数学放Algorithms，轮速采样／PWM仍在驱动，车辆策略在App。目录说明不是新增功能任务。

## 六个现有目标

| Keil目标 | Core/Src入口 | 用途 |
| --- | --- | --- |
| LogicDemo | logic_demo.c | 无硬件协议与状态机演示 |
| HardwareBench | main.c | 串口／状态机主框架，UART默认关闭、请求输出待适配 |
| BoardSelfTest | board_self_test.c | 独立板级双闪与基础自检 |
| MotorBench | motor_bench_main.c | PWM人工阶段诊断 |
| MotorContinuous | motor_bench_main.c＋持续目标宏 | A桥持续诊断 |
| MotorDirect | motor_direct_main.c | GPIO人工单次A诊断 |

多个main由Keil逐目标显式排除，不能将Core/Src所有文件直接一起编译。对话职责继续由[协作标准](../project_planning/collaboration_standard.md)规定。
