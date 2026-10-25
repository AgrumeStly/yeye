/**
 * @file motor_bench_pwm.c
 * @brief 2026-10-25重写：仅IN1切为TIM1 PWM，IN2始终普通GPIO低。
 * A=PE9/CH1，B=PE13/CH3；PE11、PE14不参与定时器复用。
 * 本层不检测电流或堵转，500ms与人工停止由应用层1ms中断监督。
 */
#include "motor_bench_pwm.h"
#include "stm32f4xx.h"
#define INPUT_PINS (GPIO_Pin_9 | GPIO_Pin_11 | GPIO_Pin_13 | GPIO_Pin_14)
static uint8_t gpio_ready, timer_ready, active_mask, requested_mask;
static uint32_t event_ms, event_state, event_fault;
static motor_bench_stop_reason_t event_reason;
volatile motor_bench_pwm_diag_t g_motor_bench_pwm_diag;

/** @brief 配置指定脚；pins为位掩码，mode为GPIO/AF，无返回值。
 * 下拉、推挽、2MHz沿速率用于短线逻辑控制，沿速率不等于PWM频率。
 * 切GPIO输出前必须清ODR，其他PE引脚不变；不在中断内等待外部设备。
 */
static void configure_pins(uint16_t pins, GPIOMode_TypeDef mode) {
    GPIO_InitTypeDef config;
    GPIO_StructInit(&config);
    config.GPIO_Pin = pins;
    config.GPIO_Mode = mode;
    config.GPIO_OType = GPIO_OType_PP;
    config.GPIO_PuPd = GPIO_PuPd_DOWN;
    config.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOE, &config);
}

void motor_bench_pwm_diag_context(uint32_t now, uint32_t state, uint32_t fault,
                                  motor_bench_stop_reason_t reason) {
    event_ms = now;
    event_state = state;
    event_fault = fault;
    event_reason = reason;
}

/** @brief 事件后读真实寄存器，valid最后置1；frame为RAM保存区，mask为桥标签。
 * 无返回值。读数逐项采集，CNT/IDR不是波形测量，停止帧mask不代表仍输出。
 * 固定次数访问，无延时、打印或Flash写入；异常停止也可执行。
 */
static void sample_registers(volatile motor_bench_pwm_snapshot_t *frame, uint8_t mask) {
    frame->valid = 0u;
    frame->run_id = g_motor_bench_pwm_diag.enable_calls;
    frame->ms = event_ms;
    frame->state = event_state;
    frame->fault = event_fault;
    frame->mask = mask;
    frame->tim_cr1 = TIM1->CR1;
    frame->tim_psc = TIM1->PSC;
    frame->tim_arr = TIM1->ARR;
    frame->tim_cnt = TIM1->CNT;
    frame->tim_ccer = TIM1->CCER;
    frame->tim_bdtr = TIM1->BDTR;
    frame->tim_ccmr1 = TIM1->CCMR1;
    frame->tim_ccmr2 = TIM1->CCMR2;
    frame->tim_ccr1 = TIM1->CCR1;
    frame->tim_ccr2 = TIM1->CCR2;
    frame->tim_ccr3 = TIM1->CCR3;
    frame->tim_ccr4 = TIM1->CCR4;
    frame->gpio_moder = GPIOE->MODER;
    frame->gpio_afrh = GPIOE->AFR[1];
    frame->gpio_otyper = GPIOE->OTYPER;
    frame->gpio_pupdr = GPIOE->PUPDR;
    frame->gpio_odr = GPIOE->ODR;
    frame->gpio_idr = GPIOE->IDR;
    frame->rcc_ahb1enr = RCC->AHB1ENR;
    frame->rcc_apb2enr = RCC->APB2ENR;
    frame->valid = 1u;
}

/** @brief 先关MOE，再强制四脚低，最后记录停止原因；reason无单位，无返回值。
 * 重复停止不覆盖原证据，未开时钟时不访问相应外设；可在异常禁中断时调用。
 * 00为滑行/休眠，撤去驱动不等于机械瞬时停稳。
 */
static void disable_output(motor_bench_stop_reason_t reason) {
    uint8_t previous = active_mask;
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
    active_mask = 0u;
    if (previous != 0u) {
        g_motor_bench_pwm_diag.stop_ms = event_ms;
        g_motor_bench_pwm_diag.elapsed_ms = event_ms - g_motor_bench_pwm_diag.start_ms;
        g_motor_bench_pwm_diag.stop_reason = (uint32_t)reason;
        sample_registers(&g_motor_bench_pwm_diag.stopped, previous);
        ++g_motor_bench_pwm_diag.stop_count;
    }
}

void motor_bench_pwm_stop(void) {
    disable_output(event_reason == MOTOR_BENCH_STOP_NONE ? MOTOR_BENCH_STOP_DIRECT : event_reason);
    requested_mask = 0u;
}

