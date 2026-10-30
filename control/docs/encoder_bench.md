# C-02C：双编码器手转采集与标定操作教程

日期：2026-10-25（北京时间）。维护：主控／01；现场：主控／硬件，02接收记录；00汇总。
当前安装请先看[wheel_mapping.md](../../hardware_preparation/wheel_mapping.md)：2026-10-29主控已互换左右轮，并重新命名物理A=左／B=右；这不等同驱动MOTOR-A/B或软件a/b。**本页10月25日“左a、右b”与标定数值是换位前历史，不能直接当当前轮侧配置。** 旧前进旋转方向现为新轮侧后退，CPR按原轮组身份转移；当前软件通道及原始前进读数仍待对应，推导系数不冒充新实测。本轮只更新文档，EncoderBench原始a/b采集、固件与工程未改。原[C-02C任务](../../project_planning/tasks/C-02C.md)、[实物表](../../testing/2026-10-25_encoder/acceptance_record.md)及[原图](../../testing/2026-10-25_encoder/hand_turn/README.md)保留历史含义，已确认的原软件／手转交付不撤销，也不延伸成新安装动力验收。

本页为2026-10-25补充的初学者详细教程；固件、接线资源与版本不变。先按第1—8步看懂实时计数，再做第9—12步整圈标定。

## 本轮入口与资源

在Keil打开[control/MDK-ARM/encoder_bench.uvprojx](../MDK-ARM/encoder_bench.uvprojx)，唯一目标 **EncoderBench**，版本`g_encoder_bench_revision=0x020C0001`。这是新增独立工程，原六目标和Direct A/B、MotorPwm独立工程均保留且未编辑；不要到旧六目标下拉框找EncoderBench。

| 采集通道 | 驱动板信号→天空星丝印 | 外设／解码 |
| --- | --- | --- |
| 软件a（不自动等于新物理A／当前左轮） | E1A→C06／PC6；E1B→C07／PC7 | TIM3_CH1／CH2，AF2，16位CNT |
| 软件b（不自动等于新物理B／当前右轮） | E2A→B06／PB6；E2B→B07／PB7 | TIM4_CH1／CH2，AF2，16位CNT |

精确排针位置沿用[pin_plan.md八线表](pin_plan.md)。TIM3／TIM4整体用于各自编码器，不与TIM1电机计数器混用。TIM5仅为R1启动等待，退出初始化即停；SysTick为1ms时基、每10ms采样，不增加UART或定时器中断。PA0 KEY（对应WKUP）、USART2 PA2/3、SWD PA13/14和板载资源保留。

EncoderBench从应用初始化开始将PE9／11／13／14配置为普通GPIO低，之后每1ms及异常路径再次清低；不启用TIM1、不链接电机PWM／Direct驱动，不产生任何非零电机请求。**KEY没有试转或清零功能，长按也不会启动电机。** 绿灯正常亮／灭各约500ms；初始化／读接口故障改为约100ms快闪。灯态只代表软件监督，不证明编码器有电或接线正常。

编码器使用`TIM_EncoderMode_TI12`四倍频：两相的上升／下降沿都参与计数。两输入`TIM_ICPolarity_Rising`在这里表示不反相，不能理解成只取上升沿。PSC0、ARR65535、CKD1，输入直连、DIV1，ICFilter=6（fDTS/4、连续6次采样）；当前名义16MHz下过滤窗口约1.5us，实际抗干扰及最高可用边沿速度未测。GPIO内部弱上拉与已有上拉整形配合，采用驱动3V3供电；弱上拉不能代替传感器供电，还可能使未供电输入读高。

## 2026-10-25原安装初版标定结果（历史）

| 物理轮侧／编码器通道 | 车辆前进时原始计数 | 计数方向系数 | 每输出轮一圈（5圈估计） |
| --- | --- | --- | --- |
| 左／a：PC6/7、TIM3 | 增加 | +1 | 1060.8 counts |
| 右／b：PB6/7、TIM4 | 减少 | −1 | 1058.6 counts |

这是主控手转与文字确认形成的初版参数，未集成进软件。后续应用层若要把车辆前进统一为正，可将原始窗口增量分别乘+1／−1，底层保持原始CNT与符号。此系数只对应编码器计数，不决定电机AIN／BIN的前进输出极性。左右圈计数各自保留，不平均成一个常量；原始样本／上下文／限制以验收记录为准，00核对后接续使用。主控无需为本页更新重新下载或再做同向转圈。

