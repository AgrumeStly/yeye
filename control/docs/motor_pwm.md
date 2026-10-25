# MotorPwm：重写后的PWM起转测试

日期：2026-10-25（北京时间）。维护：主控／01。任务：[C-02B-PWM-R4](../../project_planning/tasks/C-02B-PWM-R4.md)。依据：主控确认AB马达直接驱动均正常，并要求删除旧PWM代码重新编写。原PWM入口与驱动已替换，Direct A/B入口保留。软件检查通过，**主控随后回报“全部符合预期”，确认A/B分别PWM起转、自动停转与阶段灯态符合本轮流程，人工验收完成**；证据来源与未单独测量项目见[本次测试](../../testing/2026-10-25_motor_pwm/acceptance_record.md)。下文保留本次已使用的操作步骤供复现。

## 工程和参数

直接打开 [motor_pwm.uvprojx](../MDK-ARM/motor_pwm.uvprojx)，唯一目标 **MotorPwm**，版本 `0x020B0004`。无需在原六目标工程中寻找目标。沿用原STM32F407VET6、SPL、Keil5、DAPLink及已确认接线。

| 项目 | 本次设定 |
| --- | --- |
| PWM | HSI名义16MHz，TIM1，PSC=0，ARR=15999：1kHz |
| 占空比 | 固定50%，CCR=8000；不自动爬升，不代表转速 |
| A | E09／PE9／CH1输出PWM；E11／PE11普通GPIO低 |
| B | E13／PE13／CH3输出PWM；E14／PE14普通GPIO低 |
| 停止 | 关闭TIM1 MOE，四输入切为GPIO低；00滑行，不保证机械瞬间停稳 |
| 启动 | KEY长按约1–2秒至绿灯常亮，再松开；每次最长500ms |
| 阶段 | 一组1闪等A，一组2闪等B，一组3闪等AB；每阶段都须重新长按松开 |
| 保护 | 运行中按KEY立即撤驱动并锁定；卡键、启动故障、PWM请求/使能失败锁定；IWDG监督CPU/滴答 |

本次先分别验收A、B，**B完成后断动力，暂不触发第3步AB**。保留第3步能力以兼容原台架序列，不代表AB同时运行已验收。与旧PWM同时改变了实现、频率及占空比，本次成败不能单独证明旧失败的具体原因；50%也不保证任意负载均可起转。

## 主控在Keil5操作

1. 驱动开关OFF，拔开XT30动力电池。两轮悬空，固定车架，线束离开转轴。主板沿用DAPLink五线供电、Type-C空着、原共地保留；保持已通过Direct测试的接线，不把驱动5V／3V3接主板。
2. 若正在调试，按Ctrl+F5退出。用 **Project → Open Project** 打开本页独立工程，目标栏应为 **MotorPwm**。执行 **Project → Rebuild all target files**，应0错误0警告。当前产物为 `control/build/firmware/motor_pwm/motor_pwm.axf`，不能下载旧Direct或持续版。
3. **Options for Target → Debug** 核对CMSIS-DAP、Settings中的SWD／1MHz。**Utilities** 使用Debug Driver；**Flash Download**为STM32F4xx 512KB、地址0x08000000，勾Program／Verify。本机已复制已验证DAPLink设置，换电脑仍需界面核对。执行 **Flash → Download**，等待Programming Done、Verify OK；由主控手动执行。
4. XT30继续拔开，退出调试，拔插DAPLink USB独立重启。KEY（实物丝印，对应PA0／WKUP）和BOOT0松开，约1秒后应每组1闪待机。无动力演练一次：KEY长按约1–2秒至常亮再松开，约500ms后退出常亮，再进入每组2闪。此次演练不会产生实物转动。
5. 演练灯态正常后，在动力仍断开时按RST回到每组1闪，保持KEY松开约1秒。Keil退出调试，驱动OFF时接XT30，再打开驱动。此时AB都应静止。
6. **测A一次**：每组1闪时长按KEY至常亮，再松开。预期仅A旋转约500ms，随后撤驱动，A停稳后进入每组2闪。期间再按KEY可提前停止并锁定。如完全不转、仅抖动、错误马达转动或持续不止，立即OFF并拔XT30，保存现象，不进入B。
7. **仅在A转停正常时测B一次**：确认A已停稳、绿灯每组2闪，重新长按KEY至常亮再松开。预期仅B旋转约500ms后撤驱动，进入每组3闪。至此驱动OFF并拔XT30，停止本轮；不要再按第3次触发AB。

没有编码器堵转、电流或温度检测；不要在地面运行，也不要在动力接入时打断点或暂停CPU。若没有自动撤驱动、异常发热或异响，直接OFF并拔XT30。不转时先停止并保存现象，不连续加功率试错。

## 回报和排查

主控回报：目标MotorPwm及Verify结果、A是否旋转和自动停、B是否旋转和自动停、停止后灯态、是否已OFF并拔XT30。A失败时只需回报A，不必继续B。能看清KEY、双轮和绿灯的录像可作为原始证据。

若不转，先断动力再读Watch，不靠反复通电定位：

- `g_motor_bench_revision`应为`0x020B0004`，`g_motor_bench_fault`应为0，`g_motor_bench_ms`递增，`g_motor_bench_watchdog_stage`应为4。
- `g_motor_bench_pwm_diag.active`保留活动帧；A的mask=1、CCR1=8000／CCR3=0，B的mask=2、CCR1=0／CCR3=8000；PSC=0、ARR=15999，BDTR的MOE位应为1。
- `stopped`保留撤驱动后帧，MOE=0、四CCR=0、四脚GPIO低。`elapsed_ms`正常为500，KEY提前停止时小于500。板内证据不能代替排针波形或马达动作。
- 故障位可组合：1=时钟、2=启动TIM5、4=LSI等待、8=IWDG更新、16=SysTick、32=PWM请求/使能失败。非零会锁定，复测须先断动力再复位。

## 本地验证

Keil5／ARMCC5.06u5：独立MotorPwm与原MotorBench均0错误0警告，Code4908／RO424／RW64／ZI1288。BIN SHA256：`ea10fb83a5497c40c346ee6005073562dade79b013fcc8c6a5f6ec4d49d65a33`。

电脑模型：新PWM 9场景168项，启动10场景154项，通用按键73项；持续7场景115项及启动154项；Direct A/B各9场景52593项及Direct启动154项均通过。覆盖人工A/B/AB序列、500ms边界、KEY停止、使能失败锁定、回绕与旧目标兼容；不表示真实频率、电压、起转或机械停稳已测。日志见[软件证据](../../testing/2026-10-25_motor_pwm/software/)。
