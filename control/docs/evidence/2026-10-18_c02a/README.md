# C-02A 官方原理图证据索引

状态：v0.1，资料级设计证据，非实物验收。日期：2026-10-18（北京时间）。维护：主控／01。对应[引脚资源方案v0.2](../../pin_plan.md)。

以下四张PNG直接下载自[立创天空星核心板官方原理图页面](https://wiki.lckfb.com/zh-hans/tkx/hardware/schematic.html)引用的原图，保留原始字节，未裁剪、标注或重绘。文件名含厂家图像日期，不代表本次实物PCB版本已签核。网页客户端渲染的图片地址通过该页公开模块定位，再逐图查看。

| 本地文件 | 官方原图 | 用途 | SHA256 |
| --- | --- | --- | --- |
| [schematic_20240815_203023.png](schematic_20240815_203023.png) | [原图](https://wiki.lckfb.com/storage/images/zh-hans/tkx/hardware/schematic/schematic_20240815_203023.png) | P1／P2各40针网络定义；八线及USART2针号 | `587b62e41647c70bc1c58a1532e4ec2b3caeef056a2e330f70d2c8a316cbe6f3` |
| [schematic_20240815_044555.png](schematic_20240815_044555.png) | [原图](https://wiki.lckfb.com/storage/images/zh-hans/tkx/hardware/schematic/schematic_20240815_044555.png) | H1 SWD／SWO／USART1及电源引出 | `577e728666d4a2bd79a866449dd3c787466e407e1a22641c61b6ba390c2ac2c6` |
| [schematic_20240815_052905.png](schematic_20240815_052905.png) | [原图](https://wiki.lckfb.com/storage/images/zh-hans/tkx/hardware/schematic/schematic_20240815_052905.png) | WKUP按键、PB2／BOOT1用户灯、NRST／BOOT0 | `4156b82a6804f5da5ffb8bfe36352b1bcb8f0c6249e9484e42e37cb01fed0798` |
| [schematic_20240815_180531.png](schematic_20240815_180531.png) | [原图](https://wiki.lckfb.com/storage/images/zh-hans/tkx/hardware/schematic/schematic_20240815_180531.png) | TF四位SDIO、检测与SPI FLASH板载网络 | `c0f9837a20f02ee6c1c1c2984ab5493d8f855e0892ee7a7aca9077c4ac9bea10` |

## 其它已核对依据

- [ST DS8626 Rev 12](https://www.st.com/resource/en/datasheet/stm32f405rg.pdf)：核对LQFP100与Table 9，重点查看第65／66／68页PB、PC、PE的AF表渲染图，及第64页PA、SWD定义。确认PE9／11／13／14 AF1分别为TIM1_CH1–4；PC6／7 AF2为TIM3_CH1／2；PB6／7 AF2为TIM4_CH1／2。
- [ST RM0090 Rev 22](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405415-stm32f407417-stm32f427437-and-stm32f429439-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)：读217–218页F405／407时钟规则；515／517／540页TIM1结构、时基和PWM；586／588／612–613页TIM3／4计数器、时基与编码器模式。未通读全手册。TIM3／4各16位，和TIM1计数器独立；同一个TIM内各通道仍共享CNT／PSC／ARR。
- [立创PA0按键教程](https://wiki.lckfb.com/zh-hans/tkx/tkx-stm32f407vxt6/beginner/key-principle.html)：与上面WKUP原图对应，取消PA0编码器旧候选，保持板载按键。
- [亚博MD310Z20官方资料](https://www.yahboom.net/public/upload/upload-html/1744700910/Motor%20introduction%20and%20usage.html)：AB霍尔增量编码器、3.3–5V供电、上拉整形；选3.3V域不等于完成电平测量。
- [亚博双驱动官方教程PDF](https://raw.githubusercontent.com/YahboomTechnology/2-Channel-Motor-Driver-Module/main/2.For%20STM32/stm32f103c8t6.pdf)：读取正文、查看第1页接线图。副本与原厂内容AT8236手册沿用[I-03证据目录](../../../../hardware_preparation/evidence/2026-10-18_i03/README.md)，不另复制。AT8236第5页真值表的来源是I-03保存的原厂内容、第三方托管PDF；不将托管地址称为厂家官网。
- [I-03主控板背面照片](../../../../hardware_preparation/evidence/2026-10-18_i03/photo_03_controller.jpg)：查看E09／E11／E13／E14、C06／C07、B06／B07的相邻标签，辅助硬件寻找；针号来自官方排针图，照片不承担导通证明。

ST手册下载与页图、I-03 PDF临时渲染保存在`tmp/pdfs/c02a/`，不是交付依赖，换电脑可按官方链接重建。以上本地原图和索引可随项目文档交接；未修改厂家图内容。

## 检查与限制

资料核对覆盖八线的端口、AF、通道及原理图针号；8条映射的端口／连接器端点唯一性、官方排针转写、AF与定时器分组、保留端口不重叠检查通过。PWM与编码器CNT隔离已按参考手册人工复核；最终51个本地Markdown链接、4张源图SHA256、git diff --check通过，固件Git差异为空。脚本只检查文档一致性，不能替代官方资料、实物导通或波形测量。

本任务没有固件改动，未编译、未运行55项电脑测试、未做板级或实车验证。实物插接面的列位／方向、两端导通、供电、默认态、电平、轮侧及正方向待硬件和02按[资源方案第5节](../../pin_plan.md)核对。C-02A不授权上电，C-02实现及台架参数由后续任务确定。
