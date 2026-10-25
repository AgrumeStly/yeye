# C-02B 双电机首次开环试转操作说明

> 2026-10-25目录迁移：当前Keil工程在control/MDK-ARM，新ARM产物在control/build/firmware；原目标、版本及保护不变。历史产物／日志留原位置，当前分层和迁移验证见[ORG-02](../../project_planning/tasks/ORG-02.md)。

2026-10-24最新简化诊断为[MotorDirect固定GPIO单次500ms](motor_direct.md)：原接线、无PWM、只A一次，结束锁定。主控当前无法去实验室，本次按该独立说明选择目标；下文是保留的原MotorBench流程。

2026-10-24新增独立[MotorContinuous持续A桥测试](motor_continuous.md)，由主控本轮直接要求持续运行。本页仍对应原MotorBench／500ms与R3快照流程，新目标按其独立说明选择及操作，不把500ms程序误当持续版本。

状态：v1.3／C-02B-R3，活动／停止寄存器保留诊断已完成编译与电脑验证，现场快照待主控。日期：2026-10-21（北京时间）。维护：主控／01；现场采集：主控，电气测量：硬件；结果交00验收。依据：[R3任务与交付](motor_bench_r3_task.md)、[R2历史](motor_bench_r2_task.md)、[接线指南](../../hardware_preparation/dual_motor_wiring_guide.md)、[引脚方案](pin_plan.md)。

本次只编码、编译和电脑检查，没有烧录、接电池或运行电机。主控汇报动力、电机六芯和九根信号／地线已接好；导通、电压、波形、方向与停稳结果仍未验证。下文现场动作由主控在前置检查通过后手动执行，轮子始终悬空。

