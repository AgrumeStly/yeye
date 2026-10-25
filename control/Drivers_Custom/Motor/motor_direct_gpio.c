/**
 * @file motor_direct_gpio.c
 * @brief SPL普通GPIO短时驱动：A版PE9高或B版PE13高，其余三脚低；无PWM／AF。
 *
 * AT8236输入10为一个方向的导通，00为滑行／休眠；A／B尚未标定左右轮。
 * 恒定高电平在电机侧相当于满导通，强于原30%PWM，500ms限制由人工状态机执行。
 * 复位最初GPIO高阻，依赖驱动下拉；进入应用后先主动拉低，再等待新的人工触发。
 * GPIO_Mode_OUT使定时器复用不参与输出，禁止用主板引脚承担电机动力电流。
 */
#include "motor_direct_gpio.h"
#include "stm32f4xx.h"

#define DIRECT_PINS (GPIO_Pin_9 | GPIO_Pin_11 | GPIO_Pin_13 | GPIO_Pin_14)
#ifdef MOTOR_DIRECT_B_TARGET
#define DIRECT_ALLOWED_MASK 2u
#define DIRECT_HIGH_PIN GPIO_Pin_13 /* BIN1=1、BIN2=0；A桥两输入保持低。 */
#else
#define DIRECT_ALLOWED_MASK 1u
#define DIRECT_HIGH_PIN GPIO_Pin_9  /* AIN1=1、AIN2=0；B桥两输入保持低。 */
#endif
static uint8_t gpio_ready, output_ready, active_mask, requested_mask;
static uint32_t diagnostic_ms, diagnostic_state, diagnostic_fault;
static motor_direct_stop_reason_t diagnostic_reason;
volatile motor_direct_gpio_diag_t g_motor_direct_gpio_diag;

void motor_direct_gpio_diag_context(uint32_t now, uint32_t state, uint32_t fault,
                                    motor_direct_stop_reason_t reason) {
    diagnostic_ms = now;
    diagnostic_state = state;
    diagnostic_fault = fault;
    diagnostic_reason = reason;
}

/** @brief 配置四根控制脚为推挽、下拉、普通输出；只改这四位，不影响其他PE脚。
 * @return 无。调用前ODR必须已清零，避免从复用／输入切回输出时出现旧高电平。
 * GPIO_Speed为输出速度等级，不是PWM频率；本目标没有周期调制。
 */
static void pins_output(void) {
    GPIO_InitTypeDef gpio;
    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = DIRECT_PINS;
    gpio.GPIO_Mode = GPIO_Mode_OUT;
    gpio.GPIO_OType = GPIO_OType_PP;
    gpio.GPIO_Speed = GPIO_Speed_2MHz;
    gpio.GPIO_PuPd = GPIO_PuPd_DOWN;
    GPIO_Init(GPIOE, &gpio);
}

/** @brief 启用／停止操作完成后固定次数读取真实GPIO／RCC，不生成期望值。
 * @param s volatile RAM保存区；mask为当前桥事件标签，停止帧mask不表示还输出。
 * @return 无。valid最后发布；IDR只读一次，不能代替稳定电压或机械状态检测。
 */
static void capture(volatile motor_direct_gpio_snapshot_t *s, uint8_t mask) {
    s->valid = 0u;
    s->run_id = g_motor_direct_gpio_diag.enable_calls;
    s->ms = diagnostic_ms;
    s->state = diagnostic_state;
    s->fault = diagnostic_fault;
    s->mask = mask;
    s->gpio_moder = GPIOE->MODER;
    s->gpio_afrh = GPIOE->AFR[1];
    s->gpio_otyper = GPIOE->OTYPER;
    s->gpio_pupdr = GPIOE->PUPDR;
    s->gpio_odr = GPIOE->ODR;
    s->gpio_idr = GPIOE->IDR;
    s->rcc_ahb1enr = RCC->AHB1ENR;
    s->valid = 1u;
}