## 详细操作教程：先准备，再下载，最后手转

本节按第一次操作编写，不要求使用终端、不改代码、不运行电机。建议先把本页和[验收表](../../testing/2026-10-25_encoder/acceptance_record.md)同时打开，按阶段逐项做；某阶段不符合预期，就停在该阶段保存现象，不跳到下一阶段。

### 第1步：认清本轮要观察什么

电机六根线中，M1／M2给电机绕组供电，V／G给编码器供电，A／B把转动脉冲送出。本轮用手转车轮，让编码器报告转动，**电机不需要通绕组电流**。固件a／b是两套编码器资源名；编码器本身也有A／B两相，这两种字母含义不同。

准备电脑、既有Keil5和DAPLink、原车辆／电机接线、稳定悬空支架、两张小纸条或胶带、笔和绝缘材料。主控在车架标一个“车头→”，再把两个电机线束分别贴为驱动MOTOR-A、MOTOR-B。沿用已确认型号和接线，不重新按颜色猜线序。

UC2继续停用，不参与本轮供电或充电；本页不安排充电器操作。

本轮完成顺序：隔离绕组→下载EncoderBench→无电池核对程序→驱动给编码器供电→分别手转→确认轮侧／符号→每侧3次整圈→断电记录。**不按KEY启动，也不打开MotorPwm复测。** KEY是PA0的WKUP用户键；RST是复位键，两个按钮不能混用。

### 第2步：全部断电，只隔离四根绕组线

主控／硬件先将驱动开关拨OFF，拔电池XT30，再拔DAPLink USB；天空星Type-C继续空着，其它主板电源也断开。等板上电源灯熄灭，再操作线束。开关OFF不等于所有连接点都已断电。

在驱动板MOTOR-A、MOTOR-B电机接口处，按下表处理。只分离绕组端，不把每束六根线整束拔掉：

| 电机端功能 | A驱动端 | B驱动端 | 本轮动作 |
| --- | --- | --- | --- |
| M1，绕组端1 | AO1 | BO1 | 拔开，两只电机各1根 |
| M2，绕组端2 | AO2 | BO2 | 拔开，两只电机各1根 |
| V，编码器电源 | 3V3 | 3V3 | 保留 |
| G，编码器地 | GND | GND | 保留 |
| A，编码器A相 | E1A | E2A | 保留 |
| B，编码器B相 | E1B | E2B | 保留 |

四根脱开的线端分别包绝缘并固定，不让端头互碰或碰到板上其它针。主控→驱动的四控制线、四编码器线和公共GND共九根线继续保留。不要靠重接V／G／A／B改变方向，不剪线、不带电挪母头。

若六针一体壳不能独立分离M1／M2，先由硬件准备可分离的匹配连接；此处保持断电，不用强拔端子或剪线凑步骤。具体线束位置以功能标记和既有[逐线表](../../hardware_preparation/dual_motor_wiring_guide.md)为准；该历史接线页中的旧供电方案不替代本页当前DAPLink单源方案。

**本步预期：两只电机各剩编码器V／G／A／B四线连着，四个绕组线端独立绝缘，XT30和DAPLink USB都还没接电。** 这样后面即使驱动板为编码器稳压供电，电机绕组也没有接在输出端上。

### 第3步：先只接DAPLink，打开正确工程

保持驱动OFF、XT30拔开。沿用已验证的DAPLink五线，只把DAPLink USB接电脑，给天空星供电。天空星Type-C和DAPLink的3V3保持空着；驱动5V／3V3不能接主板，原两板公共地保留。

如果五线本来已正常下载，不用重新拔插信号线。需要查表时，原方案为5V0→天空星5V／H1.7、GND→H1.4或H1.6、DIO→SWDIO／H1.5、CLK→SWCLK／H1.3、RST→NRST／H1.9；针号依据[既有核对表](../../hardware_preparation/motor_wiring_self_check.md)，不能凭连接器朝向猜针脚。

在Keil中：

