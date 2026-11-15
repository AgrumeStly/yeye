# 独立低速一圈试跑：操作与证据

2026-11-12最新：首次地面短直道在2044ms触发LAP_REVERSE5，原09故障已无复位保存，详见[原始失败及取证补充](../../testing/2026-11-12_field_resume/ground_straight_01/diagnostic_candidate.md)。当前本地LowSpeedLap已构建为**0x0211000B／3000ms**，Track为0x0211000C／300000ms；只增加停车前32个20ms原始编码器窗口并冻结，原始反向-5RPM／KEY／UART／源年龄／无反馈／PWM保护均保留。346项模型及生产UART主机检查、两目标ARM构建通过，不代替新版本实板时序／地面。**STM32最后实读仍09，代理未下载**；下一项人工下载选LowSpeedLap短版，不选Track。旧09／0A BIN与既有实物结论保存为历史，不能当新增记录版本已经验证。

K230取证v3已按已有自动main修改授权备份v2、部署并完整读回，R6检测器／协议未改，只加逐帧elapsed_ms／真实PATH序号、年龄及候选参数。30秒禁驱动实板380帧／46项模型与18项部署边界检查通过；v3有效动力、0B实板与地面恢复未验，整圈未完成。原图、旧日志、构建与实际供电接续以I-02文首为准。此次取证支撑完圈与避免触边／出界，不声明得分。

2026-11-10接续：新电池已安装，主控确认已充满、额定7.4V、驱动板供电正常，端电压未测；OLED独立点亮已验，板上最后确认OledBench。今晚与11-11场地逐项操作统一查[出发前操作单](../../hardware_preparation/pre_field_checklist.md)及[本轮记录](../../testing/2026-11-10_pre_field/record.md)。低速09／Track0A重新构建与原BIN哈希一致，尚未恢复下载／进行新电池动力复测。下方11-09低压读数仅属于旧电池，保留历史。当前LowSpeedLap不含OLED显示，旧屏幕内容不当运动状态证据。

2026-11-09供电待核实：主控回报2S动力电源4.95V，测点尚待确认。已指导停止动力、驱动OFF／拔XT30、暂不充电；若该值确为电池自身输出则须按厂家低压处理，不继续以此调参。准确测点与替代电源条件见[当前电源核对](../../hardware_preparation/low_speed_power_check.md)。09固件保持，现场随时可到，可在动力隔离时先做真实视觉验证。

2026-11-09最新可靠性缺口：09版准备断源测试时，左轮未起转、右轮短暂转动，312ms因NO_FEEDBACK停车；尚未拔K230 USB，不能记断源保护通过。原图见[motor_link_loss_02](../../testing/2026-11-09_low_speed_lap/motor_link_loss_02/stm32_review.json)。先核实当前动力供电与单轮起转重复性，已指导驱动OFF，未继续修改参数；此前单次直行／差速通过保留，但不能据此直接放行地面。

2026-11-09左差速接续：09版左差速悬空3000ms正常LIMIT，目标20／60、末次反馈16.9268／59.5401RPM，主控确认转动符合预期、UART错误0；SysTick最大192.5us、状态提交43.5625us，见[motor_left_01](../../testing/2026-11-09_low_speed_lap/motor_left_01/stm32_review.json)。09正负差速各一次通过，07直行三秒已通过；均非地面／实际视觉／完整一圈验收。下一步验证断源撤驱动，保留主板供电。

2026-11-09差速接续：09版右差速人工固定输入下悬空运行3000ms正常LIMIT，目标60／20、末次反馈60.8911／19.6733RPM，主控确认转动符合预期、UART错误0，见[motor_right_02](../../testing/2026-11-09_low_speed_lap/motor_right_02/stm32_review.json)。仅本轮悬空差速通过，左差速／失效撤驱动／地面与真实视觉仍待验证；前次07内轮停滞失败保留。

