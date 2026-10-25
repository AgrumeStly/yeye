/**
 * @file motor_bench_pwm.c
 * @brief SPL TIM1四通道20kHz PWM与AT8236首次开环输出。
 *
 * PE9/PE11为AIN1/AIN2，PE13/PE14为BIN1/BIN2，均AF1。
 * 四通道共享周期但各有CCR；R2仅IN1输出固定30% PWM，IN2保持0，快衰减。
 * 周期800计数、有效CCR=240，20kHz不变；500ms与人工触发约束仍由台架逻辑执行。
 * 停止使用00滑行/休眠，不使用11主动刹车，不做反转或任何自动加占空比。
 * reset期间GPIO为高阻，依赖驱动输入下拉，实际复位窗口必须现场测量；
 * 应用初始化先主动拉低，再建立CCR=0的定时器，人工触发前MOE保持关闭。
 * R3只新增启用／停止事件的真实寄存器读回；快照不反向参与输出或时长决定。
 */
#include "motor_bench_pwm.h"
#include "stm32f4xx.h"

#define MOTOR_PINS (GPIO_Pin_9 | GPIO_Pin_11 | GPIO_Pin_13 | GPIO_Pin_14)
static uint8_t gpio_ready, timer_ready, active_mask;
volatile motor_bench_pwm_diag_t g_motor_bench_pwm_diag;
static uint32_t diagnostic_ms, diagnostic_state, diagnostic_fault;
static motor_bench_stop_reason_t diagnostic_reason;
static uint8_t requested_mask;

void motor_bench_pwm_diag_context(uint32_t now, uint32_t state, uint32_t fault,
                                  motor_bench_stop_reason_t reason) {
    /* 只记下调用者提供的真实滴答／状态，不反向修改原状态机或任何输出。 */
    diagnostic_ms = now;
    diagnostic_state = state;
    diagnostic_fault = fault;
    diagnostic_reason = reason;
}

/**
 * @brief 有限次MMIO读回，保存为活动／停止快照；仅在外设已经初始化后调用。
 * @param sample 指向volatile保留区；mask为本次实际启用调用对应的桥掩码。
 * 先清valid，逐项读取TIM1/GPIOE/RCC寄存器，最后发布valid=1。
 * 寄存器字段绝不写入宏计算值；PSC/ARR/CCR/MOE等即使与期望不同，也原样保存。
 * IDR只读一次，不循环采样，不把固定1ms与20kHz同步采样造成的同相读数当波形。
 * 无延时、打印、动态内存或等待；仅启用／结束事件调用，不在每个PWM周期采集。
 */
static void capture(volatile motor_bench_pwm_snapshot_t *sample, uint8_t mask) {
    sample->valid = 0u;
    sample->run_id = g_motor_bench_pwm_diag.enable_calls;
    sample->ms = diagnostic_ms;
    sample->state = diagnostic_state;
    sample->fault = diagnostic_fault;
    sample->mask = mask;
    sample->tim_cr1 = TIM1->CR1;
    sample->tim_psc = TIM1->PSC;
    sample->tim_arr = TIM1->ARR;
    sample->tim_cnt = TIM1->CNT;
    sample->tim_ccer = TIM1->CCER;
    sample->tim_bdtr = TIM1->BDTR;
    sample->tim_ccmr1 = TIM1->CCMR1;
    sample->tim_ccmr2 = TIM1->CCMR2;
    sample->tim_ccr1 = TIM1->CCR1;
    sample->tim_ccr2 = TIM1->CCR2;
    sample->tim_ccr3 = TIM1->CCR3;
    sample->tim_ccr4 = TIM1->CCR4;
    sample->gpio_moder = GPIOE->MODER;
    sample->gpio_afrh = GPIOE->AFR[1];
    sample->gpio_otyper = GPIOE->OTYPER;
    sample->gpio_pupdr = GPIOE->PUPDR;
    sample->gpio_odr = GPIOE->ODR;
    sample->gpio_idr = GPIOE->IDR;
    sample->rcc_ahb1enr = RCC->AHB1ENR;
    sample->rcc_apb2enr = RCC->APB2ENR;
    sample->valid = 1u;
}

