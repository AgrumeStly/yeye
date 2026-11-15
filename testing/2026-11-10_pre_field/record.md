# I-02：换电池后宿舍复测准备

日期：2026-11-10（北京时间）。执行：主控侧本地准备；人工与实物由主控确认，不接替00。任务[I-02](../../project_planning/tasks/I-02-LOW-SPEED-LAP.md)。

## 主控本轮反馈

主控明确新电池已安装成功、OLED正常、驱动板供电正常；今晚在宿舍，2026-11-11去实际场地，要求完成去场地前能做的工作。随后确认具备两板连接／稳定悬空／人工KEY条件；新电源未测端电压，已充满、额定7.4V。按既定亚博7.4V／2000mAh采购身份记安装，不补造端电压、掉压、充电器到货或新电池下动力通过。

原OLED任务最后确认板上为独立OledBench，动力隔离；本轮新反馈未提供已换回低速程序证据。低速版09最后已有两次单轮校准、一次左右差速及07版直行成功，但09后续一次直行在312ms NO_FEEDBACK停止，断源未执行；旧低压电池与新电池测试条件分开。

## 已完成的本地准备

- 读取比赛第三部分、图1原图与评分表，按可靠起转／失效停车／真实视觉／连续完圈顺序组织宿舍与场地步骤，见[操作单](../../hardware_preparation/pre_field_checklist.md)。
- 重新执行真实控制模型316项断言与生产UART驱动桩检查，通过；日志复制到本目录software_logs。台架入口模型19项、真实助手FakeSession18项、runtime_r5视觉／跨语言协议42项通过，子目录中保留JSON；均没有操作设备或电机。
- 两独立ARM目标重新构建0错误0警告；LowSpeedLap09与Track0A的BIN哈希分别仍为`7f3f7b5e8c676e321e23f3c2c2b6a88cd0e3821c5b8f80af9f608cce3224e2f9`、`f7cc1c34a462a7599654bd664d0ee5ca12530fe6fc100cf60025baace547c2bb`，与前次候选相同。原固件／算法参数未修改。
- 只读查询时无UV4进程条目；串口仅见DAPLink COM9（VID:PID=0D28:0204）和蓝牙COM3—6，未见K230。枚举不是SWD读回／运行事实，不认定K230损坏。待主控重新接数据口后再枚举。
- 准备本地BIN／HEX、两个已核对K230工作包、日志与字节哈希清单；生成器在[prepare_pre_field_evidence.py](../../hardware_preparation/source/prepare_pre_field_evidence.py)。本目录为证据／候选副本，Keil仍打开原工程；manifest不表示烧录或验收。
- 建立[悬空记录表](bench_results.csv)与[场地记录表](field_results.csv)，初始只有列名，不包含虚构结果。全局project_status仍由00接收任务证据后更新。

## 尚未完成与下一步

本轮尚未烧录、运行K230脚本、启动电机或测量电压；未提交／上传／发跨聊天消息。OLED运动显示未集成；脱离电脑的两板车载供电及冷启动未验收。软件通过不等于宿舍实物、真实视觉或一圈通过。

下一步主控驱动OFF／动力隔离，接K230数据口，用Keil打开LowSpeedLap工程下载09并Run，回报版本、run_ms3000、min_feedforward200、phase0／state0、PWM0、故障及UART错误0；新电池端电压另补。随后无动力通信、悬空校准、重复直行、左右差速、KEY与断源停车逐项留证。操作细节与进入条件以操作单为准。

接续目录D:/projects/projectsyeye；分支codex/current-version-20261025；来源HEAD `a0733a8685db4c2b497539303bfe87fe1c1ebfe5`，存在多模块未提交修改，全部保留。只在本地保存检查，未改变分支。比赛基本功能60分及报告20分为支撑目标，没有实测得分结论。

## 主控恢复09版后的无动力探针

主控对上一轮明确给出的操作与Watch预期表回复“一切符合预期”，据此记录LowSpeedLap09版本、run_ms3000、min_feedforward200、g_lap.state0、g_speed_match.phase0、左右PWM0、g_speed_fault0及g_lap_uart_errors0符合。按上一轮操作条件，驱动OFF、动力电池隔离、保留DAPLink并连接K230。此为主控人工回报，没有另存本轮Keil下载日志或独立SWD读回；未补造counter_ready／时序或全部UART诊断分项。

