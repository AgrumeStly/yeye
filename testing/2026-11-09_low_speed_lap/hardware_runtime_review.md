# I-02宿舍无动力实板接续

日期2026-11-09；责任主控／本对话；主控反馈“都接好了”后，继续此前已约定的无动力诊断。主目标仍为下午争取低速自主一圈；本节不表示一圈或动力验收。

## 实际设备与执行范围

电脑枚举到COM10 USB设备；[实际连接状态](hardware_status_01/board.json)确认CanMV K230D Lushanpi Lite 128M、v1.8-0、既有固件完整版本，查询时running=false。当前工具列表没有CanMV连接工具，使用已安装CanMV扩展0.9.10自带后端，通过本机已读协议运行限定助手[canmv_lap_bench.py](../../vision/tools/canmv_lap_bench.py)。连接／断开日志出现MPY soft reboot，均保留；没有重刷固件或请求写入main.py／采集许可。

助手仅暴露status、sd_replay、live_no_drive、uart_probe四种行为；没有任意脚本入口、有效驱动许可、START、写文件／删除或Flash入口。同一COM口顺序占用，运行前查询空闲，既有脚本不自动中断；所有执行文本与哈希保存在各目录executed_source.py／run.json。

## 失败、修复与分版本结果

| 证据 | 实际版本／场景 | 结果与边界 |
| --- | --- | --- |
| [board_sd_01](board_sd_01/terminal.txt) | 最初合并包，SD已有图 | 模板建立成功；array乘整数在该MicroPython报TypeError。保留Traceback，不能称诊断通过 |
| [board_sd_02](board_sd_02/terminal.txt) | runtime_r1，修array后完整1113模板＋细搜，30张SD选片 | 全部运行结束，但算法252..782ms，中位271ms；最小剩余堆7072B，不能用于现100ms处理门槛 |
| [board_sd_03](board_sd_03/terminal.txt) | runtime_r2，4像素网格／48候选滚动粗搜，30张SD选片 | 算法54..85ms，中位70.5ms；SD解码随图片可达176ms，不能拿算法时间当相机周期；选片每图复位，全部无效许可 |
| [board_live_01](board_live_01/terminal.txt) | runtime_r2，10秒当前宿舍相机，无驱动 | 73帧，算法115..121ms，中位118ms；分阶段表明网格本身约110ms，仍超限，不能以SD较快结果冒充live通过 |
| [board_live_02](board_live_02/terminal.txt) | runtime_r3，6像素网格／48候选，10秒当前宿舍相机，无驱动 | 145帧，算法44..54ms，中位51ms；最大相邻启动间隔96ms，最小剩余堆3289824B；当前画面全部unknown，wire_valid全部false。只证明该画面运行与拒绝，不证明真实赛道识别、弯道实时或控制能力 |
| [board_sd_04](board_sd_04/terminal.txt) | runtime_r4，修正reset同时重置粗搜游标，30张SD选片 | 算法22..39ms，中位31.5ms，最小堆2924288B；全部wire_valid=false；这是当前版本的SD/API实测，不偷换成r4真实赛道live指标 |

[汇总JSON](hardware_timing_summary.json)由完整终端逐条解析；取帧、算法、两帧起点间隔分别记录。SD30张为非连续选片，每图清时序，不以合成时间提高有效数量，不拿SD解码当相机帧率。r3与r4分别归档，不把各版较好数字拼成一个“通过”结论。

修复内容：`array('H',[0]) * N`改为有界零列表构造H数组；每帧只评估48个滚动粗候选＋最多7个上一模型局部邻居，旧分数不跨帧累积。电脑4像素全量模式保留，板上合并包显式6像素，几何／正确性必须单独核验。降低网格密度会影响色块／文字与组件关联，不能只凭变快宣布净收益。

当前板上入口为[board_bundle_runtime_r4](board_bundle_runtime_r4/low_speed_lap_canmv.py)，[manifest](board_bundle_runtime_r4/manifest.json)记录源哈希和grid_step=6，包SHA256 `e9d6be398679c54980c40f92af95fa9d16d9db4c14315e792f534d2d455bf360`。默认仍idle、UART关闭、ALLOW_DRIVE=False。早先board_bundle_release是已归档的电脑候选，不应继续使用其含array乘法的旧代码上板。

[runtime_r4_checks](runtime_r4_checks/checks.json)的42项检查对实际6像素／有界搜索合并包执行：居中／左右偏移方向、真实文字与单横带拒绝、时钟／稳定门、历史期限、源年龄、短写和真实C解析交叉均通过。稳定门重复图片明确为软件合成输入，不作实测帧率或准确率。

## UART：发送端已运行，接收端仍待确认

[9秒探针完整终端](board_uart_probe_01/terminal.txt)确认K230 UART2／GPIO11/12初始化和写入调用完成，0／+600／−600无效路径各60包，末尾STOP，正常打印UART PROBE DONE。没有START，所有路径flags=0、confidence=0。发送端返回成功不是STM32收包／接线电气／电机动作的证据。

主控是否已将3秒LowSpeedLap下载并Run，当前尚未收到答复；不能假定STM32运行的是新固件。需主控在Keil确认g_speed_revision=0x02110001、g_speed_fault=0，检查g_lap_parser.accepted／g_lap.received增长、g_lap.steering符号及g_lap_uart_errors；确认后才能记实体互通。所有电机PWM仍要求为0，暂不按KEY。

