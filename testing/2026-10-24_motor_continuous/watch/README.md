# MotorContinuous：无动力Watch启用／KEY停止配对证据

日期：2026-10-24（北京时间）。来源：主控在01对话提供的三张截图；主控／01原样复制、逐项读取并归档。本轮指导条件为驱动OFF、XT30动力电池拔开、DAPLink供主板、Keil Run；截图本身不能独立证明动力电池状态，不额外补造操作确认。代理未访问板卡、烧录、改固件或上传。

当前目标按前一轮主控“完全符合期望”的反馈为MotorContinuous、revision0x020B1001、fault0且ms增长；三张图片没有显示revision或实时全局fault，不将上一轮口头反馈改写成图片内读数。活动／停止帧各自保存的fault读数另见下表。

## 第一张：没有有效活动快照

[01_before_request.png](01_before_request.png)显示g_motor_bench_ms=0x00053423（341027ms）；request_count、enable_calls、enable_count、stop_count、last_mask及active.valid均为0，活动字段全为0。该结构在采集前由启动清零，valid=0时不能当成TIM1／GPIO实际寄存器全为0，也不能据此判端口、时钟或PWM初始化失败。只能说这一屏未显示非零请求或已完成的启用采集；不推断主控是否按键、是否曾在前一次复位前启用或代码出现哪一种故障。

主控紧接着提供第二张有效活动帧，第一张“没有快照”的状态已被后续采集补齐，不继续把第一张当成当前未启用证据。

## 第二张：一次A桥有效启用

[02_active_a.png](02_active_a.png)可读原值如下；全部来自图片，并非用期望常量补入：

| 项目 | 实际读数 | 本轮判读 |
| --- | --- | --- |
| g_motor_bench_ms | 0x000691D3，430547ms | Watch拍摄时读数；不是活动采集时间 |
| request_count／enable_calls／enable_count | 1／1／1 | 一次非零请求、启用调用执行返回、活动采集读回MOE=1；不表示电机转数 |
| stop_count／last_mask | 0／1 | 尚未记录停止事件，本次A桥 |
| start_ms／active.ms | 均0x00068366，426854ms | 本次启用采集对应时间 |
| stop_ms／elapsed_ms／stop_reason | 全0 | 还没有停止事件；elapsed_ms只在停止时写，运行期间为0不代表滴答停滞 |
| active.valid／run_id／state／fault／mask | 1／1／4／0／1 | 采集完成，启用帧处于RUNNING，采集点fault0、A桥；不是当前live state的另一次采样 |
| TIM1 CR1／PSC／ARR／CNT | 0x81／0／0x31F／0x2B1 | CEN1、周期800、计数采样值689；结合本工程16MHz配置为名义20kHz，未实测外部频率 |
| TIM1 CCER／BDTR | 0x1111／0x8C00 | 普通CH1–4使能，高有效，MOE1；Break未启用 |
| TIM1 CCMR1／CCMR2 | 均0x6868 | 四通道PWM1及预装载符合当前配置 |
| TIM1 CCR1／CCR2／CCR3／CCR4 | 0xF0／0／0／0 | A的CH1比较值240，名义30%；AIN2和B两输入均零比较值 |
| GPIOE MODER／AFRH | 0x28880000／0x01101010 | PE9／11／13／14处于AF模式，AF1 |
| GPIOE OTYPER／PUPDR／ODR／IDR | 0／0x28880000／0／0x271 | 推挽、四脚下拉；AF模式ODR0不代表定时器无输出；IDR单次采样PE9为高，不是波形 |
| RCC AHB1ENR／APB2ENR | 0x00100013／1 | GPIOE与TIM1时钟使能读回为1 |

当前ms与start_ms相差3693ms，只是两处软件读数的差；Watch不是同一CPU周期原子采样，不能当作独立测得的持续输出时间或已填入elapsed_ms。CNT在结构中先读、IDR后读，不能把这两个瞬时字段强行对齐同一PWM相位，亦不能由一个IDR高值证明电压幅度、频率或占空比。

## 第三张：同一次A桥的KEY停止

主控随后提供[03_stopped_key.png](03_stopped_key.png)，已取得与活动帧run_id=1及start_ms配对的停止记录，不再将第二张的stop_count0当作当前未停止状态。

