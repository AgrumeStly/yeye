# I-02：2026-11-12恢复执行

责任：主控人工接线／KEY／Keil；本对话整车联调执行，不接替00。目标仍为比赛第三部分、图1和评分表基本功能60分对应的顺时针自主一圈≤5分钟、降低触边／完全出界风险，不把软件检查或分段当完圈。

主控表示重新摆好，并已继续进入Keil调试Run；撤销上一轮暂停。分支codex/current-version-20261025、HEAD a0733a8685db4c2b497539303bfe87fe1c1ebfe5实查一致，大量原有修改／未跟踪成果保留，无清理／回退／切分支／上传。沿用grill-me清晰任务直接执行，既有协作及授权边界不变。

本轮暂未提供专用CanMV连接器，发现工具清单中没有CanMV能力；按已确认回退方案复用官方0.9.10后端助手，不绕过其许可门槛。仅重新枚举端口：K230 COM10（1209:ABD1），DAPLink COM9（0D28:0204）；端口存在不代表版本、运行状态、校准或供电已验。

先询问上次R6试验是否按KEY／实际结果和旧快照是否仍在；当前动力接通／隔离、悬空、相机安装、逻辑供电及Keil状态读数待主控反馈。尚未连接K230或发送路径，不先Reset／重跑覆盖潜在结果。独立推进持续main草稿日志边界模型；实板RAM／刷盘性能、真实备份与部署、车载带载和冷启动、地面短线／单弯／整圈仍未验。

主控提供[当前零基线原图](baseline_watch.png)，并说明已复位、重新编译／下载、相机安装等不变、驱动OFF、仍DAP／USB供电。截图为revision0x02110009、fault0、state0／reason0、received／path_valid／PWM0。旧R6未回报试验的RAM快照现已无法取回；是否实际按键及表现仍不补造。主控随后确认悬空，以及run_ms3000／phase0／error0／UART0符合；只安排接新电池并驱动ON、保持静止，不按KEY。复位后的轮侧校准确需恢复，不重做旧完整台架。

官方助手只读status已正常连接COM10，识别K230D Lite128M／v1.8-0并确认running=false，随后关闭会话；未发路径／START或写文件。连接／断开soft reboot终端原样保存于hardware_status_01。新增[持续入口27项模型检查](runtime_entry_checks_01/checks.json)通过：精确匹配草稿字节，真实封包许可／超时／CRC，日志编号及原件保留，异常记录／退出及无自动重试，缺SD／配置错误先于相机拒绝；相机被替身替换，不当实板耗时、供电或部署通过。

主控先对接动力后静止的步骤回复“确认”，本对话据此只安排一次左轮500ms校准。主控随即纠正“刚才忘开驱动on了，重来”，因此以最新反馈为准：该次驱动实际未ON，左校准不记通过，不宣称本轮映射已建立。已要求不再按KEY、不先复位，只读取state/reason、phase/error、UART与当前PWM以保留本次可能的无反馈／校准失败信息。实际停因待读数，不从忘开驱动推定固件已报哪一种错误。

主控随后明确要求“重来一遍”，本对话已先保存忘开驱动的失败事实，未取得独立故障枚举。按授权重置流程，主控依次确认：驱动OFF／悬空／USB逻辑供电下Reset CPU→Run5秒零基线（state0/reason0、phase0/error0、PWM0、UART0、run_ms3000）；驱动ON仍静止；第一次左轮前进500ms／右轮不动反馈“正常”；第二次右轮前进500ms／左轮不动以及phase2/error0/state1/UART0/run_ms3000反馈“符合”。只恢复复位后的必要校准，未重做整套台架。

据此启动runtime_r6_suspended_01：冻结R6真实相机、120秒输入等待，当前主板09仍单次3000ms；主控人工KEY，无START／烧录／main.py改写。等待有效双边后才安排一次实际运行，结果尚未取得。使用官方后端助手，同一端口单一所有者，不并开其他脚本。

### R6真实相机悬空三秒初验通过

