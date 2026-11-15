# I-02：杜邦线5V车载供电与脱机启动

日期：2026-11-10。维护：主控／02；电源与固定复核：硬件；视觉启动文件由视觉与主控按本轮授权交接。依据主控本轮明确的实际路径、[接线基准](wiring.md)、[已部署硬件](deployed_hardware.md)及下列厂家说明。本页区分接法确认、改接操作、电气测量、上电启动和动力验证。

## 已确认路径

当前调试状态：STM32由DAPLink供电，K230由电脑Type-C供电。主控明确两板可改由电池供电，随后纠正实际方案为：**驱动板5V/GND经杜邦线分别接STM32的5V/GND和K230的5V/GND**，不采用USB-A转接板。该反馈确认供电路径，不补写本轮已断开旧电源、完成改接、测得电压或通过冷启动。

```text
新2S电池 → AT8236 Vin输入
                 ├─ 标注5V的稳压输出 → STM32标注5V的电源针
                 └─ 同一5V稳压输出   → K230标注5V0的电源针
驱动GND ─────────┬─ STM32 GND
                 └─ K230 GND
```

按实物电源丝印寻找5V／5V0与GND，不按排针第几个或线色猜位置。底部蓝色Vout不是5V稳压口；电池原电压不接两板5V／3V3或信号IO。两板UART仍为原T/R/G三线，串口座V线保持不接，不增加第二条供电路径。

### 来源与实际边界

