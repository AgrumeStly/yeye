/* R3集成回归：真实main、SysTick、状态机及PWM源码；只有芯片/SPL边界使用模型。
 * 通过完整KEY动作验证捕获先后、单次计数、停止后保留，再故意扰动寄存器读回值，
 * 确认诊断报告真实模型内容，不能由宏值冒充。此模型不模拟电压、波形或电机。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include "../../Drivers_Custom/Motor/motor_bench_pwm.c"
#define main bench_application_main
#include "../../Core/Src/motor_bench_main.c"
#undef main

model_gpio_t model_gpio_a, model_gpio_b, model_gpio_e;
model_tim_t model_tim1;
model_rcc_t model_rcc;
test_scb_t test_scb;
static jmp_buf completed;
static unsigned checks, enable_api_calls;
static uint32_t startup_counter;
static uint8_t pressed, disturb_enable, disturb_stop;
static void (*scenario)(void);
#define CHECK(e) do { ++checks; if (!(e)) { fprintf(stderr,"FAIL %s line %d\n",#e,__LINE__); exit(1); } } while (0)

void RCC_HSICmd(FunctionalState s) { (void)s; }
FlagStatus RCC_GetFlagStatus(uint32_t f) { (void)f; return SET; }
void RCC_SYSCLKConfig(uint32_t s) { (void)s; }
uint8_t RCC_GetSYSCLKSource(void) { return 0u; }
void RCC_DeInit(void) { }
void NVIC_SetVectorTable(uint32_t t, uint32_t o) { (void)t; (void)o; }
void RCC_GetClocksFreq(RCC_ClocksTypeDef *c) {
    c->SYSCLK_Frequency = c->HCLK_Frequency = c->PCLK1_Frequency = c->PCLK2_Frequency = 16000000u;
}
void RCC_AHB1PeriphClockCmd(uint32_t c, FunctionalState s) { if (s == ENABLE) RCC->AHB1ENR |= c; }
void RCC_APB2PeriphClockCmd(uint32_t c, FunctionalState s) { if (s == ENABLE) RCC->APB2ENR |= c; }
void RCC_APB1PeriphClockCmd(uint32_t c, FunctionalState s) { (void)c; (void)s; }
void GPIO_StructInit(GPIO_InitTypeDef *g) { memset(g,0,sizeof(*g)); }
void GPIO_Init(void *p, GPIO_InitTypeDef *g) {
    model_gpio_t *port = (model_gpio_t *)p;
    unsigned pin;
    for (pin=0u; pin<16u; ++pin) if ((g->GPIO_Pin & (1u<<pin)) != 0u) {
        port->MODER = (port->MODER & ~(3u<<(2u*pin))) | (g->GPIO_Mode<<(2u*pin));
        port->PUPDR = (port->PUPDR & ~(3u<<(2u*pin))) | (g->GPIO_PuPd<<(2u*pin));
        port->OTYPER = (port->OTYPER & ~(1u<<pin)) | (g->GPIO_OType<<pin);
    }
}
void GPIO_PinAFConfig(void *p, uint16_t pin, uint8_t af) {
    model_gpio_t *g = (model_gpio_t *)p;
    uint32_t shift = (pin & 7u)*4u;
    g->AFR[pin>>3] = (g->AFR[pin>>3] & ~(15u<<shift)) | ((uint32_t)af<<shift);
}
void GPIO_ResetBits(void *p, uint16_t n) { ((model_gpio_t *)p)->ODR &= ~(uint32_t)n; }
uint8_t GPIO_ReadInputDataBit(void *p, uint16_t n) { (void)p; (void)n; return pressed; }
void GPIO_WriteBit(void *p, uint16_t n, BitAction b) { (void)p; (void)n; (void)b; }
void RCC_LSICmd(FunctionalState s) { (void)s; }
void IWDG_WriteAccessCmd(uint16_t k) { (void)k; }
void IWDG_SetPrescaler(uint8_t p) { (void)p; }
void IWDG_SetReload(uint16_t r) { (void)r; }
FlagStatus IWDG_GetFlagStatus(uint16_t f) { (void)f; return RESET; }
void IWDG_ReloadCounter(void) { }
void IWDG_Enable(void) { }
uint32_t SysTick_Config(uint32_t t) { (void)t; return 0u; }
void NVIC_SetPriority(int i, uint32_t p) { (void)i; (void)p; }
void __disable_irq(void) { }
void __WFI(void) { scenario(); longjmp(completed,1); }
void TIM_DeInit(void *t) { if (t == TIM1) memset(&model_tim1,0,sizeof(model_tim1)); }
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef *t) { memset(t,0,sizeof(*t)); }
void TIM_TimeBaseInit(void *t, TIM_TimeBaseInitTypeDef *b) {
    if (t == TIM1) { TIM1->PSC=b->TIM_Prescaler; TIM1->ARR=b->TIM_Period; }
}
void TIM_GenerateEvent(void *t, uint16_t e) { (void)t; (void)e; }
void TIM_Cmd(void *t, FunctionalState s) { if (t == TIM1 && s == ENABLE) TIM1->CR1 |= 1u; }
uint32_t TIM_GetCounter(void *t) { (void)t; startup_counter+=25u; return startup_counter; }
void TIM_OCStructInit(TIM_OCInitTypeDef *o) { memset(o,0,sizeof(*o)); }
static void oc_init(unsigned channel, TIM_OCInitTypeDef *o) {
    uint32_t shift=(channel-1u)*4u;
    TIM1->CCER |= o->TIM_OutputState<<shift;
    if (channel==1u) TIM1->CCMR1 |= o->TIM_OCMode;
    if (channel==2u) TIM1->CCMR1 |= o->TIM_OCMode<<8;
    if (channel==3u) TIM1->CCMR2 |= o->TIM_OCMode;
    if (channel==4u) TIM1->CCMR2 |= o->TIM_OCMode<<8;
}
void TIM_OC1Init(void *t,TIM_OCInitTypeDef *o) { (void)t; oc_init(1u,o); }
void TIM_OC2Init(void *t,TIM_OCInitTypeDef *o) { (void)t; oc_init(2u,o); }
void TIM_OC3Init(void *t,TIM_OCInitTypeDef *o) { (void)t; oc_init(3u,o); }
void TIM_OC4Init(void *t,TIM_OCInitTypeDef *o) { (void)t; oc_init(4u,o); }
void TIM_OC1PreloadConfig(void *t,uint16_t s) { (void)t; (void)s; TIM1->CCMR1|=8u; }
void TIM_OC2PreloadConfig(void *t,uint16_t s) { (void)t; (void)s; TIM1->CCMR1|=8u<<8; }
void TIM_OC3PreloadConfig(void *t,uint16_t s) { (void)t; (void)s; TIM1->CCMR2|=8u; }
void TIM_OC4PreloadConfig(void *t,uint16_t s) { (void)t; (void)s; TIM1->CCMR2|=8u<<8; }
void TIM_ARRPreloadConfig(void *t,FunctionalState s) { (void)t; (void)s; TIM1->CR1|=128u; }
void TIM_BDTRStructInit(TIM_BDTRInitTypeDef *p) { memset(p,0,sizeof(*p)); }
void TIM_BDTRConfig(void *t,TIM_BDTRInitTypeDef *p) { (void)t; TIM1->BDTR=p->TIM_OSSIState|p->TIM_OSSRState; }
void TIM_CtrlPWMOutputs(void *t,FunctionalState s) {
    (void)t;
    if (s == ENABLE) {
        ++enable_api_calls; TIM1->BDTR|=TIM_BDTR_MOE;
        if (disturb_enable != 0u) {
            /* 模拟寄存器配置被外部条件扰动，诊断必须原样报告，不能回填期望240/799。 */
            TIM1->BDTR &= ~TIM_BDTR_MOE; TIM1->CCR1=137u; TIM1->PSC=7u; TIM1->ARR=911u;
            TIM1->CCER=0x1000u; GPIOE->AFR[1]=0x43215678u; GPIOE->IDR=0x6000u;
        }
    } else if (disturb_stop == 0u) TIM1->BDTR &= ~TIM_BDTR_MOE;
}
void TIM_SetCompare1(void *t,uint32_t c) { (void)t; TIM1->CCR1=c; }
void TIM_SetCompare2(void *t,uint32_t c) { (void)t; TIM1->CCR2=c; }
void TIM_SetCompare3(void *t,uint32_t c) { (void)t; TIM1->CCR3=c; }
void TIM_SetCompare4(void *t,uint32_t c) { (void)t; TIM1->CCR4=c; }

