/*
 * C-02B-R1启动故障的电脑复现：直接编译真实main.c调用链，SPL边界只作硬件模型。
 * 模型依据现场PVU不清与ST顺序：未启动IWDG时更新不完成。
 * 保护预算只负责让旧无限等待可由测试自动判失败，不证明实板时序已通过。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#define main bench_application_main
#include "../../Core/Src/motor_bench_main.c"
#undef main

test_scb_t test_scb;
static jmp_buf exit_point;
typedef enum {
    MODEL_NORMAL, MODEL_LSI_STUCK, MODEL_PVU_STUCK, MODEL_RVU_STUCK,
    MODEL_BOTH_STUCK, MODEL_TIMER_STUCK, MODEL_TIMER_STOPS, MODEL_BAD_CLOCK
} model_mode_t;
static model_mode_t mode;
static unsigned watchdog_enabled, polls, reloads, systick_started, output_mask;
static unsigned timer_running, timer_reads, lsi_polls, config_writes, order_errors, stop_calls;
static unsigned nonzero_output_calls, timer_configured, checks;
static uint32_t counter;
static uint32_t expected_startup_fault;
static uint8_t pressed;
#define CHECK(e) do { ++checks; if (!(e)) { fprintf(stderr, "FAIL %s line %d\n", #e, __LINE__); exit(1); } } while (0)

void RCC_HSICmd(FunctionalState s) { (void)s; }
FlagStatus RCC_GetFlagStatus(uint32_t f) {
    if (f == RCC_FLAG_LSIRDY) {
        if (++lsi_polls > 2u * STARTUP_POLL_LIMIT) longjmp(exit_point, 2);
        if (mode == MODEL_LSI_STUCK) return RESET;
    }
    return SET;
}
void RCC_SYSCLKConfig(uint32_t s) { (void)s; }
uint8_t RCC_GetSYSCLKSource(void) { return 0u; }
void RCC_DeInit(void) { }
void NVIC_SetVectorTable(uint32_t t, uint32_t o) { (void)t; (void)o; }
void RCC_GetClocksFreq(RCC_ClocksTypeDef *c) {
    c->SYSCLK_Frequency = c->HCLK_Frequency = c->PCLK1_Frequency = c->PCLK2_Frequency = 16000000u;
    if (mode == MODEL_BAD_CLOCK) c->HCLK_Frequency = c->PCLK1_Frequency = 8000000u;
}
void RCC_AHB1PeriphClockCmd(uint32_t c, FunctionalState s) { (void)c; (void)s; }
void GPIO_StructInit(GPIO_InitTypeDef *g) { memset(g, 0, sizeof(*g)); }
void GPIO_Init(void *p, GPIO_InitTypeDef *g) { (void)p; (void)g; }
void GPIO_ResetBits(void *p, uint16_t n) { (void)p; (void)n; }
uint8_t GPIO_ReadInputDataBit(void *p, uint16_t n) { (void)p; (void)n; return pressed; }
void GPIO_WriteBit(void *p, uint16_t n, BitAction b) { (void)p; (void)n; (void)b; }
void RCC_LSICmd(FunctionalState s) { (void)s; }
void IWDG_WriteAccessCmd(uint16_t k) {
    CHECK(k == 0x5555u);
    if (watchdog_enabled == 0u) ++order_errors;
}
void IWDG_SetPrescaler(uint8_t p) { CHECK(p == IWDG_Prescaler_32); ++config_writes; }
void IWDG_SetReload(uint16_t r) { CHECK(r == 249u); ++config_writes; }
FlagStatus IWDG_GetFlagStatus(uint16_t f) {
    ++polls;
    if (polls > 2u * STARTUP_POLL_LIMIT + 2000u) longjmp(exit_point, 2);
    /* 旧版在Enable前的等待保持SET，回归测试因此能捕获原始阻塞。 */
    if (watchdog_enabled == 0u) {
        if (polls > 1000u) longjmp(exit_point, 2);
        return SET;
    }
    if (mode == MODEL_BOTH_STUCK || mode == MODEL_TIMER_STOPS) return SET;
    if (mode == MODEL_PVU_STUCK && f == IWDG_FLAG_PVU) return SET;
    if (mode == MODEL_RVU_STUCK && f == IWDG_FLAG_RVU) return SET;
    return polls < 5u ? SET : RESET; /* 正常更新也异步完成，不能跳过状态检查。 */
}
void IWDG_ReloadCounter(void) {
    if (watchdog_enabled == 0u) ++order_errors;
    ++reloads;
}
void IWDG_Enable(void) { watchdog_enabled = 1u; }
uint32_t SysTick_Config(uint32_t t) {
    (void)t;
    CHECK(g_motor_bench_ms == 0u); /* 本次初始化超时必须在滴答仍为0时退出。 */
    CHECK(g_motor_bench_fault == expected_startup_fault && output_mask == 0u);
    systick_started = 1u;
    return 0u;
}
void NVIC_SetPriority(int i, uint32_t p) { (void)i; (void)p; }
void __disable_irq(void) { }
void __WFI(void) {
    unsigned i;
    for (i = 0u; i < 1100u; ++i) SysTick_Handler();
    if (g_motor_bench_fault != 0u) {
        /* 初始化失败后尝试完整长按/松开，验证实际main/SysTick安全分支不放行。 */
        pressed = 1u;
        for (i = 0u; i < 2100u; ++i) SysTick_Handler();
        pressed = 0u;
        for (i = 0u; i < 40u; ++i) SysTick_Handler();
    }
    longjmp(exit_point, 1);
}
int motor_bench_pwm_init(void) { output_mask = 0u; return mode == MODEL_BAD_CLOCK ? 0 : 1; }
void motor_bench_pwm_stop(void) { output_mask = 0u; ++stop_calls; }
int motor_bench_pwm_apply(uint8_t m) { output_mask = m; if (m != 0u) ++nonzero_output_calls; return 1; }
void motor_bench_pwm_diag_context(uint32_t ms, uint32_t state, uint32_t fault,
                                  motor_bench_stop_reason_t reason) {
    (void)ms; (void)state; (void)fault; (void)reason;
}