随后只读枚举见DAPLink COM9（0D28:0204）与K230 COM10（1209:ABD1），在COM10顺序执行现有助手`uart_probe`，输出进入[uart_probe_01](uart_probe_01/terminal.txt)。实际连接CanMV K230D Lite 128M、v1.8-0；后端报告running=false后才运行探针。终端依次打印0／+600／−600各3秒的INVALID_PATH_ONLY及UART PROBE DONE，助手正常退出，未发START／有效PATH、未写main.py；连接／运行／断开产生的soft reboot保留在原始终端。发送源码及SHA256在[执行记录](uart_probe_01/run.json)中配对保存。

K230发送端正常完成；STM32本轮接收／STOP解析／状态仍待主控Watch实值。零计数基线下预期accepted181（0xB5）、received180（0xB4）、steering=-600（int16的0xFDA8）、path_valid0、state0／reason0、phase0、左右PWM0，UART总数及overrun／noise／frame／parity／ring_full均0。isr_max_cycles为计时字段，不要求0。主控回报后再判断实际通信，不将终端DONE当接收通过。下一步先取得本轮读数；新电池端电压未测，尚未校准或启动电机。

### STM32接收反馈：本轮无动力UART通过

主控随后提供[g_lap原始截图](uart_probe_01/stm32_watch.png)，并反馈“其他的都正常”。图中直接可读：state0／LAP_CALIBRATION、reason0／LAP_OK、run_since0、received0xB4（180）、rejected／duplicates／starts_rejected均0、steering0xFDA8（有符号−600）、path_valid0、左右目标／RPM／PWM均0、history／single均0。前一轮请求的accepted181及UART总数／五类错误均0由主控概括确认，未在此截图展示，分别注明人工反馈而非独立图证，详见[结构化核对](uart_probe_01/stm32_review.json)。

结合K230真实终端正常DONE、STM32原图与其余字段人工确认，本轮无动力UART接收、负值解码及STOP解析计数关系通过；保持无运动输出。没有据此认定新电池下起转、动力中STOP／断源保护或一圈通过。新电池端电压仍未提供，下一步先保持驱动OFF／动力隔离测电池自身输出端并回报实际V，然后按既定悬空／人工KEY逐轮500ms校准；当前不启动固定有效输入。

## 万用表损坏后的无动力实时链路

主控明确“我没有万用表，坏了”。电池实测记为工具条件不足，既定新电池动力复测延后，今晚继续不依赖仪表的逻辑供电／动力隔离检查；不从工具缺失推定电池异常。明日由主控／硬件借用完好仪表补测，旧低压电池继续停用。

在保持既有动力隔离、LowSpeedLap09 Run／phase0条件下，COM10顺序执行现有助手`live_no_drive`，原runtime_r5工作包字节SHA256与manifest核对一致；仅工作副本改live／UART启用／10000ms，ALLOW_DRIVE=False保持，不写main.py、不发START。真实后端先报告空闲再运行，终端含初始化、GC2093相机启动、逐帧JSON、L1 DONE及清理soft reboot，无Traceback，进程退出码0。原件见[live_no_drive_01/terminal.txt](live_no_drive_01/terminal.txt)，[执行源码与哈希](live_no_drive_01/run.json)、[统计](live_no_drive_01/summary.json)配对保存。

实际156帧，processing41..56ms、中位46ms，含预览／日志影响的最大启动间隔101ms，to_send最大85ms，最小free_heap3293536字节；全部source=unknown、valid／wire_valid／drive_allowed=false。宿舍实际画面不是赛道证据，本轮只验证相机API／运行耗时与禁止驱动输出，不能宣称识别能力或完整圈通过。

