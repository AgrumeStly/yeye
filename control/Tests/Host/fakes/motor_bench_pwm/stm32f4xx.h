/* R3仅供电脑测试：扩展既有SPL边界，使用可扰动的volatile寄存器模型。
 * 真实PWM/main源码直接访问这些字段，因此可以验证读回值，而非测试一份常量镜像。
 * 不进入Keil工程，不代替官方库或STM32电气模型。
 */
#ifndef YEYE_TEST_MOTOR_PWM_STM32_H
#define YEYE_TEST_MOTOR_PWM_STM32_H
#include "../motor_bench_startup/stm32f4xx.h"
typedef struct {
    volatile uint32_t MODER, OTYPER, PUPDR, ODR, IDR, AFR[2];
} model_gpio_t;
typedef struct {
    volatile uint32_t CR1, PSC, ARR, CNT, CCER, BDTR, CCMR1, CCMR2, CCR1, CCR2, CCR3, CCR4;
} model_tim_t;
typedef struct { volatile uint32_t AHB1ENR, APB2ENR; } model_rcc_t;
extern model_gpio_t model_gpio_a, model_gpio_b, model_gpio_e;
extern model_tim_t model_tim1;
extern model_rcc_t model_rcc;
#undef GPIOA
#undef GPIOB
#define GPIOA (&model_gpio_a)
#define GPIOB (&model_gpio_b)
#define GPIOE (&model_gpio_e)
#define TIM1 (&model_tim1)
#define RCC (&model_rcc)
#define RCC_AHB1Periph_GPIOE (1u << 4)
#define RCC_APB2Periph_TIM1 1u
#define GPIO_Pin_9 (1u << 9)
#define GPIO_Pin_11 (1u << 11)
#define GPIO_Pin_13 (1u << 13)
#define GPIO_Pin_14 (1u << 14)
#define GPIO_PinSource9 9u
#define GPIO_PinSource11 11u
#define GPIO_PinSource13 13u
#define GPIO_PinSource14 14u
#define GPIO_AF_TIM1 1u
#define GPIO_Mode_AF 2u
typedef uint32_t GPIOMode_TypeDef;
#define TIM_BDTR_MOE (1u << 15)
#define TIM_OCMode_PWM1 0x60u
#define TIM_OutputState_Enable 1u
#define TIM_OutputNState_Disable 0u
#define TIM_OCPolarity_High 0u
#define TIM_OCIdleState_Reset 0u
#define TIM_OCPreload_Enable 1u
#define TIM_OSSIState_Enable (1u << 10)
#define TIM_OSSRState_Enable (1u << 11)
#define TIM_AutomaticOutput_Disable 0u
typedef struct {
    uint32_t TIM_OCMode, TIM_OutputState, TIM_OutputNState, TIM_Pulse, TIM_OCPolarity, TIM_OCIdleState;
} TIM_OCInitTypeDef;
typedef struct { uint32_t TIM_OSSIState, TIM_OSSRState, TIM_AutomaticOutput; } TIM_BDTRInitTypeDef;
void RCC_APB2PeriphClockCmd(uint32_t clock, FunctionalState state);
void GPIO_PinAFConfig(void *port, uint16_t pin, uint8_t af);
void TIM_OCStructInit(TIM_OCInitTypeDef *output);
void TIM_OC1Init(void *timer, TIM_OCInitTypeDef *output);
void TIM_OC2Init(void *timer, TIM_OCInitTypeDef *output);
void TIM_OC3Init(void *timer, TIM_OCInitTypeDef *output);
void TIM_OC4Init(void *timer, TIM_OCInitTypeDef *output);
void TIM_OC1PreloadConfig(void *timer, uint16_t state);
void TIM_OC2PreloadConfig(void *timer, uint16_t state);
void TIM_OC3PreloadConfig(void *timer, uint16_t state);
void TIM_OC4PreloadConfig(void *timer, uint16_t state);
void TIM_ARRPreloadConfig(void *timer, FunctionalState state);
void TIM_BDTRStructInit(TIM_BDTRInitTypeDef *protection);
void TIM_BDTRConfig(void *timer, TIM_BDTRInitTypeDef *protection);
void TIM_CtrlPWMOutputs(void *timer, FunctionalState state);
void TIM_SetCompare1(void *timer, uint32_t compare);
void TIM_SetCompare2(void *timer, uint32_t compare);
void TIM_SetCompare3(void *timer, uint32_t compare);
void TIM_SetCompare4(void *timer, uint32_t compare);
#endif
