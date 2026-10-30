/* 新入口电脑边界，复用既有fake的CMSIS／GPIO／R1声明，不进入Keil。 */
#ifndef YEYE_TEST_ENCODER_STM32_H
#define YEYE_TEST_ENCODER_STM32_H
#include "../motor_bench_pwm/stm32f4xx.h"
typedef model_tim_t TIM_TypeDef;
extern model_gpio_t model_gpio_c;
extern model_tim_t model_tim3, model_tim4;
#define GPIOC (&model_gpio_c)
#define TIM3 (&model_tim3)
#define TIM4 (&model_tim4)
#define RCC_AHB1Periph_GPIOC 4u
#define RCC_APB1Periph_TIM3 2u
#define RCC_APB1Periph_TIM4 4u
#define GPIO_Pin_6 (1u << 6)
#define GPIO_Pin_7 (1u << 7)
#define GPIO_PinSource6 6u
#define GPIO_PinSource7 7u
#define GPIO_AF_TIM3 2u
#define GPIO_AF_TIM4 2u
#define GPIO_PuPd_UP 1u
#define TIM_EncoderMode_TI12 3u
#define TIM_ICPolarity_Rising 0u
#define TIM_ICSelection_DirectTI 1u
#define TIM_ICPSC_DIV1 0u
#define TIM_Channel_1 0u
#define TIM_Channel_2 4u
typedef struct { uint16_t TIM_Channel, TIM_ICPolarity, TIM_ICSelection, TIM_ICPrescaler, TIM_ICFilter; } TIM_ICInitTypeDef;
void TIM_EncoderInterfaceConfig(void *timer, uint16_t mode, uint16_t p1, uint16_t p2);
void TIM_ICStructInit(TIM_ICInitTypeDef *input);
void TIM_ICInit(void *timer, TIM_ICInitTypeDef *input);
void TIM_SetCounter(void *timer, uint32_t count);
#endif