按键名称说明：本文此前的“WKUP／用户键”指天空星正面丝印 **KEY** 的用户按键（PA0的WKUP功能），不是要求寻找一个额外按钮。按板卡正面朝向观察，Type-C在下、TF卡槽在上时，上沿靠左三个按键从左到右为 **KEY、RST、BOOT0**，本程序按最左侧KEY。位置依据仓库`control/stm数据手册.pdf`第2页板卡资源图；KEY接PA0依据[官方按键教程](https://wiki.lckfb.com/zh-hans/tkx/tkx-stm32f407vxt6/beginner/key-principle.html)。用户找不到WKUP时按此说明定位，不按RST或BOOT0试转。

现场进展：R2已由主控回报Verify OK、绿灯正常、驱动板电源灯亮，但30%单次A完全不动、无声音；无万用表或PWM波形，根因未定，接线正确的主控确认继续采用。R1修复与R2失败历史保留。**本轮只按第13节：驱动OFF、动力电池XT30拔开、UC2断开，用Keil人工触发一次A的无动力输出并读取保留快照；不接电池、不继续B／AB、不加功率。**

操作偏好：主控要求不使用终端，采用第13节纯Keil5流程，第10节提供DAPLink连接设置；第9节图形DFU和第3／4节命令行保留为备选。SWD已有历史Verify OK，R3仍需重新下载并确认版本；主板USB不能当成CMSIS-DAP。

## 1. 目标、接线与固定参数

打开`control/MDK-ARM/yeye_control.uvprojx`，选择新增的 **MotorBench**。原LogicDemo、HardwareBench、BoardSelfTest保留；这三个目标不包含新电机源文件，原HardwareBench的左右请求仍只是Watch变量。

| 项目 | 本版参数／行为 |
| --- | --- |
| 电机／驱动／主板 | MD310Z20_7.4V两只；AT8236 Standard／YB-MNT03-V1.0；天空星STM32F407VET6青春版，沿用已确认型号 |
| 四路控制 | AIN1=PE9、AIN2=PE11、BIN1=PE13、BIN2=PE14，TIM1_CH1–4／AF1 |
| PWM | HSI名义16MHz，APB2不分频，PSC=0、ARR=799，四路共20kHz；PWM1、高有效 |
| R3固定输出（沿用R2） | 30%=300‰，CCR=240／800；选中的桥IN1输出PWM、IN2始终低。不反转、不爬升占空比，不将其视为速度值 |
| 每次试转 | 500ms后撤去电驱动；仅A→仅B→AB，每步单独触发，第三步后锁定，不循环 |
| 人工触发 | 上电／阶段间连续松键1s；PA0/WKUP长按约1–2s，灯变常亮后松开；松开稳定30ms后才起转 |
| 随时停止 | 运行中按WKUP，原始高电平在下一次1ms监督中断发停止请求，不等待消抖；随后锁定，不能继续下一步 |
| 停车方式 | 四脚主动GPIO低电平，TIM1 MOE关闭，IN1/IN2=00滑行／休眠；不是11主动刹车，机械停稳另测 |
| 误操作防护 | 启动／松键30ms消抖；短按不启动；长按达标仍不运行，必须松开；进入长按阶段持续5s锁定；上电按住只等待松开，不续跑 |
| 监督 | SysTick每1ms执行逻辑及输出；IWDG分频32、重装249，名义约250ms；R1先启动IWDG再配置／等待更新。LSI与PVU/RVU各用独立TIM5限时10ms，失败锁存故障且禁止试转 |
| R3保留诊断 | `g_motor_bench_pwm_diag`保存请求／启用计数、实际活动和停止后寄存器、时间及停止原因；只在事件时采集，停机不覆盖活动快照，下一次启用或复位才替换／清除 |

编码器PC6／PC7、PB6／PB7保持现有线，不初始化、不读取。没有PID、UART、视觉或语音依赖；A/B是桥编号，不是左／右轮或已确认前进方向。

## 2. 首次供电与下载前，先断电核对

1. 拔开2S电池XT30、电脑USB及下载器电源，驱动开关OFF；固定电机和板卡，轮子离开桌面，线不接触转轴，板底绝缘。开关OFF不代替拔电池。
2. 主控／硬件逐根核对九线，特别是E14换列、B06/B07不同排位；确认驱动GND与主板GND相通。只在全部断电时用通断档，不用通断档测带电电池。
3. 两束六芯线按功能核对：M1/M2到AO1/AO2或BO1/BO2；G到GND、V到驱动3V3、A/B到E1A/E1B或E2A/E2B。不能只凭颜色或插头能插入就认定正确；不能把电池电压送到编码器V或A/B。
4. XT30正负与Vin+/Vin−逐端确认；不接Vout作主板电源。检查螺丝端子紧固、无散股与裸铜跨接；持续低阻／蜂鸣或功能错线先保持断电查因。
5. 原USB DFU方案为电脑USB只供天空星、2S电池只供驱动，两板共地；本轮R2沿用第12节的DAPLink五线供逻辑主板，天空星Type-C空着，下载与无动力待机检查期间电池拔开。两种主板供电方案不要同时连接。驱动5V、3V3都不接主板；不使用车载USB-A供电转接板，不并联两套稳压输出。

本程序不测电池、电流或堵转。30%仍不保证起转，也不是已测安全负载参数。主控已确认接线正确，R2不重复索要照片；第2节保留为接线检查参考，现场没有仪表的项目写“未测”，不据此编造电压／导通通过。先A一次失败即断动力，由硬件补测，不继续增大占空比试错。

## 3. 编译与取得可下载文件（不操作板卡）

Keil选择MotorBench，F7只编译，不按Download或Ctrl+F5。台式机已核实Keil5.24a、ARMCC5.06u5及fromelf存在；也可在项目根目录PowerShell运行：

```powershell
Set-Location D:/Projects/yeye
powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/build_keil.ps1 -Target MotorBench
```

脚本编译并用fromelf导出BIN，**没有下载命令**。R3本次编译0错误0警告，Code5208、RO424、RW64、ZI1288字节。主控本轮使用第13节Keil图形流程，无需执行这里的命令行；以版本字段确认实际应用。输出：

- `control/firmware/build/motor_bench/motor_bench.bin`：R3为5696字节，供备选DFU使用；Keil直接使用同目录AXF。
- 同目录`motor_bench.axf`、`motor_bench.hex`供相应工具使用，不能把HEX文本当BIN交给下节命令。
- 构建日志：`control/firmware/build/MotorBench_build.log`。

R3本次BIN SHA256：`d09c4095c55eb34607d012c36611b239b6d24c00d2451497f925e812e994e0d8`。R2的5144字节／`99b03ae7…`为不含快照的30%历史版本；R1的5144字节／`9c165244…`为15%，初版4672字节／`8593c996…`为启动阻塞版本。修改代码或编译条件后以新产物记录；编译产物被Git忽略，跨电脑需重新构建。Keil Watch的`g_motor_bench_revision=0x020B0003`确认R3应用已执行。

## 4. 历史已验证的USB DFU备选下载（以下由主控手动执行）

2026-10-14已经通过天空星Type-C、ROM DFU和dfu-util 0.11写入／读回BoardSelfTest；这条路径不要求先有SWD。当前同一台电脑的dfu-util和WinUSB历史安装记录仍在，本次只运行工具`--version`核实0.11，**未枚举设备、未确认今天的USB连接或驱动状态**。换电脑时`tmp/`工具不随Git交付，须准备dfu-util及匹配WinUSB驱动；设备读保护导致备份失败时先查因，不运行unprotect、mass-erase或改Option Bytes。

1. 电池XT30在整个备份、下载和读回阶段保持拔开，只插电脑USB至天空星。
2. 主控按住BOOT0，按下并松开RESET，再松开BOOT0，进入ROM下载。设备管理器应出现STM32 Bootloader／0483:DF11；WKUP不是BOOT0。
3. 在项目根目录逐段运行以下命令。先只枚举，确认只有一块匹配设备且alt=0是Internal Flash；多个匹配设备先拔开其它设备。未识别时先排查BOOT0流程、数据线和WinUSB，不进行写入。

```powershell
Set-Location D:/Projects/yeye
$dfuBench = Join-Path $PWD 'tmp/board_tools/dfu_util/dfu-util-0.11-binaries/win64/dfu-util.exe'
$binBench = Join-Path $PWD 'control/build/firmware/motor_bench/motor_bench.bin'
& $dfuBench -l
```

4. 主控确认设备及电池拔开后，备份当前512KiB Flash到新目录；不覆盖2026-10-14旧备份。目录名每次带时间，保存备份成功后才执行写入段。

```powershell
$runBench = Join-Path $PWD ('control/build/motor_bench_dfu_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $runBench -ErrorAction Stop | Out-Null
& $dfuBench -d ',0483:df11' -a 0 -s '0x08000000:524288' -U (Join-Path $runBench 'before.bin')
if ($LASTEXITCODE -ne 0) { throw '备份失败，停止下载' }
if ((Get-Item (Join-Path $runBench 'before.bin')).Length -ne 524288) { throw '备份长度不符' }
```

5. 以下段落会**实际写Flash**，只由主控在上述检查通过后运行；地址固定内部Flash `0x08000000`，alt=0，不操作其它存储区。暂不使用leave，便于继续读回验证。

```powershell
& $dfuBench -d ',0483:df11' -a 0 -s '0x08000000' -D $binBench
if ($LASTEXITCODE -ne 0) { throw '写入失败，保持电池断开' }
$lengthBench = (Get-Item $binBench).Length
& $dfuBench -d ',0483:df11' -a 0 -s ('0x08000000:' + $lengthBench) -U (Join-Path $runBench 'readback.bin')
if ($LASTEXITCODE -ne 0) { throw '读回失败' }
if ((Get-Item (Join-Path $runBench 'readback.bin')).Length -ne $lengthBench) { throw '读回长度不符' }
$expectedBench = (Get-FileHash -Algorithm SHA256 -LiteralPath $binBench).Hash
$actualBench = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $runBench 'readback.bin')).Hash
if ($expectedBench -ne $actualBench) { throw '读回不一致，禁止接电池' }
Write-Output ('读回一致，BIN SHA256=' + $expectedBench)
```

这与历史已通过方式相同，但本次代码尚未实物下载。dfu-util 0.11对裸BIN可能提示缺少DFU suffix；历史也有同样提示，判断仍须看退出码、长度及读回哈希，不可忽略其它报错。

6. 主控确认读回一致、BOOT0已松开，单独按RESET启动；此时电池仍拔开。约1s后PB2应每2.5s闪1次，表示等待A。主控可只看灯，不按WKUP触发“空跑”。若仍是原来的双闪，先核对是否真的下载MotorBench；未出现待机灯则不连接电池。正常运行无USB串口，DFU设备消失属于预期。

原版已有本项目SWD下载Verify OK记录，本轮按第13节纯Keil下载R3并保持动力断开；本节保留为历史DFU备选。动力接通时不单步或打断点。

## 5. 电池与三次独立触发规则（历史；R3本轮禁止接动力）

本节保留原台架操作，不是R3当前授权。当前只做第13节的无动力快照采集；动力复测由00根据快照及I-05另行安排。

1. 第2节断电检查通过、BIN读回一致、USB单独供主板时待机提示正确后，保持WKUP松开，驱动开关OFF，再由主控连接XT30并开启驱动；轮子继续悬空。不要用BOOT0试转。
2. **先不触发**，观察应无自行转动、无异常发热／气味／复位。若有，立即关闭驱动并拔电池，保留现象记录，不继续按键。软件初始化主动拉低四脚；MCU复位／BOOT ROM窗口是高阻，实际默认态仍依赖AT8236下拉与正确接线，不能把编译通过当成物理零驱动已验收。
3. 有仪表时由硬件核对四路输入待机接近0V、编码器V/G间接近3.3V，不能是电池电压；测量值和位置要记录，异常先断电。R2现场无万用表，这些保持未测，不作为已通过条件；沿用主控接线正确的确认，按第12节只试A一次，失败即停止并转硬件测量。
4. LED每组闪1次时，主控长按**WKUP/用户键**约1–2s；按住时先快闪，达标常亮，此时电机仍不应转。松开后仅A桥输出500ms，再自动撤去驱动。记录实际转动电机、方向、是否能起转和停稳表现。
5. 等A轮真实停稳并确认没有异常，LED进入每组闪2次，重复一次“长按到常亮→松开”，仅B桥500ms。等待本身不触发下一步。
6. B单轮结果也正常且已停稳后，LED每组闪3次，再独立长按并松开，AB同时30%运行500ms后停止。两个电机机械方向相同与否不作为前进判断，镜像安装需要后续标定。本轮先只验A，不因软件提示推进就继续B／AB。
7. 第三次结束后灯每500ms翻转（慢闪），程序锁定，再按键也不试转；这是三次输出序列结束提示，不表示电机实际都转动成功。重新测试先断开电池、查明记录，再RESET回到A，不能跳过失败的单轮直接测双轮。

**随时停止：**运行中按WKUP立即发出00滑行请求并锁定；灯快闪时不再接受触发。RESET也会重置程序而不自动起转；真正需要切断驱动力时使用驱动开关OFF／断开XT30，不能只拔主板USB让控制端失去供电。按键、复位、500ms均指电气请求撤去，不承诺机械瞬时停稳。

LED速查：等待松键为灭；待A/B/AB每2.5s一组闪1/2/3次；按住未满长按阈值快闪；达标和运行中常亮；三步完成慢闪；人工停止／卡键／初始化错误为快闪。初始化错误与人工停止都须先断动力查因，不能靠反复复位掩盖问题。

## 6. 不转或异常时按顺序排查

| 现象 | 下一项检查 |
| --- | --- |
| 主板灯不符合提示 | 电池保持拔开，确认MotorBench目标、BIN及读回哈希，BOOT0松开后RESET；核对USB供电，不能把电源灯当PB2用户灯 |
| 长按常亮但不转 | 常亮时尚未触发，必须松开并消抖；等待当前500ms窗口结束后观察下一组提示。持续按5s会锁定，不能以一直按住方式运行 |
| R2松开后不转／仅抖动但提示推进 | 灯推进只说明软件500ms阶段结束；立即关驱动并拔XT30，不继续B／AB、不再提高占空比或反复触发。主控已确认接线正确，后续由硬件借仪表补测供电／实际PWM和驱动输出，不将低占空比认定为根因 |
| 试A却转了另一只或两只 | 先停止断电；按桥编号查四控制线和电机口。A/B尚未标定轮侧，不通过交换编码器电源线纠正 |
| 方向与预想不同 | 记录MOTOR-A/B对应轮侧及观察方向，本轮不反转；由后续方向标定处理，不交换G/V或随意改六芯线 |
| 自动停止后轮子仍滑动 | 本版00滑行，先区分输入已归零与机械惯性。用信号／停稳时间证据判断，不把滑行直接叫作刹车失效 |
| 500ms后仍持续受驱动、复位自转、主板重启或发热 | 立即切断驱动电源，保存录像与接线／电压；未定位前不继续B或AB。没有编码器反馈，本程序不能自行识别错线或堵转 |

后续有仪器时测PE9／PE13有效窗口20kHz、30%，PE11／PE14保持低；普通万用表读到的PWM平均电压不能代替占空比／频率验证。本轮尚无这些测量结果。

## 7. 返回00的记录

每次填写日期、BIN哈希／源码版本、目标MotorBench、接线版本、USB与电池供电方式、断电导通结果、实测电压、A/B轮侧、三次独立触发结果、停止方式及实际停稳表现；失败保留现象，不写“全部通过”。首次结果可保存到`testing/2026-10-20_motor_bench/`或实际测试日期目录。

当前只具备[电脑验证记录](validation.md)，没有电机板级通过结论。现场至少补：上电／RESET不自转、仅A／仅B／AB、500ms窗口、运行中按键停止、第三步锁定及复位后仍需新操作。电压、电流、PWM波形和停稳时间按实际仪器与证据注明。

实现入口：[按键／超时逻辑](../App/Diagnostics/motor_bench.c)、[SPL PWM](../Drivers_Custom/Motor/motor_bench_pwm.c)、[板端监督与看门狗](../Core/Src/motor_bench_main.c)。官方参考：[dfu-util手册](https://dfu-util.sourceforge.net/dfu-util.1.html)、[天空星下载教程](https://wiki.lckfb.com/zh-hans/tkx/tkx-stm32f407vxt6/beginner/download.html)、[厂家AT8236真值表说明](https://www.yahboom.net/study/SBR-microROS/13590/)（该页是另一控制板，仅引用芯片真值表；本板接线仍按项目接线指南）。

## 8. C-02B初版交付文件清单（历史）

以下为C-02B实际新增／修改的24个文件；已有C-02A／I-03资料及其它对话改动继续保留，不混记为本任务新成果。

- 应用新增5个：`control/App/Diagnostics/motor_bench.h`、`motor_bench_pwm.h`；`control/App/Diagnostics/motor_bench.c`、`motor_bench_pwm.c`、`motor_bench_main.c`。
- 工程／构建修改3个：`control/MDK-ARM/yeye_control.uvprojx`、`control/Core/Inc/stm32f4xx_conf.h`、`control/tools/build_keil.ps1`。
- 官方库新增4个：`control/Drivers/stdperiph/inc/stm32f4xx_tim.h`、`stm32f4xx_iwdg.h`；`control/Drivers/stdperiph/src/stm32f4xx_tim.c`、`stm32f4xx_iwdg.c`。来源记录修改2个：`control/Drivers/README.md`、`control/Drivers/stdperiph/source_manifest.json`。
- 电脑检查新增2个：`control/Tests/Host/test_motor_bench.c`、`control/tools/run_motor_bench_tests.ps1`。
- 文档新增／更新8个：`control/docs/motor_bench.md`、`control/README.md`、`control/docs/keil_quickstart.md`、`control/docs/pin_plan.md`、`control/docs/standard_library.md`、`control/docs/validation.md`、`hardware_preparation/dual_motor_wiring_guide.md`、`project_planning/project_status.md`。

本地版本位置：`D:/Projects/yeye`，分支`main`，HEAD `82640aba4cf7aa4f30db14b486aef852936118fe`加上述未提交修改。没有提交、切分支或上传；BIN与日志在本机被忽略目录，不会随Git自动同步。原board.c、board.h、main.c、car.c、protocol.c、board_self_test.c没有改动。

## 9. 全图形操作：Keil5编译＋USB DFU烧录

本节由00于2026-10-20按主控偏好补充。已核对工程MotorBench的CreateHexFile=1、输出名motor_bench及输出目录；未安装新软件、改动工程或操作板卡。STM32CubeProgrammer在两处Windows常用安装路径未找到，不据此认定其它路径也未安装；可先从开始菜单查找，没有时从[ST官网](https://www.st.com/en/development-tools/stm32cubeprog.html)取得Windows版本并按安装器提示安装。

1. 电池XT30拔开、驱动OFF，仅电脑USB连接天空星；保持第2节的接线及电气检查条件。
2. 双击`D:/Projects/yeye/control/MDK-ARM/yeye_control.uvprojx`，目标下拉选择MotorBench。点击Project → Build Target（F7）；底部Build Output应显示0 Error(s), 0 Warning(s)。工程已启用Create HEX File，生成`D:/Projects/yeye/control/firmware/build/motor_bench/motor_bench.hex`。本图形路线使用刚生成的HEX，不依赖命令行导出的BIN。
3. 按住BOOT0，按下并松开RESET，再松开BOOT0。打开STM32CubeProgrammer图形程序，右上连接方式选USB，刷新端口列表，选择实际识别到的USB1／对应端口，点Connect。识别应与当前STM32F407及512KiB内部Flash相符。未识别时检查数据线、ROM下载步骤及软件配套DFU驱动；连接失败不继续烧录。
4. 在Memory & File editing中读取内部Flash，起点0x08000000、总长度0x80000（524288字节／512KiB），用Read All或对应地址范围读取后Save As保存为新的before_motor_bench_日期时间.bin。不要覆盖10-14历史备份；读取失败先停止，不运行读保护解除或Option Bytes操作。图形版本控件名称可有差异，保存范围应为0x08000000–0x0807FFFF。
5. 打开Erasing & Programming，Browse选择第2步刚生成的motor_bench.hex。HEX内含地址，应指向内部Flash 0x08000000；勾选Verify programming，不勾Skip flash erase before programming，首次不勾Run after programming，不另外点Full chip erase。点Start Programming；等写入及校验均成功，失败保持电池拔开。
6. 点Disconnect，确认BOOT0松开，按RESET。观察PB2用户灯每组闪1次。当前程序没有USB串口，运行后DFU连接消失不单独算故障。到此完成软件下载，继续第5节的电气检查和A／B／AB试转，不能跳过。

如果改为只在Keil内点Flash → Download，使用已购DAPLink经SWD连接主板，并核对供电隔离、实际针位、CMSIS-DAP Debugger、SW端口和512KB算法；原版SWD下载已获Verify OK，本轮R2按第12节复验。普通USB直连与SWD属于不同下载路径，本节不自动启用DAPLink、不修改其电源设置。

官方依据：[ST图形程序与USB DFU支持](https://www.st.com/en/development-tools/stm32cubeprog.html)、[Memory and file edition：读取与Save As](https://dev.st.com/stm32cube-docs/prog/2.23.0/en/docs/markup/CubeProg_UserManual/Memory_file_edition.html)、[ST UM2237程序手册](https://www.st.com/resource/en/user_manual/dm00403500-stm32cubeprogrammer-software-description-stmicroelectronics.pdf)、[Keil CMSIS-DAP说明](https://www.keil.com/support/man/docs/dapdebug/default.htm)。

## 10. 本轮首选：DAPLink＋Keil5直接下载

00按主控偏好补充、01按R1更新，2026-10-20。使用原清单的立创DAPLink同时供电与SWD下载，天空星自身USB不接。原版已有Programming Done／Verify OK记录，但未通过自主启动；R1下载／启动仍待主控复验。下面仅为人工步骤，本次未改本机Keil设置或访问板卡。

### 10.1 接五根线：一路5V供电＋SWD

先拔开电池XT30、主板USB与DAPLink USB，再用杜邦线逐根连接：

| DAPLink功能标识 | 天空星主板调试口 | 官方连接器端点 |
| --- | --- | --- |
| 5V0／5V输出 | 5V／PIN_IN_+5V | H1.7 |
| DIO | SWDIO／PA13 | H1.5 |
| CLK | SWCLK／PA14 | H1.3 |
| GND | GND | H1.4或H1.6 |
| RST | NRST | H1.9 |

H1针号来自[官方调试口原图](evidence/2026-10-18_c02a/schematic_20240815_044555.png)，不是芯片脚号，不能按背面照片左右猜。U1R/U1T是串口，不是SWD。DAPLink的5V0和3V3都属电源输出，本方案只接5V0→主板5V，3V3留空；不将5V接3V3、BAT+或任何信号脚。TXD、RXD、SWO也不需要。本轮用独立线，不整条插含5V与3V3的10芯线。

五线核对后，只将DAPLink USB插电脑，天空星Type-C保持空着；电池继续拔开，BOOT0松开，无需进入DFU。主板经原有地线继续与电机驱动共地；驱动5V与3V3继续不接主板。DAPLink只带天空星逻辑负载，不给电机或视觉供电。后续动力仍按第5节由独立电池供给；其中旧“主板USB供电”字样在本接法下改为“DAPLink 5V供主板”。

### 10.2 一次性Keil设置

1. 打开现有yeye_control.uvprojx，选MotorBench。Options for Target → Debug中，选择Use旁的CMSIS-DAP Debugger，不用Use Simulator。
2. 点Settings，选择实际出现的LCKFB DAPLink／CMSIS-DAP设备；Port选SW，Max Clock先选1MHz。右侧SW Device应出现IDCODE（官方天空星示例为0x2BA01477）。只看到下载器而无SW Device时，先检查目标供电、DIO/CLK/GND、BOOT0和连线，不继续下载。
3. 在Flash Download页确认STM32F4xx 512KB算法，起点0x08000000、大小0x80000；若列表为空，从Add添加对应512KB算法。勾选Program、Verify、Reset and Run，Erase选择Sectors而非Full Chip。
4. 返回Options for Target → Utilities，启用Use Debug Driver。各层点OK保存MotorBench目标设置。

### 10.3 编译、下载与运行

点击Project → Build Target（F7），0错误0警告后点Flash → Download／工具栏下载图标。Keil直接加载当前目标，无需手选HEX或BIN，不用终端和CubeProgrammer。应看到Erase Done、Programming Done、Verify OK及运行／下载结束提示；无Verify成功不进入动力测试。

R3下载后按第13节无动力确认版本、运行并采集，整轮电池保持断开。原理图与Verify OK只说明下载／校验，不表示管脚波形或台架通过。动力接通时不进调试、单步、暂停或打断点。

官方依据：[立创DAPLink引脚及Keil设置](https://wiki.lckfb.com/zh-hans/fdb/lckfb-daplink-emulator.html)、[Keil Flash Download配置](https://www.keil.com/support/man/docs/uv4cl/uv4cl_fl_usingflashmenu.htm)。

## 11. C-02B-R1：纯Keil重新下载与无动力启动复验（历史）

本节保留R1当时的版本值与验收要求。主控已回报R1绿灯恢复；当前R2下载与版本值按第12节，不把0x020B0001当作30%版本。R1当时不接电池、不触发试转，先把“自主启动正常”作为单独验收。旧版Verify OK已经确认，无需反复刷旧文件，也不重新询问既定型号。

### 11.1 准备与重新下载

1. 主控保持电池XT30拔开、驱动开关OFF。沿用第10.1节五线：DAPLink 5V0→H1.7的5V、DIO→H1.5、CLK→H1.3、GND→H1.4或H1.6、RST→H1.9。DAPLink 3V3不接；天空星Type-C空着；两板地线保留，驱动5V／3V3不接主板。需要核对接线时先拔DAPLink USB，不带电挪线。
2. 打开`D:/Projects/yeye/control/MDK-ARM/yeye_control.uvprojx`，若在调试界面，先用Debug → Start/Stop Debug Session（Ctrl+F5）退出，再选 **MotorBench**。不要更换成其他目标。
3. Project → Rebuild all target files，确认0错误0警告；本次R1应为Code4672、RO424、RW48、ZI1048。若显示原版Code4216或没有新代码，先检查工程路径与保存状态，不下载旧版本。
4. Options for Target → Debug保留CMSIS-DAP、Port=SW、Max Clock=1MHz及可识别的SW Device。Flash Download保持STM32F4xx 512KB算法、地址0x08000000，Program／Verify／Reset and Run；Utilities使用Debug Driver。不改Option Bytes，不为了消除停机症状关闭看门狗。
5. 点Flash → Download，Keil使用`build/motor_bench/motor_bench.axf`；记录新的Programming Done、Verify OK及下载时间。不要手选旧HEX或BIN，**Verify OK仍不是本轮启动通过结论**。

### 11.2 先做不依赖调试器运行状态的断电启动

1. 保持BOOT0和WKUP松开，不进入调试；若仍在调试会话中，先退出。
2. 拔DAPLink的USB，使天空星真正断电，等板上指示灯熄灭后再插回。此时只供逻辑主板，电池一直拔开；不要以Keil Reset／Run to main代替独立断电重启。
3. 手不碰WKUP，观察约10s。连续松键约1s后应进入READY，PB2绿色用户灯每2.5s一组亮100ms、每组仅1次；首次亮起可能在约2.5s。电源红灯常亮不作为程序心跳证据。
4. 保存“未进入调试、断电重启”的短视频与现象。如果用户灯仍不闪、持续快闪或反复重启，仍判启动未通过，保持电池拔开，按下节采集诊断值；不要长按WKUP尝试消除故障。

### 11.3 再采集运行中的Watch，和自主启动证据分开记录

1. 仍无动力，Ctrl+F5进入硬件调试，先禁用已有断点。Run to main开启时可能先停在main；此时尚未完成初始化，毫秒为0正常，先建立Watch再按F5运行。
2. View → Watch Windows → Watch 1加入：`g_motor_bench_revision`、`g_motor_bench_ms`、`g_motor_bench_fault`、`g_motor_bench_watchdog_started`、`g_motor_bench_watchdog_stage`、`g_motor_bench.state`、`g_motor_bench.raw_candidate`、`g_motor_bench.output_mask`。
3. 勾选View → **Periodic Window Update**，按F5保持Run，等数秒。在运行中记录两次Watch值或视频，不用长时间Stop再判断计时。若窗口不更新，先检查该选项和Run状态；不把暂停后的静止值当作CPU启动故障。
4. 正常R1应满足下表。不要通过在Watch里改值、强设fault=0或修改IWDG状态位来“通过”。本修复没有增加调试停机冻结看门狗：Stop／断点可能改变IWDG行为或引发复位，必须与独立上电结果区分。

| Watch项 | 正常R1期望 |
| --- | --- |
| g_motor_bench_revision | 0x020B0001，说明R1应用已执行；停在main入口前可能仍为0 |
| g_motor_bench_ms | Run期间持续增加，两次读数有增长，不反复归0 |
| g_motor_bench_fault | 0 |
| g_motor_bench_watchdog_started／stage | 1／4，表示IWDG已启用且配置更新完成 |
| g_motor_bench.state | 连续松键1s后READY，枚举值1 |
| raw_candidate／output_mask | 不按键时0／0，初始化不应产生试转输出 |

### 11.4 失败代码与返回证据

`g_motor_bench_fault`为可组合的粘性位：1=PWM时钟不符合固定配置，2=TIM5启动时基失败／轮询保护触发，4=LSI等待超时，8=IWDG更新超时，16=SysTick配置失败。例如3表示1与2同时发生。非零时保持ABORTED及电机00，不进入READY，用户灯可用时快闪。LSI失败时IWDG尚未启用；IWDG已启动后更新超时，故障分支继续喂狗以保留诊断，但绝不允许试转，CPU／滴答停滞时仍会复位。

stage为最后的IWDG初始化阶段：0尚未建立时基，1时基就绪，2LSI就绪，3IWDG已启动／等待更新，4更新完成。LSI和PVU/RVU各由独立TIM5 1MHz计时最多10ms，**不用尚未启动的SysTick**；TIM5自身不运行会在有限检查中返回2，等待中若时基停滞还有轮询次数保护。该次数保护不是精确毫秒指标。

主控返回：新Keil编译与Verify日志、下载时间、是否退出调试并真正断电重启、用户灯约10s视频、运行中两次Watch读数、上述故障位／阶段。只有主控确认`ms`持续增长、`fault=0`、松键后READY及每组1次用户灯，才可把R1实物启动标为通过；否则继续暂停动力测试。

R1修复及电脑模型不能证明实物PVU/RVU时序、TIM5频率、IWDG复位时长或引脚电平。R1当时的AXF／HEX／BIN信息和故障复现结果见[修复记录](motor_bench_startup_issue.md)及[验证记录](validation.md)。运行中Watch更新依据[Keil官方Watch说明](https://www.keil.com/support/man/docs/uv4/uv4_db_dbg_watchwin.asp)。

## 12. C-02B-R2：纯Keil下载30%版本，首轮只测A一次（历史）

2026-10-21现场更新：主控已回报本轮Verify OK、绿灯正常，并确认电池已与UC2断开、完全冷却且无鼓包／异味／接头变形。此前UC2本体特别烫的原因仍待核查，UC2继续停用；主控完成本轮A后回报完全无动作、无声音，起转验收未通过；现在停止动力复测，驱动OFF拔XT30，不继续B／AB，按I-05先做电气定位。本确认不代替电气测量，不把UC2发热认定为电机未转根因。

本节保留R2当时操作与版本；当前R3按第13节无动力采集，不再按本节接电池。R2版本`0x020B0002`，固定30%／20kHz／500ms；主控已回报Verify OK、绿灯正常，板内Watch版本尚未逐项回报，A试转完全无动作／无声音，进入电气定位。原15%未转现象保留，不认定根因。A／B是桥编号，不等于左右轮或车辆前进。

### 12.1 重新编译与Download（全程无动力）

1. 主控拔开动力电池XT30、驱动OFF。沿用已用的DAPLink五线：5V0→H1.7主板5V、DIO→H1.5、CLK→H1.3、GND→H1.4或H1.6、RST→H1.9。天空星Type-C和DAPLink 3V3留空；两板共地、驱动5V／3V3不接主板。不要求重新拍照或识别型号，挪线前先断全部电源。
2. 用Keil打开`D:/Projects/yeye/control/MDK-ARM/yeye_control.uvprojx`。若在调试中先Ctrl+F5退出，再选 **MotorBench**。打开motor_bench_pwm.h应见`MOTOR_BENCH_DUTY_PERMILLE 300u`；motor_bench_main.c版本赋值应为`0x020b0002u`。
3. 点击Project → **Rebuild all target files**。底部应0错误0警告，Code4672、RO424、RW48、ZI1048。R1与R2代码大小相同，仅看大小不能判断是否新版；确认打开的文件来自本项目目录。
4. 沿用第10.2节CMSIS-DAP、SW、1MHz、STM32F4xx 512KB算法（0x08000000／0x80000）、Program／Verify／Reset and Run和Utilities的Use Debug Driver。点击 **Flash → Download**，记录新的Programming Done、Verify OK及时间。Keil直接使用当前目标的`build/motor_bench/motor_bench.axf`，无需终端或手选HEX／BIN，不改Option Bytes。

### 12.2 确认R2实际运行，再退出调试独立重启

1. 电池保持拔开。需要确认板内版本时，Ctrl+F5进入硬件调试，禁用已有断点，Watch加入`g_motor_bench_revision`、`g_motor_bench_ms`、`g_motor_bench_fault`、`g_motor_bench_watchdog_stage`、`g_motor_bench.state`、`g_motor_bench.output_mask`。Run to main停在入口时变量尚未初始化，不能在这里判失败。
2. 勾选View → **Periodic Window Update**，按F5保持运行。应为版本`0x020B0002`、ms持续增加、fault=0、stage=4，KEY松开约1s后state=READY(1)、output_mask=0。记录运行中读数，不在Watch强改值。旧值0x020B0001表示仍是15%版本，不接动力继续试。
3. **Ctrl+F5退出调试**，BOOT0、KEY均松开。拔DAPLink USB至主板灯熄灭，再插回；不要以暂停／Run to main代替独立启动。电池一直拔开，观察约10s，用户绿灯应每2.5s一组闪1次。无正常待机、fault非零或反复复位则停止，不接电池。

### 12.3 一次A试转及停止条件

1. 主控确认Keil已退出调试，电机及板卡固定、轮子悬空、线束远离轴；驱动OFF时连接2S电池XT30，再开启驱动。DAPLink仍只供主板，不能代替动力电池。先不按键，任何自行转动／发热／复位异常立即OFF并拔XT30。
2. 灯每组1次时，只按一次 **KEY长按约1–2s到常亮，再松开**。按住时不转，松开稳定30ms后应仅A桥固定30%输出500ms，再撤输出00滑行；运行中再按KEY会立即停止并锁定。需要切断动力时直接驱动OFF／拔XT30，不只拔主板供电。
3. 观察并记录是否有实际转动、声音、抖动、哪只电机及方向、撤输出后是否滑行停稳。灯推进到每组2次只表示程序进入待B，**不能作为A起转成功**。
4. **A仍不转或只抖动：立即结束本次试验，驱动OFF并拔XT30，不继续B／AB、不重复触发、不再加占空比或延长500ms。**由硬件借仪表补测供电与实际输入／输出后再定位；现场无仪表不填写电压或PWM通过。
5. 首轮到此返回A一次的结果。程序保留B／AB次序，后续仅在A实际正常并停稳后才考虑B，B实际正常并停稳后才考虑AB；任何失败都不以灯提示替代验收。

返回00：R2编译与Verify日志／时间、Watch版本与待机结果、是否退出调试并独立重启、动力电池及ON状态、A一次的视频与声音／抖动／转动／方向／停稳、是否已断动力。没有现场结果前，本版只标“电脑验证通过，起转待测”。完整新产物哈希及修改清单见[R2交付记录](motor_bench_r2_task.md)。

## 13. C-02B-R3：动力电池拔开，采集一次A的保留快照

### 13.1 纯Keil下载、运行与采集

1. 主控保持**驱动OFF、动力电池XT30拔开、UC2断开**，整轮不连接动力电池。沿用DAPLink五线供主板：5V0→H1.7、DIO→H1.5、CLK→H1.3、GND→H1.4或H1.6、RST→H1.9；天空星Type-C及DAPLink 3V3留空。两板公共地和既有四控制／四编码器线保留，驱动5V／3V3不接主板。无需重新识别型号或索要照片。
2. Keil打开`D:/Projects/yeye/control/MDK-ARM/yeye_control.uvprojx`。若在调试中先Ctrl+F5退出，选 **MotorBench**，点击Project → **Rebuild all target files**。应0错误0警告，Code5208、RO424、RW64、ZI1288；main版本赋值为`0x020b0003u`，PWM仍300‰、周期800，运行时间仍500ms。
3. 沿用第10.2节CMSIS-DAP／SW／1MHz／STM32F4xx 512KB（0x08000000，0x80000）及Utilities的Use Debug Driver，点 **Flash → Download**，保存新的Programming Done、Verify OK及下载时间。不改Option Bytes，不手选旧HEX／BIN，不使用终端。
4. Ctrl+F5进入硬件调试，禁用已有断点。打开View → Watch Windows → Watch 1，加入下方列表；勾选View → **Periodic Window Update**，按F5保持Run。Run to main停在入口时变量尚未赋值，先运行再读。KEY松开约1s后应版本0x020B0003、ms递增、fault=0、state=READY(1)，用户灯每组1次；此时请求／启用计数为0、两份valid=0才是未触发的正常值。
5. **电池一直拔开**。只做一次原KEY动作：长按约1–2s到灯常亮，再松开；不要再按KEY，也不要按RST／BOOT0。等待约3s，软件已结束A的500ms窗口并显示每组2闪。此时电机无动力，不转是预期，观察目标是保留数据。
6. 保持Run，以Periodic Window Update读取并展开`g_motor_bench_pwm_diag`中的active、stopped，保存完整Watch截图（可分多张）。无需在500ms窗口暂停、打断点或追读实时TIM1，因为实时寄存器已被停止路径清零。两次间隔读数中ms应增长，而计数／快照保持不变。先保存截图，再Ctrl+F5退出调试；不要在保存前RESET、断电或重新进入会话，以免RAM证据清零。
7. 若窗口不能可靠实时读取，保持动力断开并回报窗口状态；不强改Watch中的输出、fault或状态，不改用接电池调试、不延长窗口。输出启用0次／快照异常也先保存，不连跑B／AB或反复触发。00依据回报决定01修复或I-05电气测量。

Watch可复制列表（最后一项为结构体，点击其左侧展开箭头）：

```text
g_motor_bench_revision
g_motor_bench_ms
g_motor_bench_fault
g_motor_bench.state
g_motor_bench.output_mask
g_motor_bench_pwm_diag
```

### 13.2 字段含义与一次A的期望

下表用`D`简称`g_motor_bench_pwm_diag`，不是另一个Watch变量。`.active`为启用调用返回、切AF和MOE操作之后的实际读回；`.stopped`在关闭MOE、清CCR／UG、写GPIO低并切GPIO输出全部执行后读回。二者不相互覆盖。每份20个寄存器逐项读取，不是同一时钟沿的原子快照；valid最后写1只表示完整采集，不表示寄存器符合期望或电机已转。

| 少量关键项 | 一次A正常软件路径的期望／解释 |
| --- | --- |
| 版本、fault、live output_mask | 0x020B0003、0、停止后0；live state最终READY(1)，但stopped.state通常是刚停止时WAIT_RELEASE(0)，active.state为RUNNING(4) |
| D.request_count／enable_calls／enable_count／stop_count | 均1：分别为新非零mask请求、实际执行返回的MOE启用调用、读回MOE=1的次数、启用后停止事件次数；1ms相同mask不重复累计，均不等于电机转数 |
| D.active.valid／stopped.valid及run_id | 两个valid均1、run_id均1，配对同一次A；未启用时valid为0，不把全0当作成功。下一次启用替换最后一组，复位清零 |
| D.last_mask、start_ms／stop_ms／elapsed_ms／stop_reason | mask=1；start／stop为实际软件滴答，差及elapsed应500；reason=1。两帧的mask=1标记本次A，不表示停止后仍输出 |
| D.active.tim_cr1／tim_psc／tim_arr／tim_ccer | CR1 bit0(CEN)=1；PSC=0，ARR=799；CCER通常0x1111，四普通通道使能、高有效。CEN也可能在停止后仍为1，停止靠MOE及GPIO，不能只看计数器是否运行 |
| D.active.tim_bdtr及tim_ccr1–4 | BDTR bit15(MOE)=1；CCR为(240,0,0,0)。B／AB不是本轮步骤；预留程序对应(0,0,240,0)／(240,0,240,0) |
| D.active.gpio_moder／gpio_afrh | 只看四脚：`MODER & 0x3CCC0000 = 0x28880000`（AF）；`AFRH & 0x0FF0F0F0 = 0x01101010`（四脚AF1）。其它脚不拿全端口常量硬比 |
| D.stopped.tim_bdtr／tim_ccr1–4／gpio_moder／gpio_odr | MOE bit15=0，四CCR全0；`MODER & 0x3CCC0000 = 0x14440000`（GPIO输出）；`ODR & 0x6A00 = 0`。stopped.valid／stop_count仅标记执行与读回，必须检查这些实际值 |

补充寄存器在结构体中保留：TIM1 CCMR1／2（PWM1／预装载）、CNT，GPIOE OTYPER／PUPDR／ODR／IDR，以及RCC AHB1ENR／APB2ENR。正常GPIOE时钟AHB1ENR bit4=1，TIM1时钟APB2ENR bit0=1。ODR在AF活动时也可以为0，不能拿ODR=0认定无PWM；IDR只是一瞬间的数字读数，读到0或1都不能单独证明20kHz、30%或真实电压，故不增加长轮询／固定相位采样。

停止原因：0=无结束；1=500ms超时；2=运行中KEY原始电平停止；3=粘性fault分支；4=卡键／状态逻辑中止；5=桥mask切换预停；6=无专用原因的直接停止；7=CPU异常停止；8=非法mask。2–8出现时保存对应state／fault和帧，不强改为1；异常复位可能清掉RAM证据，不能保证跨复位保留。

### 13.3 返回00的判定表

| 观察结果 | 当前边界与下一步 |
| --- | --- |
| 版本不符、ms不增长／反复归零或fault非0 | 当前没有可信的一次正常采集；保留版本、fault、状态及是否Run，先由01核查，不反复触发 |
| request_count=0、active.valid=0 | 未记录新非零PWM请求；结合KEY、state和灯态查软件触发边界，不推断外部供电 |
| request_count>0但enable_calls=0；或enable_calls>0但enable_count=0／MOE=0；或配置字段不符 | 请求／启用边界或实际寄存器读回异常；返回两帧和计数交01定位，不能填“PWM正常” |
| 活动配置符合，停止后MOE／CCR／GPIO也符合，elapsed=500且reason=1 | 已取得板内走过启用与停止路径的证据；仍不能证明排针、外接线、驱动或电机正常，转02／硬件I-05测真实供电与输入／输出 |
| 活动符合但停止帧缺失／读回不符或reason异常 | 保存所有字段，继续保持动力断开，交01核查停止路径，不进入动力复测 |

主控返回：新编译／Verify日志与时间、始终拔电池的确认、上述Watch截图、KEY动作及灯态。当前仅电脑验证完成，尚未取得R3实板快照；真实频率／电压与电机起转保持未通过。详细实现、测试、产物哈希见[R3交付记录](motor_bench_r3_task.md)。
