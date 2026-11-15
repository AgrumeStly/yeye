# OLED12864四线接线

**2026-11-10点亮结果：**已新增并下载独立OledBench，实际地址0x3C、通信错误0、写帧计数持续增加；主控确认“完全清晰符合预期”，独立点亮验收完成。[操作入口](../control/docs/oled_bench.md)、[实板与画面证据](../testing/2026-11-10_oled_bench/record.md)。当前诊断使用PB8/PB9开漏GPIO软件I²C，不配置AF4，不占用TIM4；下文硬件I2C1/AF4表为这些引脚可用的复用功能。接线与查询阶段尚无驱动的历史过程保留并注明阶段。

日期：2026-11-10（北京时间）。接线反馈：主控／02；供电与线束复核：硬件；驱动适配：主控／01。依据：主控确认新增车载OLED12864，四针GND／VDD／SCK／SDA；主板沿用天空星STM32F407VET6青春版。安装事实见[已部署清单](deployed_hardware.md)。

接线阶段：2026-11-10主控收到本页四线接法后反馈“已接好线”，对应下表GND→GND、VDD→3V3、SCK→B08、SDA→B09。当时未取得照片／导通／电压／I²C或点亮证据。主控随后补充0.96寸、DAPLink已连接并要求联网查询；该查询阶段没有操作板卡。之后已获明确编程与无动力验证授权并实际点亮，当前结果见页首；未单独补测电压／逐线导通。

## 主板接哪里

按常见四针I²C OLED模块安排，SCK作为I²C时钟SCL使用。厂家、供电范围、控制芯片及地址须按实物说明核实，不预先认定SSD1306／SH1106或固定地址。

| OLED丝印 | 天空星板背丝印 | MCU／官方排针 | 用途 |
| --- | --- | --- | --- |
| GND | GND | P2.37，或同一主板其他空闲GND | 公共地，不接AGND或BAT |
| VDD | 3V3 | P2.40，+3V3 | 主板3.3V电源，不接5V、BAT或动力电池 |
| SCK | B08 | PB8，P2.21 | 时钟；硬件I2C1_SCL可用AF4 |
| SDA | B09 | PB9，P2.20 | 数据；硬件I2C1_SDA可用AF4 |

本方案按支持3.3V的四针模块设计；若实物说明明确不支持3.3V，应重新核对电源与总线上拉电平，不能因不亮直接改接5V。主板3V3仅给本模块供电，不与驱动板3V3输出并联。

寻找位置可对照[板背照片](evidence/2026-10-18_i03/photo_03_controller.jpg)：保持照片方向（文字朝上、底部调试口朝下），左侧长排针中段有“B09／E00”一行，其下一行是“B07／B08”。**B09与B08并非同一行**；B08紧邻编码器已用的B07，逐针按完整丝印识别。板背照片与原理图左右镜像，P2是连接器号，不是芯片脚号。

## 接线与软件边界

1. 主控将驱动置OFF，断动力电池、DAPLink USB、主板Type-C及视觉板电源，整车无电后接线；按模块丝印逐根连接，不按线色猜接。
2. 硬件复核无错位／短接；屏幕背面与金属底板绝缘，导线固定且远离转轴。首次点亮保持动力电池隔离，沿用既有DAPLink单源主板供电。
3. 接线阶段旧固件没有OLED驱动，接线本身不等于显示。当前需下载[独立OledBench](../control/docs/oled_bench.md)才显示测试图样；轮速／通信／停因接入运动程序另验。未显示时先核对实际工程、运行与诊断码，不直接判为损坏。

PB6／B06、PB7／B07已用于TIM4编码器，不能照搬其它OLED教程占用。PB8／PB9虽也有TIM4_CH3／CH4复用，本方案选择I²C功能，不占用或重配TIM4计数器。PE9／11／13／14电机控制、PC6／7编码器、PA2／3视觉USART2及SWD／板载按键灯保持原分配。

初次接线查询时已搜索源码，未发现PB8／PB9占用或OLED驱动；随后新增独立SPL显示实现，详见页首入口。未来接入运动时仍需验证屏幕断开／无应答时控制、UART、停车保护正常，不在控制或串口中断中阻塞整屏刷新。

## 来源与验证

- 已查看[归档官方P1／P2原图](../control/docs/evidence/2026-10-18_c02a/schematic_20240815_203023.png)及上述板背照片，确认P2.20=PB9、P2.21=PB8、P2.37=GND、P2.40=+3V3；来源与哈希见[证据索引](../control/docs/evidence/2026-10-18_c02a/README.md)。官方页面本日在线读取超时，本次引出位置按归档原图核对，实物导通待测。
- 本日查阅[ST DS8626 Rev12](https://www.st.com.cn/resource/en/datasheet/stm32f407ie.pdf)及[ST官方LQFP100引脚数据](https://raw.githubusercontent.com/STMicroelectronics/STM32_open_pin_data/master/mcu/STM32F407V(E-G)Tx.xml)，PB8／PB9可作I2C1_SCL／SDA；预留登记在[资源表](../control/docs/pin_plan.md)。
- 比赛第三部分、图1与基本功能60分对应、预期收益及实物验证指标见[已部署清单](deployed_hardware.md#比赛支撑与验证)。点亮、调试量一致性与控制时序回归均待留证，不声称获得加分。

## 0.96寸补充与联网查询结论（2026-11-10）

需要STM32固件中的显示驱动代码，通过I²C发送初始化命令及像素／文字数据；无需为OLED在Windows另装设备驱动。查询当时原工程尚无OLED支持，DAPLink连接本身不会增加显示功能；后续独立OledBench已实现并验证。

依据[Adafruit官方OLED程序说明](https://learn.adafruit.com/monochrome-oled-breakouts/arduino-library-and-examples)，显示库负责底层通信和绘图，接线后还需运行对应程序；其中Arduino安装步骤不能原样用于本项目SPL工程。[DAPLink官方说明](https://daplink.io/)明确其用于Arm芯片程序下载和调试，不承担OLED初始化或绘图。

[Winstar官方0.96寸128×64产品](https://www.winstar.com.tw/products/oled-module/graphic-oled-display/0_96-oled.html)采用SSD1306；[Waveshare官方同尺寸产品表](https://www.waveshare.com/product/displays/0.96inch-oled-module-c.htm)也列出SSD1306及SSD1315等不同控制芯片。因此SSD1306是可优先尝试的软件适配候选，**不能只凭0.96寸断定实物芯片**，也不能用其它厂商页面替代本模块供电规格。

查询后采用动力隔离的独立程序探测I²C应答并验证SSD1306候选初始化／图样，已取得0x3C及主控清晰画面确认；地址应答仍不用于鉴定芯片。查询阶段只回写资料，后续编码、下载及实测按页首证据单独留存。