2026-11-09最新动力接续：07版在独立人工固定输入下，首次悬空双轮起转并正常3000ms撤驱动；主控确认两轮向前且停稳、UART错误0。最后反馈41.6508／40.4017RPM，起步补偿各1个样本，原图及范围见[motor_straight_06](../../testing/2026-11-09_low_speed_lap/motor_straight_06/stm32_review.json)。这是一次悬空直行通过，差速／地面／真实视觉与一圈仍待验；RUN周期统计待补，不将最后一帧当连续达标。

2026-11-09通信接续：主控已回报180个路径包被STM32接受，负值−600解码正确、UART错误0；补充末尾STOP发送余量后，主控确认accepted比received多1符合预期，基础无动力UART及STOP解析关系确认。当前板上副本更新到`board_bundle_runtime_r5/low_speed_lap_canmv.py`（只增加清理STOP后的10ms发送余量），r4等旧包保留历史。实时无驱动发送已实跑165帧，STM32这轮累计值仍需按实际反馈留证；动力停车／循迹未验收。

2026-11-09实板接续：K230已连接并完成已有SD图／10秒无驱动相机测试；修复MicroPython数组兼容并缩小实测超时的搜索／网格。**当前板上副本改用**`testing/2026-11-09_low_speed_lap/board_bundle_runtime_r4/low_speed_lap_canmv.py`，旧board_bundle_release只保留历史。K230无效UART探针已执行，STM32实际接收仍待主控Keil读数；分版本原始证据见[实板接续](../../testing/2026-11-09_low_speed_lap/hardware_runtime_review.md)。仍不放行有效驱动或整圈。

日期2026-11-09；责任主控；任务[I-02](../../project_planning/tasks/I-02-LOW-SPEED-LAP.md)。这是研发候选，现有证据是电脑检查／ARM构建，不是板上／整车验收。首版L1仍有锐角缺口和稀疏录像重置，默认禁止发送有效运动许可；不能直接宣称下午已可完整跑圈。

## 目标与入口

比赛第三部分、图1和表1：今天争取连续顺时针自主一圈，5分钟内，减少触边与完全出界失败；冲线自动停车暂不纳入今天范围。正式运行途中不人工干预，分段重摆不能记作一次自主完圈。研发阶段可以分段验证并保留失败，按下KEY／断动力属于终止当前试验，不记本次完圈。

Keil5 Project → Open Project打开`control/MDK-ARM/low_speed_lap.uvprojx`。保留已确认CMSIS-DAP／SWD下载器，本机uvoptx从原SpeedMatch独立复制并预置Watch，不改原工程。它被Git忽略，换电脑须重新核对。选择：

| 目标 | 版本g_speed_revision | 默认运行时限 | 用途 |
| --- | --- | --- | --- |
| LowSpeedLap | 0x02110009 | 3000ms | 悬空／短线联调；增加正目标低速前馈下限 |
| LowSpeedLapTrack | 0x0211000A | 300000ms | 前序通过后的场地低速候选；不自动判圈 |

两者默认共同基速40RPM、每轮最高60RPM、PWM<=50%，这些是待验证初值。只有校准仍逐轮500ms。Track用独立编译目标保存时限选择，避免断电后Watch RAM丢失混淆3秒／5分钟；上电仍不自启动。

UART诊断版03／04增加`g_lap_uart_diag`，旧01／02版本记录保留为历史。`g_lap.state=6`且`reason=10`表示接收故障锁定，KEY不能解除，不能解释为单纯等待路径。`g_lap_uart_errors`计事件数；展开诊断结构体查看overrun／noise／frame／parity／ring_full，以及first_mask／last_mask和first_at_ms／last_at_ms。mask依次用1／2／4／8／16组合，时间单位为本板启动后ms。分项可能同时发生，不能把总数直接当某一种错误次数。分类只为定位，不改变遇错停车保护。

