# 2026-11-18：直道抑摆程序及首次连接

负责：主控。来源分支`codex/current-version-20261025`，HEAD `62b4f288b27c4e3fa9f6d213c07be186e502f43c`。本次开始时工作区干净；本地修改未提交／未上传。任务[I-03](../../project_planning/tasks/I-03-STRAIGHT-ASSIST.md)，操作[straight_assist.md](../../control/docs/straight_assist.md)。不接替00，不把原I-02失败改为通过。

## 软件交付

- STM32独立`StraightAssist`目标，版本`0x02120001`，默认80RPM／2000ms。编码器20ms左右独立PI，40RPM起步斜坡、80ms误差低通、死区／滞回、±12%差速和变化率限制；PWM仍<=50%，所有既有运动故障监督保留。
- 视觉当前双边直线拟合，横向／方向组合误差，至少3帧／80ms一致；无单边或历史续跑。v3开发版本与旧v1／v2隔离；不发START。
- [最终预览单文件](vision_bundle_final/straight_preview.py)／[最终许可单文件](vision_bundle_final/straight_drive.py)，源码清单／SHA256与各文件相邻。`vision_bundle`为早期候选；现场采用`vision_bundle_final`。
- 新旧目标ARM均0错误0警告。旧LowSpeedLap 0B和Track 0C BIN与`testing/2026-11-12_field_resume/mcu_trace_build_02`原件逐字节一致；新控制仅在独立编译宏下生效。新BIN SHA256 `e7d5a504156d63e121a554f29fe30382e98d6889cf36a1f51bbeb11ea7e84550`。
- 新直道控制844项场景断言通过；原低速347项断言及生产UART主机检查通过。视觉[94项检查](vision_checks_02/review.json)包括15张真实五姿态图在4／6像素网格下的许可和方向、已知单带／文字负例、合成折角、时间／失线／协议、Python到生产C解析器交叉和主循环异常清理。模型、静态图和设备替身不替代实车。
- 无硬件连接的ELF布局检查确认新AXF可由`lap_swd_capture.py --profile straight`解码13个原运动／时序符号，保留原layout；未据此宣称实际Flash已下载。

## 当前物理状态与授权

主控本轮确认：主板5V接车载稳压5V；DAPLink仅DIO／CLK／GND，未接DAP供电；视觉板仅电脑USB供电，未并接车载5V；两只驱动轮完全悬空，车辆位于跑道。USB枚举DAPLink COM9（0D28:0204）、视觉COM10（1209:ABD1）。这不是对稳压输出新实测电压的补填。

已指导主控Keil打开`control/MDK-ARM/straight_assist.uvprojx`，选择StraightAssist，人工Rebuild／Flash→Download，保持悬空不按KEY。**尚未收到本轮下载完成回报／新Flash实读，不执行校准或双轮RUN**。代理未下载、未主动复位／暂停STM32、未发START。

## 首次连接与无驱动实板检查

[connection_01](connection_01/board.json)识别K230D Lushanpi Lite 128M／CanMV v1.8-0。官方后端connectBoard发生旧脚本`IDE interrupt`和soft reboot提示，之后running=false；这次连接实际中断了旧脚本，不能声称对运行状态无副作用。没有改写原main.py。

[board_no_drive_01](board_no_drive_01/result.json)运行新预览派生的**10秒、ALLOW_DRIVE=False**真实相机程序，执行原件与终端均保留。204个逐帧记录，67帧几何有效，其余主要双边支持不足；最长处理60ms、发包前耗时67ms、帧间隔105ms。所有wire_valid=false，程序正常结束并发v3 STOP；没有电机启动。本轮main.py前后逐字节一致，SHA256仍为`f9a12f4ec10d1fec6ab629f3415858403b2a4d0ed4df16dfb76482f4c5fe16d8`。

**只通过执行兼容／日志与时序检查，尚未通过持续直道许可，更未通过动力或地面。** 后半段支持数降至5..7，日志主要no_pair；保存5张实际原图，后段左下方出现较大遮挡／阴影、取景变化。黑阈值100提高到110未恢复足够支持，不能简单放宽门槛或盲目增PWM。已请求主控核对测试期间车辆／相机是否移动及移开遮挡，保持悬空固定后再做针对性无驱动复测；不改变失线停车保护。

## 移开遮挡后的固定视角复测（最新）

