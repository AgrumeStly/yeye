/** @file lap_uart.h
 * @brief USART2适配：PA2/TX、PA3/RX，115200/8N1，256字节接收环。
 * 中断只接收，主循环解析；每字节保存本地ms防止积压旧包冒充新鲜路径。
 */
#ifndef YEYE_LAP_UART_H
#define YEYE_LAP_UART_H
#include <stdint.h>
void lap_uart_init(void);
void lap_uart_tick(uint32_t now);
int lap_uart_read(uint8_t *byte, uint32_t *arrival);
int lap_uart_fault(void);
extern volatile uint32_t g_lap_uart_errors;
#endif