05／06针对实际固定输入中12次ORE调整中断：UART抢占级0，SysTick抢占级1（Group2下使用CMSIS编码，逻辑优先级为4），主循环用BASEPRI屏蔽SysTick提交状态，UART仍可收字节。保留1ms监督、20ms采样、115200/8N1、错误锁定和三秒／Track上限，不修改原SpeedMatch目标。软件构建／主机检查通过，调整有效性仍待实板复测，不把推测的阻塞路径写作已证明的全部根因。

新增`g_lap_timing`：counter_ready应1、clock_hz应16000000，systick_max_cycles为包含UART抢占的SysTick最长执行周期数，motion_lock_max_cycles为最长状态提交周期数。UART本体最长周期数在`g_lap_uart_diag.isr_max_cycles`；它不是错误计数，收到包后非零属正常，不能再笼统要求整个diag全零。当前16MHz下周期数除以16为微秒。复测须核对错误分项全0、无故障、计时器有效，并检查UART耗时相对86.8us字节间隔和SysTick／提交时间相对1ms监督周期的余量；这些是队内工程门槛，不是比赛规则，计时也不替代真实停止／完整一圈。

07／08针对“已RUN但仅有声音、无转动，300ms无反馈停车”增加受限起步补偿。每轮目标从0变正、尚无编码器增量时，最多100ms输出500/1000（50%）；任一脉冲立即结束该轮补偿，随后按原PI调速。目标0不补偿，持续堵转不反复补偿，300ms无反馈、反向／超速、路径／通信与KEY保护均保持。50%上限源于既有单轮500ms校准；100ms是待实车验证的候选参数，不是实测静摩擦模型。40RPM、左右0..60RPM、三秒上限均不变；不能仅因模型通过就用于地面／赛道。

停车后展开`g_lap_last`读取最后一次真正RUN的结果：valid=1、reason、elapsed_ms、最后样本的左右目标／RPM、撤驱动前PWM和左右boost_samples。正常三秒应reason=LAP_LIMIT（11）、elapsed_ms=3000；故障时保留真实原因与已运行时间，后续K230清理STOP或实时RPM衰减不覆盖。新RUN使valid暂置0，复位清空。boost_samples是20ms补偿输出样本次数，首次起步最多5；它不是实际电流／扭矩或速度达标证据。用户观察方向、起转和停车仍须分别回报。

09／0A针对07右差速实物460ms后内轮无反馈，新增`g_lap_config.min_feedforward`，单位为PWM千分比，默认200、允许0..300，停止时可在Watch调整，下次人工启动锁定到`g_lap.active`；非法／非有限值拒绝启动。正目标前馈为原线性项与此值的较大者，因此20RPM参考由10%提高到20%，40／60RPM参考不变。它是PI基础项，不是实际PWM下限，PI仍可输出0，目标0始终停轮。原50%／100ms起步补偿、300ms无反馈、方向／超速／KEY／通信保护保持。200为候选设置，来自已验证40RPM附近的低速参考，不是实测静／动摩擦标定。07直行证据保留，09差速尚需悬空复测，不能直接用于地面／赛道。

首次复测先断开电机动力、保持逻辑板USB供电；Keil退出旧调试会话，选LowSpeedLap并Flash → Download，重新进入调试并Run。先确认版本09、UART计数／错误分项为0且state=0、counter_ready=1、min_feedforward=200，不按KEY、不重做校准。必要的无效接收复测与05版相同；09的UART实现未改，已通过的05无效包及07直行证据保留但不等同09全部实物验收。若再次错误，先保存诊断再复位；不通过修改state或清零计数绕过锁定。模型检查不覆盖真实USART电气／中断，必须以实际步骤留证。

## 宿舍先做：无动力、板上与通信