该程序开始和结束各发一个STOP，156个PATH；若STM32自上一轮探针以来未复位且无额外发送，预期accepted从181增158到339（0x153）、received从180增156到336（0x150），state／reason仍0、左右PWM0、path_valid0、UART总数与五类错误0。此为待核对的接收预期，不是已读取值；先取得主控Watch反馈，不启动校准或有效固定输入。另已询问两块计算板脱离电脑后的实际车载供电器材／接法，来源仍不足，不能直接推断可脱机跑车。

### 实时链路人工确认：通过

主控对上述339／336计数、state／reason0、左右PWM／path_valid0、UART总数与五类错误0的具体预期表回复“符合预期”。按人工反馈验收本轮相机运行／UART接收／禁止驱动链路，详见[接收确认](live_no_drive_01/stm32_review.json)。没有新的STM32原图、逐项手抄数值或独立SWD读回；复位历史亦未单独说明，不补造额外板内证据。K230真实156帧原始终端仍为本轮发送与耗时依据。

截至此步：09恢复零基线、9秒无效探针与STOP计数关系、10秒真实相机／UART无动力链路已完成；宿舍画面未知不算赛道识别通过。新电池端电压因表损坏待补，新电池下动力／断源停车、真实场地识别／过弯／一圈待验。下一步先核对STM32与K230车载供电器材、实际连接及脱机启动入口；K230当前main.py仍保留既有采集待机入口，本轮实时诊断只在RAM运行，不能认为拔电脑后会自动运行低速视觉。未改main.py、采集许可或线束，不使用损坏仪表，也不发有效固定输入。

## 车载供电路径及脱机启动候选

主控明确当前STM32由DAPLink供电、K230由电脑Type-C供电，两板可改由电池供电；随后纠正具体路径：驱动板稳压5V／GND经杜邦线分别接主板与视觉板的5V／GND，不使用USB-A转接板。按此记录切换方案，未补造已取消调试电源、完成改接或新测量／冷启动。厂家原文、同开关逻辑／动力供电的进入条件、杜邦固定与待验证项见[onboard_power.md](../../hardware_preparation/onboard_power.md)。

本地生成[cold_boot_candidate/main.py](cold_boot_candidate/main.py)，SHA256 `c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269`：已验runtime_r5派生，仅改live／UART／10000ms／无预览，增加新编号日志与启动条件门，ALLOW_DRIVE=False保持；只发送无效PATH和STOP，不发START、不读写采集许可。生成器[prepare_lap_boot_check.py](../../vision/tools/prepare_lap_boot_check.py)，电脑验证[check_lap_boot_check.py](../../vision/tools/check_lap_boot_check.py)。16项启动／日志模型检查通过，覆盖有效几何仍发无效包、真实CRC、旧日志保持、异常传播／失败记录、编号耗尽、无SD、禁止drive配置；另42项原视觉／真实C协议回归通过。相机主流程在16项中为替身，不把模型当实物。

使用现有CanMV后端**只读**备份板上main.py，11636字节、SHA256 `9ac4d097f5000ec323f255981756ada9c5c5020516651f8321f40151799222e2`；boot.py、full_lap_capture.arm、push_capture.arm当时不存在。见[startup_backup/manifest.json](startup_backup/manifest.json)与[真实备份](startup_backup/main.py)。备份不运行用户脚本、不写远程文件；连接／断开soft reboot保留原件。

随后在既有USB逻辑供电／动力隔离／不按KEY条件下，将候选以RAM脚本实跑，不替换main.py。新建`/sdcard/lap_boot_checks/check_0001.jsonl`，完整读回[本地原日志](cold_boot_ram_01/boot_log.jsonl)：144帧，算法45..57ms、最大启动间隔108ms、to_send最大84ms，全部wire_valid／drive_allowed=false，最后completed。进程退出0，源码及日志哈希配对，[实板摘要](cold_boot_ram_01/result.json)。这一轮新增144个PATH＋2个STOP；若STM32未复位且无其它发送，339／336基线后预期accepted485／received480，实际值尚无新回报，不写接收通过。

此轮只证明新日志入口可在现有实板RAM运行并正常落盘，**未替换板上main.py、未切换电源、未物理断电冷启动、未启动电机**。原任务main.py保持边界未变；下一步需主控明确同意切换为该10秒无驱动启动自检，才写入并回读。新供电的实际验证仍待借仪表，之后物理冷启动与新电池悬空动力分别留证。未上传、发跨聊天或更新00全局摘要。