| 项目 | 实际读数 | 本轮判读 |
| --- | --- | --- |
| request_count／enable_calls／enable_count／stop_count | 全部1 | 一次请求／启用／MOE读回／停止事件 |
| start_ms／stop_ms／stopped.ms | 0x00068366／0x000BA250／0x000BA250 | 起点426854ms、终点762448ms，停止帧时间与stop_ms相同 |
| elapsed_ms／stop_reason | 0x00051EEA／2 | 335594ms（335.594s），与软件滴答差完全一致；原因是KEY，非500ms超时 |
| stopped.valid／run_id／state／fault／mask | 1／1／6／0／1 | 采集完成、配对run_id1、ABORTED锁定、采集点fault0；mask1是A桥事件标签，不是仍在驱动 |
| TIM1 CR1／PSC／ARR／CNT | 0x81／0／0x31F／0x2A3 | 计数器仍运行符合停止设计；不依靠关闭CNT停电机 |
| TIM1 CCER／BDTR | 0x1111／0x0C00 | 通道配置保留，但MOE已清为0 |
| TIM1 CCMR1／CCMR2 | 均0x6868 | 原PWM模式配置保留，不代表引脚仍由定时器驱动 |
| TIM1 CCR1／CCR2／CCR3／CCR4 | 全0 | 四路比较值均已清零 |
| GPIOE MODER／AFRH | 0x14440000／0x01101010 | PE9／11／13／14均切回GPIO输出；AFR保留AF1不影响当前GPIO输出模式 |
| GPIOE OTYPER／PUPDR／ODR／IDR | 0／0x28880000／0／0x75 | 推挽，下拉保留，四控制脚ODR均低；该次IDR的四控制脚也均低 |
| RCC AHB1ENR／APB2ENR | 0x00100013／1 | 外设时钟保留，与撤MOE／GPIO低的停止设计一致 |

335.594s仅为两事件的软件滴答差，不是外部仪器测得的脉冲持续时间，不表示任何动力带载运行或可允许堵转时长。当前无动力采集指导与此前“带动力不转应约1–2s停止”是不同测试条件，不将截图较长的滴答差用作动力试验授权。

## 结论与下一步

**本次当前持续版的A请求、TIM1／GPIO配置、MOE启用，以及同次KEY停止后MOE清零／四CCR清零／四脚GPIO低的配对快照均符合预期，未发现明确的端口／AF／CCR／启停输出使能错误。** 这不等于固件全部无缺陷，也不等于PE9排针、驱动AIN1或功率输出波形正常。普通万用表AIN1约1V、AO1−AO2约0.07V仍不能补齐这些外部波形与板内VM的缺口，不据此判定驱动损坏、增加功率、改频率或复测B／AB。

当前这一组板内启停核对已完成，不再重复索要同组Watch或整套接线。下一步转外部信号测量：先确认现用万用表有无Hz频率／%占空比功能，再决定能否在动力始终断开时粗测PE9／驱动AIN1；若无该功能，则另行准备普通表可读的无动力静态信号诊断或由硬件借波形仪器。仪表功能／输入条件未确认前不指定新频率档接法，不给动力、不重复试转。保持现有代码及30%／20kHz，不修改输出、重新下载或要求换型号。

## 原图与SHA256

| 文件 | 字节 | SHA256 |
| --- | --- | --- |
| [01_before_request.png](01_before_request.png) | 207863 | `32858bbe549beea81dff8e35780f7c5b0dcfc61f36a00b5f4395f8de6e50f1b3` |
| [02_active_a.png](02_active_a.png) | 215207 | `f421a388944cafe8c072588be9e843db342fa4c7559f4cfb0c57af1003f65a95` |
| [03_stopped_key.png](03_stopped_key.png) | 214595 | `b8c2d38e416307bd46d9634e758e55a47466534ceb851614a64e0ba984ed2edc` |

原附件均在主控提供的临时目录`C:/Users/SHIDUA~1/AppData/Local/Temp/`，依次为`codex-clipboard-b3e80eb1-a325-4317-8f86-0fe8f636f59c.png`、`codex-clipboard-0cbcf811-3473-4910-951e-65a19431f2cb.png`及`codex-clipboard-b2cca003-410d-40ef-b0c3-47dba4b2345c.png`。归档不裁剪、不重绘、不修改像素。

程序及操作说明见[MotorContinuous](../../../control/docs/motor_continuous.md)，[端口自查及源码复核](../../../hardware_preparation/motor_wiring_self_check.md)。历史[500ms R3实板快照](../../2026-10-21_motor_bench/r3_watch/README.md)为另一版本的独立证据，不将其停止帧套入本次。
