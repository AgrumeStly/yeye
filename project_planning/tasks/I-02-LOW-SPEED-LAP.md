# I-02：低速自主一圈试跑链路

## 当前摘要

唯一标识：`I-02-LOW-SPEED-LAP`；阶段：S2；状态：**进行中**；整理：2026-11-19。
负责角色：主控；硬件／视觉协作沿用主控最新指派。执行对话：未重新指派；旧身份见历史。
结果／限制：原低速一圈链路两次地面未通过；11月12日最后定位左轮NO_FEEDBACK，不等于当前首弯LINK故障。
唯一下一步：总管先核对与I-03直道、I-04首弯的缺口关系，不并行恢复旧实跑。

## 任务定义

成果：I-02：低速自主一圈试跑链路。原范围、依赖、交付路径及量化标准见历史区；不自动取消遗留要求。原执行版本／环境／量化验收要求在历史区；恢复前由总管提升仍适用的缺口至本区，不能直接执行旧Prompt。
比赛关联：第三部分、图1、表1；支撑基本功能60分的可靠完圈、少触边及缩时，并保留报告20分的可引用证据，不宣称新增实测得分。
授权：本轮仅重构文档；原实现／设备／上传授权不续期。新执行按[协作规则](../collaboration_standard.md)及主控转交的当前范围。
- 事实来源：[证据／规格1](../../testing/2026-11-12_field_resume/ground_straight_02/trace_review.json)；[证据／规格2](../../testing/2026-11-12_field_resume/ground_straight_02/record.md)；[证据／规格3](../../testing/2026-11-12_field_resume/ground_straight_01/mcu0b_cal_right_01/capture.json)；[证据／规格4](../../testing/2026-11-12_field_resume/ground_straight_01/mcu0b_cal_left_01/capture.json)

## 执行结果

原实现、检查日期、版本、方法、实物反馈及未完成项保留于历史区／证据；本轮仅统一记录，未重跑原测试。完成层次限于摘要，不把软件或部分通过当整车验收。

## 主控验收

尚无覆盖原任务全部范围的主控明确验收；旧对话审核不替代主控。 后续填：日期／主控原话／通过或退回／接受范围／证据。退回继续本任务。

## 接续信息

迁移工作区D:/projects/projectsyeye，分支codex/current-version-20261025，HEAD 62b4f288b27c4e3fa9f6d213c07be186e502f43c；有共享未提交／未跟踪成果，不是原任务执行快照。
已有检查按适用源码、配置、输入和环境复用；只恢复摘要的唯一下一步。保护共享修改，先核对实际版本／设备占用。旧逐轮测试与固定聊天Prompt不作为当前指令；当前双轮流程按AGENTS。

## 历史记录（原文保留，仅作来源）

原日期、失败、授权和相对链接完整保留；下方“当前／下一步”只适用于原版本，不覆盖上方摘要。

<!-- ORIGINAL_TASK_BEGIN -->
# I-02：低速自主一圈试跑链路

日期：2026-11-09；负责主控实施与人工验证；本对话不接替00。状态：进行中。

## 2026-11-12恢复执行（最新）

**第二次地面停因已定位到左轮反馈：2881ms NO_FEEDBACK7**。[原始环及复核](../../testing/2026-11-12_field_resume/ground_straight_02/trace_review.json)确认左轮最后增量后连续300ms无脉冲、正目标9.18..19.32RPM／PWM21.5%..25.5%，右轮持续正向反馈；此前左目标曾为0，50%重起获得短暂脉冲后低请求又无反馈。当前PWM0，UART／硬件错误0。支持带载低速维持／重起缺口，尚不能单凭无脉冲区分机械／编码器，也未量电流或动力电压。0B RUN写环实测SysTick最大218.3125us，未见1ms时序超限。下一步原件保存后整车断电，隔离K230支路取逐帧视觉原日志，解释直道低目标；不盲目提PWM或放宽保护，不覆盖第一次REVERSE。两次均未通过，整圈未完成。

**第二次地面已实跑，约5cm／摇摆／无触边／自动停后快闪，待取冻结环**。主控补充“感觉马达动力很小”，按主观现象保存，未量电流或扭矩。[ground_straight_02](../../testing/2026-11-12_field_resume/ground_straight_02/record.md)按未通过，尚未读取本次停因，不直接沿用首次REVERSE或推定供电不足。下一步保持车载电、不按KEY／RST、不进Debug，仅恢复不供电SWD三线后无复位取停车快照及原始32窗口；不重跑或提PWM掩盖故障。整圈仍未完成。

**0B地面取证复测准备完成，尚待实际启动结果**：主控确认脱DAP后周期闪正常，摆顺时针直道居中、前方1米空直道并观察当前双边待机灯后反馈正常。保持0B／3000ms／phase2和车载供电，电脑线均脱开；下一步仅一次人工KEY，独立[ground_straight_02](../../testing/2026-11-12_field_resume/ground_straight_02/record.md)已建。原ground_straight_01的2044ms反向失败保留，当前只是补原始采样缺口，未改保护或宣称已修复；停止后先读冻结环，不复位／重复启动。

**0B必要左右校准已完成**：主控两轮各500ms正常，[最新实读](../../testing/2026-11-12_field_resume/ground_straight_01/mcu0b_cal_right_01/capture.json)phase2／error0／WAIT、UART与硬件故障0、目标／PWM0、3000ms，取证环仍空。悬空视角单／双边交替，尚非地面稳定许可。下一步仅脱开DAP三根SWD线、仍悬空观察周期灯，不进入Keil／RST／第三次KEY；之后摆直道做一次针对性取证复测，原2044ms失败未解决且不覆盖。

**0B左校准已恢复**：主控回报正常，[实读](../../testing/2026-11-12_field_resume/ground_straight_01/mcu0b_cal_left_01/capture.json)phase1／error0／UART0／PWM0，配置仍3000ms；下一步只第二次KEY右轮500ms。仍悬空且PATH无效，未安排双轮RUN或地面。

**RST后0B应用基线已实读建立，下一步只补左轮500ms校准**：主控明确“已按”物理RST后，[mcu0b_baseline_03](../../testing/2026-11-12_field_resume/ground_straight_01/mcu0b_baseline_03/capture.json)Flash一致、revision0x0211000B、40RPM／3000ms／前馈200、phase0／error0、CALIBRATION0、目标／PWM0，CPU运行，ms21249→22361／接收383→405，硬件与UART错误0，取证环空。DWT16MHz，SysTick基线80.75us／提交15.0625us／UART12.1875us；不代替RUN写环时序。当前悬空path_valid0，不放行双轮／地面；校准不依赖视觉，只补下载／RST清掉的两次500ms，不重做全台架。下方未初始化RAM为RST前拒收原件，不沿用为当前故障。

**主控已人工下载；Flash确认为0B，但应用启动基线尚未建立。** 主控下载反馈“正常”，无复位实读Flash与短版1fc5ee49…33e4a28完全一致；RAM版本却为0x68016041、state74／phase1134586120、毫秒不增、DWT时钟异常，不能当真实应用状态／故障计数。[原件及拒收结论](../../testing/2026-11-12_field_resume/ground_straight_01/mcu0b_baseline_01/review.json)已存，下载算法RAM残留只是假设。下一步保持悬空／车载供电，主控仅按RST一次、不按KEY／进Debug／重下载，随后无复位实读0B／3000ms及启动接收。代理未reset／halt／resume或烧录。

**当前车载上电正常，进入主控人工下载0B**：主控在接线恢复、两轮悬空且电脑USB均不接下，接新电池XT30／驱动ON并等待30秒后反馈“正常”。记灯／静止人工现象，不把它当v3冷启动有效接收证据。短目标当前BIN与mcu_trace_build_02逐字节哈希一致（1fc5ee49…33e4a28），0错误0警告；下一步接不供电DAP电脑USB，主控Keil打开low_speed_lap.uvprojx并选择LowSpeedLap，手动Flash→Download，暂不进入Debug／按KEY。下载完成及0B／3000ms／状态／UART须后续实读；代理未烧录。

**当前物理接续已更新**：主控已确认两只驱动轮完全悬空、拔K230电脑USB后两板断电，随后按全断电接线步骤回复“接好”：K230车载稳压5V→5V0／共地、UART T→A03／R→A02恢复，DAP仅SWDIO／SWCLK／GND，供电和NRST不接；全部电脑USB仍不接，驱动OFF／XT30断开。下一步只车载上电并观察两板及零运动，不按KEY／RST、不进入Keil；随后才安排主控人工下载LowSpeedLap短版0B。STM32尚未下载，最后Flash仍09；下方“仅K230电脑USB／支路隔离”属于取证时历史接法。

**最新接续：地面失败已归档，取证版已准备，先悬空再人工下载0B。** 首次地面2044ms反向反馈停车仍未解决，不记正常3秒、地面通过或完圈。原run_0009真实取回（2796084字节／8218条抽样），USB run_0010另存；长日志7处抽样大幅转向跨零缺精确时间／图像，不能指定为本次2秒根因。失败后停车位置10秒禁驱动预览保存5张图，静止双边候选稳定，不能外推移动稳定。[完整补充／当前接线](../../testing/2026-11-12_field_resume/ground_straight_01/diagnostic_candidate.md)。

本地STM32新增1952字节固定取证环，保存停车前32个20ms原始delta／rawRPM／目标／PWM及视觉来源；不改任何控制阈值或保护。短目标LowSpeedLap **0x0211000B／3000ms**、Track0C／300000ms，两目标0错误0警告，346项模型断言及生产UART主机检查通过；原09 AXF/BIN先备份，新产物及源哈希在[mcu_trace_build_02](../../testing/2026-11-12_field_resume/mcu_trace_build_02/manifest.json)。**代理未下载，STM32实际最后仍09**，新增时序和实物待验，不选Track地面。