static void ticks(unsigned n) { while (n-- != 0u) SysTick_Handler(); }
static void trigger_a(void) {
    ticks(1100u); CHECK(g_motor_bench.state==MOTOR_BENCH_READY);
    CHECK(g_motor_bench_pwm_diag.active.valid==0u && g_motor_bench_pwm_diag.stopped.valid==0u);
    pressed=1u; ticks(1100u); CHECK(g_motor_bench.state==MOTOR_BENCH_ARMED);
    pressed=0u; ticks(31u); CHECK(g_motor_bench.state==MOTOR_BENCH_RUNNING);
    CHECK(g_motor_bench_pwm_diag.request_count==1u && g_motor_bench_pwm_diag.enable_calls==1u);
    CHECK(enable_api_calls==1u && g_motor_bench_pwm_diag.active.valid==1u);
    CHECK(g_motor_bench_pwm_diag.stopped.valid==0u && g_motor_bench_pwm_diag.start_ms==g_motor_bench.run_since);
}
static void stopped_ok(motor_bench_stop_reason_t reason) {
    CHECK(g_motor_bench_pwm_diag.active.valid==1u && g_motor_bench_pwm_diag.stopped.valid==1u);
    CHECK(g_motor_bench_pwm_diag.stop_count==1u && g_motor_bench_pwm_diag.stop_reason==(uint32_t)reason);
    CHECK(g_motor_bench_pwm_diag.active.run_id==g_motor_bench_pwm_diag.stopped.run_id);
    CHECK((g_motor_bench_pwm_diag.stopped.tim_bdtr&TIM_BDTR_MOE)==0u);
    CHECK(g_motor_bench_pwm_diag.stopped.tim_ccr1==0u && g_motor_bench_pwm_diag.stopped.tim_ccr2==0u);
    CHECK(g_motor_bench_pwm_diag.stopped.tim_ccr3==0u && g_motor_bench_pwm_diag.stopped.tim_ccr4==0u);
    CHECK((g_motor_bench_pwm_diag.stopped.gpio_moder&0x3ccc0000u)==0x14440000u);
    CHECK((g_motor_bench_pwm_diag.stopped.gpio_odr&0x6a00u)==0u);
}
#ifndef MOTOR_CONTINUOUS_A_TARGET
/* 人工输入贯穿真实SysTick，核对A→B→AB各阶段只运行500ms且不自行续跑。 */
static void manual_sequence(void) {
    unsigned stage;
    uint32_t expected_mask;
    ticks(1100u);
    for (stage=0u; stage<3u; ++stage) {
        CHECK(g_motor_bench.state==MOTOR_BENCH_READY && g_motor_bench.step==stage);
        ticks(2500u);
        CHECK(g_motor_bench.output_mask==0u && (TIM1->BDTR&TIM_BDTR_MOE)==0u);
        pressed=1u; ticks(1100u);
        CHECK(g_motor_bench.state==MOTOR_BENCH_ARMED && g_motor_bench.output_mask==0u);
        pressed=0u; ticks(31u);
        expected_mask=stage==0u ? 1u : (stage==1u ? 2u : 3u);
        CHECK(g_motor_bench.state==MOTOR_BENCH_RUNNING && g_motor_bench.output_mask==expected_mask);
        CHECK(TIM1->CCR1==((expected_mask&1u)!=0u ? 8000u : 0u));
        CHECK(TIM1->CCR3==((expected_mask&2u)!=0u ? 8000u : 0u));
        CHECK(TIM1->CCR2==0u && TIM1->CCR4==0u);
        CHECK((GPIOE->MODER&0x30c00000u)==0x10400000u); /* PE11/PE14始终GPIO。 */
        ticks(499u); CHECK(g_motor_bench.state==MOTOR_BENCH_RUNNING);
        ticks(1u);
        CHECK(g_motor_bench_pwm_diag.elapsed_ms==500u && g_motor_bench.output_mask==0u);
        CHECK((GPIOE->MODER&0x3ccc0000u)==0x14440000u && (GPIOE->ODR&0x6a00u)==0u);
        CHECK((TIM1->BDTR&TIM_BDTR_MOE)==0u && g_motor_bench_pwm_diag.stop_reason==MOTOR_BENCH_STOP_TIMEOUT);
        ticks(1100u);
    }
    CHECK(g_motor_bench.state==MOTOR_BENCH_COMPLETE);
    pressed=1u; ticks(1200u); pressed=0u; ticks(1100u);
    CHECK(g_motor_bench.state==MOTOR_BENCH_COMPLETE && g_motor_bench_pwm_diag.enable_calls==3u);
}
static void normal_timeout(void) {
    motor_bench_pwm_snapshot_t kept;
    trigger_a();
    CHECK(g_motor_bench_pwm_diag.enable_count==1u && g_motor_bench_pwm_diag.active.mask==1u);
    CHECK(g_motor_bench_pwm_diag.active.tim_ccr1==8000u && g_motor_bench_pwm_diag.active.tim_ccr3==0u);
    CHECK(g_motor_bench_pwm_diag.active.tim_arr==15999u && g_motor_bench_pwm_diag.active.tim_psc==0u);
    CHECK((g_motor_bench_pwm_diag.active.gpio_moder&0x3ccc0000u)==0x14480000u);
    CHECK((g_motor_bench_pwm_diag.active.tim_ccer&0x1111u)==0x0101u);
    memcpy(&kept,(const void *)&g_motor_bench_pwm_diag.active,sizeof(kept));
    TIM1->CNT=777u; GPIOE->IDR=0x6a00u; ticks(499u);
    CHECK(g_motor_bench.state==MOTOR_BENCH_RUNNING); ticks(1u);
    stopped_ok(MOTOR_BENCH_STOP_TIMEOUT);
    CHECK(g_motor_bench_pwm_diag.elapsed_ms==500u && g_motor_bench_pwm_diag.stop_ms-g_motor_bench_pwm_diag.start_ms==500u);
    CHECK(memcmp(&kept,(const void *)&g_motor_bench_pwm_diag.active,sizeof(kept))==0);
    ticks(1500u);
    CHECK(g_motor_bench.state==MOTOR_BENCH_READY && g_motor_bench.step==1u);
    CHECK(g_motor_bench_pwm_diag.request_count==1u && g_motor_bench_pwm_diag.stop_count==1u);
    CHECK(memcmp(&kept,(const void *)&g_motor_bench_pwm_diag.active,sizeof(kept))==0);
}
#endif
static void key_stop(void) {
    trigger_a(); pressed=1u; ticks(1u); stopped_ok(MOTOR_BENCH_STOP_KEY);
    CHECK(g_motor_bench_pwm_diag.elapsed_ms==1u && g_motor_bench.state==MOTOR_BENCH_ABORTED);
    pressed=0u; ticks(2000u); CHECK(g_motor_bench_pwm_diag.stop_count==1u);
}
static void fault_stop(void) {
    trigger_a(); g_motor_bench_fault=8u; ticks(1u); stopped_ok(MOTOR_BENCH_STOP_FAULT);
    CHECK(g_motor_bench_pwm_diag.stopped.fault==8u);
    ticks(100u); CHECK(g_motor_bench_pwm_diag.stop_count==1u && g_motor_bench_pwm_diag.elapsed_ms==1u);
}
#ifndef MOTOR_CONTINUOUS_A_TARGET
static void disturbed_readback(void) {
    /* MOE被硬件模型拒绝时，新入口应同一滴答锁定并撤去GPIO，而不是继续RUNNING。 */
    ticks(1100u); pressed=1u; ticks(1100u); disturb_enable=1u;
    pressed=0u; ticks(31u);
    CHECK(g_motor_bench.state==MOTOR_BENCH_ABORTED && g_motor_bench_fault==32u);
    CHECK(g_motor_bench_pwm_diag.enable_count==0u && g_motor_bench_pwm_diag.enable_calls==1u);
    CHECK((g_motor_bench_pwm_diag.active.tim_bdtr&TIM_BDTR_MOE)==0u);
    CHECK(g_motor_bench_pwm_diag.active.tim_ccr1==137u && g_motor_bench_pwm_diag.active.tim_arr==911u);
    CHECK(g_motor_bench_pwm_diag.active.tim_psc==7u && g_motor_bench_pwm_diag.active.tim_ccer==0x1000u);
    CHECK(g_motor_bench_pwm_diag.active.gpio_afrh==0x43215678u && g_motor_bench_pwm_diag.active.gpio_idr==0x6000u);
    ticks(500u); stopped_ok(MOTOR_BENCH_STOP_FAULT);
    CHECK(g_motor_bench.output_mask==0u && g_motor_bench_pwm_diag.enable_calls==1u);
    CHECK(g_motor_bench_pwm_diag.active.tim_ccr1==137u && g_motor_bench_pwm_diag.stopped.tim_psc==7u);
}
static void failed_stop_readback(void) {
    trigger_a(); disturb_stop=1u; ticks(500u);
    CHECK(g_motor_bench_pwm_diag.stopped.valid==1u && g_motor_bench_pwm_diag.stop_count==1u);
    CHECK((g_motor_bench_pwm_diag.stopped.tim_bdtr&TIM_BDTR_MOE)!=0u);
    CHECK(g_motor_bench_pwm_diag.stopped.tim_ccr1==0u); /* 不把停止标记当MOE已清证明。 */
}
#endif
static void invalid_mask(void) {
    trigger_a(); motor_bench_pwm_apply(9u); stopped_ok(MOTOR_BENCH_STOP_INVALID_MASK);
    CHECK(g_motor_bench_pwm_diag.request_count==2u && g_motor_bench_pwm_diag.enable_calls==1u);
    motor_bench_pwm_apply(9u); CHECK(g_motor_bench_pwm_diag.request_count==2u);
}
static void change_and_wrap(void) {
    uint32_t pulse;
#ifdef MOTOR_CONTINUOUS_A_TARGET
    pulse=240u;
#else
    pulse=8000u;
#endif
    trigger_a(); motor_bench_pwm_apply(2u);
    CHECK(g_motor_bench_pwm_diag.enable_calls==2u && g_motor_bench_pwm_diag.stopped.valid==0u);
    CHECK(g_motor_bench_pwm_diag.active.mask==2u && g_motor_bench_pwm_diag.active.tim_ccr3==pulse);
    CHECK((g_motor_bench_pwm_diag.active.gpio_moder&0x3ccc0000u)==0x18440000u);
    motor_bench_pwm_stop();
    CHECK(g_motor_bench_pwm_diag.active.run_id==2u && g_motor_bench_pwm_diag.stopped.run_id==2u);
    motor_bench_pwm_diag_context(0xffffffffu-200u,4u,0u,MOTOR_BENCH_STOP_NONE);
    motor_bench_pwm_apply(3u);
    CHECK(g_motor_bench_pwm_diag.active.tim_ccr1==pulse && g_motor_bench_pwm_diag.active.tim_ccr3==pulse);
    CHECK((g_motor_bench_pwm_diag.active.gpio_moder&0x3ccc0000u)==0x18480000u);
    motor_bench_pwm_diag_context(299u,0u,0u,MOTOR_BENCH_STOP_TIMEOUT); motor_bench_pwm_stop();
    CHECK(g_motor_bench_pwm_diag.elapsed_ms==500u && g_motor_bench_pwm_diag.active.run_id==3u);
}
static void no_output(void) {
    ticks(4000u); CHECK(g_motor_bench_pwm_diag.request_count==0u && g_motor_bench_pwm_diag.enable_calls==0u);
    CHECK(g_motor_bench_pwm_diag.active.valid==0u && g_motor_bench_pwm_diag.stopped.valid==0u);
    timer_ready=0u; motor_bench_pwm_apply(1u);
    CHECK(g_motor_bench_pwm_diag.request_count==1u && g_motor_bench_pwm_diag.enable_calls==0u);
    CHECK(g_motor_bench_pwm_diag.active.valid==0u && g_motor_bench_pwm_diag.stopped.valid==0u);
}
#ifdef MOTOR_CONTINUOUS_A_TARGET
/* 真实main/SysTick持续运行120秒，越过原500ms边界；不靠反复发启用或修改时间续跑。
 * 测试中的快速毫秒推进不是实物空转，随后跨毫秒回绕仍应立即响应KEY并锁定。
 */