- 亚博[官方模块介绍](https://www.yahboom.net/public/upload/upload-html/1692605631/Introduction%20of%20Module.html)本次网页没有可提取正文；沿用[已归档原厂介绍PDF](evidence/2026-10-18_i03/vendor_driver_introduction.pdf)及[原核对来源](evidence/2026-10-18_i03/README.md)，标准板5V输出标称3A。此为资料标称，不能当两板＋相机＋电机共同运行的实测余量。
- 2026-11-10查看立创[供电FAQ第6.2节](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/faq.html)：外部5V只接电源5V0；排针输入不能用于电脑Type-C同时供电时的补电。厂家将排针5V方式定位为临时使用，并不推荐长期独立运行。按主控既有杜邦线方案先做验证，正式装车须复核接触、固定与负载压降；不要求本轮改为另一套接口。
- 立创[引脚查询说明](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/pinout-tutorial.html)覆盖Lite-K230D；定位时选Lite 128MB与实物丝印，不能照抄标准板不同GPIO脚位。
- 立创[离线运行说明](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/ide-usage/offline-run.html)：IDE临时执行位于内存，断电即失；上电在sdcard寻找boot.py／main.py。原采集入口不等于已安装低速视觉。

## 切换供电前的操作顺序

本轮万用表损坏，新电池端电压和驱动5V尚无新实测；**今晚先保留现有调试供电、完成启动候选准备，实际新供电核对由主控／硬件借到完好仪表后执行**。不使用损坏仪表，不从“已充满／额定7.4V”补造5V输出测量。

1. 主控先关驱动、隔离电池、断开DAPLink USB及K230电脑Type-C，确认无供电后再移动电源线；记录各线丝印和端点。
2. 取消DAPLink到STM32的5V0供电线并单独绝缘；主板电脑Type-C也不接。若之后保留SWD调试，只按已确认下载器接法保留信号与GND，不重新并入DAP供电输出。K230电脑Type-C拔开后才采用排针5V供电。
3. 在两计算板负载断开时，由硬件核对驱动明确标5V/GND的输出、极性与稳压值，再全部断电，按上表接入两板。两路杜邦连接分开固定，板底绝缘，避免运动拉力由针脚承受；共地沿已确认接法，不把电机大电流回路串经逻辑地线。
4. 首次仅验证零驱动冷启动，不按KEY。**此时驱动板总开关同时决定逻辑与H桥供电，关驱动不能作为“保留逻辑但断电机”的方法。** 若需物理无动力验证，先在全部断电时标记并临时拔开两组电机六芯插头；保持两板与UART供电，测试后全部断电再按原标记恢复，不交换轮侧。插头断开时不进行电机校准。
5. 验证两板上电、K230诊断日志正常结束、STM32保持零输出；再分别验证带逻辑负载的5V、相机运行时有无复位与输入掉压。记录原始读数／日志，不能只看电源灯验收供电。之后恢复电机插头并按I-02人工悬空校准／重复启停／失效停车推进。

## 已准备的脱机诊断候选

- [本地主程序候选](../testing/2026-11-10_pre_field/cold_boot_candidate/main.py)：以已验证runtime_r5为基础，live＋UART、最多10秒、ALLOW_DRIVE=False、关闭IDE预览；即便识别到有效路径也只发无效PATH，命令仅STOP，不发START，不重新开采集许可。
- 新增日志只进入`/sdcard/lap_boot_checks/check_0001.jsonl`等新编号文件，不覆盖旧组；缺SD／日志错误退出。正常完成写completed，异常写failed并退出，不自动重试；日志完成不代表STM32接收、电气供电或动力通过。
- [16项电脑启动／日志边界检查](../testing/2026-11-10_pre_field/cold_boot_checks/checks.json)与[42项视觉／实际C协议检查](../testing/2026-11-10_pre_field/cold_boot_protocol_checks/checks.json)通过。新程序已在**当前USB供电下以RAM脚本**实跑144帧，算法45..57ms、最大启动间隔108ms，日志已读回并核对禁止驱动；见[实板结果](../testing/2026-11-10_pre_field/cold_boot_ram_01/result.json)。这不是物理冷启动或电池供电验收，STM32该轮新增计数尚未独立回报。
- 已只读备份当前板上[main.py原字节](../testing/2026-11-10_pre_field/startup_backup/main.py)，11636字节，SHA256 `9ac4d097f5000ec323f255981756ada9c5c5020516651f8321f40151799222e2`；当时boot.py与两项已知采集许可均不存在，[原始备份清单](../testing/2026-11-10_pre_field/startup_backup/manifest.json)。没有改写这些板上文件。
- **主控已明确确认切换，10秒自检main.py已写入并逐字节读回一致。** [部署结果](../testing/2026-11-10_pre_field/boot_deploy_01/result.json)：34887字节，SHA256 `c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269`；写前旧文件与真实备份一致，写后boot.py与两项已知采集许可仍不存在。此次授权仅覆盖该禁止驱动自检，未扩大为有效运动或供电改接。每次上电运行一次10秒诊断；之后不再持续提供路径，不是比赛运行程序。恢复原入口须使用上述真实备份，不用旧历史副本代替当前文件。
- **原USB供电下的K230物理冷启动自检已通过一轮。** 主控按“仅K230 Type-C断开约5秒再接回、等待至少30秒、不按KEY”指导回报“已重启”。随后助手只读取得新`check_0002.jsonl`：143帧、begin至completed完整、wire_valid／drive_allowed始终false；旧RAM日志check_0001字节未变。读取会话未发runScript／写文件，连接输出无BOOT CHECK LOG新启动标记，[原始日志与结果](../testing/2026-11-10_pre_field/cold_boot_power_01/result.json)配对保存。该结论基于主控物理操作反馈与新持久化日志，不是仪器测量或电池供电验收；STM32该轮接收／错误读数仍待核对。
- 后续STM32原图确认state6／LAP_TRANSPORT10、received623、UART总错误2、左右PWM0；**本轮跨板冷启动通信未通过**，不因K230日志完整而放行。错误分项／时点待核，见[失败记录](../testing/2026-11-10_pre_field/cold_boot_uart_fault_01/review.json)。先保留现场取得g_lap_uart_diag，不复位清零，不进入动力或车载供电切换。
- 隔离复测已确认：稳定USB供电的9秒无效发包后UART／frame0；保持STM32运行、只拔K230电脑Type-C后出现frame3／总错误3、state6／LAP_TRANSPORT10，左右PWM0，详见[断电阶段原图](../testing/2026-11-10_pre_field/uart_power_off_01/review.json)。已复现断电阶段触发，具体电气机制未测；保护维持锁定。下一步仅观察重新上电是否增加错误，再验证K230稳定后人工复位STM32的准备顺序，不宣称共用电池启动或动力停车已通过。
- 重新上电后主控反馈总错误／frame仍3、故障保持；助手随后只读取得新check_0003（142帧完整无驱动自检），[反馈及日志](../testing/2026-11-10_pre_field/cold_boot_power_02/stm32_feedback.json)保存。本轮上电未新增错误是单次观察。接下来保持K230稳定供电，仅复位STM32验证零基线，作为当前无动力诊断的恢复准备；不自动清故障、不将其当硬件问题修复，也不据此放行未测量的车载5V改接。
- 最后主控按“K230稳定供电，STM32手动Reset CPU→Run，等5秒”的预期表确认恢复零基线，state／reason／received／PWM／UART错误均0、ms递增，[反馈](../testing/2026-11-10_pre_field/recovery_idle_feedback.json)归档。本轮无动力检查收尾，之后没有代理设备操作。断电FE电气机制、车载电池供电与动力停车仍待验；明日接续见[操作单开头](pre_field_checklist.md)。

比赛依据[第三部分、图1及评分表](../competition/比赛文档.md)：车载独立系统、可充电动力源、顺时针自动一圈且5分钟内。此项降低断电重启、松线与供电不足导致的未完赛／碰线风险，支撑基本60分；可追溯测试支撑报告20分。无具体得分预测，候选与软件检查不算实测完圈。