K230取证v3 main **f9a12f4ec10d1fec6ab629f3415858403b2a4d0ed4df16dfb76482f4c5fe16d8**／36244字节，R6检测器与封包AST未变，仅逐帧时间／真实序号／年龄和候选参数。46项入口模型、18项部署边界及30秒禁驱动380个连续帧实板检查通过；已按自动修改授权实际备份v2并[完整部署读回](../../testing/2026-11-12_field_resume/runtime_trace_deploy_03/result.json)。v3有效动力／物理冷启动尚未验。

当前驱动OFF／XT30断开／DAP电脑USB不接，STM32不供电；K230车载5V0与UART T/R已人工隔离，只有电脑USB供电，后端已关闭、running=false，main为v3。车辆最后在地面，下一步**仅支稳两只驱动轮完全悬空**，再全断电恢复车载接线，主控Keil人工下载LowSpeedLap 0B、保持DAP只SWD不供电；随后只补必要校准／实板时序及一次针对性复测。五姿态／全部台架不重做，无START／自动烧录／上传／跨聊天，全局留00。下方0B新增前的准备／09状态为历史。

**地面失败停因已实读：2044ms LAP_REVERSE5**。[原始快照](../../testing/2026-11-12_field_resume/ground_straight_01/fault_capture_01/capture.json)当前FAULT6／PWM0，UART及硬件故障0；末次目标6.7677／22.9803RPM、滤波12.2855／28.0351RPM、撤驱动前PWM17.2%／29.8%。任一原始归一化轮速<-5RPM会触发，原始触发采样未锁存，不能凭正滤波值断定误报或指定实际回退／编码器原因。主控反馈左右摇摆、短距慢行、无触边，按失败保存。下一步动力隔离后取相机日志分析，保持全部保护，不盲目重复地面或放宽反向阈值。整圈未完成。

**首次地面已实际执行，未通过待取停因**：主控反馈“前进了很短距离，速度较慢，无触边，左右摇摆，自动停车，停后绿灯急速闪烁”。原话及失败保留在[ground_straight_01](../../testing/2026-11-12_field_resume/ground_straight_01/record.md)，不当正常3秒LIMIT或完圈。下一步保持车载电和RAM、不复位／再按KEY／进Keil，仅接回不供电SWD三线，无复位读取g_lap_last与故障，随后按实际原因解决；不先重跑。地面距离／时长未量化，整圈未完成。

**已具备首次地面三秒试跑准备**：脱DAP后周期闪获确认，主控将车辆摆到最终赛道顺时针直道居中、前方至少1米空直道并脱开全部电脑线后，反馈每2秒亮约400ms的当前双边待机符合。保持09／3000ms／车载供电与phase2，下一步仅一次人工KEY地面短直道；[ground_straight_01](../../testing/2026-11-12_field_resume/ground_straight_01/record.md)已建，尚未反馈实际运动，不记通过。停车前不复位／重复启动，随后无复位取停车锁存及真实表现。

**DAP已脱开，主控确认周期闪符合预期**：此次Keil始终关闭，车载供电ON，phase2最近实读／零输出及故障0见下。下一步仅将车辆摆到最终赛道顺时针直道居中、正常车高，保持供电且不按KEY／RST，观察是否为每2秒亮约400ms的当前双边待机；80ms短闪不当稳定双边。尚未发生地面运动，不重复悬空三秒。

**两次必要校准已完成，准备脱开SWD**：主控确认右轮500ms向前并停、左轮不动；[无复位实读](../../testing/2026-11-12_field_resume/swd_detach_01/cal_right_01/capture.json)phase2／error0／WAIT1、UART及硬件故障0、目标及PWM0、09／3000ms。全程Keil关闭。下一步仅脱开SWD三线，仍悬空观察10秒周期灯；当前单边／双边交替，尚无稳定地面画面，不按第三次KEY。此前原phase2丢失原因未定，本次恢复不当该原因已修复。

**必要左校准已恢复**：主控回报左轮500ms向前并停、右轮不动符合；无复位[实读](../../testing/2026-11-12_field_resume/swd_detach_01/cal_left_01/capture.json)phase1／error0／UART0／PWM0。下一步仅第二次KEY右轮校准，仍悬空、车载供电ON且Keil关闭；未开始地面。

**最新无复位读取后恢复必要校准**：[capture_02](../../testing/2026-11-12_field_resume/swd_detach_01/capture_02/capture.json)CPU运行、ms627411→628976／接收9601→9622、UART及故障0、09／3000ms／输出0，phase0；本次未取得DAP拔插造成复位的证据，原始phase2丢失原因仍未定。当前有效PATH为single1，不能当双边启动。下一步保持Keil关闭和悬空，仅人工KEY恢复左轮500ms，随后读状态；不重复真实相机三秒或全部台架，地面仍待双边和校准完成。

**脱开DAP静态供电已补读数**：主控反馈STM32实际5V输入5.178V／3V3为3.315V，支持脱开DAP仍有静态供电，不证明无瞬态复位。下一步只恢复SWD三线后无复位读取计数及校准，暂不按KEY／RST、不进Keil；路径许可与必要校准仍待恢复，地面未开始。

**当前先定位脱开DAP后的变化**：主控退出Debug并脱开调试连接后反馈绿灯长灭。保持现场仅恢复SWD三线，无复位／暂停实读CPU RUNNING、ms与接收递增、UART及硬件故障0、Flash与09 BIN一致；但校准phase0／state0／PATH许可0，此前phase2不能沿用，暂不能落地。详见[swd_detach_01](../../testing/2026-11-12_field_resume/swd_detach_01/record.md)。下一步只补STM32在DAP信号脱开时实际5V／3V3电压，区分供电依赖；最新“有”无读数，不记通过。原因未定，不由累计复位标志推断，不重做整套台架。下方地面准备为异常前状态。

**当前进入地面准备**：持续相机v2已恢复车载供电上电，主控确认两轮悬空静止、两板电源正常；Keil仅SWD、不供电，K230电脑USB不接。主控对09/3000ms／初始零基线／接收递增且路径有效条件下的左轮500ms校准、右轮500ms及phase2/error0/state1/UART0/PWM0/path_valid1均回报“符合预期”。本次新入口运行／校准为人工确认，无独立新图；不重做此前车载三秒LIMIT台架。下一步保持车载电源和RAM校准，先退出Debug并脱开DAP调试连接，仍悬空不按KEY／RST，确认待机后再摆到最终赛道顺时针直道居中；首项地面仍3000ms。地面与完整一圈尚未实测。

**最新故障已定位并修复：相机十分钟期限**。车载供电三秒LIMIT后，主控补充path_valid0／received7394不递增；原图为WAIT1／KEY1、UART0／两PWM0。取回run_0006确认duration600000、最后当前双边仍有效、正常completed，与末尾STOP导致许可清零一致；未开始新的KEY或地面。完整原件及首次日志取证超512KiB失败（已仅扩展日志上限重读）保存至[runtime_window_stop_01](../../testing/2026-11-12_field_resume/runtime_window_stop_01/board_readback_02/lifetime_review.json)，不靠重启掩盖问题。

已依据本任务自动修改main授权部署**持续相机v2**：35926字节，SHA256 **838c5e9a4d14d42840c54526b1f3c4d4a848e93654de8bca5faf45f85fb2968f**，前版真实备份与完整读回见[runtime_continuous_deploy_02](../../testing/2026-11-12_field_resume/runtime_continuous_deploy_02/result.json)。DURATION_MS0仅表示相机持续输入，不更改STM32三秒／五分钟、人工KEY、视觉质量／年龄、断流／UART／编码器故障保护，异常仍STOP退出，不自动START／重试。旧R6检测器和协议未改；34项有针对性模型、30秒禁驱动实板日志及13项部署边界检查通过，超十分钟只是模型时刻测试，实板尚未长测。

当前取证／部署后：驱动OFF、XT30断开、DAPUSB拔开，K2305V0杜邦供电线已移除绝缘、仅电脑USB；后端关闭、running=false，电机插头仍按原轮侧接好且两轮此前悬空。下一步全断电恢复车载K2305V0并保持电脑USB隔离，再上电，Keil确认零基线后只补必要左右500ms校准；已有车载供电三秒LIMIT结论保留，不重复整套固定台架。地面短直道／单弯／锐角／顺时针完整一圈仍未验，不把本轮期限修复或软件检查当完圈。

**最新车载供电悬空RUN**：本次重新上电的左右单轮500ms校准及phase2/error0/state1/UART0已获“符合”确认。主控单次人工KEY后提供[快照](../../testing/2026-11-12_field_resume/onboard_visual_motor_01/stm32_review.json)，valid1／3000ms／LIMIT11，目标31.7614／35.4585RPM、末次30.2387／36.6082RPM、撤驱动前PWM19.5%／19.0%，并回报轮子正常转。供电为电池→驱动5V分支→两板，DAP只作SWD，K230USB不接；真实相机部署main，无fixture／START。当前PWM／UART、物理停稳和有无两板重启仍待补确认，动态电压未提供；不能把快照PWM当当前值或地面通过。下一步只读停车后值及物理反馈，符合后准备保持3000ms的地面短直道。

