# I-02：新电池、保留USB调试供电的悬空复测

日期：2026-11-11。执行／人工观测：主控；本对话延续I-02，不接替00。新证据只记录本次测试配置，不覆盖[同日现场供电记录](../2026-11-11_field/record.md)或11-09／11-10原始证据。

## 已取得的当前事实

- 主控表示新电池已换好、继续试车，并回报电池自身XT30端电压实测8.38V。该值为人工反馈，未另提供本次仪表照片／型号或动态波形；满足2S静态使用前初筛，尚不能替代带载与稳压5V实测。原低压电池不作为本轮动力源。
- 主控明确当前仍为DAPLink供STM32、电脑USB供K230；去场地时可切驱动板5V，但当前不自动改接。本轮先保留该调试配置，车载供电与冷启动另按onboard_power.md验证，禁止把两种供电配置的证据混记。
- 首次枚举无设备；后续实际枚举DAPLink COM9（0D28:0204）、K230 COM10（1209:ABD1）。没有据USB枚举宣称SWD连通、主板已Run或动力已接通。当前未检测到UV4／canmv-backend进程，Keil实际界面与运行状态由主控核对。
- 最新共享记录：STM32固件仍LowSpeedLap09／3000ms／min_feedforward200；K230 main.py已于11-10明确授权部署为10秒禁止驱动自检。稳定供电发包通过，K230物理断电可触发FE并锁定，稳定K230后人工复位STM32可建立一次空闲零基线。自检不提供持续运动许可，不能当连续循迹入口。

## 本次下一步

驱动板保持OFF，先保持K230 USB稳定至少30秒，让已有10秒无驱动自检结束；随后主控用Keil的LowSpeedLap目标进入调试，Reset CPU→Run并等待5秒，核对revision09／run_ms3000／min_feedforward200、phase0／g_lap.state0、PWM0与硬件／UART错误0。当前这是操作安排，未收到本轮新零基线读数，不先发有效固定输入或校准。

当前未连接CanMV后端、未runScript／写main.py、未改固件／参数／电源线、未启动电机或上传Git。源代码与历史失败保留。前序核对完成后，才开启新电池的悬空单轮校准、40RPM直行起转重复性／差速／停止验证；地面与一圈须再满足车载供电、真实视觉等前置条件。支撑比赛基本60分的可靠完赛和少触边，现场证据支撑报告20分，不声称实测比赛得分。

## 当前人工基线与第一次三秒测试

主控对稳定K230供电后，Keil LowSpeedLap Reset CPU→Run并等待5秒的零基线表回复“符合”：版本09、run_ms3000、min_feedforward200、phase0／state0、硬件／UART错误及左右PWM0按人工确认记录。随后对驱动OFF接新电池再ON、两轮完全悬空、左右各一次500ms前进校准和最终phase2／error0／state1／UART错误0回复“符合”。未补造本轮独立Watch图或精确校准脉冲。

据此启动[motor_straight_01](motor_straight_01/terminal.txt)，K230 COM10 v1.8-0初始空闲，已收到120秒straight固定输入READY，立即交回主控单次KEY。主板仍每次3000ms、目标40／40RPM。输入明确是人工fixture，不是实时相机；无自动START、烧录或main.py写入。实际起转、持续转动、三秒停止及g_lap_last／UART错误／计时待主控回报，不以READY计动力通过。

### 新电池直行第1轮结果及重复安排

主控回报“两轮缓慢转动”、UART errors0，并提供[原始快照](motor_straight_01/last_run_watch.png)：valid1、elapsed_ms0xBB8=3000、LIMIT，目标40／40RPM，末次38.8627205／42.2567825RPM，撤驱动前请求PWM0xCF／0xC1（20.7%／19.3%），补偿各1样本。最后一帧误差各在±5RPM队内参考内，不声称连续达标或地面速度。物理转动已报告，方向／停稳将与重复轮次一并明确确认，详见[结构化记录](motor_straight_01/stm32_review.json)。K230该窗口120秒2317个PATH正常结束并STOP关闭。

