# 主控：首次板级标准库测试

适用板卡：立创天空星 STM32F407VET6。2026-10-14 已实际烧录，主控确认用户灯正常双闪。完整结果见 [实物测试记录](../../hardware_preparation/board_self_test_record.md)。

## 主控：打开与编译

1. 打开 `control/firmware/yeye_control.uvprojx`。
2. 在 Keil 左上角选择 **BoardSelfTest**，按 F7 编译。
3. 预期显示 `0 Error(s), 0 Warning(s)`。输出位于 `control/firmware/build/board_test/`，测试源文件为 `control/firmware/src/board_self_test.c`。

仓库根目录也可执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/build_keil.ps1 -Target BoardSelfTest
```

编译脚本只编译，不烧录。该目标独立于 LogicDemo 和 HardwareBench，不包含整车状态机入口。外设初始化使用 STM32F4 SPL；SysTick 等内核功能使用 CMSIS。

## 测试行为

| 项目 | 行为与含义 |
| --- | --- |
| 用户灯 | PB2，高电平点亮，使用标准库 GPIO 配置 |
| 正常心跳 | 亮200ms、灭200ms、亮200ms、灭1400ms；约2秒一轮 |
| 自检失败 | 每100ms翻转一次用户灯，持续快速闪烁 |
| RAM | 独立128字节缓冲区，写入并读回两种位图样；不覆盖整片RAM |
| 时钟 | 检查 SystemCoreClock 配置值为16MHz；没有测量实际振荡频率 |
| 定时 | 使用 board.c 提供的1ms SysTick计数驱动双闪 |

正常双闪表明主程序和滴答中断运行，程序中的时钟配置值检查、专用RAM缓冲区读写检查未报告失败。LED节奏由主控目测确认，尚未用示波器测量精度。

## 主控：USB下载与启动

Type-C直连电脑可进入芯片ROM DFU下载模式。主控按住BOOT0，按下并松开RESET，再松开BOOT0；设备管理器应出现 `STM32 Bootloader`。本次已安装ST签名的WinUSB驱动，解决原先缺少驱动的问题。

本次下载使用dfu-util 0.11，只操作内部Flash的alt 0接口，起始地址为 `0x08000000`。下载前备份512KiB Flash，下载后读回固件长度范围并逐字节比较。既有Flash备份保存在台式机 `tmp/board_tools/flash_before_test.bin`，未上传GitHub；该文件是本次烧录前的备份，后续备份应另存，避免覆盖。

烧录后主控松开BOOT0，单独按RESET即可运行测试。该程序没有USB应用协议或USB串口，因此正常运行时DFU设备消失属于预期现象。USB线提供供电和ROM下载通道，Keil单步调试还需要SWD调试器。

## 主控与硬件：下一阶段

本测试没有配置电机PWM、编码器、视觉UART或外部传感器。硬件确认实物接口、电源和接线后，主控逐项增加驱动并单独验证；视觉按通信协议配合串口测试。整车功能与控制性能尚未验证。

官方依据：[天空星标准库点灯教程](https://wiki.lckfb.com/zh-hans/tkx/tkx-stm32f407vxt6/beginner/led-lib.html)、[天空星下载教程](https://wiki.lckfb.com/zh-hans/tkx/tkx-stm32f407vxt6/beginner/download.html)、[ST官方DFU驱动来源](https://github.com/STMicroelectronics/STM32PRG-TOOLBOX-DFU)、[dfu-util手册](https://dfu-util.sourceforge.net/dfu-util.1.html)。