当前K230诊断已经结束、串口会话关闭。没有代理烧录STM32、没有按KEY／供电切换／电机启动／有效路径放行，没有上传或全局摘要更新。

## 得分关联与接续

### 两次单轮校准完成与固定输入动力台架

主控依此前明确步骤反馈“均符合预期”：左／右单轮各约500ms、轮胎上缘朝车头、自动撤驱动，以及phase2／error0／g_lap.state1，记录为当前LowSpeedLap版本的悬空校准人工初验。没有附各次独立转速、计数、CPR或精密计时，不能外推为地面或精确同速。

主控随后明确“run_ms为0x00000BB8，两轮完全悬空”，满足三秒固定输入台架的操作前提。新增[固定输入独立包](motor_bench_bundle/lap_motor_bench_canmv.py)及[18项入口模型检查](motor_bench_checks/checks.json)，默认不开UART；straight人工输入只模拟0转向，软件目标40/40RPM，45秒窗口内只由主控KEY触发MCU单次3秒，不自动START，不改变实际相机ALLOW_DRIVE=False。这不是实时视觉输入，不声称存在当前双边，不能用于地面或正式比赛。

[motor_straight_01](motor_straight_01/backend.jsonl)在运行前被本地哈希检查拦截：原包CRLF字节哈希与read_text归一化LF后的哈希不同。没有发出固定输入。修复为校验原始read_bytes，执行文本按原UTF8字节保存，校验后[motor_straight_02](motor_straight_02/terminal.txt)进入READY发送窗口。是否真正KEY启动、轮侧／方向／3秒撤驱动／真实RPM由主控另反馈；暂不把发包完成计为双轮闭环实物通过。

台架与图像识别验收分开，是为确认基本60分所需的控制调用链并减少现场未启动／无法停车风险；台架本身没有官方加分，也不代表自主行驶一圈。

### 实际路径收包、STOP补测和实时发送接续

其后主控对g_lap.state=0、g_speed_match.phase=0、左右PWM=0的核对回复“符合”，记为人工初始状态／零输出确认。接下来由主控把车稳定悬空，驱动OFF时接动力电池，再逐次KEY触发左／右各500ms；此处只是下一步指导，不把指导写成实物结果。需要主控反馈轮侧、实际前进方向、自动停转和最终phase／error／state才接收该项。

主控原文：“accepted和received都是0x000000B4，steering是0xFDA8，g_lap_uart_errors是0”。换算为180／180、int16−600、错误0。确认当前三线、115200/v2的基础实体路径接收、格式／CRC及负值解析；没有据此确认相机路径正确或电机行为。

初次accepted与received相等，末尾STOP没有解析计数证据；STOP字节与原共享封包器逐字节相同，格式不是已发现的问题。探针原来write后立即deinit，存在尾部未排空的可能，增加最后20字节STOP后的10ms有界发送余量（没有改字段／CRC或放宽接收保护），再运行[board_uart_probe_03](board_uart_probe_03/terminal.txt)。主控对“accepted应比received多1，未清零预计约0x169／0x168”的问题答“符合预期”。这属于关系确认，不补写主控未单独给出的新原始读数，也不把待机下STOP解析当作运动停车性能验收。

[uart_drain_checks](uart_drain_checks/checks.json)用真实探针入口、主机UART／时间模型验证7项，包括默认不开串口、180个无效路径＋1个STOP、无START、CRC／符号及deinit前至少10ms。模型不能证明最后一位已物理发完，实体计数关系由上述主控反馈提供。

相同清理余量已加入相机脚本，当前[board_bundle_runtime_r5](board_bundle_runtime_r5/low_speed_lap_canmv.py)及其[42项实际包检查](runtime_r5_checks/checks.json)保持默认idle／UART关闭／ALLOW_DRIVE=False。[board_live_03](board_live_03/terminal.txt)随后实跑10秒：165帧，算法41..47ms、中位43ms、相邻启动最大89ms、最小堆3302400B；本轮当前宿舍画面全部unknown且wire_valid=false。实际生成165个路径包及开始／结束STOP，STM32累计增量需另以主控读数确认，不拿发送端日志冒充实际收到。

K230程序已结束并关闭会话。准备人工悬空单轮校准前，等待主控核对g_lap.state／g_speed_match.phase均0、两PWM为0。该校准与视觉路径无关；进入双轮循迹仍需赛道当前有效观测，尚未放行有效驱动。全项目一圈与运动停车仍未验收。

### 新固件Watch后再次探针

主控提供[原始Watch截图](stm32_version_watch_01.png)，g_speed_revision为0x02110001、g_speed_fault=0、g_lap_uart_errors=0；这些是实际读数，尚未展开的结构体不补写其状态／计数。对应[board_uart_probe_02](board_uart_probe_02/terminal.txt)已再次发送180个无效路径及末尾STOP并正常结束；尚待STM32 accepted／received、末次steering和UART错误读数，不以K230写入完成认定互通。

比赛第三部分／图1基本60分依赖可靠自主一圈、少碰边与不出界；实际处理时延、内存和失效拒绝为这一目标排除部署阻塞，100／200ms是队内保护而非官方规则。真实失败／分版本数据支撑报告20分。没有声称取得分数、完成一圈或自动冲线停车。