主控提供[原始快照](runtime_r6_suspended_01/last_run_watch.png)并反馈“符合”：valid1／3000ms／LIMIT11，左右目标40／40RPM，末次反馈40.739109／39.5514641RPM，撤驱动前PWM各19.6%，起步补偿各1样本。按本轮两轮向前、自动停稳、当前两PWM0／UART0的明确操作上下文作人工确认，细分来源见[stm32_review.json](runtime_r6_suspended_01/stm32_review.json)。真实相机输入，不是fixture；不外推连续误差、大幅差速、地面或整圈。

主控随后明确确认动力已隔离：驱动OFF、XT30断开、仍DAP／USB供两板，不按KEY。原120秒助手已结束后，才顺序启动runtime_log_probe_01：从固定白名单持续草稿仅改30秒与ALLOW_DRIVE=False，日志包装／真实相机／清理流程保持，先只读备份当前main.py／boot.py，再实际运行并读回新日志。未覆盖main.py，运行结果待完成，未因主机27项模型通过而宣称板上刷盘性能通过。

### 持续入口日志实跑与当前main备份已取得

[runtime_log_probe_01/result.json](runtime_log_probe_01/result.json)正常退出：30秒禁止驱动真实相机运行完成，读回/sdcard/lap_runtime_logs/run_0001.jsonl，15049字节、begin至completed完整、45行，其中43条算法日志样本／最高index390，前4帧无效，其余样本有效候选；所有日志wire_valid／drive_allowed=false。算法37..58ms、封包前总耗时39..75ms、日志相邻周期58..98ms，见[统计](runtime_log_probe_01/summary.json)；不是总帧统计，不代表600秒实跑或有效动力通过。

已分块保存当前main.py真实34887字节及哈希c0eeed8e60c72cc87d8c3128146b4c2b5e884266e4c4e269490e6be8c4a74269，boot.py不存在。写盘验证后重读main字节未变；本次只新增独立编号日志，没有写main／boot或发START。

持续候选仍为35638字节、SHA256 397d6a7d91983bffe7655704e727e458ca35f2b0910982dcdf53ad72e8aa5db1；已经准备[具体部署／备份／回读／回退方案](runtime_deployment_plan.md)和受限工具。新增[11项假Session写入边界检查](runtime_deploy_checks_01/checks.json)通过：确切候选授权、运行中／未知当前main／未知boot先拒绝，备份原件、固定唯一写路径及回读不一致拒绝。工具未在板上执行写入，等待主控对这一具体候选授权，不把“继续”当覆盖main的同意。

完整120秒R6相机窗口日志另有无效段（845..846、984..1009）及短历史／单边样本，详见其summary.json；本次三秒RUN在此前已经正常结束。不能据三秒通过声称整窗每帧稳定，也不能在没有对应原图的情况下擅称无效段都是操作遮挡。后续短线／弯试需按实测确认稳定性，保留无效即停的保护。

### 持续main实际部署及授权更新

主控先对具体候选回复“同意”，随后明确“可以自动修改”。该新授权在本I-02范围内允许后续必要main调整自动备份、修改和回读，不再逐次询问；此前反复确认的边界被替代。人工接线／KEY／Keil下载，不自动START／烧录，不上传或跨聊天等边界保持。

[runtime_deploy_01/result.json](runtime_deploy_01/result.json)确认：写前当前main与本次真实10秒入口备份字节相同，固定R6候选35638字节写入/sdcard/main.py并分块逐字节回读一致，哈希397d6a7d91983bffe7655704e727e458ca35f2b0910982dcdf53ad72e8aa5db1；boot.py仍不存在，写后running=false。未runScript或发送START、未烧录主板、未自动接电。旧10秒main的本次写前原件和新回读文件均另存。

当前安排仅主控K230电脑USB物理拔开约5秒再接回、至少等待30秒，驱动OFF／XT30断开／STM32 DAP供电Run，不按KEY。之后只读新编号持久日志，既不runScript也不写文件，以区分上电执行与RAM手动执行；等待主控完成反馈，不提前记冷启动通过。