## 主控授权切换main.py：写入与读回完成

主控对明确列出的10秒禁止驱动启动候选回复“确认”，本次获得替换main.py授权，条件仍为当前USB逻辑供电、动力隔离。执行[固定部署脚本](deploy_boot_check.py)：候选字节与已通过16／42检查及RAM实测的源码哈希相同；连接COM10后先确认空闲，重新读板上旧main.py并与真实备份逐字节比较，一致才允许写入。另存[写入前原件](boot_deploy_01/previous_main.py)，不覆盖原备份。

随后使用同一已安装CanMV官方后端`io.writeFile`写入`/sdcard/main.py`，未经过前端自动压缩；完整读回[readback_main.py](boot_deploy_01/readback_main.py)与候选逐字节一致：34887字节，SHA256 `c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269`。[结果](boot_deploy_01/result.json)与backend.jsonl保存写前／后依据；boot.py、full_lap_capture.arm及push_capture.arm写前后均不存在，未改动原始采图组或许可。部署进程退出0，最后查询running=false，连接／断开soft reboot保留终端。

本次没有runScript／手动执行入口，没有电机启动、供电改接、物理断电重启、Git上传或00摘要更新。**已完成的是新启动文件写入与回读；物理冷启动仍待主控操作。** 下一步保持电机动力断开、STM32 DAPLink供电与Keil Run，只拔K230电脑Type-C约5秒再插回，至少等待30秒、不按KEY；主控回报完成后只读下载新编号启动日志。现有SD的`check_0001.jsonl`为上轮RAM运行，不能用它冒充本次上电验收。电池供电测量及新电池动力试验仍待条件具备。

## USB断电重接后的自动启动：一轮通过

主控对前述“电机动力隔离、DAPLink继续供STM32且Run，只拔K230电脑Type-C约5秒再接回、等待至少30秒、不手动运行”的具体操作回复“已重启”。据此记录主控已执行物理断电重接；没有电压波形、单独录像或精确断电时长，不额外补造。

随后执行[只读日志接收](read_boot_after_power.py)：COM10连接后报告running=false，读取会话未发runScript／stopScript／写文件；连接原始输出有soft reboot但没有BOOT CHECK LOG标记。板上main.py仍为已授权SHA256，目录只有check_0001与check_0002，旧RAM组check_0001的SHA256保持。完整下载新[check_0002.jsonl](cold_boot_power_01/check_0002.jsonl)，48003字节，SHA256 `1d7e40fe358686818a9000f8e0622b1a7356529a42aa88166795c0a309d19654`；begin至completed完整，143帧全部wire_valid／drive_allowed=false。

本轮算法46..57ms，最大启动间隔168ms、to_send最大87ms；保存日志的磁盘I/O及GC影响包含在帧间隔内，不能把算法耗时等同端到端周期或据此认定场地可连续循迹。[结果与会话事实](cold_boot_power_01/result.json)、backend.jsonl与终端一并保存。

结合主控物理操作反馈、新编号持久化日志与只读接收证据，验收**当前电脑USB供电下K230的10秒禁止驱动main.py自启动一轮通过**。不外推为两板电池供电、动力中断源保护、真实视觉或一圈通过。STM32从上一轮已确认339／336以后，RAM日志版144 PATH＋2 STOP、冷启动143 PATH＋2 STOP，若期间未复位且无其它发送，预期累计accepted630（0x276）／received623（0x26F）；尚无本轮实值。下一步主控最后核对state／reason0、左右PWM0、g_lap_uart_errors及五类分项0，不按KEY、不换供电；之后按明日清单补仪表与新电源／场地验证。当前10秒诊断结束不持续发送路径，不作为比赛运行固件。

## 冷启动后STM32故障原图：本轮跨板通信未通过