为检验此前不稳定的起转，保持新电池、悬空及当前校准，不复位／改参数，启动[motor_straight_repeat_01](motor_straight_repeat_01/intent.json)。本次明确安排两次独立人工KEY（三秒上限各自保留），每次完整停稳后另等至少5秒才下一次，任一异常即停止后续；两次分别保存g_lap_last，最后补执行计时／UART错误。不同于首轮单次操作，本次人工起动次数限定2，脚本仍只提供固定输入、绝不发START。K230空闲确认且新120秒READY收到，当前两次结果尚待回报。

主控随后询问是否需要Reset CPU，已明确正常LIMIT结束不需要复位，保持Run和校准直接进入下一次人工KEY；复位会丢失phase2。查询时输入窗口启动已350.1秒，客户端完整2317个PATH正常DONE／退出，未收到第2／3轮的实际结果，不能假定两轮已经做过或未做。

为减少问答导致反复错过窗口，已把独立fixture输入等待由120秒延长到600秒，并将客户端仅motor模式的超时改为630秒，其他诊断模式仍150秒。STM32固件09、3000ms上限、50%输出／100ms起步／300ms无反馈等均未改，无自动START；每次仍人工KEY，只有明确安排重复轮次才允许停稳并再等5秒后下一次。新[R3包](motor_bench_bundle_r3/manifest.json)默认IDLE，R2历史包保持，vision_protocol.py／lap_protocol.py与R2哈希逐字节相同。19项真实入口模型检查及18项FakeSession助手入口检查通过，见[motor_fixture_checks_r3](motor_fixture_checks_r3/checks.json)与[helper_modes_checks_r3](helper_modes_checks_r3/checks.json)。这些只是窗口／门槛软件证据，不充当新增动力结果；未改main.py／上传或重烧主板。

随后[motor_straight_repeat_02](motor_straight_repeat_02/intent.json)实际连接COM10确认空闲并收到600秒READY，立即交回剩余第2／3轮人工操作，明确不Reset CPU；如主控已经复位，则先读取phase恢复校准，不直接按重复测试步骤。当前尚无新增轮次结果。

### 新电池直行三次记录完成

主控将两张图标为本次重复的“第一次／第二次”，按先前安排对应总第2／3轮：[第2轮](motor_straight_repeat_02/trial_02_watch.png)及[第3轮](motor_straight_repeat_02/trial_03_watch.png)。两图均valid1、elapsed_ms3000、LIMIT、目标40／40RPM。第2轮末次40.057869／41.9328308RPM、撤驱动前PWM20.5%／19.3%；第3轮41.1314087／39.2592697RPM、20.2%／19.7%；补偿均各1样本，主控明确UART错误均0。结构化值与验收边界见[stm32_review.json](motor_straight_repeat_02/stm32_review.json)。

结合首轮38.8627／42.2568RPM正常3000ms结束，已取得新电池下三次悬空直行起转、定时结束与末帧±5RPM参考内的独立结果，不把末帧数据写成连续500ms同速；也不因新电源成功就认定旧故障只有一个原因。当前供电仍DAP／USB逻辑加新2S动力，车载供电／新电池差速／KEY和断源实物保护、真实视觉与一圈各自待验。

准备下一项单次试验时，长窗口尚未结束。助手新增仅在120000／600000两种固定白名单间选择的`--motor-window-ms`，默认仍600000；基础R3包哈希核对后只改RAM等待时长与READY文字、对应客户端超时，记录精确执行文本和input_window_ms。STM32固件、3000ms限制及全部动力门槛不变。新增短窗口／非法值连接前拒绝等检查后，共30项FakeSession入口检查通过，见[helper_window_checks_01](helper_window_checks_01/checks.json)；未触及运行中的原会话或板上main.py。单次差速／急停可用120秒窗口，需较长问答时用600秒，避免切换等待；这些都是输入等待，不是连续驱动时间。

长窗口最终正常发送11546个固定PATH、DONE后关闭；保持当前校准与供电，启动[motor_right_01](motor_right_01/terminal.txt)使用120秒短窗口。新电池仍8.38V静态读数、09目标3000ms、min_feedforward200，固定+500→目标60／20RPM。COM10初始空闲且120秒READY已收到，立即提示人工单次KEY。右差速结果待回报，未以旧电池差速证据或输入就绪代替新电源验收。