void RCC_APB1PeriphClockCmd(uint32_t c, FunctionalState s) { CHECK(c == RCC_APB1Periph_TIM5 && s == ENABLE); }
void TIM_DeInit(void *t) { CHECK(t == TIM5); }
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef *t) { memset(t, 0, sizeof(*t)); }
void TIM_TimeBaseInit(void *t, TIM_TimeBaseInitTypeDef *b) {
    CHECK(t == TIM5 && b->TIM_Prescaler == 15u && b->TIM_Period == 0xffffffffu);
    ++timer_configured;
}
void TIM_GenerateEvent(void *t, uint16_t e) { CHECK(t == TIM5 && e == TIM_EventSource_Update); }
void TIM_Cmd(void *t, FunctionalState s) { CHECK(t == TIM5); timer_running = s == ENABLE ? 1u : 0u; }
uint32_t TIM_GetCounter(void *t) {
    (void)t;
    ++timer_reads;
    if (timer_running != 0u && mode != MODEL_TIMER_STUCK &&
        !(mode == MODEL_TIMER_STOPS && timer_reads > 2u)) counter += 25u;
    return counter;
}

static void run_case(model_mode_t scenario, uint32_t initial_counter, uint32_t expected_fault) {
    mode = scenario;
    expected_startup_fault = expected_fault;
    watchdog_enabled = polls = reloads = systick_started = output_mask = 0u;
    timer_running = timer_reads = lsi_polls = config_writes = order_errors = stop_calls = 0u;
    nonzero_output_calls = timer_configured = 0u;
    pressed = 0u;
    counter = initial_counter;
    g_motor_bench_ms = g_motor_bench_fault = g_motor_bench_revision = 0u;
    g_motor_bench_watchdog_started = g_motor_bench_watchdog_stage = 0u;
    startup_timer_clocked = 0u; /* 模拟每次复位的BSS初始化。 */
    {
    int result = setjmp(exit_point);
    if (result == 0) { SystemInit(); (void)bench_application_main(); }
    if (result == 2) {
        fprintf(stderr, "FAIL startup wait did not exit: mode=%d, ms=%lu, SysTick=%u\n",
                (int)mode, (unsigned long)g_motor_bench_ms, systick_started);
        exit(1);
    }
    }
    CHECK(g_motor_bench_fault == expected_fault);
    CHECK(systick_started == 1u && g_motor_bench_ms >= 1100u);
    CHECK(output_mask == 0u && nonzero_output_calls == 0u && order_errors == 0u);
#ifdef MOTOR_CONTINUOUS_A_TARGET
    CHECK(timer_running == 0u && g_motor_bench_revision == 0x020b1002u);
#else
    CHECK(timer_running == 0u && g_motor_bench_revision == 0x020b0004u);
#endif
    if (expected_fault == 0u) {
        CHECK(g_motor_bench.state == MOTOR_BENCH_READY);
        CHECK(g_motor_bench_watchdog_stage == 4u && watchdog_enabled == 1u && config_writes == 2u);
        CHECK(reloads > 1u && timer_configured == 1u);
    } else {
        CHECK(g_motor_bench.state == MOTOR_BENCH_ABORTED && stop_calls > 1u);
        if (scenario == MODEL_LSI_STUCK || scenario == MODEL_TIMER_STUCK || scenario == MODEL_BAD_CLOCK)
            CHECK(watchdog_enabled == 0u && reloads == 0u);
        else CHECK(watchdog_enabled == 1u && reloads > 0u);
    }
}

int main(void) {
    run_case(MODEL_NORMAL, 0u, 0u);
    run_case(MODEL_NORMAL, 0xfffffff0u, 0u);
    run_case(MODEL_LSI_STUCK, 0u, MOTOR_BENCH_FAULT_LSI_TIMEOUT);
    run_case(MODEL_LSI_STUCK, 0xfffffff0u, MOTOR_BENCH_FAULT_LSI_TIMEOUT);
    run_case(MODEL_PVU_STUCK, 0u, MOTOR_BENCH_FAULT_IWDG_TIMEOUT);
    run_case(MODEL_RVU_STUCK, 0u, MOTOR_BENCH_FAULT_IWDG_TIMEOUT);
    run_case(MODEL_BOTH_STUCK, 0xfffffff0u, MOTOR_BENCH_FAULT_IWDG_TIMEOUT);
    run_case(MODEL_TIMER_STUCK, 0u, MOTOR_BENCH_FAULT_STARTUP_TIMER);
    run_case(MODEL_TIMER_STOPS, 0u, MOTOR_BENCH_FAULT_STARTUP_TIMER);
    run_case(MODEL_BAD_CLOCK, 0u, MOTOR_BENCH_FAULT_PWM_CLOCK | MOTOR_BENCH_FAULT_STARTUP_TIMER);
    printf("PASS MotorBench startup: %u checks in 10 hardware-model scenarios (real main/SysTick; no board access)\n", checks);
    return 0;
}