主控随后提供[主状态原图](cold_boot_uart_fault_01/lap_fault_watch.png)与[UART总错误原图](cold_boot_uart_fault_01/uart_errors_watch.png)。直接读值：g_lap.state=6／LAP_FAULT、reason=10／LAP_TRANSPORT、run_since0、received0x26F=623、path_at0x001B6561、rejected／duplicates／starts_rejected0，左右目标／RPM／PWM均0、path_valid0；g_lap_uart_errors=2。[结构化核对](cold_boot_uart_fault_01/review.json)保留所见与未知分项。

623包与已知三个发送阶段的累计预期吻合，说明完整结果包计数相符；这不等于无硬件接收错误，也不能证明错误发生在某个具体包或电源边沿。当前固件任一UART硬件错误或软件环满都会上报传输故障，主循环锁定LAP_TRANSPORT并撤PWM；截图支持零输出／未进入RUN，不以此扩大为动力中停止实测。主控尚未提供错误分项、first／last_mask及发生时间，不据2次总数直接判断是过载、断电噪声、接线或调试暂停。

原K230新编号日志仍支持其自动入口与本地运行通过；**本轮两板冷启动后的STM32通信状态验收未通过，缺陷保持未解决**。保存原现场，指导主控不复位、不按KEY、保持动力断开与Keil Run，展开g_lap_uart_diag提供overrun／noise／frame／parity／ring_full、first_mask／last_mask、first_at_ms／last_at_ms及g_speed_ms。此步没有重新连接／运行K230、复位／暂停STM32、改源码或清零计数，也不放宽任何错误停车保护。收到分项及时间后才决定隔离复测或修复。

### 错误分项已确认：两次FE，复测尚未开始

主控提供[诊断原图](cold_boot_uart_fault_01/uart_diag_watch.png)：overrun0、noise0、frame2、parity0、ring_full0；first_mask=last_mask=4；first_at_ms=0x001AF2D1（1766097ms）、last_at_ms=0x001AF2FE（1766142ms）；isr_max_cycles=0xE3（227cycles）；g_speed_ms=0x0025083F（2426943ms）。结构化值、图像SHA256与换算保存于[diag_review.json](cold_boot_uart_fault_01/diag_review.json)。两次FE相隔**45ms**，首次评论口头误写29ms已立即更正，正式计算采用45ms。若内核仍为此前已确认16MHz，ISR峰值约14.1875µs；本图没有单独展示当前clock_hz，不将此条件换算当新的时钟测量。

