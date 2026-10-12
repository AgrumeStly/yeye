# 第三方依赖来源

本目录仅携带工程需要的 CMSIS 和 STM32 设备头文件；保留原始版权与许可证。

- `cmsis/`：ARM.CMSIS 5.0.1 的 Cortex-M4 核心头文件，许可证见 `cmsis/LICENSE.txt`。
- `stm32/`：官方 Keil.STM32F4xx_DFP 2.17.1 中的 ST STM32F407 设备头文件，许可证见 `stm32/LICENSE.txt`。
- `../startup/startup_stm32f407xx.s`：同一 ST 设备包的 ARMCC 启动文件，许可证随文件保存。

官方芯片包：[Keil.STM32F4xx_DFP.2.17.1.pack](https://www.keil.com/pack/Keil.STM32F4xx_DFP.2.17.1.pack)。固定版本用于兼容现有 Keil5.24、ARM Compiler 5，并不代表最新版。

不复制 Keil 编译器、商业库、安装配置或账号信息。工程使用本地相对包含路径，笔记本须另行安装相应 Keil 编译器与设备包。
