/** @file straight_pwm.c
 * @brief SPL TIM1双轮1kHz开环驱动，与已有MotorPwm工程独立。
 * PE9/11为A桥IN1/2，PE13/14为B桥IN1/2，分别为CH1/2/3/4。
 * 每桥只允许一脚输出PWM，另一脚始终GPIO低；无互补输出和换向过程。
 */
#include "straight_pwm.h"
#include "stm32f4xx.h"
#define INPUT_PINS (GPIO_Pin_9 | GPIO_Pin_11 | GPIO_Pin_13 | GPIO_Pin_14)
#define PERIOD 16000u
#if (STRAIGHT_BRIDGE_A_FORWARD != 1 && STRAIGHT_BRIDGE_A_FORWARD != -1) || \
    (STRAIGHT_BRIDGE_B_FORWARD != 1 && STRAIGHT_BRIDGE_B_FORWARD != -1)
#error Invalid straight test bridge direction
#endif
static uint8_t gpio_ready, timer_ready, running;
static uint16_t last_left_duty, last_right_duty;

/** @brief pins为引脚掩码，mode为GPIO或AF；推挽下拉，无延时和中断等待。 */
static void configure_pins(uint16_t pins, GPIOMode_TypeDef mode) {
    GPIO_InitTypeDef config;
    GPIO_StructInit(&config);
    config.GPIO_Pin = pins; config.GPIO_Mode = mode;
    config.GPIO_OType = GPIO_OType_PP; config.GPIO_PuPd = GPIO_PuPd_DOWN;
    config.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOE, &config);
}

void straight_pwm_stop(void) {
    if (timer_ready != 0u) {
        TIM_CtrlPWMOutputs(TIM1, DISABLE);
        TIM_SetCompare1(TIM1, 0u); TIM_SetCompare2(TIM1, 0u);
        TIM_SetCompare3(TIM1, 0u); TIM_SetCompare4(TIM1, 0u);
        TIM_GenerateEvent(TIM1, TIM_EventSource_Update);
    }
    if (gpio_ready != 0u) {
        GPIO_ResetBits(GPIOE, INPUT_PINS);
        configure_pins(INPUT_PINS, GPIO_Mode_OUT);
    }
    running = 0u; last_left_duty = last_right_duty = 0u;
}

int straight_pwm_init(void) {
    RCC_ClocksTypeDef clocks;
    TIM_TimeBaseInitTypeDef base;
    TIM_OCInitTypeDef channel;
    TIM_BDTRInitTypeDef gate;
    timer_ready = 0u; running = 0u; last_left_duty = last_right_duty = 0u;
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOE, ENABLE);
    GPIO_ResetBits(GPIOE, INPUT_PINS);
    configure_pins(INPUT_PINS, GPIO_Mode_OUT);
    gpio_ready = 1u;
    RCC_GetClocksFreq(&clocks);
    if (clocks.SYSCLK_Frequency != 16000000u || clocks.HCLK_Frequency != 16000000u ||
        clocks.PCLK1_Frequency != 16000000u || clocks.PCLK2_Frequency != 16000000u) return 0;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1, ENABLE);
    TIM_DeInit(TIM1);
    TIM_TimeBaseStructInit(&base);
    base.TIM_Prescaler = 0u; base.TIM_Period = PERIOD - 1u;
    TIM_TimeBaseInit(TIM1, &base);
    TIM_OCStructInit(&channel);
    channel.TIM_OCMode = TIM_OCMode_PWM1;
    channel.TIM_OutputState = TIM_OutputState_Enable;
    channel.TIM_OutputNState = TIM_OutputNState_Disable;
    channel.TIM_OCPolarity = TIM_OCPolarity_High;
    channel.TIM_OCIdleState = TIM_OCIdleState_Reset;
    channel.TIM_Pulse = 0u;
    TIM_OC1Init(TIM1, &channel); TIM_OC2Init(TIM1, &channel);
    TIM_OC3Init(TIM1, &channel); TIM_OC4Init(TIM1, &channel);
    TIM_OC1PreloadConfig(TIM1, TIM_OCPreload_Enable); TIM_OC2PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_OC3PreloadConfig(TIM1, TIM_OCPreload_Enable); TIM_OC4PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_ARRPreloadConfig(TIM1, ENABLE);
    TIM_BDTRStructInit(&gate);
    gate.TIM_OSSIState = TIM_OSSIState_Enable; gate.TIM_OSSRState = TIM_OSSRState_Enable;
    gate.TIM_AutomaticOutput = TIM_AutomaticOutput_Disable;
    TIM_BDTRConfig(TIM1, &gate);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource9, GPIO_AF_TIM1);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource11, GPIO_AF_TIM1);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource13, GPIO_AF_TIM1);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource14, GPIO_AF_TIM1);
    timer_ready = 1u;
    straight_pwm_stop();
    TIM_Cmd(TIM1, ENABLE);
    return 1;
}

int straight_pwm_apply(uint16_t left_duty, uint16_t right_duty) {
    uint32_t left_pulse, right_pulse;
    uint16_t pins;
    if (left_duty == 0u && right_duty == 0u) { if (running != 0u) straight_pwm_stop(); return 1; }
    if (timer_ready == 0u || left_duty > 500u || right_duty > 500u) { straight_pwm_stop(); return 0; }
    if (running != 0u && (TIM1->BDTR & TIM_BDTR_MOE) == 0u) {
        straight_pwm_stop(); return 0;
    }
    if (running != 0u && left_duty == last_left_duty && right_duty == last_right_duty) return 1;
    left_pulse = PERIOD * left_duty / 1000u;
    right_pulse = PERIOD * right_duty / 1000u;
    TIM_SetCompare1(TIM1, STRAIGHT_BRIDGE_A_FORWARD == 1 ? left_pulse : 0u);
    TIM_SetCompare2(TIM1, STRAIGHT_BRIDGE_A_FORWARD == -1 ? left_pulse : 0u);
    TIM_SetCompare3(TIM1, STRAIGHT_BRIDGE_B_FORWARD == 1 ? right_pulse : 0u);
    TIM_SetCompare4(TIM1, STRAIGHT_BRIDGE_B_FORWARD == -1 ? right_pulse : 0u);
    if (running == 0u) {
        /* 首次输出先装载零/非零CCR再切AF；运行中占空比更新在下个PWM周期装载，
         * 延迟小于等于1ms，不重启定时器、不翻转方向。 */
        TIM_GenerateEvent(TIM1, TIM_EventSource_Update);
        pins = (STRAIGHT_BRIDGE_A_FORWARD == 1 ? GPIO_Pin_9 : GPIO_Pin_11) |
               (STRAIGHT_BRIDGE_B_FORWARD == 1 ? GPIO_Pin_13 : GPIO_Pin_14);
        configure_pins(pins, GPIO_Mode_AF);
        TIM_CtrlPWMOutputs(TIM1, ENABLE);
        running = 1u;
    }
    last_left_duty = left_duty; last_right_duty = right_duty;
    if ((TIM1->BDTR & TIM_BDTR_MOE) == 0u) { straight_pwm_stop(); return 0; }
    return 1;
}