主控明确已移开遮挡，车辆位于赛道左侧斜直道中央，继续两轮悬空。相同程序、相同10秒禁驱动条件下，[board_no_drive_02](board_no_drive_02/result.json)取得240帧／234帧几何有效，末2秒全部有效；误差约-83，方向稳定，没有来回跨零。处理最大61ms、发送前80ms、帧间隔101ms；全部wire_valid=false，正常退出，main.py前后字节一致。没有放宽任何几何／控制／超时门槛。

本轮仅确认固定姿态当前双边观测／执行时序；不把234/240称实际运动识别率，初始自动曝光与稳定门的无效帧保留。运行中姿态、振动、偏移、误差响应和接收端均待验，未发电机START或人工KEY，未完成新程序动力／地面。

## 一个下一步

主控已回报下载完成、驱动电源打开，仍沿用此前两轮悬空。进程检查未见UV4。只读[mcu_baseline_01](mcu_baseline_01/capture.json)确认Flash与新BIN完全一致（e7d5a504…7e84550），但应用基线拒收：两次相隔约1秒的RAM版本均0x68016041、毫秒1229080643不增、state148、phase1134586120、配置和DWT时钟非法；CPU显示RUNNING。不能把这些值当真实PWM／故障或已执行新应用，现象与既有下载后RAM残留一致，但未确认PC或指定根因。代理未halt／resume／reset／写Flash。

主控已按实物RST，[mcu_baseline_02](mcu_baseline_02/capture.json)确认应用正常运行：Flash一致、revision0x02120001、ms21832→22947、80RPM／2000ms、phase0／error0、目标及PWM均0，UART和硬件故障0，IWDG已启动、16MHz时序诊断有效。原baseline_01拒收原件保留，不当复位解决了某种实际电机故障。

随后[board_no_drive_03](board_no_drive_03/result.json)以相同10秒禁驱动视觉验证新MCU实际v3互通；209帧／134几何有效，后半段又出现no_pair，不放行持续视觉／双轮RUN。相机全程wire_valid=false，处理最大68ms、帧间隔103ms、main.py不变。[mcu_uart_01](mcu_uart_01/capture.json)确认实际received209、拒收和重复0、UART各错误0、phase0／error0、目标及PWM0；SysTick最大79.5us、提交55.6875us、UART12.125us。该时序是待机／收包，不代替新RUN计算时序。

主控确认第一次KEY左轮朝前500ms并停、右轮不动符合。[cal_left_01](cal_left_01/capture.json)实读phase1／error0、UART和硬件故障0、目标及PWM0，新版本及80RPM／2000ms保持，未复位。

主控随后明确要求“尽量减少这些预处理检测，直接运行……直线上的跑线程序，我来检验效果”。按本轮指令缩短人工步骤：不再要求重复10秒视觉预检或完整悬空矩阵；仅补固件必要的右轮500ms配对，然后运行最终straight_drive.py并进行一次80RPM／2秒地面研发试跑。软件内编码器、失线、通信、KEY和时限保护不变，不把减少人工检查写成取消保护或已经通过地面。

当前操作：仍悬空再按一次KEY完成右轮校准，预期右轮朝前约500ms后停。正常停后CanMV运行最终许可单文件，再居中摆正到左侧斜直道、前方至少2米留余量，KEY长按松开试跑一次2秒，主控直接观察摆动、速度、偏移和停因。视觉板目前只由电脑USB供电，研发短段测试须保持该供电且线束有充分松弛、不受牵拉；没有独立供电时不能拔USB后期望相机继续运行，也不能把连线短段当正式自主完圈。测试后回报实际现象并保留停车数据；不复位重复掩盖停因。程序支撑比赛基本60分的用时与少触边目标，当前无实测得分收益。

## KEY无动作与直接接管视觉（最新）

主控回报长按KEY没有运动。[no_motion_01](no_motion_01/capture.json)定位到**没有新视觉输入**：phase2／error0，说明右轮配对已完成；LAP_WAIT、starts_rejected2、run_since0、last_run.valid0；received仍209、源时间55694ms而本地约408000ms、path_valid0。UART／硬件错误0、PWM0，启动手势确已到达，不能把本次归为KEY失灵或马达没动力。