只读cold_boot_readback模式已准备，限定当前候选哈希、固定启动路径和新编号日志，要求有真实算法帧；非KeyboardInterrupt的运行失败不记正常，IDE取证可能中断的边界另列。尚未执行该读回，因为没有收到物理重启完成反馈。另只询问现有完好万用表／可调5V或车载5V充电宝器材，不指示改线；驱动5.20V容差及两板带载仍待实际依据。当前没有助手后端或脚本由本对话运行；板上已部署持续main，主控物理重启后可能自动运行，但未取得反馈前不推定其状态。

### USB物理冷启动：自动入口已证实，取证中断原样保留

主控回复“已重启”，按前述仅K230 USB拔开5秒接回、等待至少30秒、动力隔离及DAP供STM32 Run的操作上下文确认。本对话随后只读启动文件和新编号日志，未发runScript、写文件或START。

[runtime_usb_cold_boot_01](runtime_usb_cold_boot_01/review.json)得到run_0002.jsonl新日志45228字节、SHA256 54207b6d6b856dacc6f578fbf9690e5ecdb6814fae0845c5dfa8428ab6ae372d；begin声明600000ms／真实相机／有效PATH许可／无自动启动，131条算法日志样本、最高index1280，128条样本wire_valid=true，只有初始1..3帧无效；算法43..71ms、日志周期68..120ms。当前main SHA256仍397d6a7d…e8aa5db1，boot.py无。主控物理反馈、新编号持久日志和本次无runScript／写入共同支持USB配置下持续入口上电自动运行，不是手动RAM替代。

原助手退出1、result.json passed=false保留：读取会话连接后、首次文件读取前，官方后端产生Exception: IDE interrupt，终止正在运行的主循环；板上日志末行也记录Exception('IDE interrupt',)。检查器原仅接受KeyboardInterrupt，误将此明确IDE中断分成程序故障。本轮修正为仅在异常确切类型与本次终端证据同时匹配时归类取证中断；相机／SD等其它错误仍拒绝。新增10项离线核对通过，原始失败不覆盖，新结论单列review.json，不重启／重跑取证。

本次不能称600秒连续运行通过或自然completed，也不能据K230日志证明STM32跨板冷启动无故障、车载电源或一圈。工具连接后running=false，会话已关闭；主控继续动力隔离、不按KEY，不先Reset，待读state/reason、UART总数／必要分项和PWM，保存此次主板结果。此前已知单独K230断电可触发FE锁定，不能提前补造本次实值。完好仪表及可用独立5V器材仍待主控反馈，尚无改线动作。

### 本次STM32冷启动传输故障原件与供电准备

主控提供[主状态](runtime_usb_cold_boot_01/stm32_fault_watch.png)、[UART总数](runtime_usb_cold_boot_01/uart_errors_watch.png)、[UART分项](runtime_usb_cold_boot_01/uart_diag_watch.png)：state6／TRANSPORT10、received0xCE3=3299、steering43／bend343、path_valid0、目标／PWM0；UART总2、frame2、其余四类0，首末mask4，843465／843467ms，相隔2ms，ISR峰值227周期。结构化值及边界见[stm32_review.json](runtime_usb_cold_boot_01/stm32_review.json)。旧run_since105090ms不证明本次进入RUN；本次动力隔离，不当运动中停车新证据。不能把K230上电自动运行通过改写为STM32跨板冷启动零故障通过，也不把本次FE精确归因到某一电气瞬间。

主控再次确认实际车载接法为杜邦线接驱动稳压5V，两板型号和方案沿用；另确认有完好万用表。按原方案分级负载验收，不要求另购器材。首先主控已确认全断电准备：驱动OFF、XT30断开、拔DAPLink和K230电脑USB，两板无供电；尚未接驱动5V或测量。主控询问是否关闭Debug，已指导Keil Debug→Start/Stop Debug Session（Ctrl+F5）退出并保留工程，Flash固件无需重下。接线和测量下一步逐项执行，不推定已接好或已取得电压。

