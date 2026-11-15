/* 复用真实Core／PWM／encoder_hw及SPL边界模型；验证100%寄存器与异常撤驱动。 */
#include "speed_match_integration_harness.h"
static void wait_ready(void) {
    unsigned i;
    for (i = 0u; i < 5000u && g_speed_match.state != SPEED_READY; ++i) ticks(1u);
    CHECK(g_speed_match.state == SPEED_READY);
}
static void trigger(void) {
    wait_ready(); pressed = 1u; ticks(1100u); CHECK(g_speed_match.state == SPEED_ARMED);
    pressed = 0u; ticks(31u);
}
static void stopped(void) {
    CHECK((TIM1->BDTR & TIM_BDTR_MOE) == 0u);
    CHECK(TIM1->CCR1 == 0u && TIM1->CCR2 == 0u && TIM1->CCR3 == 0u && TIM1->CCR4 == 0u);
    CHECK((GPIOE->MODER & 0x3ccc0000u) == 0x14440000u);
}
static void prepare(void) {
    CHECK(g_speed_revision == 0x020f1002u && g_speed_fault == 0u && g_speed_watchdog_stage == 4u);
    ticks(1100u); stopped(); CHECK(g_speed_match.phase == 0u && g_sprint.best_rpm == 0.0f);
    trigger(); CHECK(TIM1->CCR1 == 8000u && TIM1->CCR4 == 0u);
    ticks(500u); stopped(); CHECK(g_speed_match.phase == 1u);
    trigger(); CHECK(TIM1->CCR1 == 0u && TIM1->CCR4 == 8000u);
    ticks(500u); stopped(); CHECK(g_speed_match.phase == 2u);
    CHECK(g_speed_match.left_channel == 1u && g_speed_match.right_channel == 2u);
    CHECK(g_speed_match.left_sign == 1 && g_speed_match.right_sign == -1);
}
static void sequence(void) {
    uint32_t begin;
    prepare(); trigger(); begin = g_speed_ms;
    CHECK(g_speed_match.command_rpm == 10.0f);
    CHECK(TIM1->CCR1 > 0u && TIM1->CCR4 > 0u && TIM1->CCR2 == 0u && TIM1->CCR3 == 0u);
    ticks(2999u); CHECK(g_speed_match.state == SPEED_RUNNING && g_speed_fault == 0u);
    ticks(1u); stopped(); CHECK(g_speed_match.stop_ms - begin == 3000u);
    CHECK(g_sprint.result_id == 1u && g_sprint.stop_reason == 1u && g_sprint.best_rpm == 0.0f);
    trigger(); CHECK(g_speed_match.state == SPEED_RUNNING && g_speed_match.runs == 2u);
    pressed = 1u; ticks(1u); stopped();
    CHECK(g_speed_match.error == SPEED_ERROR_KEY && g_sprint.last_result == SPRINT_FAULTED);
}
static void full_pwm_and_bounds(void) {
    prepare(); wait_ready();
    CHECK(straight_pwm_apply(1000u, 1000u));
    CHECK(TIM1->ARR == 15999u && TIM1->CCR1 == 16000u && TIM1->CCR4 == 16000u);
    CHECK(TIM1->CCR2 == 0u && TIM1->CCR3 == 0u && (TIM1->BDTR & TIM_BDTR_MOE) != 0u);
    CHECK(((GPIOE->MODER >> 22) & 3u) == GPIO_Mode_OUT && ((GPIOE->MODER >> 26) & 3u) == GPIO_Mode_OUT);
    CHECK(!straight_pwm_apply(1001u, 0u)); stopped();
    CHECK(!straight_pwm_apply(0u, 1001u)); stopped();
    CHECK(straight_pwm_apply(0u, 1000u)); CHECK(TIM1->CCR1 == 0u && TIM1->CCR4 == 16000u);
    straight_pwm_stop(); stopped();
    g_speed_config.target_rpm = 300.0f; g_speed_config.pi.kp = 10.0f; g_speed_config.pi.ki = 20.0f;
    trigger(); ticks(2000u); stopped();
    CHECK(g_sprint.last_result == SPRINT_FAULTED && g_speed_match.error == SPEED_ERROR_SYNC);
}
static void distance_stop(void) {
    prepare(); g_sprint_config.distance_limit_mm = 200u; trigger();
    while (g_speed_match.state == SPEED_RUNNING) ticks(1u);
    stopped(); CHECK(g_sprint.stop_reason == 2u && g_sprint.last_distance_mm >= 200.0f);
}
static void read_failure(void) {
    prepare(); trigger(); ready = 0u; ticks(20u); stopped();
    CHECK(g_speed_fault == 64u && g_sprint.last_result == SPRINT_FAULTED);
}
static void moe_failure(void) {
    prepare(); trigger(); TIM1->BDTR &= ~TIM_BDTR_MOE; ticks(1u); stopped();
    CHECK(g_speed_fault == 32u && g_sprint.last_result == SPRINT_FAULTED);
}
static void offline_sequence(void) {
    unsigned i;
    uint32_t runs;
    feedback_divisor_left = feedback_divisor_right = 200u;
    prepare();
    for (i = 0u; i < 3u; ++i) {
        trigger(); ticks(3000u); stopped(); wait_ready();
        CHECK(g_sprint.last_result == SPRINT_ENCODER_PASS);
        /* 真正Core滴答读取KEY并驱动绿灯；不通过Watch写任何确认命令。 */
        CHECK((GPIOB->ODR & GPIO_Pin_2) != 0u);
        ticks(300u); CHECK((GPIOB->ODR & GPIO_Pin_2) != 0u);
        ticks(300u); CHECK((GPIOB->ODR & GPIO_Pin_2) == 0u);
        pressed = 1u; ticks(250u); pressed = 0u; ticks(31u); stopped();
        CHECK(g_sprint.accepted_runs == i + 1u && g_sprint.review_error == 0u);
    }
    CHECK(g_sprint.best_rpm == 60.0f && g_speed_config.target_rpm == 80.0f);
    wait_ready(); runs = g_speed_match.runs;
    pressed = 1u; ticks(3000u); CHECK(g_speed_match.state == SPEED_ARMED);
    pressed = 0u; ticks(31u); stopped();
    CHECK(g_speed_match.runs == runs && g_speed_config.target_rpm == 60.0f);
    CHECK(g_sprint_config.search_enabled == 0u);
    wait_ready();
    CHECK((GPIOB->ODR & GPIO_Pin_2) != 0u);
    ticks(300u); CHECK((GPIOB->ODR & GPIO_Pin_2) != 0u);
    ticks(300u); CHECK((GPIOB->ODR & GPIO_Pin_2) != 0u); /* 保持档状态3闪。 */
}
int main(void) {
    void (*cases[])(void) = {sequence, full_pwm_and_bounds, distance_stop, read_failure, moe_failure, offline_sequence};
    unsigned i;
    for (i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        memset(&model_gpio_a, 0, sizeof(model_gpio_a)); memset(&model_gpio_b, 0, sizeof(model_gpio_b));
        memset(&model_gpio_c, 0, sizeof(model_gpio_c)); memset(&model_gpio_e, 0, sizeof(model_gpio_e));
        memset(&model_tim1, 0, sizeof(model_tim1)); memset(&model_tim3, 0, sizeof(model_tim3));
        memset(&model_tim4, 0, sizeof(model_tim4)); memset(&model_rcc, 0, sizeof(model_rcc));
        g_speed_ms = g_speed_fault = g_speed_watchdog_started = g_speed_watchdog_stage = 0u;
        gpio_ready = timer_ready = running = startup_timer_clocked = 0u;
        last_left_duty = last_right_duty = 0u; last_sample_at = 0u; ready = 0u;
        pressed = disturb_enable = disturb_stop = 0u; enable_api_calls = 0u; startup_counter = 0u;
        g_speed_config.target_rpm = 60.0f; g_speed_config.pi.kp = 2.0f;
        g_speed_config.pi.ki = 4.0f; g_speed_config.pi.feedforward = 300.0f; g_speed_config.run_ms = 3000u;
        g_sprint_config.distance_limit_mm = 3000u; g_sprint_config.wheel_diameter_mm = 67.5f;
        g_sprint_config.search_enabled = 1u;
        feedback_divisor_left = 400u; feedback_divisor_right = 300u;
        scenario = cases[i]; if (setjmp(completed) == 0) (void)bench_application_main();
    }
    printf("SpeedSprint full integration: 6 scenarios %u checks PASS (model only)\n", checks);
    return 0;
}