**当前步骤：恢复电机前**。主控在DAP供电输出隔离、K230电脑USB不接、两板车载供电且电机插头断开的条件下，进入Keil LowSpeedLap Debug→Run并对版本09／3000ms、接收递增／路径有效／UART0／两PWM0核对回复“符合预期”。按人工通信初验记录，没有独立新截图、state/phase逐项实值或是否自动复位说明，不当纯冷启动零故障。下一步全断电后按原轮侧标记恢复两组电机六芯插头，接好先不上电；再重新确认校准起点、恢复必要单轮校准，做一次车载供电真实视觉3000ms联动及电源现象核验。原USB供电台架不重复，地面与整圈未验。

**当前现场一步**：主控按全断电恢复K230车载5V0／UART T→A03、R→A02、G共地（V不接）、隔离DAP供电输出、保留SWD信号的步骤应答后，在新电池给两板上电／等待30秒、不按KEY、电机插头仍断开且两板电脑USB不接的条件下反馈“正常”。当前驱动保持ON，K230电脑USB不接。下一步只接不供电的DAP USB、进入Keil读版本／3000ms／state及reason／phase及error／UART／PWM／接收，不主动Reset或Download；若调试入口自动复位，必须区分于原始共电源冷启动。未取得实读前不记通信通过，详见本轮record。

**最新电池供电运行证据**：[runtime_battery_cold_boot_01](../../testing/2026-11-12_field_resume/runtime_battery_cold_boot_01/result.json)已只读取回明确选定的run_0003（100918字节、294条算法样本、最高index2640、无failed）；后续USB的run_0004另存，未混作电池证据。算法21..89ms、周期41..111ms；无效段1..5、34..58、428..429保留，不宣称整窗每帧稳定，断电结束无completed不当600秒自然结束。主控反馈灯／重启等现象正常，结合5.176V人工读数与操作顺序，完成两板静态负载及K230电池供电自动相机运行初验。UART T/R与电机当时均断开，共电源UART接收／电机动态／地面仍待验。

当前取证后K230只接电脑USB、其5V0杜邦供电线已移除绝缘；驱动OFF／XT30断开、STM32 DAP／USB不接、电机插头与T/R隔离。后端已关闭，无脚本由本对话运行。下一步在全断电下恢复K230车载5V0和UART T/R，明确移除DAP的5V／3V3供电输出并仅留已确认SWD信号／共地，才能在外部供电下用Keil核对版本／状态／UART／零输出；随后再恢复电机和必要校准。不得并接USB与外部5V。

**最新两板带载读数**：主控完成全断电下驱动5V/GND并联供STM32与K230 5V0/GND的接线（电机插头／UART T/R／DAP和USB均隔离），随后按K230输入端测两板负载步骤回报“稳定5.176”，记人工直流读数约5.176V。未补造独立5秒／30秒两值、灯／重启现象或电机动态合格。下一步先确认OFF／XT30断开及运行现象，再读电池供电时新编号日志；恢复USB后的额外启动须与本次日志分开，不能只拿最新USB日志当电池供电证明。详细测量和资料推断边界见[record](../../testing/2026-11-12_field_resume/record.md)及[power_input_basis](../../testing/2026-11-12_field_resume/power_input_basis.md)。

**最新供电读数**：主控按STM32单板负载步骤回报输入端5.182V、无异常；电机插头隔离／UART T/R断开、K230不供电、DAP及USB断开、不按KEY的测量上下文已保存至[本轮记录](../../testing/2026-11-12_field_resume/record.md)。只作为单板人工读数，不作K230容差、两板带载、纹波／电机动态或整车通过。测量后已指导驱动OFF／断XT30；后续需核对K230供电路径依据再进入其负载和两板冷启动。

**最新现场接续**：STM32冷启动后的三张图已保存，见[主板核对](../../testing/2026-11-12_field_resume/runtime_usb_cold_boot_01/stm32_review.json)：state6／TRANSPORT10、UART总2且frame2、其余0、首末843465／843467ms、当前两PWM0。本次跨板冷启动零故障不通过，K230自动入口已运行仍单独成立；不重做拔源试验、不放宽锁定。原件保存后进入车载供电分级验证。

主控明确仍采用驱动板5V／GND经杜邦线供两板，并确认有完好万用表。已确认全断电（驱动OFF、XT30断开、DAP／K230电脑USB拔开、两板无供电）；主控询问关闭Debug，已指导Keil退出Debug并保留工程，不重编译／下载。**当前尚未接驱动5V或做负载测量**。下一步在全断电下标记隔离电机六芯插头与未供电K230的UART T/R，再先做STM32单板负载测量；两板同时带载／相机电源及车载冷启动、地面与整圈各自待验，不将旧5.20V空载当合格。

**最新冷启动结果**：主控确认K230物理USB重启后，已只读取回新run_0002.jsonl，131条算法日志样本／最高index1280、128条有效PATH样本，算法43..71ms、周期68..120ms；main哈希与部署一致，本会话无runScript／写入，支持USB配置下持续入口上电自动运行。取证连接明确触发Exception: IDE interrupt，中断运行并产生日志failed；助手初判退出1源于仅识别KeyboardInterrupt，已保留原始失败并用本次终端时序／类型作10项离线复核，新结论见[review.json](../../testing/2026-11-12_field_resume/runtime_usb_cold_boot_01/review.json)。不称600秒连续运行／自然完成，也不代替STM32冷启动通信／车载供电验收。无需重做本次物理重启。

当前只需主控在动力隔离、不按KEY、不先Reset下读取STM32 state/reason、UART及PWM，并说明现场完好万用表、可调5V或车载USB充电宝是否可用。后端已关闭；未开始改车载供电线。实际下一步根据主板故障原件和现有器材安排，不把5.20V空载读数当已通过。

**本轮新增明确授权与部署**：主控先对具体R6持续候选回复“同意”，随后明确“可以自动修改”。在本I-02范围内，后续必要main.py调整可自动先备份、修改、逐字节回读，无需再逐次询问；此前“不得自动改main／每次须另获候选写入授权”的限制被本条替代。人工接线、KEY、Keil下载、不自动START／烧录、不上传／跨聊天等其余边界保持。

持续R6 main.py已实际写入35638字节并完整回读一致，SHA256 `397d6a7d91983bffe7655704e727e458ca35f2b0910982dcdf53ad72e8aa5db1`，boot.py仍不存在、写后running=false，旧10秒入口真实备份保留，见[部署结果](../../testing/2026-11-12_field_resume/runtime_deploy_01/result.json)。因此下方“板上main仍10秒自检”是部署前历史事实，当前已为持续相机候选；输入窗口600000ms、真实有效PATH／日志，不发START，主板09每次仍3000ms。尚未验证物理冷启动及车载电源／地面／整圈。

已安排主控仅对K230电脑USB拔开约5秒接回、等至少30秒，保持驱动OFF／XT30断开／DAP供STM32 Run、不按KEY。反馈后只读新编号日志，不runScript冒充上电运行；本步骤尚待实际反馈。30秒禁止驱动RAM日志实跑已正常结束，算法37..58ms、周期58..98ms；与持续有效PATH／600秒窗口、冷启动各自区分。

主控已重新摆好并进入Keil Run，明确主板复位、重新编译／下载、相机安装及DAP／USB供电保持、驱动OFF。分支／HEAD实查与原记录一致，全部原有成果保留；本轮证据见[2026-11-12记录](../../testing/2026-11-12_field_resume/record.md)。上次R6未回报试验的旧RAM快照已无法取回，不推定已做或通过。当前原图确认09版本、初始校准态、输出与故障0；3000ms／phase0／error0／UART0及完全悬空获主控确认。

本轮首次安排左轮校准后，主控纠正忘开驱动ON；已保存该次未通过及实际停因未取得的边界。主控明确重来后依次确认驱动OFF下Reset CPU→Run零基线、驱动ON仍静止、左500ms前进、右500ms前进，以及phase2/error0/state1/UART0/3000ms。没有重做全套固定输入台架或五姿态。

**R6真实相机悬空三秒本轮已通过一次人工初验**：[快照与反馈](../../testing/2026-11-12_field_resume/runtime_r6_suspended_01/stm32_review.json)valid1、3000ms、LIMIT11、目标40／40RPM、末次40.739109／39.5514641RPM、撤驱动前PWM各19.6%，主控反馈符合；当前PWM0／UART0按操作上下文人工确认。原120秒窗口已正常结束。此为实时相机，非fixture；不外推大幅差速、连续误差统计、地面或一圈。

主控已明确确认驱动OFF、XT30断开、DAP／USB继续供两板、不按KEY。持续草稿[27项日志／封包／失败边界模型](../../testing/2026-11-12_field_resume/runtime_entry_checks_01/checks.json)通过，模型相机替身不当实板性能。本轮无专用CanMV连接器，使用官方0.9.10后端受限助手；端口重新枚举K230 COM10／DAPLink COM9。正在顺序执行runtime_log_probe_01：只读备份当前main／boot，然后从固定白名单草稿生成30秒ALLOW_DRIVE=False写盘实跑，读回新日志并核对main字节未变；具体结果待完成，不提前记通过。该工具无main写入或任意远端路径能力。

下一阶段仍为持续入口实板／写盘证据、当前入口真实备份及具体部署／回读方案，获明确候选写入授权后才替换main；车载两板带载及冷启动、短直道／单弯／锐角、顺时针完整一圈各自待验。不自动START／烧录／上传／跨聊天，不改00全局汇总。

## 2026-11-11最新接续（优先于下方历史“待验”描述）

### 主控本轮暂停位置（最新，恢复先读本段）

主控明确“先暂停一会继续”，已停止工作并保存现场。最新已取得：**R5真实相机→UART→轮速控制的一次悬空3000ms正常LIMIT及自动停稳证据**，主控原图／反馈见[visual_link_suspended_01](../../testing/2026-11-11_field_live/visual_link_suspended_01/stm32_review.json)：左右目标39.6526／40.1314RPM、末次反馈40.3884／39.9327RPM、撤驱动前PWM20.1%／19.7%，随后驱动OFF／当前PWM0／UART0获人工确认。不是固定fixture，不是地面、连续误差统计或完整一圈。已完成该轮前的两次悬空单轮校准，勿重新当作全部台架未做。