1. 两板断电，按[三线接线](../../hardware_preparation/low_speed_lap_wiring.md)接好T→A03、R←A02、G共地，V不接；主控保持电机动力断开。
2. Keil选LowSpeedLap，Project → Rebuild all target files，检查0错误0警告；Flash → Download下载，Debug → Start/Stop Debug Session进入调试并Run。观察`g_speed_revision=0x02110009`、`g_speed_fault=0`、`g_lap.state=LAP_CALIBRATION`。**此时不按KEY**；没有动力就不能做动力通道校准。
3. 通信可以先独立检查：K230打开`vision/src/lap_uart_probe_canmv.py`，默认ENABLED=False仅IDLE；保持电机动力断开，在工作副本改True后手动运行。9秒内分别发送0／+600／−600无效路径各3秒，始终flags=0且不发START，末尾STOP。Keil应看到accepted／received增长、steering按三档变化、path_valid=0、PWM为0。此脚本不需要相机模块，先把接线／CRC与图像耗时分开定位。
4. K230手动运行独立合并文件`testing/2026-11-09_low_speed_lap/board_bundle_runtime_r5/low_speed_lap_canmv.py`。原件默认MODE=idle，先确认只打印IDLE。不要选择“保存为main.py”，不改变旧采集入口／许可。
5. SD诊断使用工作副本MODE=sd_replay、UART_ENABLED=False、ALLOW_DRIVE=False，读取SD已有30张。它们是非连续选片，每图清时序状态；只验证API／空间输出／堆和耗时，不能当30帧实时循迹。保存完整终端，包含模板数量、剩余堆、每图结果和错误。
6. SD/API通过后，电机仍断动力，工作副本MODE=live、UART_ENABLED=True、ALLOW_DRIVE=False。配置已明确UART2/11/12，不改串口0。Keil检查`g_lap_parser.accepted`与`g_lap.received`增长，`g_lap.path_valid=0`、PWM为0。坏CRC／错版本不刷新路径；不能拿“发送成功”代替真实接收。
7. 保存每10帧日志的acquire_ms／copy_ms／processing_ms／to_send_ms／interval_ms／free_heap。要求处理不超过100ms、含报告年龄的当前路径未达200ms、历史支持未达120ms，源年龄<150ms；这些是软件保护门槛，不是比赛规则。若不满足，先修实际瓶颈，不能放宽超时来冒充实时通过。SD解码时间不当相机帧率。

当前L1与昨晚T2不是等价移植。L1纯基础Python／math／array，不含NumPy/OpenCV；预计算双边折线的稀疏网格模板，运行时当前黑组件匹配。双边／当前单边关联／无支持短历史／未知分开。首帧与断流后必须重新出现稳定双边；文字和单横带不能凭模板直接升级为可信启动路径。二维横向投影、车体余量和官方色块适应性仍待验。

## 动力步骤的进入条件与人工操作

基础无动力通信和零输出／状态确认后，可先做与视觉路径无关的两次悬空单轮校准；这两次仍是原有500ms／<=50%手动识别。进入双轮视觉循迹则必须另有实际当前画面几何、稳定许可及悬空控制证据。本地检查不替代这些条件。当前默认ALLOW_DRIVE=False，不应在缺少实物证据时直接改True跑整圈。

先稳定悬空并确认轮侧、前进方向及紧急撤动力方式。首次选3秒LowSpeedLap。KEY是主板PA0／WKUP对应的实物按键：每次长按约1—2秒后松开，第一次左轮500ms，停稳后第二次右轮500ms；均须实际前进且仅对应反馈通道有脉冲。原校准识别通道／符号但不能证明实际朝车头。校准完毕后等待车体静止。

下一次KEY启动需当前双边新鲜许可，历史／单边不能启动；按键按住期间不运动，松开后才接受。运行中任何KEY立即撤驱动并锁故障；5秒卡键也故障。运行故障需要复位并重新校准，不会因图像恢复自动续跑。停止是00滑行，不保证车轮立即停稳。

