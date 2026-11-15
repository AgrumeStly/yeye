# OledBench：0.96寸OLED独立点亮测试

日期：2026-11-10。维护：主控／01；画面确认：主控。任务[C-OLED-01](../../project_planning/tasks/C-OLED-01.md)，实际证据见[测试记录](../../testing/2026-11-10_oled_bench/record.md)。本工程用于无动力显示检查，未接入LowSpeedLap运动程序。

## 当前程序与画面

工程[oled_bench.uvprojx](../MDK-ARM/oled_bench.uvprojx)，目标 **OledBench**，版本 **0x02120001**。GND→GND、VDD→3V3、SCK→B08、SDA→B09，见[接线说明](../../hardware_preparation/oled_wiring.md)。本次主控已确认动力电池断开、DAPLink保持连接，程序已实际下载／运行，最终反馈“完全清晰符合预期”。

上电等待200ms，探测7位地址0x3C／0x3D，优先选择应答的0x3C；依次显示全亮、全黑、两个互补棋盘格，各阶段约800ms（可见时长受传输影响），约3.2秒后显示边框、`OLED OK`、`128X64 I2C`、实际地址、PB8／PB9接线和每秒更新的TIME。实际地址0x3C，初始化为SSD1306候选，不据地址断言实物芯片身份。

四个电机控制脚PE9／11／13／14先置低并每毫秒维持，不启用PWM、编码器或视觉UART；KEY（对应WKUP）不触发电机。当前板上保留此显示测试程序，不能用来行驶。

## Keil复现

1. 保持驱动OFF、动力电池拔开、DAPLink单源供主板；Project → Open Project打开`control/MDK-ARM/oled_bench.uvprojx`，选择OledBench。
2. Project → Build Target（F7）应0错误0警告；Flash → Download应出现`Programming Done`、`Verify OK`。本机沿用CMSIS-DAP／SWD／1MHz及STM32F4xx_512.FLM。
3. 按主板RST重看图样序列。也可Debug → Start/Stop Debug Session进入后按Run（F5）。确认边框四边完整、文字清晰、无偏移／乱码，TIME持续增加。

下载前已保存完整512KiB原Flash，不自动恢复。后续要行驶时，须按现行任务重新下载相应运动工程，再按该任务的供电／校准步骤操作。

## Watch与实现边界

| 变量 | 正常含义 |
| --- | --- |
| g_oled_revision／g_oled_fault | 0x02120001／0；fault位1时钟、2启动时基、4 LSI超时、8 IWDG更新超时、16 SysTick、32显示操作失败 |
| g_oled_stage | 稳定文字页6；刷新中5；255为锁存故障 |
| g_oled_address／g_oled_ack_mask | 本次0x3C／1；mask bit0为3C应答、bit1为3D应答 |
| g_oled_ms／g_oled_frames | 毫秒与成功整帧数持续增加；帧数不是面板内部刷新频率 |
| g_oled_phase | 4为文字计数页，0..3为测试图样 |
| g_oled_bus.error | 0正常；1 NACK、2 SCL拉低超时、3 SDA拉低超时、4 DWT时钟异常、5参数无效 |
| g_oled_bus.nack_bytes | 本次1是0x3D地址探测的预期NACK，稳定显示后不应增加 |
| g_oled_bus.idle_pins／g_oled_motor_odr | 本次0x300／0，分别为总线初始化空闲电平及电机板内输出锁存，不代替电压测量 |

驱动[oled_i2c.c](../Drivers_Custom/Display/oled_i2c.c)使用SPL开漏GPIO与CMSIS DWT计时，不占用TIM3／TIM4。每次SCL等待有200us与4096次双限，DWT延时也有次数上限。复用既有TIM5启动限时和IWDG，主循环逐128字节页传输并喂狗，ISR不执行显示或喂狗，防止总线卡死长期停住主循环。故障锁存后绿灯快闪。

[图样生成](../App/Diagnostics/oled_pattern.c)不访问硬件。[独立入口](../Core/Src/oled_bench_main.c)负责初始化、时序和诊断。页写入是阻塞诊断接口，未来接入运动仍须分块调度并回归控制周期／UART／失联停车，不直接放入控制中断。本次显示清晰不代表整车功能验收。

## 构建与取证工具

`python control/tools/build_oled_bench.py`沿用D:/software/Keil5编译并导出BIN，不访问板卡。[oled_bench_probe.py](../tools/oled_bench_probe.py)指定本次唯一ID的CMSIS-DAP：`--backup-before`只读原Flash并拒绝覆盖，`--capture`按AXF符号读状态并比对Flash／BIN，不下载或复位。依赖pyOCD／pyelftools，本次本机使用`vision/.venv/Scripts/python.exe`和pyOCD 0.46.1，仅作调试工具依赖。

本机WFI睡眠态背景RAM读取曾返回无效零；最终通过短暂停核读两个小块、立即恢复取得有效值，每次约11ms，已记录原状态与暂停时间。早期失败读数保留，不用它们判定屏幕损坏；这种取样不作为无干扰控制时序测量。