1. 若当前处于调试状态，用 **Debug → Start/Stop Debug Session** 或`Ctrl+F5`退出。
2. 选择 **Project → Open Project**。
3. 在文件选择窗口打开`D:/Projects/yeye/control/MDK-ARM/encoder_bench.uvprojx`。从资源管理器双击这个文件也可；不能打开旧`control/firmware/`缓存中的工程。
4. 查看Keil顶部目标下拉框，应直接显示 **EncoderBench**。本工程只有这个目标，不需要手动新建目标，也不需要在原六目标里找它。

如打开的是MotorPwm／MotorDirect或HardwareBench，先退出调试并重新打开上述文件。切换旧窗口时，若只询问是否保存旧工程配置，且没有需要保留的配置编辑，本次选No；存在主动编辑的源文件或配置时应先另存／备份，不要不加区分地丢弃工作。

### 第4步：Rebuild，然后核对下载设置

选择 **Project → Rebuild all target files**，等下方Build Output结束。应看到包含`0 Error(s), 0 Warning(s)`的结果，当前参考大小为Code4500、RO424、RW60、ZI1236。这里的成功只证明电脑编译链接完成，不是下载完成。

若有错误，保持XT30拔开，保存Build Output最后的错误行；不把编译失败后目录里残留的旧AXF当新程序下载。本目标输出AXF的路径应为`control/build/firmware/encoder_bench/encoder_bench.axf`。

选择 **Project → Options for Target 'EncoderBench'**，按下面核对。本机新工程已复制既有成功DAPLink配置；若界面已一致，不必重新配置其它工程。

| 入口 | 本轮核对内容 |
| --- | --- |
| Debug页 | 选择硬件CMSIS-DAP调试器，不能选Use Simulator |
| Debug → Settings | 选择实际连接的既有DAPLink；Port为SW／SWD，时钟1MHz；应能发现目标SW设备 |
| Utilities页 | 使用Debug Driver，沿用该硬件调试器 |
| Settings → Flash Download | STM32F4xx 512KB对应算法，FLASH起点0x08000000，Program和Verify启用 |
| Update Target before Debugging | 关闭；本轮显式手动Download，进入Watch不额外自动刷写 |

如果能看到DAPLink却找不到目标SW设备，先检查主板供电和原DIO／CLK／GND／RST，不换成其它下载链路，也不要为了“能连接”给驱动接电池。目标SWD由主板供电即可。

### 第5步：手动下载，再检查独立启动

1. 点击 **Flash → Download**，等待Programming Done和Verify OK等成功信息。
2. 记下工程名、目标和Verify结果，保留Build Output截图或日志。此步写入主板由主控手动执行，代理没有自动操作。
3. 若进入了调试，先`Ctrl+F5`退出。XT30继续拔开，拔DAPLink USB，等主板灯熄灭，再重新插回，使主板从断电状态启动。
4. 松开KEY和BOOT0。观察用户绿灯，应约亮500ms、灭500ms地慢闪；本程序不需要长按KEY，不再使用MotorPwm的“每组1／2／3闪”等待序列。

绿灯慢闪表示应用监督在运行，不能据此认定编码器计数正常。快闪或反复重启时先不接XT30，进入下一步只读故障字段定位；没有Verify成功时也不继续供电检查。

### 第6步：进入Watch，先确认程序身份和运行状态

XT30仍拔开，只给天空星供电。使用 **Debug → Start/Stop Debug Session** 或`Ctrl+F5`进入调试，再按 **F5（Debug → Run）**持续运行。刚进入调试可能停在main入口、ms暂为0；应先F5，再判断是否增长，不能把尚未Run当成启动故障。

打开 **View → Watch Windows → Watch 1**。如果已有旧MotorPwm变量，可以保留它们但不能用来判断本程序；旧变量可能显示找不到符号。在Watch最下面的`<Enter expression>`空行双击，每次粘贴一个表达式并回车，输入下节给出的六行。然后勾选 **View → Periodic Window Update**，让窗口在程序运行中刷新。

先只核这五个条件：

- revision为0x020C0001：下载的是本轮EncoderBench。
- ms在多次刷新间增加：CPU和滴答在运行。
- fault为0：没有已锁存的初始化／接口故障。
- watchdog_stage为4：R1看门狗初始化完成。
- motor_odr为0：四电机控制脚的板内输出锁存读回为低；不是外部电压测量。