### STM32单板负载：5.182V，无异常

后续指导主控在全断电下标记隔离两组电机六芯插头、临时断开UART T/R、仅驱动标5V/GND接STM32电源5V/GND，K230不供电、DAP及电脑USB保持断开。单次测量步骤为表笔置STM32输入端、接新电池XT30／驱动ON，稳定约5秒读数，随后OFF并断XT30、不按KEY。主控回复“5.182v”“无异常”，按该明确测量上下文记录STM32输入端单板负载电压 **5.182V**，来源人工读数，无仪表照片／纹波／瞬态记录；电源灯状态未单独描述，不补造。

此值不是K230接入后的电压，也不证明两板带载／相机持续运行／电机动态时电源合格。旧5.20V空载值保留，不能据两次读数差0.018V作精密压降／稳压率或仪表精度结论。下一步依据K230供电路径资料准备其受限负载核验，不擅称5.182V已经满足厂家整板容差。

### 两板车载供电支路已接，负载直流读数5.176V

依据[电源输入资料核对](power_input_basis.md)，5.182V低于已查主要输入路径器件正常工作上限，可继续动力隔离的受限负载核验；不把器件范围当整板正式容差。主控随后对全断电下从驱动稳压5V/GND另分一路到K230 5V0/GND、保留STM32支路、电机插头／UART T/R／DAP及USB均断开、先不上电的步骤回复“完成”。

本次测量明确要求表笔置K230输入端、接XT30／驱动ON，不按KEY，上电约5秒及30秒记录电压和电源现象，随后OFF／断XT30、暂不接USB。主控反馈“稳定5.176”，按该两板负载上下文记录 **K230输入端稳定约5.176V**，人工读数。未单独给5秒／30秒两笔原始值、仪表照片或灯／重启现象，不补造两次相同数值或完整电气验收；也不据0.006V差异计算稳压率。

本轮两板供电来自新电池→驱动稳压5V→各自杜邦支路，电机插头和UART T/R仍隔离；尚不能据电压读数宣称K230相机已经运行。计划只读本次电池供电新日志（预期run_0003），随后恢复电脑USB会产生后续编号日志，必须分别取回，禁止拿后续USB日志代替电池供电原件。主控完成OFF／断XT30后的实际状态及通电时灯／有无异常仍待明确反馈，暂不自动连接／重跑。

### 电池供电持续相机日志已取回

主控对通电时两板电源灯／有无反复重启或异常回复“正常”；随后按驱动OFF／XT30断开下移除K230 5V0杜邦供电支路并绝缘、仅接电脑USB，STM32 DAP／USB不接、电机插头和UART T/R保持隔离的取证接法回复“接好”。

本次明确选择预计电池启动编号3，未用“最新文件”代替。重新枚举K230 COM10，受限助手只读[runtime_battery_cold_boot_01/result.json](runtime_battery_cold_boot_01/result.json)，run_0003.jsonl为100918字节、SHA256 cdd5e0d59cef349d0ffe96b1466900f4ee581395c537bfb94dfdb3030aecfd2a；后续USB启动run_0004.jsonl另存11590字节／哈希0b43d8918ead73aa89f328c584ced3e0380f1acd1cee55f68d9ad8b5ece9dfba。本会话无runScript／写入／START，main哈希仍397d6a7d…e8aa5db1，boot.py无，返回正常，后端已关闭。

电池日志294条算法样本、最高index2640，262条有效；算法21..89ms、日志周期41..111ms，见[summary.json](runtime_battery_cold_boot_01/summary.json)。无failed事件；本次按操作断电截断，没有completed，不当自然600秒结束或完整帧数。无效段为1..5、34..58、428..429，未取得对应原图，不猜成全由操作遮挡；这些若发生在RUN仍应停车，不能据多数有效宣称连续行驶稳定。

