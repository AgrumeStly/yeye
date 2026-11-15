/** @file lap_uart.h
 * @brief USART2适配：PA2/TX、PA3/RX，115200/8N1，256字节接收环。
 * 中断只接收，主循环解析；每字节保存本地ms防止积压旧包冒充新鲜路径。
 */
#ifndef YEYE_LAP_UART_H
#define YEYE_LAP_UART_H
#include <stdint.h>
/* 抢占优先级数字越小越高。UART只搬运一个字节，可抢占含浮点计算的SysTick；
 * 使用NVIC_PriorityGroup_2，主入口必须通过NVIC_EncodePriority设置系统异常。
 */
#define LAP_UART_PREEMPT_PRIORITY 0u
#define LAP_SAFETY_PREEMPT_PRIORITY 1u
/** @brief 接收故障分类，位可同时出现；仅作诊断，不改变任一错误即撤驱动的策略。 */
#define LAP_UART_ERROR_OVERRUN 1u
#define LAP_UART_ERROR_NOISE 2u
#define LAP_UART_ERROR_FRAME 4u
#define LAP_UART_ERROR_PARITY 8u
#define LAP_UART_ERROR_RING_FULL 16u
/** @brief 本次上电累计诊断，可在Keil Watch展开g_lap_uart_diag。
 * overrun表示USART数据未及时读取；ring_full表示软件接收环无空位。
 * noise/frame/parity记录硬件接收状态，不能仅凭其中一项断定接线根因。
 * first/last_mask使用上面的位定义，时间为本板启动后的毫秒数。
 * 一个中断可能同时包含多个错误，因此分项之和可以大于总错误事件数。
 * 仅初始化清零，主循环消费故障或协议恢复均不清除，保留首次现场。
 */
typedef struct {
    uint32_t overrun, noise, frame, parity, ring_full;
    uint32_t first_mask, last_mask, first_at_ms, last_at_ms;
    uint32_t isr_max_cycles; /* DWT周期数；不含异常入口/退出，用于核对接收ISR开销。 */
} lap_uart_diag_t;
void lap_uart_init(void);
void lap_uart_tick(uint32_t now);
int lap_uart_read(uint8_t *byte, uint32_t *arrival);
int lap_uart_fault(void);
extern volatile uint32_t g_lap_uart_errors;
extern volatile lap_uart_diag_t g_lap_uart_diag;
#endif
