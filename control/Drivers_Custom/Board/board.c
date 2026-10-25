#include "board.h"
#include "stm32f4xx.h"
static volatile uint32_t milliseconds;
uint32_t SystemCoreClock = HSI_VALUE;
volatile int16_t board_left_request, board_right_request;
volatile uint32_t board_uart_errors;
#if BOARD_UART_ENABLE
static volatile uint16_t rx_write, rx_read;
static volatile uint8_t rx_fault;
static uint8_t rx_bytes[256];
#endif
/* 标准库启动：使用16 MHz内部HSI，到货前不依赖外部晶振。 */
void SystemInit(void) {
    RCC_HSICmd(ENABLE);
    while (RCC_GetFlagStatus(RCC_FLAG_HSIRDY) == RESET) { }
    RCC_SYSCLKConfig(RCC_SYSCLKSource_HSI);
    while (RCC_GetSYSCLKSource() != 0x00u) { }
    RCC_DeInit();
    NVIC_SetVectorTable(NVIC_VectTab_FLASH, 0u);
    /* FPU属于Cortex-M4内核，CMSIS启动设置保留；外设配置使用SPL函数。 */
    SCB->CPACR |= 0x00f00000u;
}
void SystemCoreClockUpdate(void) {
    RCC_ClocksTypeDef clocks;
    RCC_GetClocksFreq(&clocks);
    SystemCoreClock = clocks.SYSCLK_Frequency;
}
void SysTick_Handler(void) { ++milliseconds; }

#if BOARD_UART_ENABLE
static void board_uart_init(void) {
    GPIO_InitTypeDef gpio;
    USART_InitTypeDef usart;
    NVIC_InitTypeDef interrupt;

    /* 1. 打开GPIOA和USART2外设时钟。 */
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);

    /* 2. PA2为TX，PA3为RX，配置为USART2复用功能AF7。 */
    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = GPIO_Pin_2 | GPIO_Pin_3;
    gpio.GPIO_Mode = GPIO_Mode_AF;
    gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_OType = GPIO_OType_PP;
    gpio.GPIO_PuPd = GPIO_PuPd_UP;
    GPIO_Init(GPIOA, &gpio);
    GPIO_PinAFConfig(GPIOA, GPIO_PinSource2, GPIO_AF_USART2);
    GPIO_PinAFConfig(GPIOA, GPIO_PinSource3, GPIO_AF_USART2);

    /* 3. 115200波特率、8位数据、1位停止、无校验、无硬件流控。 */
    USART_StructInit(&usart);
    usart.USART_BaudRate = 115200u;
    usart.USART_WordLength = USART_WordLength_8b;
    usart.USART_StopBits = USART_StopBits_1;
    usart.USART_Parity = USART_Parity_No;
    usart.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    usart.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART2, &usart);

    /* 4. 打开接收与错误中断；中断里只收字节，不解析整包。 */
    USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
    USART_ITConfig(USART2, USART_IT_ERR, ENABLE);
    interrupt.NVIC_IRQChannel = USART2_IRQn;
    interrupt.NVIC_IRQChannelPreemptionPriority = 2u;
    interrupt.NVIC_IRQChannelSubPriority = 0u;
    interrupt.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&interrupt);
    USART_Cmd(USART2, ENABLE);
}
#endif
void board_init(void) {
    board_left_request=0; board_right_request=0;
    /* 更新时钟变量后配置1 ms内核滴答；SysTick_Config属于CMSIS。 */
    SystemCoreClockUpdate();
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    (void)SysTick_Config(SystemCoreClock / 1000u);
#if BOARD_UART_ENABLE
    board_uart_init();
#endif
}
uint32_t board_millis(void) { return milliseconds; }
#if BOARD_UART_ENABLE
void USART2_IRQHandler(void) {
    FlagStatus received, overrun, noise, framing, parity;
    uint8_t byte;
    uint16_t next;
    /* 先读状态，再读数据；该顺序同时清除ORE/NE/FE/PE错误标志。 */
    received = USART_GetFlagStatus(USART2, USART_FLAG_RXNE);
    overrun = USART_GetFlagStatus(USART2, USART_FLAG_ORE);
    noise = USART_GetFlagStatus(USART2, USART_FLAG_NE);
    framing = USART_GetFlagStatus(USART2, USART_FLAG_FE);
    parity = USART_GetFlagStatus(USART2, USART_FLAG_PE);
    if (received == SET || overrun == SET || noise == SET || framing == SET || parity == SET) {
        byte=(uint8_t)USART_ReceiveData(USART2);
        if (overrun == SET || noise == SET || framing == SET || parity == SET) { ++board_uart_errors; rx_fault=1; return; }
        next=(uint16_t)((rx_write+1u)&255u);
        if (next == rx_read) { ++board_uart_errors; rx_fault=1; return; }
        rx_bytes[rx_write]=byte; __DMB(); rx_write=next;
    }
}
#endif
int board_uart_read(uint8_t *byte) {
#if BOARD_UART_ENABLE
    if (rx_read == rx_write) return 0;
    *byte=rx_bytes[rx_read]; __DMB(); rx_read=(uint16_t)((rx_read+1u)&255u); return 1;
#else
    (void)byte; return 0;
#endif
}
int board_uart_fault(void) {
#if BOARD_UART_ENABLE
    uint32_t mask=__get_PRIMASK();
    int fault;
    __disable_irq(); fault=rx_fault;
    if (fault) { rx_fault=0; rx_read=rx_write; }
    __set_PRIMASK(mask); return fault;
#else
    return 0;
#endif
}
void board_apply_requests(int16_t left, int16_t right) {
    /* Observable in Keil Watch only. No motor pins, timers, or PWM are configured. */
    board_left_request=left; board_right_request=right;
}
