# C-02C软件证据

日期：2026-10-25（北京时间）。执行：01。来源：本机实际GCC／Keil输出，非板卡记录。
目录D:/Projects/yeye，来源分支codex/current-version-20261025，HEAD与formal-2026-10-25解引用提交均为`0b0343577895d8eb03a337165da6ce9c5e433519`。正式标签本身是标签对象，`^{commit}`取得对应提交；未切分支／提交／上传。

| 证据 | 结果和边界 |
| --- | --- |
| [encoder_counter_tests.txt](encoder_counter_tests.txt) | 真实纯算法8022次断言，包含2000段已知双路轨迹；正反向、首样、静止、正反回绕、时间回绕、异常间隔、半量程歧义及64位饱和 |
| [encoder_bench_tests.txt](encoder_bench_tests.txt) | 真实Core／App／编码器适配及算法，12个SPL边界模型场景，241898次断言含等待循环；检查R1、10ms调度、两路读回、错误锁定及零电机输出，不能模拟真实AB电气解码 |
| [EncoderBench_build.txt](EncoderBench_build.txt) | Keil5／ARMCC5.06u5，新独立目标0错误0警告；Code4500／RO424／RW60／ZI1236 |
| 原六目标构建日志 | LogicDemo、HardwareBench、BoardSelfTest、MotorBench、MotorContinuous、MotorDirect各命名_build.txt，全部0错误0警告 |
| [MotorPwm_build.txt](MotorPwm_build.txt)、[MotorDirectB_build.txt](MotorDirectB_build.txt) | 两个既有独立目标兼容构建0错误0警告；原Direct A独立工程字节保留，同入口在六目标MotorDirect构建通过，本轮未重复编译该独立文件 |
| checks.json | 完整源码／工程／产物SHA256、既有配置不变、旧电机BIN匹配、16份官方文件、向量布局、文档链接、空白与Git差异检查；由本机检查脚本产生 |

当前固件版本0x020C0001，AXF／HEX／BIN目录为`control/build/firmware/encoder_bench/`，具体字节与SHA256以`checks.json`和[操作说明产物表](../../../control/docs/encoder_bench.md)为准；产物被Git忽略。没有把未上传的本机uvoptx当成其它设备已配置。

同日教程补充：checks.json保留初次软件交付指纹。补充教程时观察到工程XML字节和AXF哈希变化，XML归一化语义相同，源码及BIN／HEX保持原哈希；最新AXF指纹见操作说明及tutorial_checks.json。01本次只更新教程，没有写工程或构建，不将该变化来源猜成已确认事实，也不覆盖原始构建／模型日志。

本轮只对共享SPL配置增加ENCODER_BENCH_TARGET条件，已有.c／.h（该配置头以外）及全部既有工程／本机调试配置与开工快照逐字节相同。MotorPwm／MotorBench BIN均匹配已验收版本ea10fb83…，原频率／占空比／500ms与保护未改；不因重建AXF调试信息改变而要求重测已通过电机功能。

启动监督复用了既有6个函数，去注释和名称映射后可执行代码相同。真实AXF反汇编含编码器配置／CNT读取，无PWM启用、比较值更新或电机置高调用；本机文件`control/build/c02c_disassembly.txt`。开工源码／配置哈希与工程副本在`control/build/c02c_baseline/`；这些是本机缓存，不是需上传的产品文件。

复现：电脑脚本为`control/tools/run_encoder_tests.ps1 -Compiler C:/software/mingw64/bin/gcc.exe`，PATH需含同目录；新ARM脚本为`control/tools/build_encoder_bench.ps1`，只构建和导出BIN，不访问DAPLink。主控人工复验只需[纯Keil说明](../../../control/docs/encoder_bench.md)。本轮原有电机／通信算法未改变，未重复运行无关旧电脑模型。

限制：没有自动连接、烧录、驱动、示波器或供电操作；现场采集、滤波、轮侧、方向、CPR和手转独立性均见[待填验收](../acceptance_record.md)，当前未通过。SysTick暂停／多次CNT回绕混叠等边界见操作说明；没有输出假RPM或m/s。