电脑复用原图定位R5误删斜线：整个组件横向包围盒过宽误判ROI上沿厚背景。R6仅将该判据改成ROI上沿这一行实际黑格宽度，保留原支持／白走廊／双帧／协议时限。独立R6哈希 `de2341cafcdadf2d843a566dafeef28ae4439c041aec15f7ee709e7afd738fcf`；[42项回归](../../testing/2026-11-11_field_live/runtime_r6_checks_01/checks.json)、[37项旧偏航原图回归](../../testing/2026-11-11_field_live/runtime_r6_yaw_checks_01/checks.json)和[65项入口检查](../../testing/2026-11-11_field_live/visual_link_checks_04/checks.json)通过，原R5未覆盖。R6已有[10秒板上禁止驱动实跑](../../testing/2026-11-11_field_live/runtime_r6_board_no_drive_01/summary.json)及1张新预览，正常完成，算法日志样本43..72ms，发送始终禁止驱动；不是地面或有效动力验收。

主控随后已确认R6悬空试验前驱动ON／两轮完全悬空／phase2／error0／state1／UART0／PWM0／run_ms3000。本对话启动[runtime_r6_suspended_01](../../testing/2026-11-11_field_live/runtime_r6_suspended_01/pause.json)，收到有效实时双边后指导**仅一次人工KEY三秒试验**；主控尚未回报是否已按键／运行结果即要求暂停。因此这轮动力结果保持未知，不能重复启动覆盖尚未取回的g_lap_last。收到暂停后立即中断本对话自己的相机脚本、确认running=false并显式断开连接器；日志已保存，主动中断不当十分钟持续运行通过。已指导驱动OFF／拔XT30／保持稳固悬空，**尚无物理断开完成反馈**。连接器断开可能产生已知UART瞬态，当前state／phase／错误须恢复时实读，不假定过去phase仍可用。

恢复的一个下一步：先简短核对动力隔离、相机安装未变，并询问主控暂停前是否执行这一次R6 KEY；若执行，先保存g_lap_last／UART和实际表现，不先复位或重跑。若没执行，明确记录后按当前实读状态准备R6受限悬空，不重做五姿态／探针／全套固定台架。主控人工接线、KEY及Keil下载；无START、自动烧录、Git上传或跨聊天授权。

暂停前已生成[持续相机main草稿及待验证说明](../../testing/2026-11-11_field_live/runtime_r6_cold_boot_candidate/README.md)，SHA256 `397d6a7d91983bffe7655704e727e458ca35f2b0910982dcdf53ad72e8aa5db1`。只有本地生成／语法检查，新增日志包装模型／实板RAM／刷盘周期尚未验，未部署；**板上main仍原10秒禁止驱动自检**。持续入口具体备份、部署与回读方案尚待形成和获明确写入授权，不静默覆盖。车载5V5.20仍仅旧空载读数，两板带载／冷启动未验；地面短线／单弯／锐角／连续顺时针一圈均未验，I-02仍进行中，当前按主控意愿暂停，不改00全局状态。详细证据与角色／来源见[现场记录最新节](../../testing/2026-11-11_field_live/record.md)。

### 本轮继续执行更新（真实相机有效接收已取得人工初验）

整车联调执行对话按主控新指令继续，非00。已实查分支／HEAD一致、保留共享修改，无清理／切分支／上传。主控澄清只移动了整车，现已放回赛道中间，相机在车上的安装未变。复用五姿态15张、R5原42项，不重新采集或重做全台架；[电脑方向复核](../../testing/2026-11-11_field_live/direction_review_01/review.md)保存原件哈希、软件方向与预期轮速。另两张旧偏航图各50次合成时刻输入仍unknown，见[yaw_search_review_01](../../testing/2026-11-11_field_live/yaw_search_review_01/review.json)，此为具体候选识别限制，不能将R1五姿态有效外推R5，也不能当真实动态失败。

显式新增prepare_lap_visual_link.py及助手live_link_isolated／live_link_suspended：冻结R5哈希、真实snapshot、无START，许可前验证动力隔离或当前悬空／09／3000ms／校准；默认no_drive。新[55项检查](../../testing/2026-11-11_field_live/visual_link_checks_03/checks.json)与[助手30项回归](../../testing/2026-11-11_field_live/helper_regression_01/checks.json)通过；前两次检查器自身失败保留原目录，未用软件结果充实物通过。

本轮发现专用CanMV连接器可用，实跑使用该连接器；已重新枚举K230 COM10、DAPLink COM9。主控按动力隔离条件恢复Keil LowSpeedLap Reset CPU→Run后提供[零基线图](../../testing/2026-11-11_field_live/visual_link_isolated_01/baseline_watch.png)，revision09／fault0／state0／reason0／输出0，其余3000ms／phase0／error0／UART0按“其他符合预期”确认。继而在动力隔离下实跑120秒真实相机有效路径，源码SHA256 `664428762ea755b3937defdb348aae74cbd8e3825129de4391ad1e686b4dccb1`，正常DONE且running=false。日志167条样本／最高index1630，163条有效样本，后段steering／bend由+43／343转0／0；算法27..59ms、日志周期46..87ms，不是全帧统计。主控回报0／0，并对接收递增／许可／UART0／两PWM0回复“符合预期”，按[人工初验及边界](../../testing/2026-11-11_field_live/visual_link_isolated_01/stm32_review.json)记录，不补造精确received总数或读数时刻。

**当前下一步**：真实相机有效接收已按人工反馈初验；K230该RAM脚本结束，专用连接器保持会话、不并开原助手。主控只被指导在驱动OFF／XT30断开下支稳底盘、确认两轮完全悬空，尚未收到该动作反馈。当前校准为复位后phase0，须在悬空和供电确认后恢复两次500ms单轮校准，再运行受限真实相机悬空入口并人工KEY验证，不能把旧校准沿用。车载两板带载／冷启动／持续main候选与部署、地面直道／单弯／一圈仍未验。详细流水在[现场记录](../../testing/2026-11-11_field_live/record.md)。下方旧“助手无真实视觉模式”等描述是本轮扩展前事实，以此更新为准；板上main.py未变、STM32固件未改。

主控明确要求把当前任务交给下一对话继续，生成完整Prompt；仅文件交接，不自动发跨聊天消息。本任务仍由整车联调执行对话承接，不接替00。最后核对目录D:\projects\projectsyeye，分支codex/current-version-20261025，完整HEAD为a0733a8685db4c2b497539303bfe87fe1c1ebfe5；有大量已有已跟踪修改、未跟踪源码和证据，未提交／未上传，须先实查并保留，不清理、回退、切分支或覆盖。

### 已完成及直接证据

- [11-11新电池台架记录](../../testing/2026-11-11_battery_bench/record.md)：新2S电池自身8.38V人工读数；USB／DAP逻辑供电下，40／40RPM直行三次、60／20与20／60RPM差速各一次均正常3000ms LIMIT、UART0，KEY提前撤驱动通过一次。末帧速度吻合不等于连续500ms稳定。
- 同记录motor_link_loss_01：K230物理掉电后两轮停稳，TRANSPORT10，UART frame2，其余错误0，当前PWM0。是传输故障撤驱动通过，不是纯200ms断流超时；保留该区别，不重复拔源测试。
- [最终安装V-03五姿态](V-03.md)：居中、左右平移、左右偏航15张已齐；[R5实际包42项检查](../../testing/2026-11-09_low_speed_lap/runtime_r5_checks/checks.json)及旧R4/L1检查已复用真实样本核对方向。主控指出重复后，本对话已撤回重新左移5cm的指令。不得再从头采整套姿态或把已完成项目改回未做；明确新疑点后只补最少测试。
- [11-11现场实时记录](../../testing/2026-11-11_field_live/record.md)与[首轮汇总](../../testing/2026-11-11_field_live/straight_center_01/summary.json)：最终场地直道，XT30断开，10秒live_no_drive正常完成，5张原始预览JPEG。17条打印样本中13条有效候选steering+43，processing43..57ms、相邻周期65..88ms，所有打印样本wire_valid／drive_allowed=false。日志为全部无效帧及每10个有效帧抽样，非全帧统计；IDE预览帧号不等于算法帧号。候选有效不等于实际纠偏或准许行车。
- 主机助手新增受限预览取证；[8项传输检查](../../testing/2026-11-11_battery_bench/preview_transport_checks_01/checks.json)、[30项助手回归](../../testing/2026-11-11_battery_bench/helper_preview_lifecycle_checks_01/checks.json)通过。未修改STM32固件、未重新烧录或写板上main.py。

### 当前设备与版本

最后人工确认已到最终场地、相机位置不变、电机动力XT30物理断开、驱动OFF；STM32由DAPLink供电，K230由电脑USB供电。没有新的电机动作，最近现场诊断已正常结束，助手会话已关闭；Keil主板当前state／phase／错误尚未在该轮后回读，不假定仍有可用校准。跨对话只核对位置／供电／悬空等可能变化的事实，不重问既定目标。

最后枚举K230 COM10、DAPLink COM9，端口可能变化。优先发现专用连接器；若无，沿用vision/tools/canmv_lap_bench.py调用已安装CanMV官方0.9.10后端。该助手现仅status／sd_replay／uart_probe／live_no_drive及固定输入motor模式；没有真实视觉有效许可模式，不把fixture冒充视觉，不绕过硬编码门槛临时运行任意脚本。必要扩展应显式新增受限模式、默认禁止驱动，保存源码／哈希、模型检查、输入种类和物理前提；同一串口单一所有者，不自动打断别的脚本。