/** @brief TIM1独占CH1/CH3，初始CCR=0、MOE关闭、四脚GPIO低。
 * @return 1=16MHz时钟及配置就绪，0=时钟不符，维持零驱动。
 * APB不分频，频率=16MHz/(ARR+1)；不使用TIM1中断、DMA或互补输出。
 */
int motor_bench_pwm_init(void) {
    RCC_ClocksTypeDef clocks;
    TIM_TimeBaseInitTypeDef base;
    TIM_OCInitTypeDef channel;
    TIM_BDTRInitTypeDef gate;
    timer_ready = 0u;
    active_mask = requested_mask = 0u;
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
    base.TIM_Prescaler = 0u;
    base.TIM_Period = MOTOR_BENCH_PWM_PERIOD - 1u;
    base.TIM_CounterMode = TIM_CounterMode_Up;
    base.TIM_ClockDivision = TIM_CKD_DIV1;
    base.TIM_RepetitionCounter = 0u;
    TIM_TimeBaseInit(TIM1, &base);
    TIM_OCStructInit(&channel);
    channel.TIM_OCMode = TIM_OCMode_PWM1;
    channel.TIM_OutputState = TIM_OutputState_Enable;
    channel.TIM_OutputNState = TIM_OutputNState_Disable;
    channel.TIM_OCPolarity = TIM_OCPolarity_High;
    channel.TIM_OCIdleState = TIM_OCIdleState_Reset;
    channel.TIM_Pulse = 0u;
    TIM_OC1Init(TIM1, &channel); TIM_OC3Init(TIM1, &channel);
    TIM_OC1PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_OC3PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_ARRPreloadConfig(TIM1, ENABLE);
    TIM_BDTRStructInit(&gate);
    gate.TIM_OSSIState = TIM_OSSIState_Enable;
    gate.TIM_OSSRState = TIM_OSSRState_Enable;
    gate.TIM_AutomaticOutput = TIM_AutomaticOutput_Disable;
    TIM_BDTRConfig(TIM1, &gate);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource9, GPIO_AF_TIM1);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource13, GPIO_AF_TIM1);
    TIM_GenerateEvent(TIM1, TIM_EventSource_Update);
    TIM_Cmd(TIM1, ENABLE);
    timer_ready = 1u;
    motor_bench_pwm_stop();
    return 1;
}

/** @brief 应用桥掩码，重复1ms请求不重启输出；IN2始终普通输出低。
 * @param mask 0=停止，1=A，2=B，3=AB；其它值先停止再拒绝。
 * @return 1=成功；0=非法请求/未初始化/MOE读回失败，入口须锁存故障。
 * 先关MOE、四脚低→写CCR→UG装载→选中IN1切AF→开MOE，无等待与自动加占空比。
 */
int motor_bench_pwm_apply(uint8_t mask) {
    uint16_t selected = 0u;
    uint32_t pulse = MOTOR_BENCH_PWM_PERIOD * MOTOR_BENCH_DUTY_PERMILLE / 1000u;
    if (mask != 0u && mask != requested_mask) {
        ++g_motor_bench_pwm_diag.request_count;
        g_motor_bench_pwm_diag.last_mask = mask;
    }
    requested_mask = mask;
    if (mask == 0u) {
        if (active_mask != 0u) motor_bench_pwm_stop();
        return 1;
    }
    if (timer_ready == 0u || mask > 3u) {
        disable_output(MOTOR_BENCH_STOP_INVALID_MASK);
        return 0;
    }
    if (active_mask == mask) return 1;
    disable_output(MOTOR_BENCH_STOP_MASK_CHANGE);
    if ((mask & 1u) != 0u) selected |= GPIO_Pin_9;
    if ((mask & 2u) != 0u) selected |= GPIO_Pin_13;
    TIM_SetCompare1(TIM1, (mask & 1u) != 0u ? pulse : 0u);
    TIM_SetCompare3(TIM1, (mask & 2u) != 0u ? pulse : 0u);
    TIM_GenerateEvent(TIM1, TIM_EventSource_Update);
    configure_pins(selected, GPIO_Mode_AF);
    TIM_CtrlPWMOutputs(TIM1, ENABLE);
    active_mask = mask;
    ++g_motor_bench_pwm_diag.enable_calls;
    g_motor_bench_pwm_diag.start_ms = event_ms;
    g_motor_bench_pwm_diag.stop_ms = 0u;
    g_motor_bench_pwm_diag.elapsed_ms = 0u;
    g_motor_bench_pwm_diag.stop_reason = 0u;
    g_motor_bench_pwm_diag.stopped.valid = 0u;
    sample_registers(&g_motor_bench_pwm_diag.active, mask);
    if ((g_motor_bench_pwm_diag.active.tim_bdtr & TIM_BDTR_MOE) == 0u) {
        disable_output(MOTOR_BENCH_STOP_FAULT);
        return 0;
    }
    ++g_motor_bench_pwm_diag.enable_count;
    return 1;
}
