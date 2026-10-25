# 第三方依赖来源

本目录携带工程需要的CMSIS、匹配的STM32标准库设备头文件和标准外设库驱动；保留原始版权与许可证。2026-10-25由control/firmware/vendor整体迁至control/Drivers，源码字节与原来源校验值不变；source_manifest中的project_path现相对control根目录。

- `cmsis/`：ARM.CMSIS 5.0.1 的 Cortex-M4 核心头文件，许可证见 `cmsis/LICENSE.txt`。
- `stm32/`：Keil.STM32F4xx_DFP 1.0.8中与SPL V1.3.0配套的设备头文件，选择STM32F40_41xxx器件组，许可证见stdperiph/LICENSE.pdf。
- `stdperiph/`：同一官方分发包的SPL V1.3.0，携带RCC、GPIO、USART、misc及C-02B新增的TIM、IWDG驱动。当前MotorBench、MotorContinuous、MotorDirect三个独立诊断目标使用TIM／IWDG相关模块，原三个目标保持显式排除；Direct保留TIM5时基而不启用TIM1 PWM。原始文件校验值与来源见stdperiph/source_manifest.json，原始许可见stdperiph/LICENSE.pdf；本次从已有SHA256一致的1.0.8官方归档提取，厂家源码保持原字节。
- `../Core/Startup/startup_stm32f407xx.s`：同一 ST 设备包的 ARMCC 启动文件，许可证随文件保存。

官方芯片包：[Keil.STM32F4xx_DFP.2.17.1.pack](https://www.keil.com/pack/Keil.STM32F4xx_DFP.2.17.1.pack)。固定版本用于兼容现有 Keil5.24、ARM Compiler 5，并不代表最新版。

标准库源码来源：[Keil.STM32F4xx_DFP.1.0.8.pack](https://www.keil.com/pack/Keil.STM32F4xx_DFP.1.0.8.pack)。仅提取配套源码，不安装或替换本机2.17.1设备包。ST官方标准库产品为 [STSW-STM32065](https://www.st.com/en/embedded-software/stsw-stm32065.html)；V1.3.0是当前固定源码版本，不声称最新。

不复制 Keil 编译器、商业库、安装配置或账号信息。工程使用本地相对包含路径，笔记本须另行安装相应 Keil 编译器与设备包。