STM32 Keil工程control/MDK-ARM/low_speed_lap.uvprojx：最后确认LowSpeedLap revision0x02110009、3000ms，基速40RPM、轮目标0..60、min_feedforward200、PWM最高50%；LowSpeedLapTrack revision0x0211000A默认300000ms仅是已构建候选，尚未现场放行。正常LIMIT可保留校准重复人工启动；故障先保存证据，再K230稳定供电后主控Keil Reset CPU→Run并按需悬空两次单轮校准。KEY即PA0/WKUP，非RST。g_lap_last是停车前真实RUN快照，当前PWM与RPM可能已经归零，勿混读。

K230当前RAM候选冻结包testing/2026-11-09_low_speed_lap/board_bundle_runtime_r5/low_speed_lap_canmv.py，默认idle／UART关闭／ALLOW_DRIVE=False；R5较R4仅清理STOP后增加10ms发送余量。板上/sdcard/main.py仍是11-10部署的10秒禁止驱动自检，SHA256 c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269，非持续循迹程序；旧main备份testing/2026-11-10_pre_field/startup_backup/main.py。不得把通电自检完成当持续行驶就绪，不静默覆盖main.py。

当前T/R/G UART三线保持，K230丝印2：T GPIO11→STM32 PA3，R GPIO12←PA2，G共地，V不接。新电池8.38V仅静态；[另一轮电源记录](../../testing/2026-11-11_field/record.md)驱动标5V/GND空载5.20V，最后只安排STM32单板负载检查，无完成反馈。该计划不覆盖本对话最后人工确认的USB供电状态。两板车载逻辑供电、带载电压和冷启动均未验；驱动蓝色Vout是电池原压，不是5V。切换全断电，不让DAP5V／K230 USB与驱动5V输出并供；不得自行认定5.20V已符合K230容差。旧约5V的2S电池及过热UC2停用，勿重新安排使用或充电。

### 下一对话执行顺序和验收

1. 先读取本节、AGENTS.md、默认grill-me技能、协作标准／状态页／任务README，以及control/README.md、docs/architecture.md、control/docs/low_speed_lap.md、协议、对应视觉源码与上述最新证据。比赛依据competition/比赛文档.md第三部分、赛道图和评分表，冲突查PDF。顺时针自主一圈≤5分钟，触边扣分／完全出界失败；收益对应基本功能60分的可靠完赛和少触边，不编造官方扣分或预测分数。
2. 第一个实际工作在电脑完成：核对R5已完成的42项检查及原图／源码，结合新现场图解释输出方向、控制映射和具体剩余缺口；复用现成有效证据，不为交接重跑全部模型／ARM构建。旧y120图像偏差与当前steering量纲不同，不能直接相减当偏置；不得只因居中标签而强行调零+43。确认具体新问题才做最少补测。
3. 准备受限的真实相机有效路径验证入口，先电机动力物理隔离，核对主板接收、路径有效／符号、UART0和零输出；再主控确认两轮完全悬空、主板3000ms上限、版本／校准／供电正确后，人工KEY验证一次真实视觉→UART→差速／停车。发送端日志不替代接收端或轮子证据；固定fixture严禁落地。默认门槛、时限、无反馈／过速／反向／路径／通信／KEY保护保留，不自动发START。
4. 车载逻辑供电与冷启动另行留证，与上述静态/悬空验证按依赖顺序推进。接线用实物丝印，供电资料不足先查官方板卡资料，不再问已经明确的型号。持续运行／脱线入口必须先形成可审查候选并保存旧main备份，明确部署与运行步骤，不能沿用只有10秒的自检充当持续循迹。
5. 前序通过后才进入地面短直道、单弯／锐角及连续顺时针一圈。一次给一个现场动作、立即检查并归档结果，不因交接重复已完成台架。未通过时保存失败并修实际缺陷；按KEY终止、重摆或分段不能合称自主完圈。今天原目标不含冲线自动停车，语音不在本次新增范围。

本次已有授权为实现低速一圈所需本地视觉／联调工具／必要控制修改、适当模型或构建检查，以及按明确实物前提逐步指导主控操作；清晰工作持续执行，不停在计划或反复要求总授权。主控人工接电、KEY和Keil下载；不自动烧录、启动电机或发START，不自动改板上main.py，不提交／推送／更新远程PR、不发跨聊天消息。现有SPL和原六目标保留，修改主代码补中文注释；改外设先读standard_library.md。无新硬件／外部状态确认时不替主控填写通过。

详细新增结果放testing/2026-11-11_field_live/的独立目录及record.md，必要时新增日期目录；不要覆盖testing/2026-11-11_field/另一轮证据或冻结包。回写本任务最新摘要、版本／源码哈希、检查及原始日志／图、主控实物反馈、未完成和一个下一步；project_status.md仍由00汇总。完成是实车完整一圈有证据，或如实列出尚未达到的具体缺口，不能把交付软件当整车通过。

## 已确认目标与授权

主控经grilling确认：出发前3—4小时可连续投入，下午携带全部设备到最终比赛现场，争取连续顺时针低速自主一圈；今天暂不包含冲线自动停车。相机安装、电机／驱动／主板／编码器接线保持，K230与STM32尚未连接。允许新增独立试跑目标、轻量实时视觉与必要本地构建／验证，保留原工程和离线成果；没有Git上传、自动烧录、远程消息或自动启动电机授权。

依据比赛PDF第三部分、图1及评分表：基本功能60分要求顺时针自动一圈、5分钟内，触边扣分、完全出界失败；尺寸／重量／可充电电池约束不变。改进意图是提高完赛率、减少触边与出界；软件检查不折算实测得分。官方未给每次碰线扣分及用时折算公式。

## 现状、实现与验收边界

- SpeedMatch已有悬空同速初验，只有共同目标与3秒试验；HardwareBench只有通信／演示请求，未驱动电机。
- T2为电脑候选，不能直接CanMV运行；BP1只是诊断，不以取消valid保护冒充循迹。
- 新增独立LowSpeedLap目标，复用原PWM／编码器／PI／逐轮校准；统一时基、动态差速及真实撤驱动保护。原目标行为保持。
- 局部二维路线与固定y120含义不同，必须明确区分试跑消息版本，原v1布局／行为保持；新版本在唯一协议文档补记适用范围。
- 资料、主机模型、ARM构建、板上API／耗时、实体通信、悬空、单弯、连续一圈分别记录；没有证据的层次保持待验。
- 新现场原件与结果进入testing/2026-11-09_low_speed_lap/；全局摘要由00读取本文件后维护。

## UART接线依据

立创官方：https://wiki.lckfb.com/zh-hans/lushan-pi-k230/basic/uart.html （查阅2026-11-09）。K230D丝印2的GH1.25-4P：T=GPIO11/UART2_TXD→STM32 A03/PA3 RX；R=GPIO12/UART2_RXD←A02/PA2 TX；G共地；V为5V，本轮不接并绝缘。不是串口0或任意缓存IO3/4示例。连接须断电、按实物丝印核对；板上实际API／互通待验。

## 本轮执行结果（软件候选已交付，整圈未验收）

已交付[独立Keil工程](../../control/MDK-ARM/low_speed_lap.uvprojx)、[操作说明](../../control/docs/low_speed_lap.md)、[完整证据报告](../../testing/2026-11-09_low_speed_lap/review.md)及[板上独立入口](../../testing/2026-11-09_low_speed_lap/board_bundle_release/low_speed_lap_canmv.py)。三线按官方资料核实，尚未收到主控接好／连接USB的反馈。

真实编码器／PI／校准／v2／差速监督模型188项通过，视觉／协议42项检查通过，两独立ARM目标0错误0警告；原SpeedMatch全调用链110项回归通过且BIN哈希保持。L1真实时间732帧回放仍有大量无效段，不能认定可连续过弯或完圈；电脑耗时不当板上实时性能。默认idle、UART关闭及ALLOW_DRIVE=False，不把诊断改成有效路径冒充整车就绪。

板上／UART／动力／连续一圈均未验收；没有自动烧录／运行／main.py写入／上传／跨聊天或全局状态更新。下一步由主控断电接T/R/G三线、保持电机动力断开、接K230 Type-C数据口，再执行9秒无效路径UART探针，保存完整终端及Keil实际接收；此后SD／live性能与悬空、单弯、整圈顺序推进。主状态保持进行中，不将今天目标记为完成。

## 接续

### 主控反馈“都接好了”后的实板阶段

主控对两次悬空单轮校准回复“均符合预期”：左／右各约500ms、方向与自动撤驱动符合，最终phase=2、error=0、g_lap.state=1，按此前具体操作要求记为人工反馈初验；没有独立每通道数值／CPR／波形，不补造。随后明确回报run_ms=0x00000BB8（3000ms）、两轮完全悬空，允许按已确认三秒限制组织下一项人工KEY动力台架。

已准备独立motor_bench_bundle及18项入口模型检查：只在已核对悬空／3000ms条件下提供人工固定输入，明确NOT CAMERA；不发START，运行由主控KEY触发，不能当真实双边识别或地面／比赛输入。初次助手在发包前因CRLF文本归一化后的哈希误比被拦截，未运行台架；已改按原文件字节校验后重新执行motor_straight_02。实际双轮表现等待主控反馈，不以启动脚本或发包代替动力验收。

