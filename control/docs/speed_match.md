# SpeedMatch：编码器双轮同速与实时调参

日期：2026-10-30（北京时间）。维护：主控／01；主控现场验证，02接收证据，00汇总。任务：[C-02F](../../project_planning/tasks/C-02F.md)。依据：主控要求复用原采集代码，使两轮速度一样，并减少调参时反复拔插DAPLink。

当前状态：独立程序及电脑检查完成，**未烧录，未实车调好**。目标是两轮实际RPM接近共同设定值；两轮PWM可以不同。相同RPM不保证轮胎有效直径、安装阻力或地面打滑相同，之后仍需地面直行验证。

## 当前程序

打开 [speed_match.uvprojx](../MDK-ARM/speed_match.uvprojx)，唯一目标 **SpeedMatch**，版本`0x020F0001`。保留StraightTest（含主控已改为12的旧修正值）、MotorPwm、EncoderBench和原六目标。

| 功能 | 当前行为 |
| --- | --- |
| 原采集复用 | 原encoder_hw读取TIM3 PC6/7、TIM4 PB6/7；原encoder_counter计算回绕、有符号增量及实际dt的counts/s，文件不改 |
| 第一次长按松KEY | 仅左轮／驱动A，50% PWM、500ms；识别变化通道和前进反馈符号 |
| 第二次长按松KEY | 仅右轮／驱动B，50% PWM、500ms；识别另一通道和符号，禁止两轮共用一个通道 |
| 第三次及以后 | 两轮独立PI跟踪同一个目标，默认60 RPM、3000ms，然后撤驱动 |
| 重复测试 | 正常结束后等待编码器静止至少500ms，再松键等待1秒，重新长按松开；不用拔DAPLink或复位 |
| 停止 | 原始KEY在下一次1ms滴答撤驱动并锁定；target_rpm改为0也停止并锁定；故障须先断动力再复位 |
| 反馈和控制 | 20ms采集／控制，真实dt换算；一阶低通alpha=1/4，减少计数量化抖动，有约数十ms延迟 |
| 运动输出 | 原straight_pwm驱动，HSI名义16MHz，TIM1 1kHz，任一轮0..50%，没有换向或超过上限的自动加功率 |
| 前进极性 | 左A：PE9 PWM、PE11低；右B：PE13低、PE14 PWM，沿用主控已反馈的方向关系 |
| 保护 | 无效／丢窗编码器、无反馈300ms、反向反馈、超速、采样过期、非法配置、看门狗和异常停车 |

校准须悬空，且仍需主控亲眼确认各次转动的是预期轮、朝车头前进。自动识别只建立驱动桥与反馈通道／符号关系，不能替代机械转向观察。每次复位重新识别，不把旧安装的a/b顺序写死。

CPR按[当前轮位](../../hardware_preparation/wheel_mapping.md)跟随轮组：左1058.6、右1060.8 counts/圈，属于10月25日5圈手转估计的继承值；未重做多圈标定，不称为本次新板测量。程序识别的通道映射仅在RAM有效，尚没有新的实物结果可回写为固定安装事实。

## 主控第一次在Keil5操作

1. 驱动OFF、拔XT30动力，车架固定且两轮悬空；沿用DAPLink给主板供电、两板共地、驱动给编码器供3V3的现有方式。驱动5V／3V3不并到主板电源；本轮不改供电。主板连接DAPLink可保持不拔。
2. 若正在调试，先Ctrl+F5退出。**Project → Open Project** 打开本页独立工程，目标必须为 **SpeedMatch**。**Project → Rebuild all target files** 应零错误零警告。沿用CMSIS-DAP／SWD／1MHz，Flash算法STM32F4xx 512KB、起点0x08000000，执行 **Flash → Download**，等待Programming Done、Verify OK。
3. **Debug → Start/Stop Debug Session**（Ctrl+F5）进入，**Debug → Run**（F5）持续运行。动力接入前完成调试连接／启动，运行中不暂停、单步或打断点。**View → Watch Windows → Watch 1** 添加下节变量，勾 **View → Periodic Window Update**。本机配置已预填Watch和周期刷新；换电脑仍以界面核对为准。
4. 保持KEY（实物丝印，对应PA0／WKUP）松开。确认`g_speed_revision=0x020F0001`、`g_speed_fault=0`、`g_speed_match.error=0`、`g_speed_ms`递增，四电机输出均为0。驱动OFF时接XT30，再ON，保持双轮悬空且静止，待绿灯每组1闪。
5. **校准左轮**：长按KEY约1–2秒至绿灯常亮再松开。应仅左轮向车头转约500ms后撤驱动。停稳并等待后绿灯每组2闪。若轮侧或转向错误，立即OFF并拔XT30，停止本轮，不进入右轮。
6. **校准右轮**：重新长按松开。应仅右轮向车头转约500ms后撤驱动，停稳并等待后每组3闪。`phase=2`，左右channel分别1或2且互不相同，sign分别为+1或−1；依据实际识别，不提前指定正负。若快闪，按故障表查看原因，不反复强行启动。
7. **双轮同速**：再次长按松开，两轮同时跟踪默认60 RPM，约3秒后撤驱动。观察左右RPM是否靠近60、difference是否减小，输出可能不同。完成后无需复位；停稳、等待每组3闪，即可再次触发。运行中KEY会锁定停止，复测该故障需先OFF／拔动力再RST，复位后需重新两次校准。