按主控直接运行授权，新增`vision/tools/run_straight_live.py`保持官方后端和真实相机许可会话，使用当前生成器的最终drive源码，10分钟输入窗口，不写main.py、不发START，STM32仍每次KEY独立2秒。[live_drive_01](live_drive_01/run.json)保存执行原件及后台终端；本轮会话已实际启动，SD日志`/sdcard/straight_logs/run_0004.jsonl`，ready／wire_valid=True，误差约77、发送前约31..34ms。

[live_ready_01](live_ready_01/capture.json)确认STM32真收到新输入：received533→562、path_valid1、steering77、phase2、LAP_WAIT、左右目标／PWM0、UART／硬件错误0。reason1为相机开头STOP留下的原因，当前并非FAULT；映射未清除。下一步由主控居中摆正、等待2秒后一次KEY长按松开，直接检验80RPM／2秒。相机会话继续运行，不能再连接另一CanMV客户端或断开视觉USB中断输入；试跑结果待回报。

## 首次地面116ms停车与视觉R2修正（最新）

主控回报“只走很短、动一下停、绿灯快闪”。[ground_01_capture](ground_01_capture/capture.json)保存真实失败：LAP_FAULT6／LAP_PATH3，运行116ms；左右目标48／48RPM，滤波反馈9.8302／8.7824RPM，撤驱动前PWM36.2%／36.3%，均用过一个20ms起步补偿窗口。冻结5个20ms样本，两轮已有前进反馈；UART和硬件错误0。本次由视觉无效包触发，未发生无反馈或反向停车，不把短距离归因为动力故障，也不称已经同速达标。

停止live_drive_01后取回[ground_01_visual](ground_01_visual/review.json)原SD日志4153帧／1720968字节。用旧received209基线、冻结PATH序号165..167和逐帧序号对齐：第1961帧／seq168是首个无效包，支持13行、near0.2511／far0.1987、方向代理-0.00262、残差0.4752、完整深度17.16..58.99、处理32ms／发送前34ms。旧其余几何门均满足，拒绝来自两半短线斜率差0.12门槛；短跨度的网格变化会被放大。这是对程序和日志的定位，缺少该瞬时原图，不补造动态画面。

停车后短时原图显示镜头横看赛道，主控随后已重新摆正；不拿停车后新姿态代替触发帧。ground_01_view原命令错误沿用了suspended标志，但当前应按**地面FAULT、PWM0的禁驱动取景**解释，不作为悬空实物确认；工具现允许明确`--confirmed-mcu-fault`，后续原始记录正确填false／true。本次没有新增电机动作。原raw result不覆盖。

视觉R2只改直道判断，不改主板：将固定半段斜率差改成实际观测跨度内的弯折偏离量，增加单点残差／半段跨度检查；保留全局残差、位置、方向、当前双边／失线立即停车与时间限制，增加逐项geometry_failures诊断。97项检查通过，新增“13行轻微量化V形旧门拒绝／新门通过、明显折角仍拒绝”几何回归；模型不冒充触发帧原图。[vision_r2_board_01](vision_r2_board_01/result.json)3秒真实禁驱动69帧／64几何有效、末2秒全部有效，处理最大61ms、周期104ms，main.py不变。

当前交付为[vision_bundle_r2](vision_bundle_r2/straight_drive.py)，原vision_bundle_final及live_drive_01源码保留R1。已实际启动[live_drive_02](live_drive_02/run.json)，SD新日志run_0007，ready／wire_valid=True、误差约28、发送前31..34ms；后台保持，不发START、不写main.py。STM32仍保持首次失败FAULT，尚未人工复位／重跑。下一步最短顺序：两轮悬空→主控RST一次→KEY长按松开两次分别完成左／右500ms、每次待停稳→落地居中摆正等2秒→一次KEY直接80RPM／2秒复测。无需重新下载主板，不再要求额外完整悬空测试；保留原软件保护。

## 第二次地面右偏／563ms停车与固件02（最新）

主控回报“初始很快、微向右偏、偏到一定程度突然停、绿灯快闪”。[ground_02_capture](ground_02_capture/capture.json)确认LAP_PATH3／563ms，硬件与UART错误0；停车前目标70.4／89.6RPM、滤波反馈110.7726／82.5106RPM，PWM33.5%／50%，左右已有正向原始反馈。共28个20ms窗口全留：从起步左轮实际持续快于右轮，视觉转向从-35增至-658，目标已要求左慢右快，但实际差速仍向右，左轮减PWM响应过迟。左右PWM与实际轮速的原因不能直接归为轮径或供电已测定；本轮没有新电压／电流实测。

