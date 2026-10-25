# MotorDirect：不用PWM的A桥单次起转诊断

> 2026-10-25目录迁移：现行独立工程为[control/MDK-ARM/motor_direct.uvprojx](../MDK-ARM/motor_direct.uvprojx)，新输出在control/build/firmware/motor_direct。目标、版本和行为未变；以下10-24产物哈希与日志路径按历史记录阅读，新AXF调试路径已变化，BIN／HEX迁移前后相同。迁移结果见[ORG-02](../../project_planning/tasks/ORG-02.md)。

日期：2026-10-24（北京时间）。维护：主控／01。状态：代码、编译和电脑检查完成，下载／板级／电机结果待主控。依据：主控本轮表示暂时无法去实验室，要求用不用PWM的方法快速验证；沿用已确认硬件、九线、DAPLink和Keil5。全部成果仅本地保存。

**目标找不到时的最新入口：直接打开[独立工程 motor_direct.uvprojx](../MDK-ARM/motor_direct.uvprojx)，其中只有MotorDirect一个目标。** 主控反馈原工程找不到目标后，实际核对磁盘文件已回到五目标，而Keil打开路径正确；没有证据确定由哪次保存覆盖。已备份当时配置、恢复原工程第六目标，并建立不受原窗口保存影响的独立入口。两入口链接相同源码、宏与输出目录，固件逻辑未改；独立入口已实际编译0错误0警告。

操作时动力电池保持拔开，先退出调试（如正在调试按Ctrl+F5），再Project → Open Project打开上述独立工程；若关闭旧工程询问保存，当前这次选No，避免旧窗口覆盖恢复的多目标工程。载入后目标栏应直接显示MotorDirect。新入口沿用CMSIS-DAP及已验证下载配置，本机uvoptx仍为忽略文件；换电脑按下文核对调试器。

## 方法与边界

新增独立Keil目标 **MotorDirect**，版本 **0x020B2001**。不使用TIM1／PWM／AF，直接用SPL普通GPIO将PE9置高、PE11／PE13／PE14保持低，让AT8236 A桥按10状态导通；**KEY人工触发一次，500ms后四脚归低并锁定，不循环、不进入B／AB**。再按KEY可提前停止并锁定。复位后也不会自动续跑。

GPIO只提供约3.3V控制电平，电机仍由驱动板和原2S电池供电；不能把电机接PE9或主板3V3／5V。本目标相当于外部满导通控制，强于原30%PWM，电机可能突然起转，轮子必须悬空并固定车架／电机。芯片自身限流／保护仍可能关断内部功率管，不承诺绕组始终得到理想电池电压。

**这条方法仍经过AT8236，不能独立排除驱动板。** 能转说明电机在当前供电／驱动链下能起转；不转仍可能是驱动供电、保护、输出、线束或电机等条件，不能直接判电机坏。彻底隔离电机的[限流电源测试](../../hardware_preparation/motor_dc_check.md)继续留待设备具备，不在家用裸线碰接电池替代。

本次方法由主控最新要求选定，只有新目标使用固定高／低电平；原MotorBench 30%／20kHz／500ms和MotorContinuous 30%／20kHz持续目标均保留。没有声称原PWM不转根因已解决。

## 原接线与灯态

| 驱动输入 | 天空星丝印／端口 | 本目标初始化／停止 | 人工运行的500ms |
| --- | --- | --- | --- |
| AIN1 | E09／PE9 | GPIO低 | GPIO高，不是PWM |
| AIN2 | E11／PE11 | GPIO低 | GPIO低 |
| BIN1 | E13／PE13 | GPIO低 | GPIO低 |
| BIN2 | E14／PE14 | GPIO低 | GPIO低 |

AIN2／AIN1／BIN2／BIN1在驱动左下从上到下排列；沿用[完整接线自查表](../../hardware_preparation/motor_wiring_self_check.md)，不重认型号或重新分配端口。**若此前测电阻／准备独立电机测试时拔过A的线，必须在全部断电时按原标记复原**：M1→AO1、M2→AO2、G→GND、V→3V3、B→E1B、A→E1A。电机端编码器的A／B不是AIN控制针。

主板仍仅由DAPLink五线供电，Type-C空着；驱动5V／3V3不接主板，原共地保留；驱动动力来自2S XT30。KEY即PA0／WKUP用户按键，PB2为用户绿灯。

| 情况 | 绿灯／输出 |
| --- | --- |
| 上电、KEY松开约1s后待机 | 每2.5s一组闪1次，无电机输出 |
| KEY长按过程中 | 先快闪，满约1s变常亮；还需松开才输出 |
| 松开消抖后运行 | 常亮，A桥固定电平，最长500ms |
| 正常500ms结束 | 慢闪（亮／灭各约500ms），完成锁定；再按也不重启 |
| 运行中按KEY／按住超过5s／故障 | 快闪锁定、四输入低；需先断动力再复位重来 |