下载产物是`control/build/firmware/speed_match/speed_match.axf`，不是旧StraightTest。DAPLink接电脑时即可实时显示；若线会限制地面试车，本程序优先用于悬空调参，不能把有线Watch说成无线监控。供电方式未经确认时不安排脱线运行。

## 最少Watch：先看实测值，再改参数

```text
g_speed_revision
g_speed_fault
g_speed_ms
g_speed_watchdog_stage
g_speed_config
g_speed_match
```

展开`g_speed_match`，重点看：

| 字段 | 含义 |
| --- | --- |
| state／phase／error | 当前状态、0左校准／1右校准／2双轮闭环、粘性停止原因 |
| left_rpm／right_rpm | 归一化为前进正值后的滤波实测RPM，未完成两次通道识别时不作左右RPM解释 |
| difference_rpm | 左RPM减右RPM；负数表示右轮较快 |
| left_pwm／right_pwm | 实际请求PWM千分比，250=25%，500=50%，停车均0 |
| left_saturated／right_saturated | 1表示当前已到50%上限；若仍达不到目标，应降低目标并检查负载，不提高保护上限 |
| active | 本次锁定目标、PI和时限，运行中改普通配置不会中途改变本次控制 |
| matched_ms | 当前连续满足两轮相差≤5 RPM，且两轮各距目标≤5 RPM的持续时间 |
| last_left_rpm／last_right_rpm／last_difference_rpm | 停机前最后一帧滤波值，停车后保留，避免两轮都归零造成“同速达标”的误判 |
| last_left_pwm／last_right_pwm | 同次停止事件保留的PWM，不表示停车后仍输出 |
| last_matched_ms | 上次结束时的连续达标时间；先以≥500ms作为队内初验指标，非官方规则 |
| left_channel／right_channel／left_sign／right_sign | 校准识别结果；channel1=a/TIM3，2=b/TIM4；sign是编码器反馈系数，不是PWM极性 |

原始计数需要排查时再添加`g_speed_encoder_a.sample`、`g_speed_encoder_b.sample`。它们继续保留raw_cnt、delta、total_count、counts_per_s、valid/status/flags等原采集语义。Watch周期刷新慢于20ms控制，分项读取不是原子快照；本程序的last字段在停车后保持，适合读取本次最后结果。未提供自动串口曲线或无线回传。

## 停车时直接调参，不重复烧录

必须处于待机、双轮停稳且程序保持F5运行时修改。先维持默认值做一次，主控回报实测RPM后再按现象调，不根据肉眼猜PI：

| Watch变量 | 初值／边界 | 调整意义 |
| --- | --- | --- |
| g_speed_config.target_rpm | 60；启动允许10..120 | 两轮共同目标，只需改一个；目标0在运行中也会撤驱动并锁定 |
| g_speed_config.pi.kp | 2；0..10 permille/RPM | 比例修正；误差大且反应慢时小幅增加，来回振荡时减小 |
| g_speed_config.pi.ki | 4；0..20 permille/(RPM·s) | 消除持续误差；稳态总偏离目标可小幅增加，明显过冲／反复追赶时减小 |
| g_speed_config.pi.feedforward | 300；0..500 | 基础前馈30%，不是目标转速；初次建议保持，由PI分别修正左右差异 |
| g_speed_config.run_ms | 3000；500..3000ms | 本次窗口，启动锁定，不允许在运行中改值延长 |

