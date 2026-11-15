/** @file lap_uart.c
 * @brief 独立UART驱动，不链接带SystemInit／SysTick的旧board.c，避免重复向量。
 * USART2抢占优先级0高于SysTick1；单次ISR无循环、无等待、无协议解析或浮点。
 */
#include "lap_uart.h"
#include "stm32f4xx.h"
static volatile uint16_t write_at, read_at;
static volatile uint8_t transport_error;
static volatile uint32_t milliseconds;
static uint8_t bytes[256];
static uint32_t arrivals[256];
volatile uint32_t g_lap_uart_errors;
volatile lap_uart_diag_t g_lap_uart_diag;
void lap_uart_tick(uint32_t now) { milliseconds = now; }
void lap_uart_init(void) {
    GPIO_InitTypeDef gpio; USART_InitTypeDef uart; NVIC_InitTypeDef irq;
    const lap_uart_diag_t empty_diag = {0u};
    write_at = read_at = 0u; transport_error = 0u; milliseconds = 0u; g_lap_uart_errors = 0u;
    g_lap_uart_diag = empty_diag;
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);
    GPIO_StructInit(&gpio); gpio.GPIO_Pin = GPIO_Pin_2 | GPIO_Pin_3;
    gpio.GPIO_Mode = GPIO_Mode_AF; gpio.GPIO_Speed = GPIO_Speed_50MHz;
    gpio.GPIO_OType = GPIO_OType_PP; gpio.GPIO_PuPd = GPIO_PuPd_UP;
    GPIO_Init(GPIOA, &gpio);
    GPIO_PinAFConfig(GPIOA, GPIO_PinSource2, GPIO_AF_USART2);
    GPIO_PinAFConfig(GPIOA, GPIO_PinSource3, GPIO_AF_USART2);
    USART_StructInit(&uart); uart.USART_BaudRate = 115200u;
    uart.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART2, &uart);
    USART_ITConfig(USART2, USART_IT_RXNE, ENABLE); USART_ITConfig(USART2, USART_IT_ERR, ENABLE);
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    irq.NVIC_IRQChannel = USART2_IRQn; irq.NVIC_IRQChannelPreemptionPriority = LAP_UART_PREEMPT_PRIORITY;
    irq.NVIC_IRQChannelSubPriority = 0u; irq.NVIC_IRQChannelCmd = ENABLE; NVIC_Init(&irq);
    USART_Cmd(USART2, ENABLE);
}
/** @brief 单次ISR只读取一个字节并记录错误分类；无等待、无打印、无动态内存。
 * 参数/返回值：无。沿用SPL状态读取和SR/DR清错顺序，不更改115200/8N1。
 * 任一硬件接收错误或软件环满仍丢弃该字节、置传输故障，由主循环锁定
 * LAP_TRANSPORT；统计绝不用于自动恢复。毫秒数取本驱动的SysTick快照。
 * 分项计数只在错误路径更新；首次记录保持不变，便于区分首次与后续干扰。
 */
static void record_isr_cycles(uint32_t started) {
    uint32_t elapsed = DWT->CYCCNT - started;
    if (elapsed > g_lap_uart_diag.isr_max_cycles) g_lap_uart_diag.isr_max_cycles = elapsed;
}
void USART2_IRQHandler(void) {
    uint32_t started = DWT->CYCCNT;
    FlagStatus rx = USART_GetFlagStatus(USART2, USART_FLAG_RXNE);
    FlagStatus overrun = USART_GetFlagStatus(USART2, USART_FLAG_ORE);
    FlagStatus noise = USART_GetFlagStatus(USART2, USART_FLAG_NE);
    FlagStatus frame = USART_GetFlagStatus(USART2, USART_FLAG_FE);
    FlagStatus parity = USART_GetFlagStatus(USART2, USART_FLAG_PE);
    uint8_t byte; uint16_t next; uint32_t error_mask = 0u;
    if (rx != SET && overrun != SET && noise != SET && frame != SET && parity != SET) {
        record_isr_cycles(started); return;
    }
    byte = (uint8_t)USART_ReceiveData(USART2);
    next = (uint16_t)((write_at + 1u) & 255u);
    if (overrun == SET || noise == SET || frame == SET || parity == SET || next == read_at) {
        if (overrun == SET) { ++g_lap_uart_diag.overrun; error_mask |= LAP_UART_ERROR_OVERRUN; }
        if (noise == SET) { ++g_lap_uart_diag.noise; error_mask |= LAP_UART_ERROR_NOISE; }
        if (frame == SET) { ++g_lap_uart_diag.frame; error_mask |= LAP_UART_ERROR_FRAME; }
        if (parity == SET) { ++g_lap_uart_diag.parity; error_mask |= LAP_UART_ERROR_PARITY; }
        if (next == read_at) { ++g_lap_uart_diag.ring_full; error_mask |= LAP_UART_ERROR_RING_FULL; }
        if (g_lap_uart_errors == 0u) {
            g_lap_uart_diag.first_mask = error_mask; g_lap_uart_diag.first_at_ms = milliseconds;
        }
        g_lap_uart_diag.last_mask = error_mask; g_lap_uart_diag.last_at_ms = milliseconds;
        ++g_lap_uart_errors; transport_error = 1u; record_isr_cycles(started); return;
    }
    bytes[write_at] = byte; arrivals[write_at] = milliseconds; __DMB(); write_at = next;
    record_isr_cycles(started);
}
int lap_uart_read(uint8_t *byte, uint32_t *arrival) {
    if (read_at == write_at) return 0;
    *byte = bytes[read_at]; *arrival = arrivals[read_at]; __DMB();
    read_at = (uint16_t)((read_at + 1u) & 255u); return 1;
}
int lap_uart_fault(void) {
    uint32_t mask = __get_PRIMASK(); int fault;
    __disable_irq(); fault = transport_error;
    if (fault != 0) { transport_error = 0u; read_at = write_at; }
    __set_PRIMASK(mask); return fault;
}
