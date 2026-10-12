#include "board.h"
#include "stm32f4xx.h"
static volatile uint32_t milliseconds;
volatile int16_t board_left_request, board_right_request;
volatile uint32_t board_uart_errors;
#if BOARD_UART_ENABLE
static volatile uint16_t rx_write, rx_read;
static volatile uint8_t rx_fault;
static uint8_t rx_bytes[256];
#endif
/* Standalone reset: 16 MHz internal HSI, no dependency on the board's external crystal. */
void SystemInit(void) {
    RCC->CR |= RCC_CR_HSION;
    while ((RCC->CR & RCC_CR_HSIRDY) == 0u) { }
    RCC->CFGR = 0u;
    while ((RCC->CFGR & RCC_CFGR_SWS) != 0u) { }
    RCC->CR &= ~(RCC_CR_PLLON | RCC_CR_HSEON | RCC_CR_CSSON);
    SCB->VTOR = 0x08000000u;
    SCB->CPACR |= 0x00f00000u;
}
void SysTick_Handler(void) { ++milliseconds; }
void board_init(void) {
    board_left_request=0; board_right_request=0;
    (void)SysTick_Config(16000u);
#if BOARD_UART_ENABLE
    /* Proposed USART2: PA2 TX, PA3 RX, AF7, 115200 8N1, APB1=16 MHz. */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;
    (void)RCC->AHB1ENR;
    GPIOA->MODER = (GPIOA->MODER & ~0x000000f0u) | 0x000000a0u;
    GPIOA->AFR[0] = (GPIOA->AFR[0] & ~0x0000ff00u) | 0x00007700u;
    GPIOA->PUPDR = (GPIOA->PUPDR & ~0x000000f0u) | 0x00000040u;
    USART2->BRR=139u;
    USART2->CR1=USART_CR1_UE | USART_CR1_RE | USART_CR1_TE | USART_CR1_RXNEIE;
    NVIC_EnableIRQ(USART2_IRQn);
#endif
}
uint32_t board_millis(void) { return milliseconds; }
#if BOARD_UART_ENABLE
void USART2_IRQHandler(void) {
    uint32_t status=USART2->SR;
    uint8_t byte;
    uint16_t next;
    if (status & (USART_SR_RXNE | USART_SR_ORE | USART_SR_NE | USART_SR_FE | USART_SR_PE)) {
        byte=(uint8_t)USART2->DR;
        if (status & (USART_SR_ORE | USART_SR_NE | USART_SR_FE | USART_SR_PE)) { ++board_uart_errors; rx_fault=1; return; }
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