下一步首先取得主控Keil实际读数，必要时在新固件Run后重发同一无效探针；随后需要赛道真实画面验证当前双边、单边关联及锐角路径，悬空／带动力与连续一圈仍未验收。

### 实验室接续：双轮悬空测试尚未执行

主控返回实验室后明确说明上一轮双轮悬空测试未做，要求重来。`motor_straight_02`仅有K230固定输入发送记录，不能作为双轮转动、方向、闭环转速或三秒停车的验收证据。先前单轮校准反馈保留，但搬运后是否断电、当前校准阶段和运行上限均须重新读取。

本次USB枚举仍为DAPLink COM9（0D28:0204）、K230 COM10（1209:ABD1）。正在等待主控确认两轮完全悬空、Keil Run，以及`g_speed_match.phase`、`g_lap.state`、`g_lap_config.run_ms`当前值；在这些条件明确前不重发有效固定输入。后续测试仍由主控KEY启动、STM32限制3000ms，固定输入不是相机识别结果。这一步为基本功能60分的一圈目标验证双轮执行基础，不计作实测比赛得分。

实验室当前读数由主控回报：phase=0、state=0、run_ms=0x00000BB8，两轮已悬空。按原流程逐次指导左、右单轮500ms校准；主控分别回复“一切正常”“符合预期”，对应两侧各自朝前、最终phase=2、error=0、g_lap.state=1的核对要求。未补造脉冲计数或实测RPM。

随后启动独立`motor_straight_03`固定输入，COM10识别K230D v1.8-0、初始脚本空闲，实际收到`BENCH FIXTURE READY`后向主控明确提示“现在按KEY”。本轮仍只由主控按键启动，输入窗口45秒、MCU运行限制3000ms。双轮实际表现等待主控反馈，K230日志不代替动力验收。

[本轮终端](motor_straight_03/terminal.txt)正常结束：870个固定输入PATH，末尾STOP及10ms发送余量按已检查入口执行，助手进程退出码0并关闭K230会话。主控实际按键、转动及停止结果仍待回报；窗口结束后不继续提示按KEY。

主控随后明确回报未赶上按键窗口、绿灯持续闪烁、按KEY无反应。本轮动力测试因此记为未执行，不计成功或动力故障。代码中缺少新鲜输入会拒绝启动；绿灯待机为每2000ms短亮（无新鲜输入80ms、有当前输入400ms），故障为每100ms切换，仅凭“闪烁”不能确定当前状态。已请求g_lap.state／reason、g_speed_match.phase及按键是否长按1–2秒后松开，尚待当前读数。

为改善人工操作时间，固定输入源改为120秒窗口，独立生成`motor_bench_bundle_r2`，旧包保留。STM32固件、3000ms运行上限、人工KEY启动与真实视觉禁用策略均未改；延长等待窗口不表示延长单次驱动时间，整轮仍只按一次。入口模型19项检查通过，含真实默认120秒发送期限、三种场景固定输入／CRC／仅STOP命令及清理发送余量，见[motor_fixture_checks_r2/checks.json](motor_fixture_checks_r2/checks.json)。新包尚未实板运行，仍须当前状态核对后重测。这一修正支撑基本功能60分所需的可执行动力验证，没有实测得分声明。

### 当前确定阻塞：UART接收故障锁定

主控实报`g_lap.state=0x06`、`g_lap.reason=0x0A`、`g_speed_match.phase=2`，KEY为长按。按当前枚举，对应LAP_FAULT／LAP_TRANSPORT：当前不是单纯缺少新鲜输入的待机，而是接收驱动报告错误后锁定，KEY不会清除。先前对窗口结束拒绝启动的说明不足以解释这个实测状态，后续以当前故障读数为准。

`lap_uart.c`将USART ORE／NE／FE／PE和256字节接收环满合并累计到`g_lap_uart_errors`，现有计数不能区分各类别。尚不能判定暂停调试、串口电气、K230初始化／清理或其他具体原因。先请求错误累计值、g_speed_fault以及是否中途暂停／单步的事实；保留现场、不重发有效固定输入、不绕过故障保护。故障恢复须复位并重新两次校准，但读取现场证据应先完成。双轮动力仍未验收。

主控随后实报全程Run、`g_lap_uart_errors=3`、`g_speed_fault=0`。本轮无暂停／单步的主控事实，不再把暂停作为已证实原因；错误发生的具体阶段和类别仍待核实。

已在原SPL UART驱动错误分支增加分项统计`g_lap_uart_diag`：overrun／noise／frame／parity／ring_full，首次／末次原因位及本地ms。保留原ISR读取／丢弃／故障上报逻辑，不自动恢复、不清除锁定。为区分固件，LowSpeedLap版本升为0x02110003，Track为0x02110004；控制参数与运行时限保持。两个ARM目标均0错误0警告（Code14068、RO436、RW212、ZI2668），188项控制模型断言通过；模型不覆盖硬件USART诊断，实板仍待验。三秒BIN SHA256为`28b3e8bfcb698fb4a8c0f1750a740634ed972a4c408abaa36ba3cf958353c347`，Track为`04ec4bd2b699c07fdb9dca4e1cacb7da0f8bc193eefeabca046d25e8304d0386`。

下一步主控先断开电机动力，使用Keil下载三秒诊断版并Run，确认版本／零诊断基线；不先校准。之后只做无效UART探针，区分接收与清理／断开阶段的分项计数。不替代动力验收，120秒有效固定输入尚未运行。诊断用于消除一圈基本60分的执行链阻塞并保留报告证据，不声称实测加分或根因已解决。