主控又确认准备悬空校准前的状态符合：g_lap.state=0、g_speed_match.phase=0、左右PWM=0。10秒实时无驱动程序已结束，后续不并行运行K230脚本，以免其启动／清理STOP中断人工校准。进入主控人工、轮子完全悬空的两次单轮500ms识别；尚未收到轮侧／方向／phase2／error0反馈，不提前记动力校准通过。当前不做第三次KEY启动、不落地、不放行有效视觉路径。

最新实体反馈：主控明确回报accepted=received=0x000000B4、steering=0xFDA8、g_lap_uart_errors=0，对应180条路径包和int16−600，基础接收／CRC解析／负值解码已有主控实值证据。初次两个计数相等，未宣称STOP已到；探针增加最终STOP后10ms发送余量，重发后主控对accepted=received+1的核对回复“符合预期”，据此确认STOP解析计数关系，不补造新的独立原始计数。运动中的真实停车仍未验。

当前板上包runtime_r5，42项实际包检查通过，7项探针入口模型覆盖180无效PATH＋STOP和deinit前发送余量。另已运行[10秒实时无驱动链路](../../testing/2026-11-09_low_speed_lap/board_live_03/terminal.txt)：165帧、算法41..47ms、中位43ms、最大启动间隔89ms，当前宿舍画面全部unknown／wire_valid=false；仅K230端运行证据，STM32该轮累计值尚无新的原始读数。下一步先核对g_lap.state=0、g_speed_match.phase=0及两PWM=0，符合后组织独立悬空校准；不自动启动电机、不将通信通过当动力／一圈通过。

主控随后提供[Keil初始Watch截图](../../testing/2026-11-09_low_speed_lap/stm32_version_watch_01.png)：g_speed_revision=0x02110001、g_speed_fault=0、g_lap_uart_errors=0，确认读到新LowSpeedLap版本及这两个零故障值；g_lap／parser尚未展开，不补造状态、时基或收包数。已在该截图之后再次运行[9秒无效UART探针](../../testing/2026-11-09_low_speed_lap/board_uart_probe_02/terminal.txt)，K230端正常完成；等待主控提供g_lap_parser.accepted、g_lap.received、g_lap.steering及UART错误实值再判互通。

随后主控按既定DAPLink五线接法重新接好并说明两个USB均换了端口；[最新端口枚举](../../testing/2026-11-09_low_speed_lap/ports_reconnected_01.json)识别DAPLink VID/PID 0D28:0204为COM9，K230 VID/PID 1209:ABD1为COM10。[K230重连状态](../../testing/2026-11-09_low_speed_lap/hardware_status_02/board.json)实际连接COM10成功、running=false。DAPLink的COM9是虚拟串口，Keil仍选CMSIS-DAP／SWD；USB枚举不代表SWD目标连通或STM32已下载新固件。此步没有代理STM32烧录或电机操作。

主控已反馈全部接好；COM10实际识别K230D v1.8-0，完成限定无动力诊断，详见[实板接续与原始终端](../../testing/2026-11-09_low_speed_lap/hardware_runtime_review.md)。修复实板array乘法异常；完整搜索实测252..782ms后改48候选及板上6像素网格，r3宿舍相机145帧算法44..54ms、全部无效输出；r4已有SD30张和实际包42项主机检查通过。上述不是赛道识别／一圈验收。

K230已运行9秒无效UART探针，未发START／有效路径；STM32新固件是否已下载Run及接收计数尚待主控答复，互通仍未验收。当前副本用board_bundle_runtime_r4，旧release保留历史。连接／断开出现系统soft reboot已归档，没有请求写main.py／采集许可、没有代理STM32烧录或电机操作。主状态继续进行中。

目录D:/projects/projectsyeye；分支codex/current-version-20261025；来源HEAD a0733a8685db4c2b497539303bfe87fe1c1ebfe5。共享修改已存在，全部保留；本轮只本地保存与检查，不切分支／复位／上传。

实验室接续：主控明确上一轮双轮悬空测试未执行，`motor_straight_02`仅记固定输入发送，动力表现仍未验收。当前USB枚举仍为DAPLink COM9、K230 COM10；等待搬运后当前悬空／Run状态、phase／state／run_ms读数，再按原3000ms人工KEY方案重测。详见[实板接续记录](../../testing/2026-11-09_low_speed_lap/hardware_runtime_review.md)。

实验室后续：主控实报phase=0、state=0、run_ms=3000且两轮悬空，逐次重做两次单轮校准并确认最终phase=2／error=0／state=1符合预期。已启动`motor_straight_03`，收到固定输入READY后明确提示人工KEY；双轮结果待反馈，不计作闭环／整圈通过。

主控后续确认`motor_straight_03`未赶上窗口，绿灯闪烁且按KEY无反应，动力测试记未执行。为留足人工操作时间，已制作120秒输入等待窗口的`motor_bench_bundle_r2`，19项入口模型检查通过；STM32单次3000ms限制及人工启动保持不变，新包尚未上板。等待当前state／reason／phase及按键方式后重测，不能仅凭灯闪断定故障。

当前新证据：主控实报state=6、reason=10、phase=2，KEY长按，确定为UART传输接收故障锁定（LAP_TRANSPORT），不再按单纯等待输入解释。暂停固定输入复测，先取g_lap_uart_errors／g_speed_fault及调试运行事实；现有驱动未细分硬件接收错误与环满，具体根因待核实，保持故障保护。

主控确认全程Run、UART errors=3、g_speed_fault=0。已添加UART分项／首末原因与时间诊断，版本03（3秒）／04（Track），不改变遇错锁定。两个ARM目标0错误0警告，188项原控制模型断言通过；真实USART诊断待上板。下一步先断电机动力，用Keil下载LowSpeedLap 0x02110003并Run，核对零基线后重做无效通信探针；不先校准、不发送有效固定输入。详细哈希、字段及证据边界见模块文档与实板接续记录。

主控已确认诊断版03零基线及断电机动力符合。先执行uart_diag_status_01仅连接／读空闲／断开，无runScript或UART测试包；正常完成，日志有两次soft reboot。等待STM32回读，尚未进行后续无效包探针或动力测试。

status隔离步骤后主控回报错误计数／诊断／state／reason均零；仅连接／断开这轮未复现。随后uart_diag_probe_01完成180个无效路径＋STOP，K230正常退出；STM32收包数及错误分项待反馈，动力仍未测。

uart_diag_probe_01后曾收到overrun=1截图及一组手抄计数，主控随即说明读错、要求全部重来。手抄值标为待复核，不据此继续定因；保留原图／日志。重新从断电机动力、诊断版03复位Run后的零基线逐步验证，固件不再新增改动，双轮仍未验收。

重新验证：主控确认诊断版03复位Run后的phase／state／UART计数与分项零基线符合，电机动力断开。uart_diag_probe_02已正常发送同一180个无效PATH＋STOP，等待本轮STM32 Watch接收与错误证据；不沿用上一轮有歧义读数，不先做动力校准。

uart_diag_probe_02：主控对Watch预期表确认符合，accepted=181／received=180，state／reason0、UART总数及所有诊断分项0。本次无动力接收通过，不声称先前故障根因已解决。进入重新两次单轮悬空校准，完成后核对phase2／error0／state1与3000ms再做双轮；动力和一圈仍未验收。

主控确认重新两次校准及phase2／error0／state1／run_ms3000均符合。motor_straight_04已启动120秒固定输入窗口并收到READY，随后立即提示主控单次KEY；双轮实际结果待反馈，不预先计通过。

motor_straight_04实证：主控截图确认LAP_TRANSPORT锁定、run_since=0，UART errors=overrun=12，其余错误分项0；校准器停止时刻与首次UART错误一致。未进入双轮RUN。K230正常发送2317个固定PATH，但不能记作STM32完整接收或动力通过。

已制作05（3秒）／06（Track）候选：UART抢占SysTick、BASEPRI提交运动状态、DWT计时，保留1ms监督／20ms采样／115200／故障锁定／运行时限。两个ARM目标0错误0警告，原188断言及新增生产UART ISR桩检查通过。原代码阻塞路径是修正依据，具体旧耗时尚无实测，不宣称根因完全解决。下一步主控先断电机动力、Keil下载0x02110005并Run，再无动力复测及读取时间余量；详细原始截图、哈希、边界见实板接续记录及irq_fix_build_01.json。

主控确认05版零基线与counter_ready1符合，电机动力断开。uart_diag_probe_03已完成180个无效PATH＋STOP，等待STM32接收／错误及新增周期统计；未恢复动力，修正有效性仍待本轮实板数据。

05版uart_diag_probe_03实板短接收通过：主控确认accepted181／received180、state／reason0／UART错误0，截图五类错误全0、16MHz计时有效。UART ISR最大12.125us、SysTick79.4375us、状态提交52.125us，当前校准前有执行余量；原图与stm32_review.json已归档。不外推为校准后／RUN或长期接收通过，下一步重新悬空单轮校准及双轮三秒验证。

后续校准时主控回报忘开驱动板电源，长按后灯闪。此轮校准不记通过，具体故障码未读，不将其视为UART修正失效。按无动力校准可能锁定的既定策略，指导驱动OFF／悬空／Reset CPU→Run、重新开驱动后逐次校准；固件05不改，无需重烧。此前通信与计时通过证据保留，双轮仍未测。

校准恢复后主控提供原始截图：phase2／error0，g_lap WAIT1／OK0，UART错误0，run_ms3000；反馈通道1／2、符号+1／−1。已启动motor_straight_05的120秒固定输入，收到READY后立即提示主控单次KEY。实际双轮结果待反馈，校准后／RUN通信和计时仍需留证，不提前计动力通过。

