/* 直接编译生产UART驱动，验证接收环回绕、硬件/软件错误分类及故障锁存。
 * SPL/寄存器由独立stub替代；此处不模拟NVIC抢占或真实硬件处理耗时。
 */
#include <assert.h>
#include <stdio.h>
#include "stm32f4xx.h"
#include "lap_uart.h"
test_dwt_t test_dwt;
uint32_t test_flags,test_byte,test_reads,test_primask,test_priority;
void USART2_IRQHandler(void);
static void feed(uint32_t flags,uint32_t value) {
    test_flags=flags; test_byte=value; USART2_IRQHandler();
}
int main(void) {
    uint8_t byte; uint32_t arrival,i;
    lap_uart_init();
    assert(test_priority==0u);
    assert(g_lap_uart_errors==0u && g_lap_uart_diag.isr_max_cycles==0u);
    feed(0u,0u); assert(test_reads==0u && !lap_uart_fault());
    /* 超过环大小的逐次推入/取出仍保持字节及各自到达时间。 */
    for (i=0u;i<600u;++i) {
        lap_uart_tick(i); feed(USART_FLAG_RXNE,i & 255u);
        assert(lap_uart_read(&byte,&arrival)); assert(byte==(uint8_t)i && arrival==i);
        assert(!lap_uart_read(&byte,&arrival));
    }
    assert(g_lap_uart_errors==0u && g_lap_uart_diag.isr_max_cycles>0u);
    /* 软件环只能存255字节；满时报告故障，消费故障后清环但保留统计。 */
    lap_uart_init();
    for (i=0u;i<255u;++i) feed(USART_FLAG_RXNE,i);
    feed(USART_FLAG_RXNE,255u);
    assert(g_lap_uart_errors==1u && g_lap_uart_diag.ring_full==1u);
    assert(g_lap_uart_diag.first_mask==LAP_UART_ERROR_RING_FULL);
    test_primask=1u; assert(lap_uart_fault()); assert(test_primask==1u);
    test_primask=0u; assert(!lap_uart_fault()); assert(!lap_uart_read(&byte,&arrival));
    assert(g_lap_uart_errors==1u);
    /* 同一事件可以同时有多个硬件错误，首次证据不被后续错误覆盖。 */
    lap_uart_init(); lap_uart_tick(123u);
    feed(USART_FLAG_RXNE|USART_FLAG_ORE|USART_FLAG_NE|USART_FLAG_FE|USART_FLAG_PE,0u);
    assert(g_lap_uart_errors==1u && g_lap_uart_diag.first_mask==15u);
    assert(g_lap_uart_diag.overrun==1u && g_lap_uart_diag.noise==1u);
    assert(g_lap_uart_diag.frame==1u && g_lap_uart_diag.parity==1u);
    assert(g_lap_uart_diag.ring_full==0u && !lap_uart_read(&byte,&arrival));
    lap_uart_tick(456u); feed(USART_FLAG_ORE,0u);
    assert(g_lap_uart_errors==2u && g_lap_uart_diag.overrun==2u);
    assert(g_lap_uart_diag.first_at_ms==123u && g_lap_uart_diag.last_at_ms==456u);
    assert(g_lap_uart_diag.first_mask==15u && g_lap_uart_diag.last_mask==1u);
    assert(lap_uart_fault() && !lap_uart_fault());
    assert(g_lap_uart_errors==2u && g_lap_uart_diag.first_mask==15u);
    puts("UART production driver checks PASS: ring wrap/full, errors, latch, priority configuration; hardware timing NOT tested");
    return 0;
}