任一项不符，先保存这五项和灯态，XT30保持断开，不转入编码器供电步骤。此时编码器还未由驱动3V3供电，`raw_cnt`不变或输入读高都不能作为编码器故障结论。

### 第7步：保持绕组隔离，给编码器供电

上述程序核对正常后，先退出调试、手离开车轮。确认四根绕组线仍然断开且分别绝缘、编码器四线仍保留。驱动开关OFF时插合XT30，再拨ON。DAPLink继续单独供主板，两块板仍共地。

本轮电源关系是：电脑USB→DAPLink→主板；2S电池→驱动板稳压→编码器V/G；AB脉冲经既有驱动转接与四根编码器信号线进入主板。**只接DAPLink通常不能给驱动侧编码器供电；驱动OFF时不转计数，不足以判坏。** 驱动电源灯亮也不能代填“编码器3V3已测量合格”；有实测电压就记数值，无仪表就记供电路径及“电压未测”。

供电稳定后可以重新进入调试并F5，建立本轮测试起点。若为了清除上电阶段计数或flags需要复位，应在转圈测量开始前完成：停止手转、退出调试、按主板RST，再进入调试并F5；重新核对五个条件和两个flags。**RST会清除累计，复位前后的total_count不能相减。**

**本步预期：绿灯正常慢闪，fault0／motor_odr0，编码器有既有方案供电，电机M1/M2仍未连接。** 若出现异常发热、异味、反复重启或非预期动作，驱动OFF、拔XT30并结束本轮，保存现场现象。

### 第8步：展开计数，先静止，再一次只手转一轮

在`g_encoder_bench`左侧点`+`或展开箭头，再分别展开`a`、`b`。如果不方便展开，可另外把`g_encoder_bench.a.total_count`和`g_encoder_bench.b.total_count`各加一行；这是同一字段的快捷入口，不会改程序。

先让双轮都静止，等至少两次Watch刷新，记录两个`total_count`。初始值不强求0；需要的是静止后读数稳定。`sample_count`仍应增长，`dt_ms`正常约10，`valid=1/status=0/flags=0`；首样status1会在后续正常采样后变0。

接着按下面顺序做，期间保持F5 Run，不点击Stop／单步、不打断点，也不在Value列改数：

1. 主控只手转物理左轮半圈左右，另一轮保持不动；停止后等两次刷新再抄两个累计。
2. 记录是a变还是b变，以及另一轮／通道是否真的保持不动。不要提前把a填成左轮。
3. 把同一只轮往反方向慢转一段，观察该通道累计变化方向是否反过来。数值可以经过0变负，不必总为正数。
4. 对物理右轮重复同样操作。手转遇明显机械卡住时不强扭，记录卡顿或实际联动。
5. 两侧都记录后再进入整圈标定；没有任何变化的通道先按后文现象表定位，不继续算CPR。

例如首次手转左轮只有b累计变化，只能先记录“本次左轮对应b”；这不代表线接错。正向让累计减小也不自动代表故障，尚需按车辆前进方向登记符号。`delta`／`counts_per_s`只代表最近一个很短窗口，慢速手转时可能多数刷新为0，应优先用停稳前后的`total_count`判断是否计数。