### 新电池右差速通过，准备左差速

主控提供[停止快照](motor_right_01/last_run_watch.png)，确认轮子符合预期、UART不报错。图证valid1／3000ms／LIMIT，目标60／20RPM，末次61.3045464／19.5409946RPM，撤驱动前PWM0xDA／0xB4（21.8%／18.0%），补偿各1样本。按本轮两轮前进、左快右慢且内轮持续、三秒停稳的操作上下文，验收新电池下右差速一次；只确认最后一帧误差参考内，不声明连续稳定时长。来源见[stm32_review.json](motor_right_01/stm32_review.json)。

客户端120秒2317个PATH正常结束并STOP关闭，保留校准后启动[motor_left_01](motor_left_01/terminal.txt)，−500、左20／右60RPM、120秒输入窗口，仍由主控单次KEY运行3000ms。COM10初始空闲及READY已收到，立即交回人工操作，左差速实际结果待回报；没有改固件／参数／main.py／供电或上传。

### 新电池左差速通过，开始KEY急停验证

主控回报轮子正常、UART无报错，并提供[原图](motor_left_01/last_run_timing_watch.png)：valid1／3000ms／LIMIT，目标20／60RPM，末次19.5300598／59.9548531RPM，撤驱动前PWM0xB8／0xD7（18.4%／21.5%），补偿各1样本。结合本轮两轮前进、右快左慢且内轮持续、三秒停稳的预期，验收新电池左差速一次，量化值见[stm32_review.json](motor_left_01/stm32_review.json)。末帧吻合不代表连续500ms统计。

同图计时器有效、16MHz，SysTick峰值0xD04=3332周期（208.25us），状态提交0x625=1573周期（98.3125us）。提交统计包含允许的UART抢占，不是全局屏蔽UART的时长，不能拿其超过86.8us就判定新溢出；当前UART0错误，观测周期相对1ms监督仍有余量，不当全工况最坏界限。客户端窗口2317个PATH正常结束并STOP关闭。

随后保持供电与当前校准，启动[motor_key_stop_01](motor_key_stop_01/intent.json)，复用直行固定输入／120秒窗口，主板每次3000ms上限。COM10初始空闲且READY已收到，立即提示主控长按松开启动、转约1秒后短按一次同一KEY；保持两轮悬空、逻辑供电和Keil Run，预期提前撤驱动并锁定，先保存快照不复位。没有改固件或自动发送START，急停功能实物结果尚待回报。

### KEY人工急停通过，准备恢复并验证断源

主控明确回报“撤驱动了”、UART无报错，提供[原图](motor_key_stop_01/last_run_watch.png)：valid1、elapsed_ms=0x324（804）、reason1（LAP_KEY），目标40／40RPM，末次39.6054955／39.8795319RPM，撤驱动前PWM0xCB／0xC8（20.3%／20.0%），补偿各1样本。按本轮先长按起动、转动后短按KEY的操作上下文，功能急停验收通过；804ms为整次RUN时长，绝不能当按键响应耗时，具体按键沿到PWM撤除未做波形测量。源见[stm32_review.json](motor_key_stop_01/stm32_review.json)。

客户端随后完整2317个PATH正常DONE并STOP关闭，现已没有输入脚本运行。急停后的锁定属于预期，原件保存后才安排恢复：驱动OFF、逻辑USB／DAP保持稳定、Keil Reset CPU→Run取phase0／state0／PWM和错误0，再驱动ON、两轮悬空重新两次500ms单轮校准；最后核对phase2／error0／state1／UART错误0，再开断源测试。当前仅安排，不补写主控已复位／校准。

下一断源场景将保留DAP供主板与独立新电池动力，仅主控在转动约1秒后断K230 USB。11-10已确认该断电可能先触发FE／TRANSPORT，因此按实际停因分别记录：LINK可核对最后路径时间到停止时间；若先发生传输错误则验收对应故障撤驱动，不混写纯200ms超时。该保护功能实物结果仍待验，不因本轮KEY通过就放行地面或连续一圈。

