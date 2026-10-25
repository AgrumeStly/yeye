# 主控：标准外设库代码说明

工程已改为STM32F4标准外设库（SPL）写法。外设初始化集中在 `Drivers_Custom/Board/board.c`，通信协议与状态机保持独立，仍可在电脑上测试。

## 按这个顺序阅读

| 顺序 | 代码位置 | 主控需要理解的内容 |
| --- | --- | --- |
| 1 | SystemInit() | 启用内部HSI并切换为系统时钟，复位时钟配置，将中断向量表定位到FLASH |
| 2 | board_init() | 更新SystemCoreClock，设置中断优先级分组，开启1ms滴答 |
| 3 | board_uart_init()第1步 | 打开GPIOA和USART2时钟；不打开时钟，外设配置不会正常工作 |
| 4 | 第2步 | PA2/PA3配置成复用引脚，并选择USART2的AF7功能 |
| 5 | 第3步 | 设置115200、8N1和收发模式；USART_Init按实际总线时钟计算波特率 |
| 6 | 第4步 | 开接收/错误中断，配置NVIC，再启用USART2 |
| 7 | USART2_IRQHandler() | 通过库函数读状态与字节，放入缓冲；协议解析在主循环执行 |

UART默认关闭；主控与硬件核对接线后再改BOARD_UART_ENABLE。原HardwareBench仍不配置PWM或编码器，不会因启用UART而驱动电机。C-02B的[MotorBench](motor_bench.md)另用独立入口和TIM1驱动，不链接board.c，也不启用UART；尚未读取编码器。

2026-10-24新增[MotorDirect](motor_direct.md)独立入口：SPL普通GPIO固定PE9高、其余三控制脚低，不配置TIM1／AF／PWM；人工一次500ms后锁定。该目标仍使用TIM5建立R1看门狗初始化的独立超时时基，TIM／IWDG库及CMSIS SysTick不能因“不要PWM”而删除。原PWM与持续目标保留。

## 初始化结构体的通用写法

```c
GPIO_InitTypeDef gpio;
GPIO_StructInit(&gpio);             /* 先填默认值，避免遗漏字段 */
gpio.GPIO_Pin = GPIO_Pin_2 | GPIO_Pin_3;
gpio.GPIO_Mode = GPIO_Mode_AF;
gpio.GPIO_Speed = GPIO_Speed_50MHz;
gpio.GPIO_OType = GPIO_OType_PP;
gpio.GPIO_PuPd = GPIO_PuPd_UP;
GPIO_Init(GPIOA, &gpio);            /* 将配置应用到GPIOA */
```

GPIO_Pin表示选哪些引脚；GPIO_Mode表示输入/输出/复用等模式；GPIO_PuPd表示上拉/下拉。GPIO_Speed是输出驱动速度等级，不是USART波特率或赛车速度。复用模式还要调用GPIO_PinAFConfig选择具体外设功能。

USART采用相同思路：USART_StructInit填默认值 → 修改USART_InitTypeDef各字段 → USART_Init应用配置 → USART_Cmd启用。

## 工程如何找到标准库

- `Drivers/stdperiph/inc/`：库函数声明、结构体和参数宏。
- `Drivers/stdperiph/src/`：真正的库函数实现；Keil分组为StdPeriph_Driver。
- `Drivers/stm32/stm32f4xx.h`：与标准库匹配的设备定义，不与HAL设备头混用。
- `Core/Inc/stm32f4xx_conf.h`：启用RCC、GPIO、USART、misc并定义assert_param；三个电机诊断目标均定义MOTOR_BENCH_TARGET，另引入TIM／IWDG声明。
- Keil预定义宏为 `STM32F40_41xxx,USE_STDPERIPH_DRIVER,HSE_VALUE=8000000`。HSE为未来核对外部晶振预留，当前实际时钟仍为HSI 16MHz。

USE_STDPERIPH_DRIVER使设备头自动包含stm32f4xx_conf.h；STM32F40_41xxx选择F407所属器件组。这些宏用于配套SPL V1.3.0，不把它们换成HAL示例宏。

## 内核部分仍使用CMSIS

SysTick_Config、__disable_irq、__DMB和SCB的FPU启动设置属于Cortex-M4内核支持，不是HAL，也不是标准库缺失。SPL负责RCC/GPIO/USART等STM32外设；CMSIS负责内核操作。应用代码不再手写RCC/GPIO/USART寄存器位配置，标准库内部仍会操作寄存器。

## 到货后新增PWM或编码器

主控先确认实际引脚与定时器资源，再加入同版本TIM驱动并在Keil启用。C-02B已从原官方1.0.8包补入SPL V1.3.0的TIM／IWDG模块；当前MotorBench、MotorContinuous和MotorDirect均通过MOTOR_BENCH_TARGET引入对应声明，原三个目标显式排除新源文件。PWM台架采用先GPIO低→时钟与计时参数→四通道零比较值→人工触发后切AF并开MOE的顺序；Direct不启用TIM1输出，仍保留TIM5时基及IWDG。编码器极性及PID仍待后续实现与标定。

来源与许可见Drivers/README.md。可在Keil通过函数名查找对应库源码，结合注释理解参数，再修改应用初始化。