[ST RM0090 USART章节](https://www.st.com.cn/resource/en/reference_manual/rm0090-stm32f405415-stm32f407417-stm32f427437-and-stm32f429439-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)将FE定义为预期时点未识别到停止位，可与失同步或过多噪声有关；这不直接指明本车电源／接线／波特率哪项为根因。当前图中硬件NE标志统计0也不排除导致FE的瞬态电平异常。本轮没有ORE或软件环满证据，不沿旧12次ORE问题继续修改中断优先级。

若两张STM32图同属未复位的启动周期、旧path_at确对应check_0002的最后帧，last_error到最后path_at相隔29283ms；K230该组第一到最后帧启动间隔累计9993ms，估算last_error比首帧早约19290ms。该推导支持优先检查断电／上电或UART初始化阶段，而不是直接认定10秒相机发送期间持续出错；不同板时钟未同步、没有波形或拔插瞬间读数，**触发阶段及电气根因仍待隔离复测**。

原图与首次故障现场已归档，接下来允许做新的隔离实验：K230维持现有USB稳定供电且脚本已结束，电机动力保持断开；主控仅在Keil对STM32执行Reset CPU→Run，等待5秒，不按KEY、不重启K230、不运行新发送脚本。先核对g_lap.state／reason0、received0、左右PWM0、UART总错误／五类分项0及g_speed_ms递增，再逐项安排稳定发包、仅断K230电源、上电三个阶段。此复位是保留原证据后建立新实验基线，不是通过清零既有错误宣称修复；STM32／K230固件均保持原字节。

### 隔离阶段1：稳定物理供电下重新发送

主控对上述“仅复位STM32并Run，保持K230供电，等待5秒取空闲零基线”回复“符合”。据具体预期表记state／reason／received／左右PWM／UART总数与五类分项均0、g_speed_ms递增；这是新实验人工反馈，没有独立截图，不覆盖此前两次FE失败证据。

随后在K230物理USB供电不变、动力隔离、无KEY条件下执行[uart_isolation_probe_01](uart_isolation_probe_01/terminal.txt)：COM10连接后报告空闲，旧9秒探针依次发送0／+600／−600无效PATH共180个，再STOP，正常DONE退出、进程退出0。未写main.py／许可／固件，未发START或有效路径，也没有物理拔插K230。官方后端连接／runScript／断开产生soft reboot，原始终端保留；本阶段因此覆盖后端软件重启／UART初始化／发包／清理的组合，若复现仍不能仅凭总数把错误归于纯数据发送。

[执行哈希](uart_isolation_probe_01/run.json)与原始源码配对保存，[实验条件／预期](uart_isolation_probe_01/review.json)单独区分人工空闲基线和未回报的接收结果。下一步先读取本轮STM32 accepted181／received180、state／reason0、左右PWM0、path_valid0、UART总数及五类错误0，特别frame0。当前K230发送完成不等于该预期已通过；暂不再次复位或拔K230电源，不改任何错误锁定策略。

主控随后对本轮具体预期表回复“符合”：按人工反馈确认accepted181／received180、state／reason0、左右PWM／path_valid0、UART总数及五类分项0（frame0），[反馈依据](uart_isolation_probe_01/operator_feedback.json)归档。该轮稳定物理供电下的后台连接／软件重启／UART初始化／发送／清理组合未复现FE；这只是本轮通过，不代表此前冷启动故障已修复或所有软件重启均无影响。

### 隔离阶段2准备：仅断K230物理电源，暂不上电

以本轮错误0／frame0／state0为基线，安排主控保持电机动力电池隔离、DAPLink持续供STM32且Keil Run；仅拔掉K230电脑Type-C，保持拔开约5秒，不接回、不复位STM32、不按KEY。读取g_lap_uart_errors、frame及g_lap.state／reason；如变化，保存g_lap_uart_diag首末mask／时间与g_speed_ms原图。此阶段助手不连接K230，不发包、不改变main.py／固件，分开观察断电与上电，见[阶段计划](uart_isolation_probe_01/power_off_stage_plan.json)。当前只完成计划与前基线归档，实际拔线和结果等待主控回报，不提前认定触发阶段。

### 隔离阶段2结果：仅断电阶段已复现FE与锁定

主控按上述“仅拔K230、保持拔开、不复位STM32”的指令返回三张原图：[错误总数](uart_power_off_01/uart_errors_watch.png)、[分项](uart_power_off_01/uart_diag_watch.png)、[状态](uart_power_off_01/lap_fault_watch.png)。图证直接确认UART总数3、frame3、overrun／noise／parity／ring_full0；首末mask4，first_at_ms=0x0007FCC6（523462ms）、last_at_ms=0x0007FCD2（523474ms），3次事件跨度12ms。state6／LAP_TRANSPORT10、run_since0、received仍180、左右目标／RPM／PWM0、path_valid0，steering仍−600。[结构化结果](uart_power_off_01/review.json)与image_hashes保留原始字节来源。

由主控确认的稳定发包后0错误基线，到本次只断K230电源后的FE3／锁定，**已将可复现触发阶段缩小到K230物理断电过程**。没有示波器／电源实测，不将其直接认定为某个RX瞬态、反灌、电压跌落、特定线束或芯片故障；上电阶段是否另外增加错误仍待单独观察。也不能把frame3解释为丢失3个协议包；received180保持，仅说明本轮未新增完整PATH。

传输错误锁定与零PWM符合当前既定保护策略；无需为使断电后错误保持0而忽略FE或自动解除故障。此次没有RUN，不能替代动力中拔源的实际撤驱动／停车验收。正常准备流程应另验证“K230先启动稳定，再人工复位STM32、重做校准”的可操作性；两板共电源同时启动／复位时序仍需实测，不能直接声称该顺序已解决正式场地问题。

下一阶段仅恢复K230：主控保持电机动力断开、DAPLink供STM32且Run，接回K230原电脑Type-C，等待至少30秒，让已授权10秒无驱动main.py执行并退出；先不复位STM32、不按KEY、不手动运行／连接CanMV。回报UART总错误／frame是否从3增加及state／reason。现有故障锁定预期继续6／10，不因接回电源自行清除；若错误增加，再保存首末mask／时间。取得这一阶段值后，再安排恢复零基线验证；本轮助手不连接已断电K230、不改任何代码或供电线束。

### 隔离阶段3结果：重新上电未新增错误，保护没有自动解除

主控对上述“接回K230、等至少30秒、不复位STM32、不按KEY”的步骤回复“仍为3；保持锁定”。按该具体上下文记UART总数／frame仍3、state6／reason10继续锁定，没有本轮独立STM32原图。相较断电后的基线，本轮被观察到的重新上电没有新增错误，保护未自动解除；不将一轮观察泛化为上电永不触发FE或故障根因已修复。[人工反馈与边界](cold_boot_power_02/stm32_feedback.json)归档。

在收到主控反馈后再只读连接K230核实自启动，避免助手会话改变先前观察条件。复用日志读取器并增加受限输出目录名／after-log参数，未请求runScript／复位／写板上文件。COM10报告空闲，main.py哈希保持；新组仅[check_0003.jsonl](cold_boot_power_02/check_0003.jsonl)，47669字节、SHA256 `c9e874a0c04ebb6024492505e0251379a27cc0c762eb20bb3ffd11b5b2c48910`，142帧完整completed、全部wire_valid／drive_allowed=false；算法45..58ms、最大帧间隔137ms，最大发送前年龄87ms。旧RAM日志字节未变，连接输出没有BOOT CHECK LOG标记，见[接收结果](cold_boot_power_02/result.json)。这证明本轮K230重新上电实际执行了10秒自检，并非仅电源灯亮；仍不是电池供电或STM32新增包数验收。

到此隔离顺序得到：稳定物理供电发送180个PATH时0错误；只拔K230后出现3次FE并锁定；接回K230跑完自检后错误仍3、故障保持。下一步验证实际恢复准备顺序：保持K230现有USB稳定供电且自检已结束、动力隔离，仅由主控在Keil Reset CPU→Run复位STM32，等待5秒、不按KEY，检查state／reason／received／PWM／UART总数和五类分项0、g_speed_ms递增。该步骤是在保存失败原件后建立新实验基线，不能把计数清零称为修复；也不能当连续视觉或比赛启动流程已完成。两板固件／main.py、错误锁定策略与供电线束不改。

## 本轮无动力检查收尾：恢复空闲基线通过

主控对上述“保持K230稳定供电，STM32仅Reset CPU→Run，等待5秒，不重新下载不按KEY”的具体预期表回复“是”。按人工反馈确认state／reason／received／左右PWM／UART总数及五类错误均0、g_speed_ms递增；[反馈原意与验收边界](recovery_idle_feedback.json)保存，没有单独STM32新图或自动读回。这证明当前无动力条件下，K230稳定后人工复位STM32的空闲恢复操作通过一次；不声明先前FE电气故障已修复，不声明自动解锁或比赛准备流程已全部验证。

本轮已完成的软件／无动力硬件检查闭环，保留旧源码／旧失败／真实main.py备份与新日志。此后不再连接／复位板卡，不发新包或启动电机；动力隔离条件保持。I-02仍进行中，后续必须补新电池端电压／驱动5V、两板车载逻辑供电与冷启动、新电池起转重复性／差速／动力中停止、真实场地识别及连续一圈。当前K230上电入口只有一次10秒无驱动日志诊断，STM32保持09版3秒，均不能据此直接放行地面试跑。

明日11-11接续顺序已置于[pre_field_checklist.md开头](../../hardware_preparation/pre_field_checklist.md)：先借仪表／电气与结构，再车载逻辑供电，再悬空动力和停止，再实际场地无动力视觉及基于证据的运行版本，最后短线／单弯／一圈。记录路径、现场表、原始备用固件／脚本清单均在本目录；多模块未提交修改保留，不上传、不改分支、不替00更新全局摘要。比赛基本60分完赛／少触边与报告20分证据仍为支撑目标，没有实测比赛得分。