static void continuous_run(void) {
    trigger_a(); ticks(120000u);
    CHECK(g_motor_bench.state==MOTOR_BENCH_RUNNING && g_motor_bench.output_mask==1u);
    CHECK(g_motor_bench.step==0u && TIM1->CCR1==240u && TIM1->CCR2==0u);
    CHECK(TIM1->CCR3==0u && TIM1->CCR4==0u && (TIM1->BDTR&TIM_BDTR_MOE)!=0u);
    CHECK(g_motor_bench_pwm_diag.request_count==1u && g_motor_bench_pwm_diag.enable_calls==1u);
    CHECK(g_motor_bench_pwm_diag.stop_count==0u && g_motor_bench_pwm_diag.stopped.valid==0u);
    g_motor_bench_ms=0xfffffff0u; ticks(40u);
    CHECK(g_motor_bench.state==MOTOR_BENCH_RUNNING && g_motor_bench.output_mask==1u);
    pressed=1u; ticks(1u); stopped_ok(MOTOR_BENCH_STOP_KEY);
    pressed=0u; ticks(2000u); pressed=1u; ticks(1500u); pressed=0u; ticks(40u);
    CHECK(g_motor_bench.state==MOTOR_BENCH_ABORTED && g_motor_bench.output_mask==0u);
    CHECK(g_motor_bench_pwm_diag.enable_calls==1u);
}
static void continuous_bad_step(void) {
    trigger_a(); g_motor_bench.step=1u; ticks(1u);
    stopped_ok(MOTOR_BENCH_STOP_LOGIC);
    CHECK(g_motor_bench.state==MOTOR_BENCH_ABORTED && TIM1->CCR3==0u);
}
#endif
static void run(void (*test)(void)) {
    memset(&model_gpio_a,0,sizeof(model_gpio_a)); memset(&model_gpio_b,0,sizeof(model_gpio_b));
    memset(&model_gpio_e,0,sizeof(model_gpio_e)); memset(&model_tim1,0,sizeof(model_tim1));
    memset(&model_rcc,0,sizeof(model_rcc)); memset((void *)&g_motor_bench_pwm_diag,0,sizeof(g_motor_bench_pwm_diag));
    gpio_ready=timer_ready=active_mask=requested_mask=startup_timer_clocked=0u;
    g_motor_bench_ms=g_motor_bench_fault=g_motor_bench_revision=0u;
    g_motor_bench_watchdog_started=g_motor_bench_watchdog_stage=0u;
    event_ms=event_state=event_fault=0u; event_reason=MOTOR_BENCH_STOP_NONE;
    pressed=disturb_enable=disturb_stop=0u; startup_counter=0u; enable_api_calls=0u; scenario=test;
    if (setjmp(completed)==0) { SystemInit(); (void)bench_application_main(); }
#ifdef MOTOR_CONTINUOUS_A_TARGET
    CHECK(g_motor_bench_revision==0x020b1002u);
#else
    CHECK(g_motor_bench_revision==0x020b0004u);
#endif
}
int main(void) {
#ifdef MOTOR_CONTINUOUS_A_TARGET
    run(continuous_run); run(continuous_bad_step); run(key_stop); run(fault_stop);
    run(invalid_mask); run(change_and_wrap); run(no_output);
    printf("PASS continuous A: %u checks in 7 real-main/PWM model scenarios (120s, wrap, stop, fault, lockout; no board)\n",checks);
#else
    run(normal_timeout); run(key_stop); run(fault_stop); run(disturbed_readback);
    run(failed_stop_readback); run(invalid_mask); run(change_and_wrap); run(no_output); run(manual_sequence);
    printf("PASS rewritten PWM: %u checks in 9 real-main/PWM model scenarios (A/B/AB, timeout, stop, fault, wrap; no board access)\n",checks);
#endif
    return 0;
}
