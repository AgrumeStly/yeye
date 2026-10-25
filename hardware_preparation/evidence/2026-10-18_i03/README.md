# I-03 原始证据索引

状态：v0.1，照片／资料证据；非实物验收。日期：2026-10-18（北京时间）。整理：主控／02；实物复核：硬件；控制接口：主控／01。

照片拍摄日期与设备未知，日期只表示本次接收和核对。照片以原始字节复制，无裁剪或标注。SHA256只验证复制和后续版本一致，不证明器件真伪或接线正确。原始附件路径保留如下，工程内副本用于跨设备交接。

原附件目录：`C:/Users/ShiduanTian/.codex/codex-remote-attachments/01a14d20-8fe4-7d93-81ae-766498c0862f/39A53CE4-D6BA-4A3C-85E1-A97DE119D3D2/`，依次为`1-Photo-1.jpg`、`2-Photo-2.jpg`、`3-Photo-3.jpg`。

## 文件与SHA256

| 文件 | 来源／内容 | SHA256 |
| --- | --- | --- |
| [photo_01_driver.jpg](photo_01_driver.jpg) | 主控提供的照片1 | `9bfecc56fdd6a09f984fefcbd7ededbc55f9fca994d89645016a840a778495cb` |
| [photo_02_motor.jpg](photo_02_motor.jpg) | 主控提供的照片2 | `02b54dea8ba2f4db2a1845dbbb6e58f1ae2251aa4f35f99f5ac50eba500cfc14` |
| [photo_03_controller.jpg](photo_03_controller.jpg) | 主控提供的照片3 | `8583abae38dbddd6c76b72a6721e823e326238e3cf963a4a0629d0598ba77659` |
| [vendor_driver_stm32.pdf](vendor_driver_stm32.pdf) | 亚博官方仓库STM32教程 | `f9f89b99a1a130ba3227180be5915d25f080af704653e0c14e92983dc64b6a26` |
| [vendor_driver_introduction.pdf](vendor_driver_introduction.pdf) | 亚博官方仓库模块介绍 | `9b722fb735ba061634c40528445c0c410e4b092a09fcd72b2830f99216cff9e8` |
| [at8236_datasheet.pdf](at8236_datasheet.pdf) | 杭州中科微原厂内容，第三方托管 | `4e27dcd41816e75ae6d13948e6495cd3ca15ac31596fab0194069fd292c54fef` |

## 厂家资料来源与已读范围

获取日期：2026-10-18；以下为公开资料只读下载，未访问本项目远端或上传资料。保留厂商版权和原始内容，未重新生成PDF。

- 亚博官方STM32教程：[教程入口](https://www.yahboom.net/study/Dual-MD-Module/6604/)、[官方仓库原始PDF](https://raw.githubusercontent.com/YahboomTechnology/2-Channel-Motor-Driver-Module/main/2.For%20STM32/stm32f103c8t6.pdf)。PDF共3页，提取全部正文并渲染全部页面，重点查看第1页接线图；F103示例引脚不适用于直接冻结本项目F407资源。
- 亚博标准版模块介绍：[官方介绍入口](https://www.yahboom.net/public/upload/upload-html/1692605631/Introduction%20of%20Module.html)、[官方仓库原始PDF](https://raw.githubusercontent.com/YahboomTechnology/2-Channel-Motor-Driver-Module/main/1.Introduction%20of%20Module/Introduction%20of%20Module.pdf)。1页，提取并渲染查看，确认5–12V输入、5V/3A和3.3V/500mA标称输出。商店的电机电流宣传与该介绍存在不同口径，本任务不据此确认实际连续／堵转能力。
- 杭州中科微AT8236-S409-V1.1：[第三方托管的原厂内容PDF](https://offer-product.oss-cn-beijing.aliyuncs.com/product/offer/attachment/null/file/subPdf_143103_65242_20211117-164925002.pdf)。10页，读取第1、2、4、5、6页正文，渲染查看第4、5页电气门限及真值表。托管地址不等于芯片厂家站点，来源性质保留；第4页测试条件为TA=25℃、VM=24V，不能把所有芯片参数直接当作5–12V模块实测值。板级控制逻辑另可对照[亚博AT8236 H桥说明](https://www.yahboom.net/study/SBR-microROS/13590/)，此页对应另一控制板，只用于芯片真值表，不用于本板物理接线。
- 立创[天空星原理图说明](https://wiki.lckfb.com/zh-hans/tkx/hardware/schematic.html)，读取供电及调试接口说明；本次未取得与实物版本签核一致的完整板级原理图快照，接口物理针号仍待硬件核对。
- ST [STM32F405/407 DS8626](https://www.st.com/resource/en/datasheet/stm32f405rg.pdf)，在线查阅引脚复用表，供01核对TIM/UART资源；本次没有分配PWM引脚。

原项目采购PDF与生成源保持原样，读取7页PDF正文，并与生成源的供电、编码器及驱动控制段核对。本次不是旧采购方案重发或全面性能复核。

## 照片观察与边界

- P1为驱动正面，版号YB-MNT03-V1.0；电源端子、控制与编码器标识可读。没有连接电机口的线束终端照片，也没有实际电压。
- P2仅展示一只电机六芯接口和电机端线束，M2/V/A/B/G/M1可读，另一端连接未展示。型号由2026-10-18主控“按清单采购”确认，采用MD310Z20_7.4V，不再列为未知。
- P3为天空星背面，照片自身未展示芯片顶标与PCB版本；主控已确认按清单采购STM32F407VET6青春版。调试口的U1R/U1T是串口标识，不凭已插线束确认SWD。

待补：两束线的两端连接与断电导通记录、左右轮对应、供电转接关系及极性、下载器端口。既定型号无需重复识别；PCB修订或顶标仅在出现具体差异时定点补证。照片整理已完成，不等于上述电气核对已由硬件执行。

接线定义见[接线核对](../../wiring.md)，角色交接见[I-03交接](../../i03_handoff.md)。临时渲染文件位于工作区tmp/pdfs/i03，未作为最终证据交付；所需原PDF副本已在本目录保存。
