/** @file lap_uart.c
 * @brief 独立UART驱动，不链接带SystemInit／SysTick的旧board.c，避免重复向量。
 * USART2优先级2低于停止监督SysTick0；单次ISR无循环、无等待、无协议解析。
 */
#include "lap_uart.h"
#include "stm32f4xx.h"
static volatile uint16_t write_at, read_at;
static volatile uint8_t transport_error;
static volatile uint32_t milliseconds;
static uint8_t bytes[256];
static uint32_t arrivals[256];
volatile uint32_t g_lap_uart_errors;
void lap_uart_tick(uint32_t now) { milliseconds = now; }
void lap_uart_init(void) {
    GPIO_InitTypeDef gpio; USART_InitTypeDef uart; NVIC_InitTypeDef irq;
    write_at = read_at = 0u; transport_error = 0u; milliseconds = 0u; g_lap_uart_errors = 0u;
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
    irq.NVIC_IRQChannel = USART2_IRQn; irq.NVIC_IRQChannelPreemptionPriority = 2u;
    irq.NVIC_IRQChannelSubPriority = 0u; irq.NVIC_IRQChannelCmd = ENABLE; NVIC_Init(&irq);
    USART_Cmd(USART2, ENABLE);
}
void USART2_IRQHandler(void) {
    FlagStatus rx = USART_GetFlagStatus(USART2, USART_FLAG_RXNE);
    FlagStatus overrun = USART_GetFlagStatus(USART2, USART_FLAG_ORE);
    FlagStatus noise = USART_GetFlagStatus(USART2, USART_FLAG_NE);
    FlagStatus frame = USART_GetFlagStatus(USART2, USART_FLAG_FE);
    FlagStatus parity = USART_GetFlagStatus(USART2, USART_FLAG_PE);
    uint8_t byte; uint16_t next;
    if (rx != SET && overrun != SET && noise != SET && frame != SET && parity != SET) return;
    byte = (uint8_t)USART_ReceiveData(USART2);
    next = (uint16_t)((write_at + 1u) & 255u);
    if (overrun == SET || noise == SET || frame == SET || parity == SET || next == read_at) {
        ++g_lap_uart_errors; transport_error = 1u; return;
    }
    bytes[write_at] = byte; arrivals[write_at] = milliseconds; __DMB(); write_at = next;
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
