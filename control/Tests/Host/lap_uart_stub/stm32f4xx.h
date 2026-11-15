/* 仅主机测试：模拟SPL调用结果，实际编译生产lap_uart.c的接收/故障路径。
 * 不模拟芯片时序或电气，不能用这些断言代替板上收包和停车证据。
 */
#ifndef LAP_UART_TEST_STM32F4XX_H
#define LAP_UART_TEST_STM32F4XX_H
#include <stdint.h>
typedef enum {RESET=0, SET=1} FlagStatus;
typedef struct {uint32_t GPIO_Pin,GPIO_Mode,GPIO_Speed,GPIO_OType,GPIO_PuPd;} GPIO_InitTypeDef;
typedef struct {uint32_t USART_BaudRate,USART_Mode;} USART_InitTypeDef;
typedef struct {uint32_t NVIC_IRQChannel,NVIC_IRQChannelPreemptionPriority,NVIC_IRQChannelSubPriority,NVIC_IRQChannelCmd;} NVIC_InitTypeDef;
typedef struct {uint32_t CYCCNT;} test_dwt_t;
extern test_dwt_t test_dwt;
extern uint32_t test_flags,test_byte,test_reads,test_primask,test_priority;
#define DWT (&test_dwt)
#define USART2 2u
#define GPIOA 0u
#define ENABLE 1u
#define RCC_AHB1Periph_GPIOA 1u
#define RCC_APB1Periph_USART2 1u
#define GPIO_Pin_2 4u
#define GPIO_Pin_3 8u
#define GPIO_Mode_AF 2u
#define GPIO_Speed_50MHz 3u
#define GPIO_OType_PP 0u
#define GPIO_PuPd_UP 1u
#define GPIO_PinSource2 2u
#define GPIO_PinSource3 3u
#define GPIO_AF_USART2 7u
#define USART_Mode_Rx 1u
#define USART_Mode_Tx 2u
#define USART_IT_RXNE 1u
#define USART_IT_ERR 2u
#define NVIC_PriorityGroup_2 5u
#define USART2_IRQn 38u
#define USART_FLAG_RXNE 32u
#define USART_FLAG_ORE 8u
#define USART_FLAG_NE 4u
#define USART_FLAG_FE 2u
#define USART_FLAG_PE 1u
#define RCC_AHB1PeriphClockCmd(a,b) ((void)(a),(void)(b))
#define RCC_APB1PeriphClockCmd(a,b) ((void)(a),(void)(b))
#define GPIO_StructInit(a) ((void)(a))
#define GPIO_Init(a,b) ((void)(a),(void)(b))
#define GPIO_PinAFConfig(a,b,c) ((void)(a),(void)(b),(void)(c))
#define USART_StructInit(a) ((void)(a))
#define USART_Init(a,b) ((void)(a),(void)(b))
#define USART_ITConfig(a,b,c) ((void)(a),(void)(b),(void)(c))
#define NVIC_PriorityGroupConfig(a) ((void)(a))
#define NVIC_Init(a) (test_priority=(a)->NVIC_IRQChannelPreemptionPriority)
#define USART_Cmd(a,b) ((void)(a),(void)(b))
#define __DMB() ((void)0)
#define __get_PRIMASK() (test_primask)
#define __disable_irq() (test_primask=1u)
#define __set_PRIMASK(a) (test_primask=(a))
static inline FlagStatus USART_GetFlagStatus(uint32_t uart,uint32_t flag) {
    (void)uart; test_dwt.CYCCNT+=8u;
    return (test_flags & flag)!=0u ? SET : RESET;
}
static inline uint16_t USART_ReceiveData(uint32_t uart) {
    (void)uart; ++test_reads; test_flags=0u; return (uint16_t)test_byte;
}
#endif