/** @brief 所有停止路径统一先写四脚低，再按需保留一次停止帧。
 * @param reason 停止原因，无单位；仅记录，不改变锁定语义。
 * @return 无。可由SysTick或异常禁中断路径调用，不等待、不打印、不访问TIM1。
 */
static void stop_with_reason(motor_direct_stop_reason_t reason) {
    uint8_t was_active = active_mask;
    if (gpio_ready != 0u) {
        GPIO_ResetBits(GPIOE, DIRECT_PINS);
        pins_output();
    }
    active_mask = 0u;
    if (was_active != 0u) {
        g_motor_direct_gpio_diag.stop_ms = diagnostic_ms;
        g_motor_direct_gpio_diag.elapsed_ms = diagnostic_ms - g_motor_direct_gpio_diag.start_ms;
        g_motor_direct_gpio_diag.stop_reason = (uint32_t)reason;
        capture(&g_motor_direct_gpio_diag.stopped, was_active);
        ++g_motor_direct_gpio_diag.stop_count;
    }
}

void motor_direct_gpio_stop(void) {
    stop_with_reason(diagnostic_reason != MOTOR_DIRECT_STOP_NONE ?
                     diagnostic_reason : MOTOR_DIRECT_STOP_DIRECT);
    requested_mask = 0u;
}

int motor_direct_gpio_init(void) {
    RCC_ClocksTypeDef clocks;
    output_ready = 0u; /* 时钟检查失败时，即使调用者误传非零mask，本层也拒绝置高。 */
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOE, ENABLE);
    GPIO_ResetBits(GPIOE, DIRECT_PINS); /* 输出锁存先归零，随后才启用GPIO输出。 */
    pins_output();
    gpio_ready = 1u;
    RCC_GetClocksFreq(&clocks);
    /* 500ms及R1启动等待沿用16MHz时基，配置不符拒绝人工启用。 */
    if (clocks.SYSCLK_Frequency != 16000000u || clocks.HCLK_Frequency != 16000000u ||
        clocks.PCLK1_Frequency != 16000000u || clocks.PCLK2_Frequency != 16000000u)
        return 0;
    output_ready = 1u;
    return 1;
}

int motor_direct_gpio_apply(uint8_t mask) {
    if (mask != 0u && mask != requested_mask) {
        ++g_motor_direct_gpio_diag.request_count;
        g_motor_direct_gpio_diag.last_mask = mask;
    }
    requested_mask = mask;
    if (mask == 0u) {
        if (active_mask != 0u) motor_direct_gpio_stop();
        return 1;
    }
    if (output_ready == 0u || mask != DIRECT_ALLOWED_MASK) {
        /* 只接受目标宏选定的单桥；其它桥／AB／未初始化均锁存故障。 */
        stop_with_reason(MOTOR_DIRECT_STOP_INVALID_MASK);
        return 0;
    }
    if (active_mask != 0u) return 1; /* 每1ms重复请求不重启500ms窗口或重复置高。 */
    GPIO_ResetBits(GPIOE, DIRECT_PINS);
    pins_output();
    GPIO_SetBits(GPIOE, DIRECT_HIGH_PIN); /* 只给当前目标选定桥的IN1逻辑高。 */
    active_mask = DIRECT_ALLOWED_MASK;
    ++g_motor_direct_gpio_diag.enable_calls;
    g_motor_direct_gpio_diag.start_ms = diagnostic_ms;
    g_motor_direct_gpio_diag.stop_ms = 0u;
    g_motor_direct_gpio_diag.elapsed_ms = 0u;
    g_motor_direct_gpio_diag.stop_reason = 0u;
    g_motor_direct_gpio_diag.stopped.valid = 0u;
    capture(&g_motor_direct_gpio_diag.active, DIRECT_ALLOWED_MASK);
    if ((g_motor_direct_gpio_diag.active.gpio_odr & DIRECT_PINS) == DIRECT_HIGH_PIN)
        ++g_motor_direct_gpio_diag.enable_count;
    return 1;
}
