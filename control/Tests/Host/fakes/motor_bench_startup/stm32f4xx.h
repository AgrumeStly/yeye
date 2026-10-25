/* 仅电脑启动回归使用的SPL边界模型声明；不是官方库替代物，不进入Keil工程。 */
#ifndef YEYE_TEST_MOTOR_STARTUP_STM32_H
#define YEYE_TEST_MOTOR_STARTUP_STM32_H
#include <stdint.h>
typedef enum { RESET = 0, SET = 1 } FlagStatus;
typedef enum { DISABLE = 0, ENABLE = 1 } FunctionalState;
typedef enum { Bit_RESET = 0, Bit_SET = 1 } BitAction;
typedef struct { uint32_t CPACR; } test_scb_t;
extern test_scb_t test_scb;
#define SCB (&test_scb)
#define HSI_VALUE 16000000u
#define RCC_FLAG_HSIRDY 1u
#define RCC_FLAG_LSIRDY 2u
#define RCC_SYSCLKSource_HSI 0u
#define NVIC_VectTab_FLASH 0u
#define RCC_AHB1Periph_GPIOA 1u
#define RCC_AHB1Periph_GPIOB 2u
#define GPIOA ((void *)1)
#define GPIOB ((void *)2)
#define GPIO_Pin_0 1u
#define GPIO_Pin_2 4u
#define GPIO_Mode_IN 0u
#define GPIO_Mode_OUT 1u
#define GPIO_PuPd_DOWN 2u
#define GPIO_PuPd_NOPULL 0u
#define GPIO_OType_PP 0u
#define GPIO_Speed_2MHz 0u
#define IWDG_WriteAccess_Enable 0x5555u
#define IWDG_Prescaler_32 3u
#define IWDG_FLAG_PVU 1u
#define IWDG_FLAG_RVU 2u
#define SysTick_IRQn 0
#define TIM5 ((void *)3)
#define RCC_APB1Periph_TIM5 8u
#define TIM_CounterMode_Up 0u
#define TIM_CKD_DIV1 0u
#define TIM_EventSource_Update 1u
typedef struct { uint32_t SYSCLK_Frequency, HCLK_Frequency, PCLK1_Frequency, PCLK2_Frequency; } RCC_ClocksTypeDef;
typedef struct { uint32_t GPIO_Pin, GPIO_Mode, GPIO_PuPd, GPIO_OType, GPIO_Speed; } GPIO_InitTypeDef;
typedef struct { uint32_t TIM_Prescaler, TIM_Period, TIM_CounterMode, TIM_ClockDivision, TIM_RepetitionCounter; } TIM_TimeBaseInitTypeDef;
void RCC_HSICmd(FunctionalState state);
FlagStatus RCC_GetFlagStatus(uint32_t flag);
void RCC_SYSCLKConfig(uint32_t source);
uint8_t RCC_GetSYSCLKSource(void);
void RCC_DeInit(void);
void NVIC_SetVectorTable(uint32_t table, uint32_t offset);
void RCC_GetClocksFreq(RCC_ClocksTypeDef *clocks);
void RCC_AHB1PeriphClockCmd(uint32_t clock, FunctionalState state);
void GPIO_StructInit(GPIO_InitTypeDef *gpio);
void GPIO_Init(void *port, GPIO_InitTypeDef *gpio);
void GPIO_ResetBits(void *port, uint16_t pins);
uint8_t GPIO_ReadInputDataBit(void *port, uint16_t pin);
void GPIO_WriteBit(void *port, uint16_t pin, BitAction bit);
void RCC_LSICmd(FunctionalState state);
void IWDG_WriteAccessCmd(uint16_t key);
void IWDG_SetPrescaler(uint8_t divider);
void IWDG_SetReload(uint16_t reload);
FlagStatus IWDG_GetFlagStatus(uint16_t flag);
void IWDG_ReloadCounter(void);
void IWDG_Enable(void);
uint32_t SysTick_Config(uint32_t ticks);
void NVIC_SetPriority(int irq, uint32_t priority);
void __disable_irq(void);
void __WFI(void);
void RCC_APB1PeriphClockCmd(uint32_t clock, FunctionalState state);
void TIM_DeInit(void *timer);
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef *timebase);
void TIM_TimeBaseInit(void *timer, TIM_TimeBaseInitTypeDef *timebase);
void TIM_GenerateEvent(void *timer, uint16_t event);
void TIM_Cmd(void *timer, FunctionalState state);
uint32_t TIM_GetCounter(void *timer);
#endif