motor_straight_05实证：已进入RUN，主控听见电机声音但未转，截图reason=7（NO_FEEDBACK）、UART错误0，未达三秒正常动力验收。40RPM原初始输出约28%而单轮50%校准已通过；起转不足为候选解释，实际阈值／电流／供电未测，不认定唯一根因。

已制作07（3秒）／08（Track）候选：每轮0→正目标且无增量时50%最多100ms补偿，首个增量即退出，零目标不补偿、正目标堵转不重触发，300ms无反馈与其他保护保持。新增g_lap_last停止快照。237控制断言及UART桩检查通过，两ARM目标0错误0警告，尚未烧录／实测；下一步主控断动力用Keil下载07，零基线后重新悬空校准与单次KEY验证。截图、解释边界与哈希在实板接续及startup_fix_build_01.json。

主控已确认07下载后的零基线／3000ms，以及重新两次单轮前进、phase2／error0／state1／UART错误0符合。motor_straight_06已收到120秒固定输入READY，随后立即提示人工单次KEY；起步补偿与三秒运行实物结果待反馈。

motor_straight_06首次悬空直行通过：g_lap_last原图valid1／3000ms／LIMIT，目标40／40、末次反馈41.6508／40.4017RPM，撤驱动前PWM22.6%／22.1%，补偿各1个20ms样本；主控明确确认两轮向前并停稳、UART errors0。只记一次悬空起步与三秒撤驱动，不记连续500ms同速／地面／真实视觉／一圈。K230120秒2317个PATH正常结束，当前校准可保留。RUN周期峰值待补。

后续正负差速入口已准备为motor_right／motor_left白名单（+500→60/20，−500→20/60目标），未实板运行；18项真实助手入口FakeSession检查通过，保留悬空／3000ms、哈希、人工KEY及无自动START限制。下一步取得RUN计时，再分别悬空验证正负差速与失效撤驱动。

直行RUN计时原图已补：16MHz有效，SysTick最大205.5us、状态提交44.75us、UART ISR12.1875us，五类接收错误全0，当前观测有余量。已在保留校准／供电和悬空条件下启动motor_right_01（+500、左60右20目标），120秒READY后提示人工单次KEY；右差速实物结果待反馈。

motor_right_01失败已留原图：460ms因NO_FEEDBACK停止，目标60／20、末次74.5326／0.0726RPM、PWM27.6%／16.9%、补偿各1样本，UART错误0；主控回报内轮动力不足。不能计右差速或3秒通过，07直行证据保留。

已制作09（3秒）／0A（Track）候选，增加启动锁定的min_feedforward默认200（允许0..300），正目标前馈至少20%但PI实际输出仍可为0，零目标绝不驱动；40／60RPM参考及其他保护保持。316控制断言及UART桩检查通过、两个ARM目标0错误0警告，09尚未烧录／实测。下一步主控断动力下载09，核对min_feedforward200／run_ms3000，重新悬空校准后先复测右差速；原图／候选解释／模型边界与哈希见实板接续及low_speed_feedforward_build_01.json。

主控已确认09下载零基线／min_feedforward200与3000ms，重新两次单轮前进及phase2／error0／state1／UART错误0均符合。motor_right_02已收到120秒右差速输入READY，立即交回人工单次KEY，目标60／20；实物复测结果待反馈。

09版motor_right_02右差速悬空三秒通过：原图valid1／3000ms／LIMIT、60/20目标、60.8911/19.6733RPM，PWM27.2%/20.4%、补偿各1样本；主控确认转动符合预期、UART错误0。K230正常结束后保留供电／校准，motor_left_01（−500，左20右60）已READY并提示人工单次KEY；左差速结果待反馈。单次末采样匹配不记连续同速／地面／一圈验收。

09版motor_left_01悬空三秒通过：原图20/60目标、16.9268/59.5401RPM、3000ms LIMIT、PWM21.7%/26.8%、补偿各1样本；主控确认符合预期且UART错误0。SysTick峰值192.5us／提交43.5625us，原图已归档，仍只为单次悬空与末帧反馈。左右差速均已通过一次。下一项准备断源撤驱动：主控手动启动直行约1秒后拔K230 USB，保留DAP主板供电，并按真实LINK或传输故障原因记录，不提前记保护实物通过。

motor_link_loss_01直行输入已READY，已保存人为K230 USB断源意图与验收边界，随后提示主控单次KEY及运行约1秒后断源；当前结果待反馈。

主控询问断源含义，已澄清仅K230断电，主板DAP和电机供电保持。第01轮已正常结束且无断源实物结果，不记保护通过；重新启动motor_link_loss_02并收到READY，立即交回人工KEY／约1秒后拔K230 USB操作，待真实停因与时间证据。

motor_link_loss_02断源未执行：主控明确尚未拔USB，左轮没起转、右轮短动即停；原图312ms NO_FEEDBACK，左补偿满5样本／右1样本，末次请求32.8%/23.6%。K230正常完整结束，未再开输入。已指导驱动OFF，09固件未继续改，先取当前2S供电／电压与单轮重复性证据；20点后场地可用性亦待主控答复。此前成功记录保留，但可靠起转及断源实物保护仍未验收，不放行地面／一圈。

新供电读数：主控确认2S动力源并报4.95V，最终比赛现场随时可到。准确测点（电池XT30还是5V轨）与替代电池条件待回复。已指导驱动OFF／拔XT30／暂不充电，按Tattu厂家低压条款分支核实，不能用当前未明确电压继续调参或建议复活充电。09程序保持、无新动力操作；当前源若不合格，仍可去现场做动力隔离的真实视觉验证。处理与来源见hardware_preparation/low_speed_power_check.md，全球状态由00后续读文件更新。

测点已确认是电池XT30，主控表述“5V多”、无备用电池。停止动力与充电建议保持；首次4.95V与后续近似值分别保留，未取得单节／厂家检测，不写已永久损坏。主控准备充电的设备明确为原过热停用UC2，已说明继续停用；若已接，先断UC2输入电源再断电池。实际充电是否开始待答复，无代理充电操作。可继续的授权工作是动力隔离的现场视觉验证与准备合格动力源，非地面试车放行。

## 2026-11-10：宿舍推进与11-11场地接续

主控确认新电池安装成功、OLED正常、驱动板供电正常，今晚在宿舍、明日到实际场地，要求继续完成出发前工作。随后明确可以两板连接、稳定悬空并人工操作KEY；新电池已充满、额定7.4V但端电压未测。恢复悬空工作条件，电气实测与新电池下动力结果各自留证，旧电池4.95V不套用于新电池。

已读取比赛第三部分、赛道图与评分表，更新[电池](../../hardware_preparation/battery_record.md)／[部署清单](../../hardware_preparation/deployed_hardware.md)，准备[宿舍及场地操作单](../../hardware_preparation/pre_field_checklist.md)、[本轮记录与原始检查](../../testing/2026-11-10_pre_field/record.md)、空白动力／场地结果表。重新检查控制316断言及生产UART桩、台架入口19项、助手FakeSession18项、runtime_r5视觉／协议42项通过；两个ARM目标0错误0警告且BIN与此前09／0A一致。保存候选固件／脚本与字节哈希，未改运动算法／参数。

只读枚举当时见DAPLink COM9、无K230；当前板上最后确认OledBench。下一步主控驱动OFF／动力隔离、接K230数据口，用Keil恢复LowSpeedLap09并Run，核对3000ms／前馈200／故障0／UART错误0／phase0／state0／PWM0，再无动力收包。新电池端电压补录后按悬空校准、重复直行、差速、KEY及断源停车顺序推进。两板车载逻辑供电／脱机冷启动尚待确认，真实场地视觉、地面与一圈均待验。

本轮只完成本地资料／软件准备，未下载、运行K230脚本或启动电机，未提交／上传／跨聊天消息／更新00全局摘要；主状态继续进行中。目标支撑基本60分可靠完赛、少触边与报告20分证据，不估造得分。

随后主控对恢复LowSpeedLap09及零基线预期表明确回复“一切符合预期”，按人工反馈记版本09／3000ms／前馈200／phase0／state0／PWM0／硬件及UART错误0符合，不补造独立下载读回。K230重新枚举为COM10，已在动力隔离条件下执行本轮[9秒无效UART探针](../../testing/2026-11-10_pre_field/uart_probe_01/terminal.txt)，真实K230 v1.8-0空闲后运行、正常DONE退出，仅无效PATH＋STOP，无START或main.py写入。STM32本轮accepted／received／steering／UART分项／状态读数等待主控反馈；新电池端电压仍未测，尚未启动电机。详细条件与证据保存在[本轮记录](../../testing/2026-11-10_pre_field/record.md)，通信尚不提前记通过。

主控随后提供[STM32原图](../../testing/2026-11-10_pre_field/uart_probe_01/stm32_watch.png)并反馈“其他的都正常”：截图直接确认received180、steering−600、state／reason0、path_valid0、左右目标／RPM／PWM0；accepted181及UART总数／五类错误0为同轮其余预期值的主控确认，未独立展示原图。结合K230终端，本轮无动力UART／STOP计数关系验收通过，[结构化结果](../../testing/2026-11-10_pre_field/uart_probe_01/stm32_review.json)区分图证与人工反馈。下一步补测新电池自身输出端电压，再进入稳定悬空、人工KEY两次500ms单轮校准；本轮尚未提供新电池端电压或动力结果，不提前发送有效台架输入。

主控说明万用表已损坏，端电压因工具条件待测；新电池动力复测延后，今晚继续动力隔离的实时链路。已执行[10秒live_no_drive](../../testing/2026-11-10_pre_field/live_no_drive_01/terminal.txt)，K230 v1.8-0正常完成156帧，算法41..56ms／中位46ms，最大启动间隔101ms，全部unknown／wire_valid=false／驱动禁止。没有main.py写入、START或电机操作；[统计与接收预期](../../testing/2026-11-10_pre_field/live_no_drive_01/summary.json)已归档。STM32若未复位预期accepted339／received336，实际值待主控反馈；两板车载供电器材与接法已询问，尚不推定已具备脱机运行。明日借完好仪表补电气证据，真实场地／动力／一圈仍未验。