结合主控明确供电切换顺序、稳定约5.176V和电源现象正常，取得两板静态负载与K230电池供电自动相机运行的初验。UART T/R当时断开，**尚未验证两板共电源UART冷启动接收／零故障**；电机拔开，未验动态电源或地面。当前主控仍需恢复全断电下K230 5V0支路和T/R，同时明确去除DAP供电输出，只保留SWD信号／共地用于后续Keil核对；不自动接电、不自动烧录或启动。

### 恢复UART后的两板共电源上电

之后逐步指导主控：全断电、拔K230电脑USB，恢复K230 5V0/GND车载供电支路和UART T→STM32 A03／R→A02／G共地、V不接；电机插头仍隔离、DAP不接。再单独指导去掉DAP→主板5V供电线并绝缘，3V3电源输出也不接主板电源，保留原SWD信号／GND／复位接法。主控分别回复“好”，记录为步骤应答，不当独立接线照片或逐线验收。

在“车载接线及DAP电源隔离完成后才执行、电机插头仍断、K230和DAP的USB不接、新电池XT30接回／驱动ON、等30秒、不按KEY”的明确条件下，主控反馈“正常”，按操作上下文记录两板共电源上电外观无异常；此轮驱动先保持ON。UART实际接收、错误与PWM尚未读回，不能只看灯验收通信。下一步仅接DAP USB，在K230电脑USB不接、DAP供电输出已隔离的前提下进入Keil读取；不点Reset或Download，若调试入口自动复位则按实际记录，不能混写未经干预的纯冷启动状态。

主控按“DAP供电输出已隔离、只接DAP电脑USB，K230电脑USB仍不接；Keil LowSpeedLap进入Debug→Run、不主动Reset或Download、不按KEY；读revision/run_ms/state/reason/phase/error/UART/PWM/received递增/path_valid”的步骤回复“符合预期”。按人工反馈记录进入调试后的revision09／run_ms3000、接收递增、有效路径及UART0／两PWM0；没有新独立截图或逐字段数值，state/reason/phase/error未单独实报，进入Debug是否自动复位亦未明确，不据此声称未经调试干预的共电源冷启动零故障。

电机插头仍隔离，本轮尚未进行车载供电下的动力校准或RUN。下一步只恢复电机接线：驱动OFF、断XT30并拔DAP电脑USB确保全断电后，按原轮侧标记接回MOTOR-A/MOTOR-B六芯插头；其它车载5V和UART保持，接好先不上电。之后须重新读复位后的校准起点并完成必要单轮校准，再进行一次3000ms真实视觉联动及电源现象核验，不重做五姿态或完整固定输入台架。

### 车载供电下电机恢复与校准前基线

主控对全断电后按原标记接回电机插头的步骤应答“好”；随后在确认两轮完全悬空、接新电池XT30／驱动ON、等待30秒、K230及DAP电脑USB暂不接、不按KEY的条件下回复“确认”，按实际操作上下文记录上电静止和电源现象正常。之后仅接供电输出隔离的DAP作SWD，K230保持车载供电且电脑USB不接，Keil LowSpeedLap进入Debug→Run，不主动Reset／Download。

主控提供[配置原图](onboard_visual_motor_01/config_watch.png)：straight_rpm40／run_ms3000／min_feedforward200，并对明确预期表revision09、state0/reason0、phase0/error0、UART0／两PWM0、received递增／path_valid1回复“符合”。[基线来源](onboard_visual_motor_01/baseline_review.json)区分截图与人工确认；未独立验证Keil入口是否自动复位，不当纯冷启动原始零故障。当前未发新的电机动作，只准备本次上电后必要的左、右各500ms校准，再单次真实相机联动，不重复全套旧台架。

主控随后对左轮500ms校准回复“符合”；对右轮500ms校准、phase2/error0/state1/UART0回复“符合”。在两轮悬空、Keil Run、当前双边path_valid1/history0/single0/UART0的明确条件下只安排一次人工KEY，主板限3000ms、真实相机持续main，不重新发fixture或START。

