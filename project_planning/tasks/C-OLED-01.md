# C-OLED-01：独立OLED点亮与通信验证

日期：2026-11-10；状态：完成（独立显示软件、实板通信与主控画面确认）；责任：主控／01实现，主控确认实物画面，硬件复核接线。依据：主控本轮“现在写个代码点亮oled，确保一切正常”，并明确确认“断开电池；daplink保持连接”。

## 范围、授权与验收

本地新增独立OledBench工程，PB8/SCL、PB9/SDA、3V3/GND，SPL沿用，保留现有工程与共享修改；允许在当前已隔离动力的主板上下载／运行OLED点亮程序、读取状态。未授权远端上传、跨聊天操作或动力试车。

比赛第三部分、图1及评分表已读取：车载显示支撑定位通信/运动异常，降低基本功能60分中的未完赛／碰线／出界风险，调试证据可用于报告；规则未设OLED直接加分。新增屏幕仍计入整车尺寸与重量。工程验收要求编译零错误零警告、各字节I²C ACK、帧计数持续增加、错误码0、电机输入锁存为0；像素完整性、边框、文字及变化秒数由主控目视确认，不能由Flash校验代替。

## 已确认输入与实施

- 主板天空星STM32F407VET6；0.96寸128×64四针OLED已装车并按前述接法完成，实际芯片未归档，先采用SSD1306候选初始化。
- 来源分支`codex/current-version-20261025`，HEAD `a0733a8685db4c2b497539303bfe87fe1c1ebfe5`，已有多模块未提交改动，保留原位。
- 驱动位于`control/Drivers_Custom/Display/`，图样位于`control/App/Diagnostics/oled_pattern.*`，独立入口`control/Core/Src/oled_bench_main.c`，工程`control/MDK-ARM/oled_bench.uvprojx`。
- 保留原EncoderBench的TIM5启动限时及IWDG，四电机脚先置低并持续维持；显示只在主循环分128字节页写入，逐页喂狗，SCL等待有时间和次数双限。PB8/PB9使用开漏GPIO，不重配TIM4。
- 控制命令依据[Solomon SSD1306原厂手册及附录](https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf)第19～21页I²C、第28～32页命令、第37页显示模式与末尾电荷泵初始化。ACK不用于鉴定芯片。
- 已通过独立ARMCC5.06u5编译，零错误零警告；下载及运行证据后续回填[测试记录](../../testing/2026-11-10_oled_bench/record.md)。

## 实际结果与接续

已通过原Keil/CMSIS-DAP下载与Verify OK，完整原Flash备份已保存，当前Flash与BIN逐字节一致。有效三次取样地址0x3C、fault与bus.error均0、成功帧184→186→188、电机输出锁存0；主控随后明确确认“完全清晰符合预期”。本任务完成，详细日志／原失败读数与定位限制见[测试记录](../../testing/2026-11-10_oled_bench/record.md)。

当前板上保留OledBench无动力测试程序，不自动恢复运动，不接回动力，不改00全局摘要或既有运动验收。未来接入运动程序时需另做分块刷新与控制／UART／停车保护回归，本次没有整车运动验收或加分结论。