随后主控对339／336计数及状态／输出／UART错误零值预期表回复“符合预期”，按人工反馈验收本轮真实相机／UART无动力链路；[接收确认](../../testing/2026-11-10_pre_field/live_no_drive_01/stm32_review.json)区分概括反馈与独立原图／SWD证据。至此09零基线、无效UART探针／STOP计数关系、10秒实时无驱动链路已完成。下一步核对两块计算板车载供电器材／接法与脱机启动入口；既有K230采集main.py保持，RAM诊断正常不代表上电自动循迹。万用表损坏、电压待测及新电池动力／断源／地面一圈未验边界保持，无新硬件动作或上传。

主控确认当前DAPLink供STM32、电脑Type-C供K230，并明确车载切换采用驱动板稳压5V/GND经杜邦线分别接两板5V/GND，不用USB-A转接板；[实际路径与进入条件](../../hardware_preparation/onboard_power.md)已回填。已只读备份真实main.py（11636字节，SHA256 `9ac4d097f5000ec323f255981756ada9c5c5020516651f8321f40151799222e2`），当时boot.py和两项已知采集许可不存在。准备[10秒无驱动启动候选](../../testing/2026-11-10_pre_field/cold_boot_candidate/main.py)，16项启动／日志模型与42项原视觉协议检查通过，原USB供电下RAM实跑144帧／落盘读回完成，见[实板结果](../../testing/2026-11-10_pre_field/cold_boot_ram_01/result.json)。候选不发START／有效PATH，不自动续跑；**尚未替换main.py／切换电源／物理冷启动或启动电机**。下一步主控明确同意切换10秒无驱动启动入口后才写入并回读；电池供电测量、真正冷启动与动力复测仍各自待验，不把RAM执行作为脱机验收。详细原始证据留本轮record，未上传或改00摘要。

2026-11-10新增明确授权：主控对“是否允许把K230的main.py切换为已备份、已检查的10秒无驱动自检”回复“确认”。本次允许在当前USB逻辑供电／动力隔离条件下替换`/sdcard/main.py`并回读校验，候选SHA256限定`c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269`；保留真实旧入口备份、boot.py及采集许可，不授权有效运动、START或自动改接供电。此次授权补充前述main.py保持边界，仅适用于该10秒禁止驱动自检。执行结果另附后续证据，不以授权当部署成功。

该授权已执行：[部署结果](../../testing/2026-11-10_pre_field/boot_deploy_01/result.json)确认板上main.py写入34887字节且回读逐字节一致、SHA256与指定候选相同。写前再次核对旧入口与真实备份一致，boot.py及两项已知采集许可写前后均不存在，原备份／采图保持。最后查询running=false，未runScript、未启动电机或改接电源。下一步主控保持动力隔离／DAPLink供STM32且Run，只对K230原电脑Type-C执行拔开约5秒再接回、等待至少30秒，不按KEY；然后只读核对新编号启动日志。真正冷启动、电池供电及动力／一圈仍未验，不能用先前RAM日志替代。完整证据在本轮record，未上传或改00摘要。

主控随后回复“已重启”，按前述具体操作记USB物理断电重接已执行。只读下载新[check_0002启动日志](../../testing/2026-11-10_pre_field/cold_boot_power_01/check_0002.jsonl)，143帧、完整completed、始终禁止驱动；旧RAM日志字节未变、main.py哈希不变，本次接收会话未runScript／写文件且连接输出没有BOOT CHECK LOG标记。[证据结果](../../testing/2026-11-10_pre_field/cold_boot_power_01/result.json)支持原USB供电下K230自启动一轮通过；算法46..57ms、最大帧间隔168ms，不代表赛道能力。下一步最后核对STM32 state／reason／PWM及UART错误零值；未单独取得该轮接收实值，电池供电／新电池动力／断源／地面一圈仍未验。未改供电或上传，主状态保持进行中。

上述STM32核对失败：[主状态](../../testing/2026-11-10_pre_field/cold_boot_uart_fault_01/lap_fault_watch.png)与[错误总数](../../testing/2026-11-10_pre_field/cold_boot_uart_fault_01/uart_errors_watch.png)确认state6／LAP_TRANSPORT10、run_since0、received623、左右PWM0、UART总错误2。累计包数与预期吻合，但错误分项与发生时间尚未知，不能据此认定根因或整链路通过。K230自启动／本地日志通过结论保留，跨板冷启动通信未通过。已保存原件，下一步保持动力隔离／Run、不复位不按KEY，取g_lap_uart_diag五类分项与首末mask／时间及g_speed_ms后再决定复测；未改固件、清零故障或重启设备，不放宽传输错误保护。主状态继续进行中，具体证据在本轮record。

后续[诊断原图](../../testing/2026-11-10_pre_field/cold_boot_uart_fault_01/uart_diag_watch.png)确认frame2、其余四类0，首末mask4、时间1766097／1766142ms，相隔45ms；[换算与假设](../../testing/2026-11-10_pre_field/cold_boot_uart_fault_01/diag_review.json)已保存。旧path_at与K230帧间隔仅支持错误可能早于首帧约19秒的条件推断，断电／启动／初始化哪个阶段触发尚未实证。不改UART优先级或错误锁定策略。原现场已保存，下一步K230保持稳定USB供电／空闲，电机动力隔离，仅由主控Keil Reset CPU→Run建立STM32新基线，等待5秒核对state／reason／received／PWM／UART错误0与ms递增，再分阶段发包／断源／上电，不用复位清零冒充已修复。

主控对仅STM32复位后的5秒空闲零基线回复“符合”，按具体表记人工确认。保持K230物理USB供电与动力隔离后，已执行[稳定供电9秒无效UART隔离探针](../../testing/2026-11-10_pre_field/uart_isolation_probe_01/terminal.txt)，K230正常DONE／退出0，仅180无效PATH＋STOP，无START或main.py写入。后台连接／运行／断开有soft reboot，仍保留其影响边界。本轮STM32 accepted181／received180及state／reason／PWM／UART错误零值待主控回报；在取得结果前不复位、不拔K230、不改固件。原FE失败与新基线分开，未提前宣布修复。

主控随后对该轮181／180及状态／输出／UART错误零值预期表回复“符合”，按人工反馈确认稳定物理供电探针通过、frame0，见[反馈](../../testing/2026-11-10_pre_field/uart_isolation_probe_01/operator_feedback.json)。原FE未因此视为已修复。下一隔离步骤只让主控拔K230电脑Type-C约5秒、保持拔开，STM32 DAP供电／Run与动力隔离不变、不复位不按KEY；先回读错误及state／reason，有变化保存首末诊断和g_speed_ms，再决定上电阶段。助手本轮不再连接K230或发包，不改固件／main.py；拔线实际结果尚待主控回报。

只断K230物理电源阶段已收到[三张原图与核对](../../testing/2026-11-10_pre_field/uart_power_off_01/review.json)：从0错误基线变为UART总数3／frame3，其余四类0，首末523462／523474ms（12ms跨度），state6／LAP_TRANSPORT10、run_since0、received180、左右PWM0。可复现触发阶段已定位到断电过程，电气机制尚无波形／电压证据；保持传输错误锁定，不忽略FE或自动续跑，不把无RUN测试当动力中停车验收。下一步只接回K230原电脑Type-C、等至少30秒、不复位STM32／不按KEY，先观察总错误／frame是否从3增加（故障仍6／10预期保持），之后再决定恢复零基线。无代码／供电线束修改、无K230助手连接或Git上传。

重新上电阶段主控回复“仍为3；保持锁定”：UART总数／frame3、state6／reason10按人工反馈记录，本轮未新增错误、没有自动解锁。收到反馈后再只读取得新[check_0003日志](../../testing/2026-11-10_pre_field/cold_boot_power_02/check_0003.jsonl)，142帧completed／始终禁止驱动，main.py哈希不变，证实K230该轮自启动实际运行；[接收结果](../../testing/2026-11-10_pre_field/cold_boot_power_02/result.json)与[STM32反馈边界](../../testing/2026-11-10_pre_field/cold_boot_power_02/stm32_feedback.json)分开保存。下一步K230保持稳定USB供电／空闲、动力隔离，主控仅Keil Reset CPU→Run复位STM32并等5秒，取state／reason／received／PWM／UART错误0及ms递增的新空闲基线。原FE故障未视为修复，未改固件／策略／供电，不把当前10秒诊断当持续循迹。

本轮收尾：主控对恢复操作的5秒零基线预期表回复“是”，按人工反馈确认state／reason／received／左右PWM／UART总数和五类分项0、ms递增，[来源与边界](../../testing/2026-11-10_pre_field/recovery_idle_feedback.json)已归档。K230稳定后手动复位STM32的无动力空闲恢复通过一次；既有FE失败保留，没有电气修复或自动恢复声称。此后无代理板卡操作，本轮宿舍软件／无动力检查收尾，**I-02仍进行中**。明日先借仪表补电气与车载逻辑供电，再悬空新电池动力／停止、真实场地无动力视觉及基于实测的连续运行版本，前序通过后才短线／单弯／一圈；[接续清单开头](../../hardware_preparation/pre_field_checklist.md)集中当前状态。当前K230 main.py仅10秒禁止驱动诊断，STM3209仍3秒。未上传、改分支或更新00摘要。
