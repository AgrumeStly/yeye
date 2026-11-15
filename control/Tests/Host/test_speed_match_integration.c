#include "speed_match_integration_harness.h"
static void wait_ready(void) {
    unsigned i;
    for(i=0u;i<3500u && g_speed_match.state!=SPEED_READY;++i) ticks(1u);
    CHECK(g_speed_match.state==SPEED_READY);
}
static void trigger(void) {
    wait_ready(); pressed=1u; ticks(1100u); CHECK(g_speed_match.state==SPEED_ARMED);
    pressed=0u; ticks(31u);
}
static void stopped(void) {
    CHECK((TIM1->BDTR & TIM_BDTR_MOE)==0u);
    CHECK(TIM1->CCR1==0u && TIM1->CCR2==0u && TIM1->CCR3==0u && TIM1->CCR4==0u);
    CHECK((GPIOE->MODER & 0x3ccc0000u)==0x14440000u);
}
static void prepare(void) {
    CHECK(g_speed_revision==0x020f0001u && g_speed_fault==0u && g_speed_watchdog_stage==4u);
    ticks(1100u); stopped(); CHECK(g_speed_match.phase==0u);
    trigger(); CHECK(TIM1->CCR1==8000u && TIM1->CCR4==0u);
    ticks(500u); stopped(); CHECK(g_speed_match.phase==1u);
    trigger(); CHECK(TIM1->CCR1==0u && TIM1->CCR4==8000u);
    ticks(500u); stopped(); CHECK(g_speed_match.phase==2u);
    CHECK(g_speed_match.left_channel==1u && g_speed_match.right_channel==2u);
    CHECK(g_speed_match.left_sign==1 && g_speed_match.right_sign==-1);
}
static void sequence(void) {
    uint32_t begin;
    prepare(); trigger(); begin=g_speed_ms; CHECK(g_speed_match.state==SPEED_RUNNING);
    CHECK(TIM1->CCR1!=0u && TIM1->CCR4!=0u && TIM1->CCR2==0u && TIM1->CCR3==0u);
    ticks(2999u); CHECK(g_speed_match.state==SPEED_RUNNING && g_speed_fault==0u);
    ticks(1u); stopped(); CHECK(g_speed_match.stop_ms-begin==3000u);
    trigger(); CHECK(g_speed_match.state==SPEED_RUNNING && g_speed_match.runs==2u);
    pressed=1u; ticks(1u); stopped(); CHECK(g_speed_match.error==SPEED_ERROR_KEY);
    pressed=0u; ticks(1500u); CHECK(g_speed_match.state==SPEED_FAULT);
}
static void read_failure(void) { prepare(); trigger(); ready=0u; ticks(20u); stopped(); CHECK(g_speed_fault==64u); }
static void moe_failure(void) { prepare(); trigger(); TIM1->BDTR &= ~TIM_BDTR_MOE; ticks(1u); stopped(); CHECK(g_speed_fault==32u); }
int main(void) {
    void (*cases[])(void)={sequence,read_failure,moe_failure}; unsigned i;
    for(i=0u;i<sizeof(cases)/sizeof(cases[0]);++i) {
        memset(&model_gpio_a,0,sizeof(model_gpio_a)); memset(&model_gpio_b,0,sizeof(model_gpio_b));
        memset(&model_gpio_c,0,sizeof(model_gpio_c)); memset(&model_gpio_e,0,sizeof(model_gpio_e));
        memset(&model_tim1,0,sizeof(model_tim1)); memset(&model_tim3,0,sizeof(model_tim3)); memset(&model_tim4,0,sizeof(model_tim4));
        memset(&model_rcc,0,sizeof(model_rcc));
        g_speed_ms=g_speed_fault=g_speed_watchdog_started=g_speed_watchdog_stage=0u;
        gpio_ready=timer_ready=running=startup_timer_clocked=0u; last_left_duty=last_right_duty=0u;
        last_sample_at=0u; ready=0u;
        pressed=disturb_enable=disturb_stop=0u; enable_api_calls=0u; startup_counter=0u;
        g_speed_config.target_rpm=60.0f; g_speed_config.pi.kp=2.0f; g_speed_config.pi.ki=4.0f;
        g_speed_config.pi.feedforward=300.0f; g_speed_config.run_ms=3000u;
        scenario=cases[i]; if(setjmp(completed)==0) (void)bench_application_main();
    }
    printf("SpeedMatch full integration: 3 scenarios %u checks PASS\n",checks);
    return 0;
}