主控提供[本次停止前快照](onboard_visual_motor_01/last_run_watch.png)，反馈“轮子正常转”：valid1、elapsed_ms3000、LIMIT11；左右目标31.7614498／35.4585495RPM，末次反馈30.2387314／36.6081734RPM，撤驱动前PWM19.5%／19.0%，起步补偿各1样本。本次为车载逻辑供电配置下的一次真实相机悬空RUN及定时撤驱动证据；当前PWM0／UART0、物理停稳、两板有无重启及动态电压尚未单独回报。原件／人工来源及边界见[stm32_review.json](onboard_visual_motor_01/stm32_review.json)，不外推连续误差统计、地面或整圈。

### 地面准备前发现相机输入停止，禁止启动并修复生命周期

主控先对两轮停稳、两板未重启、PWM0/UART0、phase2/error0以及received递增/path_valid1预期表回复“符合”，随后明确纠正path_valid0和received不递增，以最新实读为准。[新原图](runtime_window_stop_01/stm32_review.json)确认received7394、WAIT1／KEY1、UART0、目标/PWM0、path_valid0。三秒LIMIT原结果保留，未安排下一次KEY或地面；不能把多数字段符合误作当前路径仍许可。

原部署main有600000ms输入期限，到期finally发送STOP，与当前待机形态一致，但需读取日志确认。已保存原图；主控按驱动OFF／断XT30／拔DAPUSB、全断电后移除K2305V0杜邦供电线并绝缘、仅接K230电脑USB的取证接法回复“接好了”。断电会清校准，后续只补必要两次单轮校准，不重复整套台架。

已独立生成持续相机候选runtime_continuous_candidate_02，保持R6检测器／协议／异常清理，取消相机会话到期；不改STM32三秒／五分钟限制、人工KEY或任何故障保护，不自动START／重试。候选哈希838c5e9a4d14d42840c54526b1f3c4d4a848e93654de8bca5faf45f85fb2968f，34项有针对性模型检查通过，覆盖超过600000ms仍供图、受限探针仍能限时结束、默认禁驱动及日志／故障边界；未部署，不把模型当实板。正在只读编号5及后续日志，待确认实际停因。

实际取证先读run_0005后，run_0006为875969字节，超过助手原512KiB文件上限而退出；原目录board_readback/result.json失败保留，没有重跑相机。仅把固定日志路径的读取上限改为8MiB，启动脚本仍512KiB、32KiB分块不变，再只读明确编号6至board_readback_02。

[run_0006原件与期限复核](runtime_window_stop_01/board_readback_02/lifetime_review.json)确认begin duration600000，最后为completed，无failed；最后记录帧8470仍为当前双边有效、steering91／bend391，与STM32末次路径字段一致。故本次停流是原main会话期限到期并发STOP，非新UART故障／算法在末尾失效。7394为主板本地接收计数、8470为视觉最高抽样帧号，基线和语义不同，不能相减判丢包。整窗记录2588条样本、其中1935条无效，未有全段对应原图，不声称整窗视觉稳定；后续地面遇PATH失败仍须另查真实缺陷。

新持续入口以DURATION_MS=0明确表示相机不按会话时长退出，实际主循环调用被检查的_runtime_duration_elapsed；默认生成仍禁驱动，旧有界候选可精确重建。独立保留R6检测器／协议／所有门槛，异常仍STOP／退出且无自动重试。34项模型检查见runtime_continuous_checks_01，超过十分钟／半小时仅为合成时刻门槛检查，不是实板长测。

[runtime_continuous_board_probe_01](runtime_continuous_board_probe_01/result.json)从同候选只改30秒／禁驱动实际运行，读取新run_0008完整日志，43条样本／最高index400、算法43..73ms、周期72..121ms、全部wire_valid／drive_allowed=false，正常completed，旧main字节未变。部署工具新增固定continuous-v2白名单及真实前版备份，13项假Session门槛检查通过，未使用任意源文件／远端路径。