/**
 * @brief 为四个控制脚同时选择GPIO输出或AF模式，统一下拉和推挽。
 * @param mode GPIO_Mode_OUT或GPIO_Mode_AF；无单位。
 * @return 无。ODR必须先写0再切换为GPIO输出，避免停机时出现高电平毛刺。
 */
static void pins_mode(GPIOMode_TypeDef mode) {
    GPIO_InitTypeDef gpio;
    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = MOTOR_PINS;
    gpio.GPIO_Mode = mode;
    gpio.GPIO_OType = GPIO_OType_PP;
    gpio.GPIO_Speed = GPIO_Speed_2MHz;
    gpio.GPIO_PuPd = GPIO_PuPd_DOWN;
    GPIO_Init(GPIOE, &gpio);
}

/**
 * @brief 执行原有安全停止，再为确实走过启用路径的一轮保留停止后读数。
 * @param reason 停止原因枚举，无单位，只作说明，不改变关断操作或允许重启。
 * @return 无。初始化／重复stop也执行必要的安全写入，但不伪造新的有效停止帧。
 * 此函数可在SysTick或异常禁中断路径调用；先撤MOE和四脚输出，再作固定次数采集，
 * 不打印、不等待调试器，避免诊断阻塞停止；GPIO／定时器尚未就绪时不访问它们。
 */
static void stop_with_reason(motor_bench_stop_reason_t reason) {
    uint8_t was_active = active_mask;
    /* 异常处理也可调用；时钟尚未开启时不访问相应外设。 */
    if (timer_ready != 0u) {
        TIM_CtrlPWMOutputs(TIM1, DISABLE);
        TIM_SetCompare1(TIM1, 0u); TIM_SetCompare2(TIM1, 0u);
        TIM_SetCompare3(TIM1, 0u); TIM_SetCompare4(TIM1, 0u);
        TIM_GenerateEvent(TIM1, TIM_EventSource_Update);
    }
    if (gpio_ready != 0u) {
        GPIO_ResetBits(GPIOE, MOTOR_PINS);
        pins_mode(GPIO_Mode_OUT);
    }
    active_mask = 0u;
    if (was_active != 0u) {
        /* 所有安全写入完成后才采集，绝不以活动快照代替真正的停止后读数。
         * 重复停止（含故障每毫秒重复stop）不改时间／原因或覆盖活动证据。
         */
        g_motor_bench_pwm_diag.stop_ms = diagnostic_ms;
        g_motor_bench_pwm_diag.elapsed_ms = diagnostic_ms - g_motor_bench_pwm_diag.start_ms;
        g_motor_bench_pwm_diag.stop_reason = (uint32_t)reason;
        capture(&g_motor_bench_pwm_diag.stopped, was_active);
        ++g_motor_bench_pwm_diag.stop_count;
    }
}

void motor_bench_pwm_stop(void) {
    stop_with_reason(diagnostic_reason != MOTOR_BENCH_STOP_NONE ?
                     diagnostic_reason : MOTOR_BENCH_STOP_DIRECT);
    requested_mask = 0u; /* 外部停止终结当前请求；内部换mask预停不清请求去重基线。 */
}

