# StraightTest：3秒直行与左右输出修正

日期：2026-10-30（北京时间）。维护：主控／01。适用：当前同型号新主板、新驱动及当前接线。任务：[C-02E](../../project_planning/tasks/C-02E.md)。当前版本`0x020E0002`，替代快1秒／慢1秒的`0x020E0001`；本轮软件完成，尚未烧录或实车验证。

主控本轮反馈“小车会拐弯，右轮转速偏快”，要求改为只前进3秒，并留下左右转速偏移调试变量。本次采用开环PWM差值修正，不代表测得RPM或实现闭环。上一版的转向反馈保留在任务历史中，不补记未明确回报的精确计时及停车结果。

## 工程与运行

打开 [straight_test.uvprojx](../MDK-ARM/straight_test.uvprojx)，唯一目标 **StraightTest**。人工长按KEY约1–2秒至绿灯常亮再松开，按本次锁定的左右占空比连续前进3000ms，随后撤驱动并锁定，不自动重复，也不作快慢切换。运行中按KEY在下一次1ms滴答提前停止；保留卡键、启动等待限时、独立看门狗、异常及PWM使能失败保护。

| 项目 | 当前设置 |
| --- | --- |
| 基准占空比 | 50%，定义在straight_test.h的STRAIGHT_BASE_PERMILLE=500 |
| 默认修正 | +20：左50%、右48%；试调起点，尚未实车标定 |
| 时长 | STRAIGHT_RUN_MS=3000；从实际启动时刻计时 |
| PWM | HSI名义16MHz，TIM1 PSC=0、ARR=15999，名义1kHz |
| 左轮／驱动A | PE9 CH1 PWM，PE11 GPIO低 |
| 右轮／驱动B | PE13 GPIO低，PE14 CH4 PWM；保留已确认的反向极性 |
| 灯态 | 待机每组1闪；运行常亮；完成亮灭各500ms；中止快闪 |
| 停止 | MOE关闭、四CCR清零、四控制脚GPIO低；滑行撤驱动，机械仍有惯性 |

当前桥／轮侧依据见[轮位入口](../../hardware_preparation/wheel_mapping.md)。本轮不改引脚、方向、SPL及原MotorPwm／EncoderBench／六目标工程。

## 主控调参：只改一个变量

打开 [straight_test.c](../App/Diagnostics/straight_test.c)，在文件开头查找：

```c
volatile int32_t g_straight_trim_permille = 20;
```

每单位为PWM占空比的0.1个百分点。正数降低右轮输出，负数降低左轮输出；不把另一轮提高到50%以上。

| 修正值 | 左轮PWM | 右轮PWM | 用途 |
| ---: | ---: | ---: | --- |
| 0 | 50% | 50% | 无差值修正 |
| 10 | 50% | 49% | 右轮略降 |
| 20 | 50% | 48% | 当前默认试调值 |
| 30 | 50% | 47% | 右轮进一步降低 |
| -20 | 48% | 50% | 左轮偏快时降低左轮 |

主控每次只改5–10（0.5–1个百分点），其他条件保持一致。若右轮仍明显偏快，从20改25或30；若修正过头、左轮反而明显偏快，先将正值减小到15或10。数值不是实际轮速百分比，也不保证固定值适用于不同电池电量、地面和载荷。

修正量在松键启动时读取一次，保存到`g_straight_test.trim_applied_permille`，本轮运行中不跟随变量变化。输入先限到±基准，实际占空比在0..500内；极端值会让一轮为零，只是边界保护，不是正常调直设定。修改源码初值后须重新编译下载；Watch修改RAM不会跨复位保存。

## 主控在Keil5操作

1. 驱动OFF、拔XT30动力；若正在调试，Ctrl+F5退出。用 **Project → Open Project** 打开上述独立工程，选择 **StraightTest**。
2. 修改修正变量，执行 **Project → Rebuild all target files**，预期零错误零警告。沿用原CMSIS-DAP／SWD／1MHz及STM32F4xx 512KB下载配置，执行 **Flash → Download**，预期Programming Done、Verify OK。产物是`control/build/firmware/straight_test/straight_test.axf`。
3. 退出调试，双轮悬空，KEY（实物丝印，对应PA0／WKUP）松开后按RST；约1秒后进入每组1闪待机。驱动OFF时接XT30并打开驱动，长按KEY约1–2秒至常亮后松开，检查双轮朝车头、约3秒后撤驱动。
4. 悬空方向及停止正常后，先断动力、复位，再在平整开阔地面启动一次。车头留足3秒行程空间，线束远离车轮；完成后不重复，复测先断动力再RST。
5. 记录修正值、电池状态、行驶距离、偏左／偏右、终点横向偏移及是否按时撤驱动；固定起始朝向和地面，比较每次修正效果，保存录像。没有官方直行偏移阈值，本次不自行补造。

可选Watch调参：动力断开、尚未启动时，用 **Debug → Start/Stop Debug Session** 进入调试，将`g_straight_trim_permille`加入 **View → Watch Windows → Watch 1** 并改值。完成修改后让程序恢复运行；动力接入时不暂停CPU或打断点。复位恢复源码默认值，因此常规调参优先改源码后重新编译下载。

异响、发热或持续不止时直接OFF并拔XT30。按KEY能撤驱动，机械停稳仍受惯性影响。本程序没有电流、堵转或车道位置检测。

## 软件证据与边界

版本`0x020E0002`，ARMCC5.06u5零错误零警告；Code4816／RO424／RW56／ZI1056。BIN SHA-256：`8c913d58a821e6768b577032f3714056100fcf02a99c39b2b7d3f8047f03ce81`。

`control/tools/build_straight_test.ps1`只构建并导出BIN，不访问板卡；日志`control/build/firmware/StraightTest_build.log`。`control/tools/run_straight_tests.ps1`验证3000ms边界、计数回绕、短按／卡键、按键停止与终态锁定，以及正负修正、极值限幅和参数锁定；集成模型7场景90项通过，检查默认CCR1=8000／CCR4=7680，3000ms后均为0、CCR2/3始终0，以及负修正、单轮零输出、非法输入、使能失败与运行中MOE丢失锁定。日志在`control/build/straight_test_tests.log`和`control/build/straight_integration_tests.log`。

Watch预期：`g_straight_revision=0x020E0002`、`g_straight_fault=0`、`g_straight_watchdog_stage=4`；`g_straight_test`保存run_since、stop_ms、trim_applied_permille、left_duty_permille及right_duty_permille。正常`stop_ms-run_since=3000`。故障位仍为1=PWM时钟、2=TIM5、4=LSI、8=IWDG更新、16=SysTick、32=PWM请求／使能失败。

电脑模型只验证软件逻辑和寄存器边界，不证明真实轮速、直行、机械停稳或实测得分。主控回报右轮偏快是本轮修正依据；默认+20仍待新一轮实车比较。

## 比赛对应

沿用已读取的[比赛文档](../../competition/比赛文档.md)第三部分、原PDF第2—4页与赛道图：基本功能60分要求自动顺时针一圈、5分钟以内，触边扣分、完全出界失败。输出修正与直行观察用于降低左右动力差造成的触边／出界风险，为后续循迹提供运动基础；没有直接加分承诺，不作为闭环、正式完赛或自动冲线停车验收。