通过本次后台stop.request正常停止live_drive_02，保留退出／STOP和日志；[ground_02_visual](ground_02_visual/review.json)取回5670帧。冻结末序号10对应第3851帧：near-10.9873、far-16.8296、方向代理-0.2921、支持8行、所有R2几何门满足；第3852帧seq11支持降7／no_pair而触发停车。停车前近处偏差和方向持续增长，属于此次可见路径丢失，没有继续放宽视觉条件。

本地固件更新 **0x02120002**，仅独立StraightAssist：PI Kp2／Ki12改为Kp6／Ki8；轮速滤波alpha1/4改1/2；PI输出后加入编码器差速误差补偿，误差=(实测左-实测右)-(目标左-目标右)，增益4千分比/RPM、幅度±100千分比，左偏快就减左加右，保留视觉有意安排的目标差速。默认80RPM／2秒、40RPM起步／100RPM每秒斜坡、50%PWM上限及所有故障保护不变；不新增反转或强制最低PWM。

893项新控制断言通过，含真实停车快照的补偿方向／限幅、目标差速保留、近似带载惯性模型；该模型由本次137..557ms原始短段拟合，仅作早期瞬态假设，不能作为稳态标定。模型前600ms最大左右速度差6.98RPM、积分差2.93RPM*s，仅为模型值，不能与实物前后当成已测改善。原低速347项及生产UART主机检查通过；新固件与旧两目标ARM均0错误0警告，旧0B／0C BIN仍与原件一致。新BIN SHA256 `361a5842ddbd52047c097dc4b0167bb9ee8dd293508b6604a6a52355af4bd848`。旧01产物保留在ground_02_capture/firmware_before_update和software_evidence。

当前STM32最后实读仍01，**02尚待主控人工下载／地面验证**。已指导同一StraightAssist目标重新下载；视觉R2在[live_drive_03](live_drive_03/run.json)重新保持运行，日志run_0008，此刻车头偏后no_pair属当前取景，不称ready。主控下载后关闭Keil，两轮悬空RST一次，KEY两次完成必要左右500ms，再回直道中央、车头沿边界摆正等2秒，KEY一次直接80RPM／2秒复测；不追加完整预检。后续以最大实际轮速差、起步超调、横向／朝向偏移、2秒成功率和触边验证，支撑比赛基本功能用时与少触边目标，不预告实测得分。

## 第三次地面：固件02正常2秒直行（当前有效基线）

主控反馈原话：**“正常跑直线了，走了大概一半距离的左侧斜直道，状态很好，没有明显摇摆。”** 距离为目测描述，没有换算为实测米数；触边次数未单独反馈，不补写0次或整圈成绩。

[ground_03_capture](ground_03_capture/capture.json)与[review](ground_03_capture/review.json)确认实际Flash与固件02 BIN一致、版本0x02120002、80RPM／2000ms；真正运行2000ms，以LAP_LIMIT11正常撤驱动，非失线／故障停车。当前回到WAIT、phase2／error0、目标及PWM0，UART与硬件错误0，路径当前有效。停车前末帧目标79.5913／80.4087RPM、滤波反馈82.8269／84.8574RPM，左右实测末帧差约2.03RPM，PWM28.2%／27.5%；这些是末帧，不当全程恒定转速。

本次共100个20ms采样，冻结环保留32个，即运行1368..1988ms；该窗口全为当前有效双边，原始左右转速差最大8.3255RPM、目标差最大5.4081RPM，左右PWM范围22.1%..30.4%／26.0%..32.5%，均未饱和。环不保留起步前约1.36秒，不能用此窗口证明全程最大误差或起步过冲上限。会话SysTick最长258.3125us、运动提交83.6875us、UART12.1875us，未见1ms调度超限；不外推所有负载条件。

结论：**直道程序交付及一次80RPM／2秒地面直行效果已由主控确认，保存为当前可用基线**。两次失败原件和软件迭代全部保留。参数暂保持，不自动提速或延长运行；重复成功率、量化横向偏移／触边、提高速度、弯道及正式完整圈另验。此结果支撑比赛基本功能60分中的用时与少触边目标；未测圈时、未得官方分数，不宣布比赛完赛通过。全局摘要仍由00读取I-03及本证据更新。