00为滑行／休眠，不保证车轮机械瞬间停稳。复位最初GPIO高阻，驱动下拉与真实复位窗口仍属于实物验证范围。

## 主控纯Keil操作

1. **驱动OFF、XT30电池拔开，UC2断开**；恢复原接线时也拔DAPLink USB／主板Type-C。接线复原后只接DAPLink USB给主板供电，动力继续断开。
2. 推荐直接打开`D:/Projects/yeye/control/MDK-ARM/motor_direct.uvprojx`，目标栏直接显示 **MotorDirect**。原`yeye_control.uvprojx`中第六目标也已恢复，但当前已打开的旧窗口可能仍只有五目标；切换工程时不要保存旧窗口覆盖磁盘，按页首步骤打开独立入口。若正在调试先Ctrl+F5退出。
3. Project → **Rebuild all target files**，应0错误0警告，Code3888／RO424／RW64／ZI1184。Options for Target → Debug沿用CMSIS-DAP、SW、1MHz；Utilities使用Debug Driver，Flash Download为STM32F4xx 512KB／0x08000000。新目标已复制已验证配置；Utilities的Update Target before Debugging设为关闭，避免进入调试自动改写，手动Flash → Download仍可用。
4. 点击 **Flash → Download**，等Programming Done、Verify OK。使用的是`control/build/firmware/motor_direct/motor_direct.axf`，无需终端或手动挑BIN。退出调试，电池保持拔开，拔插DAPLink USB让主板独立重启；KEY、BOOT0松开，应进入每组1闪待机。
5. **先做一次无动力按键演练**：KEY长按约1–2s到常亮后松开，应运行提示约500ms后变慢闪锁定；再按不能重新进入运行。若不自动结束、异常复位或灯态不符，保持动力断开并回报，不接电池。必要时无动力Watch核版本见下节，不必重复原目标的大组Watch。
6. 演练结束，动力仍断开时按RST回到待机、松KEY约1s；退出Keil调试，固定车架并悬空轮子。驱动OFF时连接XT30，再打开驱动。未按KEY时不得自行转动；若有非预期输出，立即驱动OFF、拔XT30。
7. 待机每组1闪时，只做一次 **KEY长按到常亮→松开**。预期仅A短时动作，500ms内自动归零／慢闪锁定；运行中再按KEY也能提前停止。无论是否转动，本次完成后驱动OFF、拔XT30。完全不转／仅抖动时不复测B／AB、不自行延长500ms或反复复位尝试。拍一段包含KEY动作、灯及轮子的视频最有用；不要为等万用表读数而延长试转。

停止保护没有编码器堵转／电流／温度检测；独立看门狗用于CPU／滴答停滞，不能当作电机限流器或保证机械停稳。实车在地面运行不属于本目标。

## 可选Watch与实际读回

仅在电池拔开时进入硬件调试，保持F5 Run／Periodic Window Update，不暂停CPU、强改变量或在动力接入时打断点。读`g_motor_direct_revision`应为0x020B2001、`g_motor_direct_fault`为0、`g_motor_direct_ms`递增、`g_motor_direct_watchdog_stage`为4；旧的g_motor_bench变量不是本入口。

`g_motor_direct_gpio_diag`保存活动与停止后真实GPIO／RCC值，valid最后写1，复位清零。正常一次500ms的待对照值如下，**尚非板上已测结果**：

| 字段 | 待对照值／含义 |
| --- | --- |
| request_count／enable_calls／enable_count／stop_count | 各1；enable_count只证明活动快照ODR中四脚为仅PE9高，不证明实际电压或转动 |
| active.valid／state／fault／mask | 1／4／0／1 |
| active.gpio_moder／gpio_odr | 四脚模式掩码内0x14440000，ODR掩码0x6A00内0x0200，即普通GPIO、仅PE9高 |
| stopped.valid／state／fault／mask | 1／5／0／1；提前KEY停止则state6；停止帧mask1是事件标签 |
| stop_reason／elapsed_ms | 正常1／500；KEY提前停则2／实际软件时差，支持毫秒回绕 |
| stopped.gpio_moder／gpio_odr | 四脚GPIO输出、四位ODR均0 |

AFRH只原样记录，GPIO输出模式下残留AF值不参与输出。IDR也只读一次，不据此承诺0.5秒全程电压。非法请求被拒绝时，原始事件原因可能先记录8，随后全局fault锁存32，不能因事件发生前保存的fault0误判全局无故障。