主控对驱动OFF、保持逻辑供电、Reset CPU→Run后零基线，再驱动ON两次单轮校准及最终phase2／error0／state1／UART错误0的具体操作表回复“符合”，按人工反馈记恢复完成。本轮没有刷固件／改参数或重新切供电。

据此启动[motor_link_loss_01](motor_link_loss_01/intent.json)，COM10初始空闲、120秒直行固定输入READY已收到，立即提示人工KEY及看到转动约1秒后只拔K230 USB。主板3秒上限保留，实际断源和撤驱动待回报。该故障注入可预期导致后端设备断连，不能仅用客户端退出码判主板保护成功或失败；仍以真实轮子表现、停止快照、故障分项及本地时间为依据。

### K230掉电传输故障撤驱动通过

主控提供五张原图：[诊断](motor_link_loss_01/uart_diag_watch.png)、[总错误](motor_link_loss_01/uart_errors_watch.png)、[主状态](motor_link_loss_01/lap_fault_watch.png)、[复用校准器](motor_link_loss_01/calibrator_fault_watch.png)、[停止快照](motor_link_loss_01/last_run_watch.png)，并随后明确确认“是，已停稳”。因此本轮K230物理掉电后传输故障撤驱动功能通过一次；不混写纯断流超时分支。

原图值：valid1，elapsed_ms0x622=1570，LAP_TRANSPORT10；目标40／40RPM，末次39.2362595／39.5410347RPM，撤驱动前PWM0xCE／0xC8（20.6%／20.0%），当前左右PWM0。UART总错误2，frame2、其他四类0，首末mask4，首0x6B71F=440095ms、末0x6B725=440101ms（相隔6ms）；UART ISR峰值0xE3=227周期，按本板16MHz为约14.1875us。主策略run_since0x6B0FD=438525ms，path_at0x6B6EB=440043ms；校准器stop_ms0x6B71F=440095ms与首次错误同一毫秒，停止距最后路径参考52ms。不能据此声称物理故障零延迟，亦不是200ms LINK超时；准确分类及数值见[stm32_review.json](motor_link_loss_01/stm32_review.json)。错误事件数不等于损坏协议包数。

客户端因人为K230掉电未收到正常DONE，最终以“normal diagnostic completion marker missing”退出1，已关闭自己的后端。该结果与试验故障注入一致，不能反向当控制器停车失败；没有自动重连、提权、重跑或关闭保护。

### 当前暂停位置

至此，新电池静态端电压8.38V、USB逻辑供电配置下三次40／40直行、60／20右差速、20／60左差速、KEY急停和K230掉电传输故障撤驱动均有本次证据。仅末帧速度匹配，不声称连续500ms统计；纯200ms断流、车载两板供电、真实现场视觉、地面与一圈均未验。

主控确认当前仍在实验室，之后表示“暂时无法前往，一会继续”。按该明确意图暂停试车，当前没有任何助手脚本／设备连接运行，未开始新的相机或供电操作。已指导主控驱动OFF、拔XT30，暂停期间不必保留校准；实际断开状态待恢复时按事实核对，不从指导推定完成。STM32最后已知为09版、传输故障锁定、零PWM；K230最后为USB拔开，板上main.py仍是11-10部署的10秒禁止驱动自检，不是连续循迹入口。

恢复时优先推进最终赛道的无动力真实视觉核验：相机安装保持，电机动力物理隔离，两板沿用DAPLink／电脑USB调试供电，避免未验证的驱动5V与USB并接。到位前不运行相机诊断；车载供电／冷启动须在地面动力前另行验收。若恢复期间需要动力，保持K230稳定后重新建立主板零基线并校准，不能直接复用掉电前phase。已有通过的原始记录保留，不因复位重写成未做。

相机工具准备仅做了只读调查：当前没有专用CanMV连接器，沿用已安装官方后端；本地0.9.10扩展说明MSG_FRAME=4、载荷为4字节帧号后接JPEG。尚未修改Session预览保存、未发相机脚本／采新图、未写main.py或SD文件。后续可在已有禁止驱动live诊断上补主机原图取证，保持真实场地识别证据与电机fixture严格分开。
