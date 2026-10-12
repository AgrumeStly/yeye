#ifndef YEYE_BOARD_H
#define YEYE_BOARD_H
#include <stdint.h>
/* UART pin assignment must be confirmed by 主控 and 硬件 before enabling. */
#ifndef BOARD_UART_ENABLE
#define BOARD_UART_ENABLE 0
#endif
void board_init(void);
uint32_t board_millis(void);
int board_uart_read(uint8_t *byte);
int board_uart_fault(void);
void board_apply_requests(int16_t left, int16_t right);
extern volatile int16_t board_left_request, board_right_request;
extern volatile uint32_t board_uart_errors;
#endif