Keil菜单依据：[官方Debug命令](https://www.keil.com/support/man/docs/uv4cl/uv4cl_ui_debug.htm)、[官方View菜单](https://www.keil.com/support/man/docs/uv4cl/uv4cl_ui_view.htm)及[Watch说明](https://www.keil.com/support/man/docs/uv4/uv4_db_dbg_watchwin.asp)。这些资料核对菜单与刷新方式，不代表代理已连接本板验证界面。

## 最少Watch与判定

可直接逐行加入（本机新uvoptx已预填）：

```text
g_encoder_bench_revision
g_encoder_bench_ms
g_encoder_bench_fault
g_encoder_bench_watchdog_stage
g_encoder_bench_motor_odr
g_encoder_bench
```

展开`g_encoder_bench.a`与`.b`，优先看`raw_cnt`、`total_count`、`delta`、`dt_ms`、`counts_per_s`、`valid/status/flags`。右键取消Hexadecimal Display，带符号值按十进制看，避免把负数十六进制当巨大正转。

| 字段／情况 | 判定与边界 |
| --- | --- |
| revision／fault／watchdog_stage／motor_odr | 0x020C0001／0／4／0；motor_odr为真实ODR掩码读回，仅证明板内锁存；不是电压实测 |
| sample_ms／sample_count | 持续递增；首样建立基线，以后名义每10ms更新；两CNT先后读取并非同步硬件锁存 |
| raw_cnt | 实际16位CNT，0..65535，正转反转都可跨0；不为显示而定期清CNT |
| total_count | 有符号64位，单位counts，自首样起有效窗口累计；不是总行驶里程，也不是已标定轮圈数 |
| delta／dt_ms／counts_per_s | 正常每窗dt约10ms，速率=delta×1000／实际dt，整数向零截断；Watch刷新慢可能经常看到delta0，不能据此否认累计已变化 |
| valid1／status0 | 仅本窗口数学有效；静止、断线或无供电都可能仍为这个状态，不等于编码器健康 |
| status1／valid0 | 首样，仅建基线，delta／速率／dt为0；不把首次非零CNT误算成运动 |
| status2／3／4 | dt0／dt>100ms／恰好32768的半量程差，窗口拒绝累计，delta与速率置0并重建基线；flags bit0粘性标记连续性丢失 |
| status5 | int64累计溢出，饱和到±边界并冻结，flags bit1锁存；不能反转几次后伪装恢复准确累计 |
| flags非0 | 本次整圈标定不能当完整CPR证据；保存异常原因后复位重做。后续窗口恢复valid1不会清除丢窗历史 |
| pin_levels | bit0..3为PC6、PC7、PB6、PB7的真实数字输入单次读数；仅用于辅助，不能代替示波器或供电测量 |

`sequence`奇数表示正在发布，偶数表示写完；普通Watch分项读取不是事务快照，**即使见偶数也不保证所有字段来自同一次采样**。抄起点／终点前让轮子完全静止，等至少两次Watch刷新累计相同，再抄总计数；不要从转动中的混合字段算CPR。64位值在Cortex-M4上并非单指令读写，这一静止读数门槛也避免高低半字撕裂。

无符号差支持32位毫秒回绕，但仍要求每有效窗口真实净变化严格小于32768 counts；16位CNT无法识别跨多个整圈或较大变化混叠成小差。dt来自SysTick软件时间，不是独立墙钟；CPU被Keil暂停时不能可靠计入真实时间，IWDG还可能复位。因此暂停期间不转轮，发生暂停／复位就废弃该次整圈数据、重新建立基线。输入滤波和采样约束的真实高速边界未验收。

故障位可组合：1=编码器时钟检查，2=TIM5启动等待异常，4=LSI超时，8=IWDG更新超时，16=SysTick配置失败，32=编码器读接口未就绪。非零进入快闪并停止更新采集，电机仍保持零。采样status/flags是另一类数据质量信息，不直接等同全局初始化fault。

## 详细标定：前进符号和每输出轮一圈

### 第9步：把“前进方向”写清楚

先用车头箭头作为参照，主控／硬件按实际安装确认每只轮在“车辆向车头滚动”时应怎样转，再手转模拟该方向。记录“从该轮外侧观察为顺时针／逆时针”，并记录累计增加还是减少。左右轮观察面不同，不能规定两边统一顺时针就是前进。

在验收表填实际轮侧、通道a/b、外侧观察转向、前进时原始计数正负。前进时若累计减少，只登记未来方向系数候选−1；增加则候选+1。本轮不交换线、不修改符号，也不通过动力试转进一步标定。

### 第10步：贴两个标记，测一整圈

本轮CPR的意思是当前四倍频设置下，**输出轮／输出轴完整转一圈得到多少counts**。不是电机内部轴一圈，不要求拆齿轮箱，不预填厂家线数×减速比。

1. 在轮胎外侧贴一小片胶带作为活动标记，在车架不随轮转的地方贴固定标记，让两者对齐；侧面拍照会更好核对。
2. 保持F5 Run，让轮完全静止。确认该通道flags0、ms连续增长，没有暂停／复位。等至少两次Watch刷新total_count不变，记为start；另一轮不要动。
3. 沿刚确认的车辆前进方向，慢慢手转这一只输出轮整整一圈，回到两个标记再次对齐的位置。尽量从同一方向靠近终点，不用反复前后摇摆来“凑值”；出现回摆要如实记录。
4. 停稳，等两次刷新累计一致，记为end，再核对flags仍0，程序没有复位、暂停或重连造成时间中断。
5. 计算有符号差=end−start；一整圈的计数=该差的绝对值。把起点、终点、有符号差、绝对值和证据一起填表，不能只报最后的CPR结论。

**只演示算术、不是本电机预期CPR：** 假设start为−120、end为−357，则差为−237，一圈的绝对计数为237。负号说明本次原始计数减少；示例237没有硬件含义，不能填进实测表，也不能据它判断本车读数对错。

### 第11步：每侧重复3次，再反向核对

同一只轮沿同一前进方向重复一圈，共3次。**每次重新抄start和end，不需要按RST清零。** 如果上一轮停在end，下次可从这个累计继续，取两次读数之差即可。这样减少复位、暂停和跨版本数据混用。

3次结果都要保留，分别算绝对计数的平均、最小、最大和极差（最大−最小）。平均不一定是整数，不能为了整齐改原始数据。本任务尚未规定一个已经实物验证的误差阈值；先回报全部数据和对齐方法，不擅自宣布相差几个counts就一定合格或一定坏。

另一只输出轮完成同样3次，然后每侧再沿相反方向手转一整圈，检查有符号差反向、绝对量级是否一致。若不一致、出现跳数或另一轮联动，记录原始现象，不删异常值、不换线或改符号让结果“通过”。

普通Watch逐字段读取不是原子快照，64位累计也不是单指令更新；因此起终点都必须静止读两次。采样算法不能保证识别CPU暂停期间的真实墙钟间隔，也不能识别所有16位多圈混叠。**暂停／复位／flags非0时，当前整圈数据作废**；先保存异常，重新建立基线，再重做该次，不与之前累计拼接。

### 第12步：结束供电，保存最小回报

先驱动OFF，再拔XT30，最后退出调试并拔DAPLink USB。四根绕组线继续隔离，本轮不恢复后顺手触发旧电机程序。后续恢复接线也须全部断电。

将真实数值写进[同一验收表](../../testing/2026-10-25_encoder/acceptance_record.md)。主控可按下面格式回报，不需要重新描述已确认型号：

```text
C-02C手转回报（实际填写，未做的写未做）：
工程／目标：
Rebuild与Verify结果：
revision／fault／watchdog_stage／motor_odr：
ms是否持续增长，有无暂停／复位：
两电机M1/M2是否均断开绝缘：
编码器V/G实际供电接法，电压实测值或“未测”：
左轮对应a或b，前进原始计数正或负：
右轮对应a或b，前进原始计数正或负：
a三次start→end、flags及绝对计数：
b三次start→end、flags及绝对计数：
反向一圈与另一通道独立性：
已驱动OFF／拔XT30／断DAPLink：
原始照片／截图／视频位置：
```

可靠数据返回后由主控／硬件确认轮侧、方向及CPR，00再安排后续速度功能。本轮软件只给counts和counts/s，不给RPM／m/s，不因此认定闭环或整车通过。

## 常见现象：停在哪一步、先查什么

| 现象 | 主控操作与判定边界 |
| --- | --- |
| 找不到EncoderBench目标 | 打开本页独立encoder_bench.uvprojx；不是在原六目标工程里添加，不用改MotorPwm |
| 编译报错 | XT30保持拔开，保留Build Output错误，不下载残留旧AXF；回报工程路径和错误行 |
| DAPLink存在但找不到主板／下载失败 | 只查主板DAPLink供电和已验证SWD五线，不接电池来解决SWD；保留报错 |
| Watch里`cannot evaluate`／找不到变量 | 核对EncoderBench、当前AXF和变量拼写；须进入硬件调试后查看，旧g_motor_bench变量不属于本入口；不要手写内存地址替代 |
| 刚进入调试ms0 | 先F5 Run并开启Periodic Window Update；尚停在main时不是计数故障 |
| 运行后ms仍不增长／经常归零／fault非0 | 停止后续手转与供电步骤，保存五个运行字段、灯态和错误；故障位解释见前文，不删看门狗绕过 |
| 两路都不随手转变化 | 核对编码器V/G实际供电：只接DAPLink或驱动OFF通常未给编码器供电；再全断电检查编码器四线及公共地，不能先判两个编码器坏 |
| 只有一路不变 | 先确认转的是哪只物理轮、另一通道是否变化；保持动力隔离，全断电只核该路V/G及AB路径，不重新折腾全部已确认接线 |
| raw_cnt从0跳到65535一带 | 可能是正常反向16位回绕；看total_count是否连续反向变化，不改CNT“修正”显示 |
| 出现很大的十六进制数 | 可能是负数的补码；切成十进制并看字段类型，不把负数当异常大正转 |
| total_count在变，delta或counts_per_s常为0 | Watch刷新可能碰到静止的10ms窗口；用停稳前后累计差判断，不延长或启动电机来“让数据明显” |
| 静止也持续跳数／两路都变化 | 确认是否真实机械联动；否则记录供电、接地、线束和数字输入状态，结束后断电核对，可能需要02／硬件测脉冲；不据单个pin_levels值判好坏 |
| flags非0或一次整圈中暂停／复位 | 保存该次异常并标作废；重新建立基线重做，不继续用丢窗累计算CPR |
| 三次整圈计数不一致 | 保留全部起终点，检查输出轮一圈标记、回摆、机械联动和采集连续性；阈值未冻结，不擅改数字或删掉一组 |

## 软件检查和产物

新算法8022次断言，包括2000段两路独立已知轨迹；真实Core／App／SPL适配模型12场景241898次断言，包含正常／回绕、LSI／PVU／RVU停滞、TIM5停计数、错误时钟、读接口失败、SysTick失败、10ms边界和始终零电机。多数断言来自循环边界，不代表同样数量独立场景；模型不生成真实AB电气脉冲，不验证供电、滤波、转向或CPR。

新EncoderBench、原六目标、独立MotorPwm及MotorDirectB构建全部0错误0警告。MotorPwm／MotorBench BIN均仍为`ea10fb83a5497c40c346ee6005073562dade79b013fcc8c6a5f6ec4d49d65a33`，1kHz／50%／500ms及原应用源码未改。旧工程／本机调试配置与开工快照保留一致；没有重新运行未改变的协议／电机模型。

| 当前EncoderBench产物 | 字节 | SHA256 |
| --- | --- | --- |
| encoder_bench.axf | 394112 | `def5e8b97d2c103dd83fce2c192f83a032fe419f3196ef80cd5b627f1db3e3c1` |
| encoder_bench.hex | 14075 | `e36a7041feb4547bf5f0463b69c1c2a45288f88c726209f073d8b673e3100e7a` |
| encoder_bench.bin | 4984 | `e5587b20177dde0119215350b6b59f4e21d4820a3541945588a7a2e2ee5ea7f8` |

教程复核说明：初次软件交付AXF为e8ac42a1…，原记录留在software/checks.json；当前表为补教程时实际文件。核对发现工程XML文件字节及AXF指纹有变化，XML归一化语义与原生成配置完全一致，应用源码、BIN、HEX仍与原交付相同，版本不变；变化的执行来源未核实，本轮没有写工程或重跑构建。当前文件、教程链接及源码字段检查见[教程检查记录](../../testing/2026-10-25_encoder/software/tutorial_checks.json)，不覆盖原构建证据。

产物位于`control/build/firmware/encoder_bench/`，向量SP=0x20000510、Reset=0x0800019D。本机uvoptx与build被Git忽略；换设备需复建和核对调试器。电脑执行脚本为[run_encoder_tests.ps1](../tools/run_encoder_tests.ps1)、[build_encoder_bench.ps1](../tools/build_encoder_bench.ps1)，主控人工操作无需终端。源码／日志／完整检查清单见[软件证据](../../testing/2026-10-25_encoder/software/README.md)。

依据：[ST RM0090](https://www.st.com/resource/en/reference_manual/rm0090-stm32f407-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)编码器接口、ICxF与定时器章节；[ST AN4013](https://www.st.com/content/ccc/resource/technical/document/application_note/54/0f/67/eb/47/34/45/40/DM00042534.pdf/files/DM00042534.pdf/jcr%3Acontent/translations/en.DM00042534.pdf)编码器模式3四倍频说明；本地原厂SPL的TIM_EncoderInterfaceConfig／TIM_ICInit实现、[引脚方案及官方AF依据](pin_plan.md)。本轮没有修改官方库或以模型替代实物。