依主控已明确的自动main修改授权，[runtime_continuous_deploy_02](runtime_continuous_deploy_02/result.json)已写入35926字节，SHA256 **838c5e9a4d14d42840c54526b1f3c4d4a848e93654de8bca5faf45f85fb2968f**，完整回读一致，前版397d6a7d…e8aa5db1另存本次真实备份；boot.py无，写后running=false，未runScript／START或烧录STM32。当前main已不再是十分钟入口。新版本车载上电／超十分钟实际运行／地面仍待验；恢复USB隔离和车载5V接法后仅补必要校准，不重复全套台架。

### 持续v2恢复车载运行，准备首轮地面短直道

主控对拔K230电脑USB、全断电后恢复其5V0/GND车载支路、其它接线保持、两轮悬空、先不上电的步骤回复“完成”；随后确认接新电池XT30／驱动ON、等30秒、两轮静止且两板电源正常。DAP仍仅SWD不供电，K230电脑USB不接。

本次在进入Keil LowSpeedLap Debug→Run、不主动Reset，且09/3000ms、state0/phase0/error0/UART0/PWM0、received递增/path_valid1条件下安排单次左轮500ms校准，主控回报“符合预期”；第二次右轮500ms及phase2/error0/state1/UART0/PWM0/path_valid1亦回报“符合预期”。按人工确认记新持续入口车载运行的实时许可与本次上电的必要校准，无新的独立截图；未再重复刚才已通过的悬空三秒测试。

下一步先保持车载电源和主控Run，退出Keil调试并移除DAP调试连接，仍悬空、不按RST／KEY；观察绿灯和车轮确保程序仍运行且待机，随后另一步移至赛道直道居中、朝顺时针方向，保留单次3000ms低速限制做地面短直道。比赛约束仍为全车投影在车道内、触边计风险／完全出界失败，短线不能当完圈。首次地面结果尚未取得。

### 后续实际进展：DAP脱开核对与首次地面失败

最新补充：原run_0009及独立USB run_0010均已实际取回；10秒禁止驱动预览保存5张停车位置原图。为解决原始触发采样和对应视觉帧缺失，已具体实现并检查STM3232窗口冻结环，构建短版0B／Track0C（均未下载）；K230只补逐帧时间／序号取证的v3已实际备份／部署读回。软件、禁驱动实板、失败根因与地面恢复严格区分，详见[具体候选与当前接续](ground_straight_01/diagnostic_candidate.md)。当前仅K230电脑USB，车载5V0／UART T/R隔离，驱动OFF／XT30断开／DAPUSB拔开；下一步仅支稳悬空，再安排恢复接线和主控Keil人工下载LowSpeedLap 0B。

原绿灯长灭现象与无复位SWD诊断详见[swd_detach_01](swd_detach_01/record.md)。最初实读phase0，原因未定；脱DAP静态STM32输入5.178V／3V3为3.315V，CPU及接收递增。Keil关闭下仅补两次必要500ms校准，实际phase2／error0／WAIT／PWM0／UART0；脱DAP后周期闪正常获主控确认，不重做整个台架。

正常车高、最终赛道顺时针直道居中且电脑线脱开，主控确认每2秒约400ms双边待机灯后，实际进行一次短直道。主控反馈短距离慢行、左右摇摆、无触边、自停后急闪。无复位取证确认**2044ms LAP_REVERSE5**，当前FAULT6／PWM0／UART及硬件错误0；末次目标6.7677／22.9803RPM，滤波12.2855／28.0351RPM，撤驱动前PWM17.2%／29.8%。原始触发编码器采样未锁存，不能从正滤波值断言误报或指定机械原因。按失败保存，非正常三秒／地面通过／完圈，详见[ground_straight_01](ground_straight_01/record.md)。

主控随后确认驱动OFF／拔XT30／拔DAP电脑USB，K230电脑USB仍不接。原故障已归档，下一步隔离K230车载5V0和UART T/R后独立USB取相机编号日志，分析摇摆；恢复上电须补必要校准，不先盲重跑或放宽保护。