int motor_bench_pwm_init(void) {
    RCC_ClocksTypeDef clocks;
    TIM_TimeBaseInitTypeDef timebase;
    TIM_OCInitTypeDef output;
    TIM_BDTRInitTypeDef protection;

    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOE, ENABLE);
    GPIO_ResetBits(GPIOE, MOTOR_PINS);
    pins_mode(GPIO_Mode_OUT);
    gpio_ready = 1u;
    /* 本目标固定HSI 16MHz且APB均不分频，配置不符则拒绝启用，而非错误套频率。 */
    RCC_GetClocksFreq(&clocks);
    if (clocks.SYSCLK_Frequency != 16000000u || clocks.HCLK_Frequency != 16000000u ||
        clocks.PCLK1_Frequency != 16000000u || clocks.PCLK2_Frequency != 16000000u)
        return 0;
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1, ENABLE);
    TIM_DeInit(TIM1);
    timer_ready = 1u;
    TIM_TimeBaseStructInit(&timebase);
    timebase.TIM_Prescaler = 0u;
    timebase.TIM_Period = MOTOR_BENCH_PWM_PERIOD - 1u;
    timebase.TIM_CounterMode = TIM_CounterMode_Up;
    timebase.TIM_ClockDivision = TIM_CKD_DIV1;
    timebase.TIM_RepetitionCounter = 0u;
    TIM_TimeBaseInit(TIM1, &timebase);

    TIM_OCStructInit(&output);
    output.TIM_OCMode = TIM_OCMode_PWM1;
    output.TIM_OutputState = TIM_OutputState_Enable;
    output.TIM_OutputNState = TIM_OutputNState_Disable; /* 不驱动互补CHxN。 */
    output.TIM_Pulse = 0u;
    output.TIM_OCPolarity = TIM_OCPolarity_High;
    output.TIM_OCIdleState = TIM_OCIdleState_Reset;
    TIM_OC1Init(TIM1, &output); TIM_OC2Init(TIM1, &output);
    TIM_OC3Init(TIM1, &output); TIM_OC4Init(TIM1, &output);
    TIM_OC1PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_OC2PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_OC3PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_OC4PreloadConfig(TIM1, TIM_OCPreload_Enable);
    TIM_ARRPreloadConfig(TIM1, ENABLE);
    TIM_BDTRStructInit(&protection);
    protection.TIM_OSSIState = TIM_OSSIState_Enable;
    protection.TIM_OSSRState = TIM_OSSRState_Enable;
    protection.TIM_AutomaticOutput = TIM_AutomaticOutput_Disable;
    TIM_BDTRConfig(TIM1, &protection); /* 不用自动恢复输出，也未接硬件BKIN。 */
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource9, GPIO_AF_TIM1);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource11, GPIO_AF_TIM1);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource13, GPIO_AF_TIM1);
    GPIO_PinAFConfig(GPIOE, GPIO_PinSource14, GPIO_AF_TIM1);
    TIM_GenerateEvent(TIM1, TIM_EventSource_Update);
    TIM_Cmd(TIM1, ENABLE); /* 计数可运行，MOE仍关闭且脚仍为GPIO低。 */
    motor_bench_pwm_stop();
    return 1;
}

void motor_bench_pwm_apply(uint8_t mask) {
    uint32_t pulse = MOTOR_BENCH_PWM_PERIOD * MOTOR_BENCH_DUTY_PERMILLE / 1000u;
    if (mask != 0u && mask != requested_mask) {
        ++g_motor_bench_pwm_diag.request_count;
        g_motor_bench_pwm_diag.last_mask = mask;
    }
    requested_mask = mask;
    if (timer_ready == 0u || mask > 3u || mask == 0u) {
        /* 停止不等待下个PWM周期；相同的静止状态无需重复切GPIO模式。 */
        if (mask > 3u) stop_with_reason(MOTOR_BENCH_STOP_INVALID_MASK);
        else if (active_mask != 0u) motor_bench_pwm_stop();
        return;
    }
    if (mask == active_mask) return;
    stop_with_reason(MOTOR_BENCH_STOP_MASK_CHANGE);
    /* 先在MOE关闭时写完四个预装载值，再一次UG同时生效，最后接通输出。 */
    TIM_SetCompare1(TIM1, (mask & 1u) != 0u ? pulse : 0u);
    TIM_SetCompare2(TIM1, 0u);
    TIM_SetCompare3(TIM1, (mask & 2u) != 0u ? pulse : 0u);
    TIM_SetCompare4(TIM1, 0u);
    TIM_GenerateEvent(TIM1, TIM_EventSource_Update);
    pins_mode(GPIO_Mode_AF);
    TIM_CtrlPWMOutputs(TIM1, ENABLE);
    active_mask = mask;
    ++g_motor_bench_pwm_diag.enable_calls;
    g_motor_bench_pwm_diag.stopped.valid = 0u; /* 新一轮不能误读为已有配对停止。 */
    g_motor_bench_pwm_diag.start_ms = diagnostic_ms;
    g_motor_bench_pwm_diag.stop_ms = 0u;
    g_motor_bench_pwm_diag.elapsed_ms = 0u;
    g_motor_bench_pwm_diag.stop_reason = MOTOR_BENCH_STOP_NONE;
    capture(&g_motor_bench_pwm_diag.active, mask); /* 必须位于AF及MOE启用调用之后。 */
    if ((g_motor_bench_pwm_diag.active.tim_bdtr & TIM_BDTR_MOE) != 0u)
        ++g_motor_bench_pwm_diag.enable_count;
}