独立悬空固定输入测试：完成上述两次校准、主控实际核对run_ms=3000且轮子始终悬空后，最新固定输入位于`testing/2026-11-11_battery_bench/motor_bench_bundle_r3/lap_motor_bench_canmv.py`。此脚本默认IDLE，启用后straight场景只提供0转向固定输入，软件目标40/40RPM；600秒输入等待窗口内仍必须主控KEY长按松开才运行3秒，不发START。11-11因问答超过120秒造成窗口结束，将等待窗口延长为10分钟，STM32三秒上限不变；R2等旧包保留历史。每次启动只按一次；只有明确安排重复轮次时，正常停稳后再等至少5秒，才可下一次人工启动，任一异常停止后续。正常LIMIT结束不需要Reset CPU，复位会丢失校准；故障锁定仍需保留证据后按既定恢复流程处理。

该输入不是相机观测或双边识别通过，不能用于地面／比赛，不改变真实视觉ALLOW_DRIVE=False。助手motor_straight／motor_right／motor_left仅为固定白名单；入口仍要求`--confirmed-suspended --confirmed-mcu-run-ms 3000`携带已取得的主控实物确认，脚本没有STM32回读能力。R3只延长输入窗口／客户端超时，封包源码与R2逐字节相同；19项入口模型及18项假会话助手检查通过，不替代实物验收。

11-11后续助手支持`--motor-window-ms 120000`（单次明确操作）或默认600000（需要问答／明确重复轮次），只能二选一；主板单次3000ms不受影响，实际RAM执行文本与窗口记入run.json。短／长窗口、三种场景及非法窗口连接前拒绝等共30项FakeSession检查通过；客户端仍不发送START或读取主板实际配置。正常三秒停止无需复位，换场景前等待原会话正常结束，避免并发占用同一COM口。

首次只按一次KEY，观察两轮前进及约3秒后撤驱动，不暂停／单步／设断点。运行中转速可在g_lap.left_rpm／right_rpm观察；结束后实时值会衰减到0，不能用停车后的0当运行转速。结束先回报两轮真实表现，之后才安排有符号差速或真实视觉测试。固定输入只证明已限定条件下的动力调用链，运动停车、失线／断流和整圈均需分别留证。

无效探针先在Watch核对`steering`有符号解码，左右目标／PWM必须仍为0；不能要求无效包驱动目标变化。模型中的右转左目标较高、左转相反已由主机检查覆盖，真实差速须在完成校准、具有新鲜有效许可且明确的悬空受限RUN中另验。内轮目标0允许无脉冲，恢复正目标后300ms没有反馈应停车。取走视觉输入／停止K230脚本时的真实撤PWM与滑行表现也另存，不能由本次无动力收包替代。

## 下午现场顺序

主控携带全部设备到最终比赛现场。先不接电机动力查看真实边界／文字／光照下的实时路线，确认是否与昨晚连续黑带同规格；正式图1注明5cm黑色色块，连续带回放不能代替官方色块验证。图像与车体转弯余量不可靠时继续修识别，不能用盲走若干秒补弯。

前序通过后依次低速短直线、单弯（特别约77°内角）、弯后重捕获，再选择LowSpeedLapTrack尝试连续一圈。Track重启后仍重做两次悬空校准；不能把既有默认40RPM当已验证地面速度。每次记录固件／视觉副本哈希、供电／场地、成功或失败、触边、停机原因、起终点和圈时，证据入口`testing/2026-11-09_low_speed_lap/`。只有整车连续自主通过才记一圈；没有自动终点停车加分声称。

## 验证／维护

电脑控制模型：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File control/tools/run_low_speed_lap_tests.ps1`。ARM构建：`vision/.venv/Scripts/python.exe control/tools/build_low_speed_lap.py`，Track加`--target LowSpeedLapTrack`。同checkout串行构建／下载，不与主控Keil保存争写。

代理构建调用同安装uVision.com命令行包装器解决本机UV4直接批处理无新日志的问题；没有更换Keil／SPL／下载器。真实运行记录和完整限制以[I-02](../../project_planning/tasks/I-02-LOW-SPEED-LAP.md)及当日review为准，原v1协议与旧目标保留。
