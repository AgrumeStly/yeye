# 主控：Keil5 开始操作

## 台式机已配置

| 设置 | 当前值 |
| --- | --- |
| Keil | C:\Keil_v5，V5.24a |
| 编译器 | ARM Compiler 5.06 update 5 (build 528) |
| 芯片 | STM32F407VETx，对应STM32F407VET6 |
| 芯片包 | Keil.STM32F4xx_DFP 2.17.1 |
| 外设库 | STM32F4 SPL V1.3.0，随工程保存；无需另行安装旧版芯片包 |
| FLASH | 起点0x08000000，大小0x80000 |
| RAM | 起点0x20000000，大小0x20000；CCM暂不用 |
| 工程 | control/firmware/yeye_control.uvprojx |
| 演示目标 | LogicDemo，模拟器 |
| 板级目标 | HardwareBench，CMSIS-DAP；到货后确认调试器连接设置 |

## 主控：没有板卡时演示

1. 双击工程文件，左上角目标下拉选择 **LogicDemo**。
2. 按 **F7** 编译，Build Output应显示 `0 Error(s), 0 Warning(s)`。
3. 打开 `Options for Target → Debug`，确认 **Use Simulator**、Load Application at Startup、Run to main已选择。本机已预置，笔记本按后文初始化。
4. 按 **Ctrl+F5** 进入调试。打开logic_demo.c，在demo_done()函数内 `g_demo_complete=1u` 一行设置断点。
5. `View → Watch Windows → Watch 1`，添加g_car、g_parser、g_demo_checks、g_demo_failures、g_demo_complete。
6. 按 **F5**。到达断点时预期完成15项检查，g_demo_failures=0，最终g_car.state=CAR_STOPPED（枚举值2），左右请求均为0。单步执行赋值后g_demo_complete=1。
7. 在car_receive()、car_tick()内设置断点，可观察IDLE→RUNNING→FAULT→RUNNING→FAULT→STOPPED。演示使用人工推进的时间，不模拟真实电机或相机。
8. 再按Ctrl+F5退出调试。改代码后先退出调试，再F7重新编译。

验证范围见 [validation.md](validation.md)。调试变量不显示时，核对LogicDemo目标、重新编译并加载。

## 主控：电脑端自动测试

台式机已安装GCC。项目根目录打开PowerShell运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/run_host_tests.ps1
```

应显示 `PASS all 55 checks`。测试直接使用固件中的car.c、protocol.c，输出放control/build/。笔记本未安装GCC时仍可使用Keil LogicDemo，电脑端自动测试另需GCC。

Keil命令行编译：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/build_keil.ps1 -Target LogicDemo
powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/build_keil.ps1 -Target HardwareBench
powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/check_uart_build.ps1
```

Keil安装在其他位置时增加参数，例如 `-KeilRoot 'D:\Keil_v5'`。脚本只编译，不下载、不烧录。check_uart_build.ps1使用临时工程验证UART开启分支，不改变原工程的UART关闭设置。

## 主控：笔记本首次接入

1. GitHub Desktop Clone项目，或切到本次任务分支Fetch/Pull。
2. 安装Keil MDK和ARM Compiler 5。主控台式机实测使用V5.24a、编译器5.06u5；其他版本需重新验证。只有Compiler 6时，当前启动汇编和工程配置不能直接按已验证状态使用。
3. 安装 [固定版本STM32F4设备包](https://www.keil.com/pack/Keil.STM32F4xx_DFP.2.17.1.pack)，下载后双击按提示操作。
4. 在仓库根目录运行下列命令，复制默认调试设置；已有本机设置会保留。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File control/tools/setup_debug.ps1
```

5. 打开工程，选LogicDemo，F7编译。查看Options for Target → Target的编译器，未找到5.06时选择本机可用的Compiler 5并重建。
6. 用分支、提交号确认两台电脑代码一致，不复制整个Keil安装目录或账号配置。

## 主控与硬件：到货后的板级第一步

1. 核对实物确为STM32F407VET6；GD32、HC32等型号不能按本工程直接下载。
2. 暂不接电机供电。确认DAPLink的SWDIO、SWCLK、GND和目标参考电压，按调试器说明接线。
3. 选择HardwareBench，F7编译。Debug中选CMSIS-DAP Debugger，Settings中核对实际调试器、SWD端口和连接频率。
4. Utilities/Flash Download中核对STM32F4xx 512KB算法、地址0x08000000；确认后才进行下载。
5. 上板检查board_millis()增加、g_control_ticks递增、状态保持IDLE、左右请求为0。
6. UART引脚经主控、硬件确认后，在board.h把BOARD_UART_ENABLE改为1，重建再验证串口。电机输出仍是空适配层，不会产生PWM。

官方依据：[Keil命令行编译](https://www.keil.com/support/man/docs/uv4/uv4_commandline.asp)、[立创天空星原理图](https://wiki.lckfb.com/zh-hans/tkx/hardware/schematic.html)、[立创程序下载教程](https://wiki.lckfb.com/zh-hans/tkx/tkx-stm32f407vxt6/beginner/download.html)。接线以硬件手中版本和对应原理图为准。

标准库函数、配置宏与新增外设的方法见 [standard_library.md](standard_library.md)。当前STM32F40_41xxx用于选择F405/F407等器件组，芯片仍是STM32F407VET6。
