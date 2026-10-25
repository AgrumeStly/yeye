# MotorDirectB：B马达单次起转检查

日期：2026-10-25（北京时间）。维护：主控／01。依据：主控回报A马达已通电起转并自动停止，随后要求测试B马达；沿用[MotorDirect A操作与保护](motor_direct.md)、[逐线接线表](../../hardware_preparation/motor_wiring_self_check.md)。本页为B版操作入口；电脑验证已完成。主控后来回报“马达b也正常”，实物结果和未提供的细节见[现场记录](../../testing/2026-10-25_motor_direct/acceptance_record.md)。

独立工程：[motor_direct_b.uvprojx](../MDK-ARM/motor_direct_b.uvprojx)，目标 **MotorDirectB**，版本 `0x020B2002`。编译时选定B桥，KEY（板上丝印，对应PA0／WKUP）长按约1–2秒至绿灯常亮、松开后，BIN1／PE13置高、BIN2／PE14及A桥两输入保持低，最长500ms；随后四输入归低并锁定。运行中再按KEY提前停止并锁定。一次上电只允许一次触发，复测须先断动力再复位。B版无TIM1／PWM；TIM5仅供启动等待，IWDG与1ms监督保留。GPIO只是控制信号，动力仍来自驱动板的2S电池。

## 主控在Keil5操作

1. 先把驱动开关拨到OFF并拔开XT30动力电池。若正处于调试会话，先按Ctrl+F5退出。用 **Project → Open Project** 打开上面的独立工程；若Keil询问是否保存旧的A工程窗口配置，本次选No。目标栏须显示 **MotorDirectB**，不能仍是MotorDirect。保持既有DAPLink五线供主板，天空星Type-C仍空着；不把驱动5V／3V3接到主板。
2. 在动力电池未接入时，执行 **Project → Rebuild all target files**，预期0错误0警告；再执行 **Flash → Download**，等待 `Programming Done`、`Verify OK`。若目标、编译或Verify不符，停止本次测试，不接电池。下载前先让KEY和BOOT0都松开。
3. 保持XT30断开，退出调试，拔插DAPLink USB使主板独立重启。绿灯待机应每2.5秒闪一组1次。做一次无动力演练：长按KEY约1–2秒至常亮后松开，约500ms后应变为慢闪并锁定，再按KEY不应重启。灯态不符时保持动力断开。
4. 无动力演练通过后，仍在驱动OFF时按RST回到待机，固定车架，让A、B两轮都悬空，线束离开转轴。保持KEY松开约1秒；再接XT30、打开驱动。此时两轮不得自行转动，若出现非预期动作，立即驱动OFF并拔XT30。
5. 只做一次长按KEY至常亮再松开的动作。预期**仅B马达**短时转动，A马达静止，约500ms后两轮不再受驱动且绿灯慢闪锁定。若A转、双轮转、持续转、异常响动或冒烟，立即驱动OFF并拔XT30；不要反复触发或交换带电接线。
6. 无论结果如何，最后驱动OFF并拔XT30。请回报：Keil目标及Verify提示、无动力演练灯态、实际哪只轮转、是否自动停、停止后灯态，以及是否已OFF并拔开电池。若能拍到KEY、绿灯和双轮的同一段视频，可供核对。

B电机的六芯线沿用原接线，不为本次测试改A/B线：M1→BO1、M2→BO2、G→GND、V→3V3、B→E2B、A→E2A。若需核对或恢复接线，先将驱动OFF、拔XT30与DAPLink USB，按电机及驱动丝印逐线核对；不能凭另一束线的颜色判断。

可选无动力Watch：`g_motor_direct_revision`应为`0x020B2002`，`g_motor_direct_fault`应为0，`g_motor_direct_ms`递增，`g_motor_direct_watchdog_stage`为4。`g_motor_direct_gpio_diag.active`理论上应记录mask=2及四脚ODR掩码`0x2000`，停止帧ODR掩码应为0；这些只是板内读回，不代替排针电压或电机实际转动。只在XT30拔开时进入调试并读Watch。

本地检查：MotorDirectB Keil5／ARMCC5完整构建0错误0警告，Code3872／RO424／RW64／ZI1184；A版、B版各9个GPIO／入口模型场景与原启动模型10个场景通过。电脑模型不代表B马达已实际通过。本轮没有烧录、操作实物或上传。