主控对断电机动力、Keil重新下载／Run及版本03／UART计数0／诊断全0／state0的核对回复“符合预期”。先执行更小的隔离步骤：[uart_diag_status_01](uart_diag_status_01/terminal.txt)仅连接COM10、读取scriptRunning=false后断开，无runScript请求、无应用UART测试包。官方后端连接／断开各出现soft reboot，进程正常退出。等待主控回读STM32错误总数／分项与状态，区分工具复位生命周期与发送路径；尚未运行无效包探针。

主控对status隔离步骤后的UART总数、state／reason和诊断分项回报“均为零”。因此本次仅连接／断开未复现故障，不能据此排除其他阶段或偶发干扰。

随后运行[uart_diag_probe_01](uart_diag_probe_01/terminal.txt)：K230发送0／+600／−600无效路径各60帧，末尾STOP及10ms排空余量；脚本正常完成、进程退出码0并断开。全程未发有效路径／START，电机动力按已确认条件断开。等STM32的真实接收计数和错误分类，不以脚本结束认定接收无错。

主控随后发来Watch诊断截图：overrun=1，noise／frame／parity／ring_full=0，first_mask=last_mask=1，first_at_ms=last_at_ms=0x00030B24。另手抄回报errors=1、state=6、reason=10、accepted=7、received=0，后续补报rejected=0、duplicates=0、g_speed_ms持续变化。但主控紧接着明确“刚才读错了”，要求全部重来；手抄读数的错误范围未明确，因此这组手抄计数／状态标为待复核，不再据此进一步推断。截图内容保留为原始资料，具体对应时点和新一轮结论以重新核对为准。期间只做源码调查，未再修改或下载固件，未启动动力。

按主控要求重新开始当前验证流程：保持诊断版03，先断电机动力、主板Reset CPU后Run，重新核对版本、state／phase和UART总数／诊断零基线，再逐步做无动力通信；不把先前有歧义的读数当新一轮结果。已有日志、失败及校准历史保留，不覆盖。

重新验证第一步：主控对电机动力断开、Reset CPU后Run以及版本03／phase0／state0／UART总数0／诊断全0回复“符合预期”。随后执行[uart_diag_probe_02](uart_diag_probe_02/terminal.txt)，同一无效探针正常完成180个PATH和末尾STOP，助手正常退出并断开K230。当前等待本轮STM32 Watch证据；预计无故障时accepted=181（0xB5）、received=180（0xB4）、state0／reason0、UART总数和分项均0。预计值不写作已实测结果，动力仍断开且未校准。

本轮主控对上述逐项Watch预期表回复“符合预期值”：确认accepted=0xB5、received=0xB4、state／reason均0、UART总错误0及诊断各项0。该记录属于主控按表确认，不是新的截图或独立逐项原始抄值。由此确认诊断版03在本次无动力探针中接收180个无效PATH及STOP且未记录接收错误；没有固件修复根因或长期稳定性的声明。上一轮读错范围不明的数据继续保留待核实，不拿本次通过抹掉历史。下一步恢复电机动力前保持两轮稳定悬空，按既定两次单轮500ms流程重新校准，最终核对phase2／error0／state1／run_ms3000，之后才重发120秒固定输入。

主控随后对两次单轮表现及phase2／error0／state1／run_ms=0xBB8回复“符合”。因此在当前悬空、三秒限制条件下启动[motor_straight_04](motor_straight_04/terminal.txt)，使用已检查的motor_bench_bundle_r2。COM10初始脚本空闲，已收到120s输入窗口READY。助手在READY后立即交回人工KEY操作，不等待窗口结束才提示；本轮仍只按一次，双轮真实表现与执行结果待回报，不能将输入就绪当动力通过。

### motor_straight_04：未进入双轮RUN，UART溢出复现

主控回报指令前后绿灯均闪烁、长按KEY无反应，并提供[校准器故障截图](motor_straight_04/speed_match_fault_watch.png)。仅该图的SPEED_ERROR_STATE不是根因码；后续[主策略图](motor_straight_04/lap_transport_watch.png)确认state=6／reason=10（LAP_TRANSPORT）、run_since=0、received=0x998、rejected=duplicates=starts_rejected=0、目标与PWM0。[UART图](motor_straight_04/uart_overrun_watch.png)确认总错误0xC=12，overrun=12，其他错误分项0，first_mask=last_mask=1，first_at_ms=0x5C954，last_at_ms=0x7867C。校准器stop_ms也为0x5C954，与首次接收错误一致。本次有原始截图，可确认UART硬件接收溢出并锁定，双轮RUN未启动，不把无反应当电机起转不足。

K230固定输入完整运行120秒，正常发送2317个PATH后STOP并断开，助手退出码0。发送完成不等于STM32完整无错接收；此轮动力验收失败原因归为进入RUN前传输锁定，实际双轮转速／三秒撤驱动仍未验证。

### 05／06候选：接收抢占与执行计时

