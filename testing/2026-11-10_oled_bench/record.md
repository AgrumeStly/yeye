# OLED点亮：构建、下载、实板读回与画面确认

日期：2026-11-10（北京时间）。责任：主控／01；实物画面由主控确认。任务[C-OLED-01](../../project_planning/tasks/C-OLED-01.md)，[操作说明](../../control/docs/oled_bench.md)。

## 授权与实物条件

主控要求编写代码点亮已装车的0.96寸OLED12864，并明确“断开电池；daplink保持连接”。PB8/SCL、PB9/SDA、主板3V3/GND沿用已接线。既有多模块修改保留，仅新增独立显示工程；未操作动力、视觉板程序、远端或跨聊天消息。

## 构建、下载与运行证据

- ARMCC5.06u5／SPL，OledBench编译0错误0警告，Code4584、RO668、RW76、ZI2068；BIN5328字节，SHA256 `9ecfbf606a5a545fe398108376d2ef3bc09b7b60744c825694e9702e1cc28067`。[构建日志](build.log)、[源码哈希](source_sha256.json)。
- 下载前SWD attach保存[完整512KiB原Flash](flash_before_oled.bin)及[哈希／向量](flash_before_oled.json)，用于追溯，不自动恢复。
- 原Keil/CMSIS-DAP显式下载，20:52:22日志显示`Erase Done.Programming Done.Verify OK`：[下载日志](download.log)、[摘要](download.json)。随后显式SYSRESETREQ运行，见[运行记录](run.json)。
- 最终有效[三次运行取样](runtime_205617.json)：版本0x02120001、fault=0、地址0x3C、ack_mask=1、phase=4、stage=6；毫秒182560→184552→186543，成功帧184→186→188；ACK累计199300→201466→203632；bus.error=0；motor_odr=0；IWDG已启动、stage=4。
- 未连接的0x3D探测造成累计1个预期NACK，三次取样未增加；初始化空闲输入0x300。同次Flash读回与当前5328字节BIN逐字节一致。ACK只验证通信，不鉴定实际控制芯片。

## 原失败读数与定位

下载后尚未显式复位的RAM包含下载残留；运行后WFI睡眠态背景RAM读取也曾出现无效零。原`runtime_205238/205321/205432/205536.json`均保留且检查为false，不能算屏幕失败或据此补造通过。[短暂停核定位](startup_inspect.json)确认CPU已运行主循环、RAM实际已有0x3C与递增帧数；最终每次暂停约11ms读取两个小块后立即恢复，取得上述有效值，没有修改已烧录显示代码。

本机pyOCD 0.46.1明确指定generic cortex_m和当前CMSIS-DAP唯一ID，不使用其它型号的Flash算法；Flash下载仍由原Keil配置执行。Board ID 0001未识别提示不作芯片身份依据。短暂停核读回不作为无干扰时序测量。没有新增波形、电压或整车运动验证。

## 主控实物验收

在收到“完整边框、OLED OK、128X64 I2C、ADDR 3C、持续增加TIME秒数”的确认请求后，主控明确反馈：

> 完全清晰符合预期

据此验收本次独立程序画面清晰、符合预期，结合实板通信／写帧证据，**OLED点亮任务完成**。未单独逐项录像记录开机全白／全黑／互补棋盘格，未进行独立断电冷启动或每像素仪器测量，不把本次反馈扩大为整车功能验收。当前板上保留OledBench，动力电池保持隔离。

比赛对应第三部分、图1和基本功能60分的可靠完赛：显示为后续定位异常提供信息，报告可引用本轮真实证据。规则未设OLED直接加分；不声称得分或整车已正常。全局摘要由00读本记录后汇总。