在Watch的Value格输入新值，下一次长按松KEY生效。目标之外的参数中途修改只供下次启动使用。参数变化不自动启动，两次校准通过后正常结束可重复按KEY，不需重做校准或拔DAPLink。不要直接改state、phase、channel、sign或PWM输出字段。

Watch修改的是RAM，复位恢复源码初值。现场找到可重复通过的目标和PI后，将数值回填`control/App/Motion/speed_match.c`的`g_speed_config`初值，再编译下载保存；本轮默认PI只是调试起点，不宣称已适配当前实物。两轮长期需要不同PWM是正常现象，不以PWM相等替代RPM相等。

Keil运行刷新与Value编辑依据：[官方Watch说明](https://www.keil.com/support/man/docs/uv4/uv4_db_dbg_watchwin.asp)。本机未自动连接板卡验证界面；若运行中不能读写或数值不刷新，先断动力保存现象，不用暂停电机来读取。

## 故障和参数边界

`g_speed_match.state=7`是故障锁定；error：0无故障，1 KEY／目标0停止，2卡键5秒，3采样无效或启动前未静止，4通道校准失败，5配置非法，6无反馈，7反向反馈，8超速，9采样时限，10外设／启动，11非法状态。故障需先断动力再RST，不因下次正常按键自行恢复。

`g_speed_fault`硬件位：1 PWM时钟、2 TIM5、4 LSI、8 IWDG更新、16 SysTick、32 PWM请求／使能、64编码器初始化／读取。该值为0仍可能存在上表控制／反馈故障，须同时看error。初值`watchdog_stage=4`表示启动监督完成。

以下均为本程序的队内诊断阈值：校准选中通道至少20 counts、另一通道至多3，净变化至少为总绝对变化90%；采样间隔最多60ms；运行中任一轮连续300ms无计数、归一化瞬时反馈小于−5 RPM、绝对值超过600 RPM会停止。它们不能识别所有编码器故障，也不代替电流／温度／堵转硬件保护。PI输出0..500、积分限制±500并条件积分抗饱和；停机／故障清积分，不倒车。

## 软件证据与验收边界

ARMCC5.06u5零错误零警告；Code9272／RO424／RW132／ZI1252。BIN SHA-256：`e247d769752ca35d3c269aab4243d06433a769df045426573cbab29ca1dc54a7`。

- `control/tools/build_speed_match.ps1`仅构建及导出BIN，不下载；日志`control/build/firmware/SpeedMatch_build.log`。
- `control/tools/run_speed_match_tests.ps1`运行真实PI、原计数算法及新状态机：两种通道配对、反馈符号、20ms量化、32位时基回绕、500ms校准、3秒时限、重复启动、配置锁定、积分抗饱和、非法值、无反馈／反向／超速／丢窗／KEY锁定均通过。两个动力不同的虚拟电机模型在2.5秒时约62.83／63.94 RPM，差约−1.11 RPM；本次结束时持续满足5RPM门槛至少500ms。这只是给定模型下的结果，不是实车测速。
- 全调用链集成模型编译真实Core、PWM、encoder_hw、计数算法和控制策略，3场景110项通过，验证GPIO／CCR方向、逐轮到双轮序列、重复测试、3秒撤驱动、KEY、读取失败和MOE丢失。模型不模拟真实电压、AB波形或机械动力。
- 日志在`control/build/speed_match_tests.log`和`control/build/speed_match_integration_tests.log`。未改已有采集和StraightTest固件，不把其旧实物结果当本次新闭环验收。

主控下一次回报：两次校准分别是否只转预期轮并朝车头、识别channel/sign、目标RPM、左右实测／last转速、difference、last_matched_ms、左右PWM、error及视频。先以差值和各自目标误差均≤5RPM、连续≥500ms并正常撤驱动作为队内初验；多次悬空通过后再安排实际地面验证。精确轮速与直线程度不能只靠软件模型或停止后的零速判断。

## 比赛对应

依据已读取的[比赛文档](../../competition/比赛文档.md)第三部分项目要求、赛道及评分表：基本功能60分要求自动顺时针一圈、5分钟以内，碰边扣分、完全出界失败。实际轮速反馈和闭环修正用于降低电机差异／电量变化造成的跑偏，支撑提高完赛率、减少触边及后续合理提速；同速不是官方独立加分项，本轮没有实测得分收益。不修改视觉协议、正式START／STOP／失联规则，不作为循迹完赛或额外功能自动冲线停车验收。