原代码UART抢占级2低于SysTick0，且主循环状态提交使用PRIMASK全局屏蔽。SysTick含20ms采样和浮点轮速处理；这些是可能阻塞硬件单字节接收的明确代码路径，但缺少旧版执行周期测量，不能把某一段耗时写为已实测根因。[ST RM0090](https://www.st.com/resource/zh/reference_manual/DM00031020.pdf)的USART overrun说明作为接收未及时读取的硬件定义来源；[Arm Cortex-M4 TRM](https://www.keil.com/dd/docs/datashts/arm/cortex_m4/r0p1/ddi0439c_cortex_m4_r0p1_trm.pdf)作为DWT周期计数来源。

候选改为UART抢占级0、SysTick抢占级1，按实际Group2用CMSIS编码（SysTick逻辑优先级4）。单字节UART ISR不解析协议、不用浮点、不循环；主循环用BASEPRI只屏蔽运动状态写者，UART仍能搬运字节。原1ms监督、20ms采样、115200波特率、错误锁定、手动KEY及3000ms上限保持；短接收环故障消费仍用原PRIMASK。新增g_lap_timing记录计数器有效性／时钟／最长SysTick与提交区周期，UART诊断新增isr_max_cycles。后者是性能统计，非零不是错误；旧“整个diag全0”的操作表述仅适用于此前未加性能字段的版本。

三秒版本0x02110005、Track为0x02110006，两个ARM目标0错误0警告，实际反汇编确认BASEPRI_MAX／BASEPRI恢复。原188项控制断言通过；新增使用SPL桩直接执行生产UART ISR的主机检查通过，覆盖600次环回绕、环满、组合硬件错误、首末记录、故障消费不清统计及配置优先级0。扩展PowerShell测试入口首轮出现输出参数解析问题，改用原脚本同样的显式-o参数后整套通过；它不是实板或固件运行失败。构建哈希与边界见[irq_fix_build_01.json](irq_fix_build_01.json)。

下一步仍先断电机动力，Keil下载05并Run，核对版本／错误零基线及g_lap_timing.counter_ready=1，随后重做无效接收，读取周期统计。要求相对86.8us字节间隔及1ms监督周期留出余量，并验证真实停车；当前只完成候选软件检查，不能宣称溢出已修复。这一改动对应基本功能60分的一圈通信可靠性和失败风险，真实证据也支撑报告20分，不声称实测得分或完整一圈。

主控对断电机动力、下载／Run及版本05／state0／UART计数0／counter_ready1回复“符合”。随后[uart_diag_probe_03](uart_diag_probe_03/terminal.txt)正常发送180个无效PATH和STOP，助手进程退出码0并断开。等STM32 accepted／received／状态／错误分项与新增周期统计，当前不先恢复动力。性能字段允许非零，需读取具体周期数，不能用笼统“diag非零”当错误。

主控随后提供[计时截图](uart_diag_probe_03/timing_watch.png)与[UART分项截图](uart_diag_probe_03/uart_watch.png)，并确认其他预期值符合：本轮accepted181／received180、state0／reason0、UART总错误0。截图中五类错误均0；counter_ready1、clock_hz=0xF42400=16000000，SysTick最大0x4F7=1271周期（79.4375us），状态提交最大0x342=834周期（52.125us），UART ISR最大0xC2=194周期（12.125us）。数值及来源见[stm32_review.json](uart_diag_probe_03/stm32_review.json)。

本次短无效接收通过，当前校准前计时相对86.8us字节间隔／1ms监督有余量。统计不含少量计时尾部及异常入口／退出，不能用这些数值推定旧版耗时、长期接收、校准后或RUN时开销；保持实板复测范围。下一步按既定流程悬空完成两次500ms单轮校准，再核对phase2／error0／state1／run_ms3000及UART错误0，随后验证校准后的有效固定输入与双轮三秒运行。

主控在本次单轮校准操作中回报忘开驱动板电源、长按后绿灯持续闪烁。尚无该次具体故障码；源码明确500ms校准结束时无足够脉冲会以SPEED_ERROR_MAPPING锁定，再由主策略锁定LAP_ENCODER，因此不能直接补开电源后续接校准，也不能据灯闪判为UART再次故障。按已确认操作失误指导驱动OFF、悬空、Reset CPU后Run，重新确认初始phase0／state0，再开驱动并只做第一次左轮校准。固件保持05不改、不重烧，之前无动力通信／计时通过证据保留；本次校准尚未通过、双轮尚未启动。

复位恢复后，主控确认第一次左轮校准符合，第二次提供四张原图：[校准器](calibration_v5_speed_watch.png)、[主策略](calibration_v5_lap_watch.png)、[UART](calibration_v5_uart_watch.png)、[配置](calibration_v5_config_watch.png)。phase=2、error=0，左右反馈通道1／2、符号+1／−1；主策略WAIT1／OK0／run_since0、PWM0，UART错误0，基速40、run_ms=0xBB8。校准器自身SPEED_SETTLING是当前复用后保持状态，不与主策略WAIT混淆；未把反馈符号当物理前进方向或实测RPM。

在上述当前截图条件和持续悬空要求下启动[motor_straight_05](motor_straight_05/terminal.txt)，仍使用120秒固定输入R2、实际主板版本05。K230空闲确认后已收到READY，随即交回人工单次KEY操作。助手未发START；实际双轮启动、方向、三秒撤驱动及RUN阶段计时待反馈，尚不计通过。

### motor_straight_05：已RUN，低PWM起步未转，触发无反馈

主控明确回报长按松开后听到电机声音但没有转动，随后绿灯快闪。[主策略截图](motor_straight_05/no_feedback_watch.png)确认LAP_FAULT／LAP_NO_FEEDBACK（6／7）、run_since=0x434C8非零、received=0x6DF、目标／PWM已归零；[UART截图](motor_straight_05/uart_zero_watch.png)总错误0。说明本次人工启动已被接受，当前故障是无反馈，不是上一轮传输锁定。截图里的0.033／0.111 RPM是停机后实时衰减值，不当作RUN转速或达标证据。K230120秒正常发送2317个固定PATH后STOP，进程正常结束；该终端结果不替代完整STM32接收或三秒动力通过。

原40RPM初始前馈按目标缩为约20%，加P/I后首帧约28% PWM；相比已经实板通过的逐轮50%／500ms校准，存在静止起转输出不足的合理解释，但本轮没有测实际起转阈值、电流或供电跌落，不能将“静摩擦是唯一根因”写为定论。原SpeedMatch固定30%前馈／60RPM已有历史实物证据，低速按比例缩放的能力此前只有模型验证。

### 07／08候选：受限起步补偿、停止结果保留

新增仅在每轮正目标从0恢复且尚无增量时的50%／最多100ms起步补偿，每轮出现增量立即退出；目标0不补偿，持续正目标堵转不反复补偿。上限沿用已确认单轮校准，时间比校准短；300ms无反馈、KEY／方向／超速／路径／传输保护及目标40RPM、3秒／50%限制保持。候选参数不表示实测起转功率，必须悬空复测。原UART修正与数学PI模块未改。

新增g_lap_last，仅离开真正RUN时保存停止原因、elapsed_ms、最后样本的目标／RPM／PWM及每轮补偿样本数；后续实时零速和清理STOP不覆盖，新RUN先将valid清零，复位清空。解决此前三秒后难以读取运行结果的问题，不代替物理方向和真实测速。

237项控制断言及生产UART ISR桩检查通过，新增覆盖双轮／单轮无反馈、100ms补偿结束、300ms故障时限、补偿期间KEY、零目标禁补偿、假设静摩擦起步与停止快照保留。假设模型用42%静止起转门槛，仅为回归场景，不是本车测量。两个ARM目标0错误0警告，三秒版本07、Track08，Code14960／RO436／RW236／ZI2724；哈希与验证边界见[startup_fix_build_01.json](startup_fix_build_01.json)。尚未代理烧录，未做07动力实物验收。

下一步主控先断电机动力，用Keil下载LowSpeedLap 0x02110007并Run，核对初始state0／phase0／UART错误0、run_ms3000，再按既定悬空单轮流程重做校准。随后人工单次KEY验证40RPM起步、三秒撤驱动及g_lap_last，并读取RUN计时。起步可靠性支撑基本功能60分的自主一圈，限幅／无反馈保护降低失控触线／出界风险，停机证据支撑报告20分；不声称已得分或可地面直接使用。

主控对07下载后版本／初始state0／UART错误0／run_ms0xBB8回复“符合”，随后对接动力ON、两轮悬空和两次单轮前进表现及最终phase2／error0／state1／UART错误0再次确认“符合”。按此当前条件启动[motor_straight_06](motor_straight_06/terminal.txt)，120秒固定输入窗口，COM10空闲确认且READY已收到。立即交回人工单次KEY，等待实际起转、三秒停止和g_lap_last／UART／执行计时结果；未将就绪当作实物通过。

### motor_straight_06：首次悬空直行三秒通过

主控提供[g_lap_last原图](motor_straight_06/last_run_watch.png)，valid1、elapsed_ms=0xBB8（3000）、reason=0x0B（LAP_LIMIT），左右目标40／40RPM，最后采样反馈41.6508255／40.4017258RPM，撤驱动前PWM0xE2／0xDD（22.6%／22.1%），起步补偿各1个20ms样本。主控回报“两轮缓慢转动”、UART errors0，随后明确确认“均向前，均停稳”。因此本轮人工固定输入的悬空起步与自动三秒撤驱动验收通过一次。最后反馈误差分别约+1.65／+0.40RPM，但未记录连续达标时长，不声明500ms同速或地面直行达标。定量记录及边界见[stm32_review.json](motor_straight_06/stm32_review.json)。

助手固定输入完整120秒正常发送2317个PATH并STOP、关闭K230会话。没有自动START／main.py写入。当前板应保留供电与校准，不必因正常结束复位；清理STOP可以改变实时reason，但g_lap_last已保留正常LIMIT。下一步先补RUN后的g_lap_timing与UART执行峰值，随后做正负差速、运行中失效撤驱动，再到真实场地验证视觉与地面。不得把人工fixture当当前双边识别或自主一圈。

为准备后续差速，助手只新增motor_right／motor_left两个固定白名单入口，复用原R2已包含的right（+500，60／20RPM目标）与left（−500，20／60RPM目标），保留120秒输入窗口、人工单次KEY、当前主板3000ms／悬空确认及哈希校验。未运行新场景。真实助手入口经FakeSession离线18项检查通过，覆盖三种场景的精确来源文本／哈希／无自动启动元数据、关闭流程及缺少悬空／错误时限时在连接前拒绝，见[helper_modes_checks_01/checks.json](helper_modes_checks_01/checks.json)；这些输出全部是假会话，不能当实板日志。

主控补充[RUN后计时图](motor_straight_06/timing_watch.png)和[UART峰值／错误图](motor_straight_06/uart_timing_watch.png)：计数器有效、时钟16MHz，SysTick最大0xCD8=3288周期（205.5us），状态提交0x2CC=716周期（44.75us），UART ISR最大0xC3=195周期（12.1875us），五类错误及首末原因／时间均0。按当前观测峰值，相对1ms监督及86.8us接收字节间隔有余量；不把有限测试峰值当所有场景最坏时限，也不据此反推旧版实测。定量记录已补入本轮stm32_review.json。

随后保持当前供电、校准与悬空条件，启动[motor_right_01](motor_right_01/terminal.txt)，目标左60／右20RPM、固定转向+500、3000ms人工KEY上限。K230初始空闲、120秒READY已收到，立即交回单次KEY。实际左右快慢／前进方向／三秒撤驱动和停止快照待反馈；尚未验收右差速。

### motor_right_01：内轮低速未维持，无反馈停车

主控回报右轮动力不足、左轮转动较快，随后快闪。[停止快照](motor_right_01/last_run_watch.png)确认valid1、elapsed_ms=0x1CC（460）、reason=7（NO_FEEDBACK），目标左60／右20RPM，末次滤波反馈74.5325928／0.0725680441RPM，撤驱动前请求PWM0x114／0xA9（27.6%／16.9%），起步补偿各1个样本。[UART图](motor_right_01/uart_zero_watch.png)错误0。右差速不通过，不能记三秒完成或目标跟踪成功；左轮末次也高于目标，不单独宣称外轮已达标。原始数值见[stm32_review.json](motor_right_01/stm32_review.json)。K230120秒2317个固定PATH正常完成并STOP关闭会话，未继续自动启动。

该证据支持“短时补偿后低目标持续驱动不足”的候选解释：20RPM线性前馈仅10%，且右轮停止前仅请求16.9%。没有测电机端电压、电流或静／动摩擦曲线，尚不能排除其他负载／供电因素。保持已验证的40RPM直行结果，不因差速失败抹掉，也不把直行结果外推为20RPM可用。

### 09／0A候选：正目标前馈下限

新增每次人工启动锁定的min_feedforward配置，默认200/1000（20%）、有效0..300。正目标取原线性前馈与该值的较大者，20RPM参考提高，40／60RPM参考不变；PI仍可将实际PWM减至0，目标0必须输出0，不强制最低占空比。100ms／50%起步补偿、300ms无反馈、KEY／方向／超速／路径／UART、三秒上限保留。该值只是候选补偿，非本车已测得最小维持功率，实板20RPM还未验收；未来调整只在停稳且下轮人工启动时生效。

316项控制断言及生产UART桩检查通过。新增假设持续死区场景对比：min_feedforward=0时内轮无反馈，200时直行／左右差速模型均运行3秒；覆盖目标20不被偷偷改为40、零目标停轮、PI仍可给0、非法参数拒绝与启动锁定。假设18%运行死区／42%起转门槛不是实物测量。两个ARM目标0错误0警告，三秒版本09、Track0A；Code15120／RO436／RW240／ZI2728，哈希与边界见[low_speed_feedforward_build_01.json](low_speed_feedforward_build_01.json)。代理未烧录、未开始09动力实测。

下一步主控先断电机动力，Keil下载LowSpeedLap 0x02110009并Run，确认初始state0、UART错误0、run_ms3000与min_feedforward200，再重新两次悬空单轮校准，优先复测失败的右差速。验证目标为内轮持续转动、两轮前进、正常3000ms LIMIT、末次目标误差和执行计时。此改进支撑基本60分的弯道循迹并减少内轮停滞引发碰边／出界风险，仍需实物验证，不声称预得分或可直接地面运行。

主控对09下载后版本／state0／UART错误0／run_ms0xBB8／min_feedforward200回复“确认”，随后对两次单轮前进与最终phase2／error0／state1／UART错误0回复“符合预期”。在当前悬空与供电条件下启动[motor_right_02](motor_right_02/terminal.txt)，K230空闲且120秒右差速READY已收到，随即提示人工单次KEY。目标仍左60右20RPM、单次3000ms，实际内轮维持、末次速度和正常停止结果待回报。

### motor_right_02：右差速悬空三秒通过

主控回报“正常转动符合预期”及UART errors0，提供[原始停止快照](motor_right_02/last_run_watch.png)：valid1、3000ms、LIMIT，左右目标60／20RPM，末次反馈60.8911362／19.6733036RPM，撤驱动前PWM0x110／0xCC（27.2%／20.4%），补偿各1样本。对应前轮前进／左快右慢且内轮持续／三秒停稳的操作要求，记本次右差速悬空验收通过一次。末次目标误差约+0.89／−0.33RPM，不声明连续达标时长；范围见[stm32_review.json](motor_right_02/stm32_review.json)。

K230120秒2317个PATH正常结束并STOP关闭；保持当前供电／校准后启动[motor_left_01](motor_left_01/terminal.txt)，固定转向−500、目标左20／右60RPM、同一3000ms上限。空闲确认、120秒READY已收到，立即提示人工单次KEY，左差速实际结果待回报，不预先验收。

### motor_left_01：左差速悬空三秒通过

主控提供[停止原图](motor_left_01/last_run_watch.png)与[计时原图](motor_left_01/timing_watch.png)，回报转动符合预期、UART错误0。快照valid1、3000ms／LIMIT，目标20／60RPM，末次16.9267979／59.5401344RPM，撤驱动前PWM0xD9／0x10C（21.7%／26.8%），补偿各1样本。末次误差约−3.07／−0.46RPM，符合队内末帧±5参考，但没有连续达标记录。主控按前述两轮前进／右快左慢且内轮持续／三秒停稳要求确认，记一次悬空左差速通过。16MHz计时有效，SysTick0xC08=3080周期（192.5us）、提交0x2B9=697周期（43.5625us）。详见[stm32_review.json](motor_left_01/stm32_review.json)。

K230120秒2317个PATH正常结束并STOP关闭。下一项断源验证计划仍用直行固定输入与主控单次KEY、主板3000ms上限；主控看到两轮转动约1秒后拔K230 USB，保留DAPLink主板供电。故障锁定与提前撤驱动属预期测试行为，优先记录g_lap_last和g_lap.path_at／g_speed_match.stop_ms。USB掉电若触发UART接收错误，也可先于纯LINK超时撤驱动，应按实际原因归档，不能混作已证明200ms超时路径。助手后端可能因人为断开报错，不将其误记为控制器自发失败。当前仅准备此项，尚未启动。

[motor_link_loss_01](motor_link_loss_01/intent.json)已启动同一直行输入，K230初始空闲，120秒READY收到，立即交回上述主控人工断源操作；主板仍锁定每次3000ms。尚未收到断源结果，不能提前记保护通过。

主控随后询问是否就是让K230没有电。明确本项为仅K230断电断数据，主板DAPLink与电机供电保持、车轮悬空；不是给整车断电。核对时第01轮已过153秒，后端完整发送2317个PATH、正常DONE并关闭，尚无断源／控制器停止证据，不能记断源通过。为避免已结束窗口影响操作，重新启动[motor_link_loss_02](motor_link_loss_02/intent.json)，K230空闲确认及120秒READY已收到；当前人工KEY与断K230电操作待执行，结果待反馈。

### motor_link_loss_02：断源未执行，左轮起转失败

主控回报长按后只有右轮短暂转动、左轮没转，还未来得及拔USB即停。[快照原图](motor_link_loss_02/startup_fault_watch.png)valid1、elapsed_ms=0x138（312）、NO_FEEDBACK，目标40／40RPM，左RPM为约−2.8e−45的数值残余（实质近零，不能解释为持续反转），右末次滤波32.346386RPM；撤驱动前请求PWM0x148／0xEC（32.8%／23.6%），左补偿5样本、右1样本。左轮已用满当前100ms起步补偿但没有有效起转证据，右轮有起步反馈；不把此轮算作断源停车通过，当前未提供新UART总错误值。量化记录见[stm32_review.json](motor_link_loss_02/stm32_review.json)。

K230仍完整120秒2317个PATH正常结束并STOP断开，符合主控尚未拔USB的反馈。之后未开新有效输入。已指导主控驱动OFF、保留逻辑USB与Keil Run，先核实供电及左轮单轮起转重复性；未擅自继续加功率、加长无反馈时限或刷另一版。此前07直行与09左右差速各一次通过均保留，但新失败说明不能据单次成功声明可靠起转。

本地供电入口记录是DAP单源5V供主板、独立2S供驱动；10月24日的7.4／7.56V是历史测量，不能代作当前电压。已请求主控当前是否仍为同一2S动力源、能否测静态电压／是否有表；并根据本轮日志20点的实际时段询问当晚最终场地可用性，以调整现场与台架优先级。当前具体电气／机械／起步时长原因待证据，不能仅凭100ms补偿用满认定唯一根因。

主控回报“是2S电池，4.95V；随时可以到现场”。当前4.95V的准确测点仍未确认（电池XT30或5V稳压轨），故不能直接定为电池已损坏或正常。已立即指导驱动OFF、拔XT30、暂不充电，询问准确测点与是否有另一块合格2S电池。项目采购记录是Tattu TA-45C-800-2S1P-XT30，核对[Tattu厂家说明](https://genstattu.com/content/instock/Tattu-Soft-UAV-pack-Manual.pdf)确认显著低单节电压不得使用／充电的条款；若确为电池端4.95V，则至少一节不高于平均2.475V，应停用并按厂家处置，不能先建议充满或复活。UC2停用约定保持。

具体处理入口已落在[low_speed_power_check.md](../../hardware_preparation/low_speed_power_check.md)。当前不再改固件／发动力输入，先核实供电边界；没有合格动力源时可利用现场随时可到条件做无动力真实视觉验证。以前单次转动成功不能排除当前供电异常，之前低速补偿的解释仍为候选，换合格供电后必须重测。

主控已进一步确认测点为电池XT30正负极，表述“5V多”，且只有当前这块电池；不再将其当板上5V轨。原4.95V是先前确切回报，当前未另给精确复测值。已指导该电池停止动力使用、保持XT30隔离、暂不充电，未宣称已测出单节状态或永久报废。场地仍可用，后续可动力隔离做真实视觉。

主控表示现在可充电后明确充电器为UC2。按既有过热停用记录，已立即说明UC2继续停用；如已连接，应先切断UC2输入电源，再断电池，不能为了继续测试恢复原过热充电器或强充低压电池。是否已经开始充电待主控说明，不能从“可以充电／UC2”推定已充。当前09固件与所有原始运行证据保留，没有新动力／充电／main.py／上传操作。