故障位：1=GPIO时钟检查失败，2=启动TIM5异常／限时轮询，4=LSI等待超时，8=IWDG更新超时，16=SysTick失败，32=非法桥请求／输出未就绪，可组合且不自动清除。错误时保持零输出与锁定。

## 实现、验证与版本位置

新增[motor_direct_main.c](../Core/Src/motor_direct_main.c)、[motor_direct_gpio.c](../Drivers_Custom/Motor/motor_direct_gpio.c)、[接口](../Drivers_Custom/Motor/motor_direct_gpio.h)。新入口单独使用；R1时钟、按键、TIM5限时等待、IWDG顺序等六个函数去除注释／名称差异后与已验证入口代码一致。TIM5只用于启动等待，初始化后停止；TIM库保留是为了R1时基，并非使用PWM。

共享motor_bench.c只在MOTOR_DIRECT_A_TARGET宏下限制step0、500ms后COMPLETE锁定；旧宏行为保留。Keil会把新源文件视作共享文件，已在原五个目标显式Exclude，仅新目标编入独立main／GPIO并排除旧main／PWM，避免多入口或误编译。没有修改官方库或迁移HAL。

实际电脑验证：

- 新目标9个真实main／SysTick／GPIO集成场景通过：人工长按／松开、499／500ms边界、KEY提前停、故障停止、非法阶段／请求锁定、毫秒回绕、上电按住／短按／卡键不启动、实际读回扰动、时钟失败拒绝输出。日志52593次断言含循环中的SPL边界检查，不代表52593种独立场景。模型禁止调用TIM1／AF、禁止置高PE9以外的电机控制脚，不代替实际电气测试。
- 新入口R1启动154项／10场景通过，含PVU／RVU／LSI卡住、启动时基停止、错误时钟及回绕；超时不依赖未启动的SysTick。
- 原持续模型113项／7场景、同宏启动154项、原R3诊断131项／8场景、原台架73项通过。
- 六个Keil目标全部实际构建0错误0警告。MotorDirect Code3888／RO424／RW64／ZI1184；原MotorBench／MotorContinuous BIN与开工逐字节相同，原五目标除新增两源文件的显式排除外，其余配置／文件选项一致；原五份本机调试配置保持一致。
- 真实AXF反汇编有GPIO SetBits／ResetBits路径，无GPIO_PinAFConfig、TIM输出比较／CCR／MOE调用路径；官方来源文件哈希及文档检查见本地检查摘要。

产物在`D:/Projects/yeye/control/firmware/build/motor_direct/`，版本0x020B2001：

| 文件 | 字节 | SHA256 |
| --- | --- | --- |
| motor_direct.axf | 384656 | `142e7ccb7c3bc37dab12c979e391ab7fa3ae398c47e308a8549523a26f2c5d11` |
| motor_direct.hex | 12365 | `a6e5c5ff52b64597de72fbc3bc3c321a25a9f2c931f04d6b8c01a0e82b7b4fff` |
| motor_direct.bin | 4376 | `6377f00d7f9ff812a6d22ccd5c86217cd0b694092a8dce7cdc6eadb0b134fc9a` |

上述AXF为独立工程入口重建后的当前哈希，原交付AXF为125e0bf6…；BIN／HEX逐字节相同，版本及运行逻辑不变。入口修复前工程／调试配置备份与摘要在`control/build/motor_direct_entry_repair/`，独立入口构建日志为`control/firmware/build/MotorDirect_entry_build.log`。

开工工程、uvoptx、共享状态机及旧产物在本地忽略目录`control/build/motor_direct_baseline/`；新测试日志`control/build/motor_direct_tests.log`、`motor_direct_startup_tests.log`；构建日志`control/firmware/build/MotorDirect_build.log`；反汇编及检查摘要`control/build/motor_direct_*`。uvoptx及产物被Git忽略，换电脑应按本节核对调试器。主控当前设备沿用已验证DAPLink，无需换下载链路。

本地main加未提交修改，未切分支、提交、推送、跨聊天发送、自动烧录或操作板卡。主控回报：目标／Verify结果、无动力是否500ms后慢闪锁定、仅一次A是否转／抖动／声音、是否自动停及已OFF拔电池。未收到这些现场结果前不标起转成功或电机损坏。

资料：[AT8236厂家内容第5页](../../hardware_preparation/evidence/2026-10-18_i03/at8236_datasheet.pdf)的10／00逻辑（[第三方托管原厂PDF](https://atta.szlcsc.com/upload/public/pdf/source/20210923/1552D95CBAF8BE780D06AE79E7783380.pdf)）；[MD310Z20厂家资料](https://www.yahboom.net/study/MD310/14018/)推荐7.4V、范围4.2–8.4V；[当前引脚资源](pin_plan.md)与既有接线。不将厂家参数或电脑模型填成现场实测。
