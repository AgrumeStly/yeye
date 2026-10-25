/* MotorDirect真实入口／SysTick／GPIO适配器集成测试。
 * 不模拟电机转动或电压；模型只记录真实应用对SPL边界的操作和可扰动寄存器。
 * 重点验证满导通只能人工单次500ms、停止锁定、不使用TIM1／AF及不输出B。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#ifdef MOTOR_DIRECT_B_TARGET
#define TEST_MASK 2u
#define TEST_PIN GPIO_Pin_13
#define TEST_REVISION 0x020b2002u
#define OTHER_MASK 1u
#else
#define TEST_MASK 1u
#define TEST_PIN GPIO_Pin_9
#define TEST_REVISION 0x020b2001u
#define OTHER_MASK 2u
#endif
#include "../../Drivers_Custom/Motor/motor_direct_gpio.c"
#define main direct_application_main
#include "../../Core/Src/motor_direct_main.c"
#undef main

model_gpio_t model_gpio_a, model_gpio_b, model_gpio_e;
model_tim_t model_tim1;
model_rcc_t model_rcc;
test_scb_t test_scb;
static jmp_buf completed;
static unsigned checks, set_calls, reloads, watchdog_enabled;
static uint32_t startup_counter;
static uint8_t pressed, disturb_set, bad_clock;
static void (*scenario)(void);
#define CHECK(e) do { ++checks; if (!(e)) { fprintf(stderr,"FAIL %s line %d\n",#e,__LINE__); exit(1); } } while (0)

void RCC_HSICmd(FunctionalState s) { (void)s; }
FlagStatus RCC_GetFlagStatus(uint32_t f) { (void)f; return SET; }
void RCC_SYSCLKConfig(uint32_t s) { (void)s; }
uint8_t RCC_GetSYSCLKSource(void) { return 0u; }
void RCC_DeInit(void) { }
void NVIC_SetVectorTable(uint32_t t,uint32_t o) { (void)t; (void)o; }
void RCC_GetClocksFreq(RCC_ClocksTypeDef *c) {
    c->SYSCLK_Frequency=c->HCLK_Frequency=c->PCLK1_Frequency=c->PCLK2_Frequency=16000000u;
    if (bad_clock!=0u) c->HCLK_Frequency=8000000u;
}
void RCC_AHB1PeriphClockCmd(uint32_t c,FunctionalState s) { if(s==ENABLE) RCC->AHB1ENR|=c; }
void RCC_APB2PeriphClockCmd(uint32_t c,FunctionalState s) { (void)c; (void)s; CHECK(0); }
void GPIO_StructInit(GPIO_InitTypeDef *g) { memset(g,0,sizeof(*g)); }
void GPIO_Init(void *p,GPIO_InitTypeDef *g) {
    model_gpio_t *port=(model_gpio_t *)p;
    unsigned pin;
    if (p==GPIOE) CHECK(g->GPIO_Mode==GPIO_Mode_OUT && g->GPIO_Pin==0x6a00u);
    for(pin=0u;pin<16u;++pin) if((g->GPIO_Pin&(1u<<pin))!=0u) {
        port->MODER=(port->MODER&~(3u<<(pin*2u)))|(g->GPIO_Mode<<(pin*2u));
        port->PUPDR=(port->PUPDR&~(3u<<(pin*2u)))|(g->GPIO_PuPd<<(pin*2u));
        port->OTYPER=(port->OTYPER&~(1u<<pin))|(g->GPIO_OType<<pin);
    }
}
void GPIO_ResetBits(void *p,uint16_t n) { ((model_gpio_t *)p)->ODR &= ~(uint32_t)n; }
void GPIO_SetBits(void *p,uint16_t n) {
    CHECK(p==GPIOE && n==TEST_PIN); /* 非当前选定桥IN1的任何置高请求直接失败。 */
    ++set_calls;
    if(disturb_set==0u) ((model_gpio_t *)p)->ODR |= n;
}
void GPIO_PinAFConfig(void *p,uint16_t n,uint8_t af) { (void)p;(void)n;(void)af;CHECK(0); }
uint8_t GPIO_ReadInputDataBit(void *p,uint16_t n) { (void)p;(void)n;return pressed; }
void GPIO_WriteBit(void *p,uint16_t n,BitAction b) { (void)p;(void)n;(void)b; }
void RCC_LSICmd(FunctionalState s) { (void)s; }
void IWDG_WriteAccessCmd(uint16_t k) { CHECK(k==0x5555u && watchdog_enabled==1u); }
void IWDG_SetPrescaler(uint8_t p) { CHECK(p==IWDG_Prescaler_32); }
void IWDG_SetReload(uint16_t r) { CHECK(r==249u); }
FlagStatus IWDG_GetFlagStatus(uint16_t f) { (void)f; return RESET; }
void IWDG_ReloadCounter(void) { CHECK(watchdog_enabled==1u);++reloads; }
void IWDG_Enable(void) { watchdog_enabled=1u; }
uint32_t SysTick_Config(uint32_t t) { CHECK(t==16000u && (GPIOE->ODR&0x6a00u)==0u);return 0u; }
void NVIC_SetPriority(int i,uint32_t p) { (void)i;(void)p; }
void __disable_irq(void) { }
void __WFI(void) { scenario();longjmp(completed,1); }
void RCC_APB1PeriphClockCmd(uint32_t c,FunctionalState s) { CHECK(c==RCC_APB1Periph_TIM5 && s==ENABLE); }
void TIM_DeInit(void *t) { CHECK(t==TIM5); }
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef *t) { memset(t,0,sizeof(*t)); }
void TIM_TimeBaseInit(void *t,TIM_TimeBaseInitTypeDef *b) {
    CHECK(t==TIM5 && b->TIM_Prescaler==15u && b->TIM_Period==0xffffffffu);
}
void TIM_GenerateEvent(void *t,uint16_t e) { CHECK(t==TIM5 && e==TIM_EventSource_Update); }
void TIM_Cmd(void *t,FunctionalState s) { (void)s;CHECK(t==TIM5); }
uint32_t TIM_GetCounter(void *t) { CHECK(t==TIM5);startup_counter+=25u;return startup_counter; }

static void ticks(unsigned n) { while(n--!=0u) SysTick_Handler(); }
static void ready(void) {
    ticks(1100u);CHECK(g_motor_direct.state==MOTOR_BENCH_READY);
    CHECK(set_calls==0u && (GPIOE->ODR&0x6a00u)==0u);
}
static void press_to_run(void) {
    pressed=1u;ticks(1100u);
    CHECK(g_motor_direct.state==MOTOR_BENCH_ARMED && set_calls==0u);
    /* 第一次采样松键时才建立raw_since；满30ms差值需要31次1ms调用。 */
    pressed=0u;ticks(31u);
    CHECK(g_motor_direct.state==MOTOR_BENCH_RUNNING && g_motor_direct.output_mask==TEST_MASK);
    CHECK(set_calls==1u && g_motor_direct_gpio_diag.active.valid==1u);
    CHECK(g_motor_direct_gpio_diag.enable_calls==1u && g_motor_direct_gpio_diag.stopped.valid==0u);
}
static void trigger_a(void) { ready();press_to_run(); }
static void stopped_ok(motor_direct_stop_reason_t reason) {
    CHECK((GPIOE->ODR&0x6a00u)==0u);
    CHECK(g_motor_direct_gpio_diag.stop_count==1u && g_motor_direct_gpio_diag.stopped.valid==1u);
    CHECK(g_motor_direct_gpio_diag.stop_reason==(uint32_t)reason);
    CHECK(g_motor_direct_gpio_diag.active.run_id==g_motor_direct_gpio_diag.stopped.run_id);
    CHECK((g_motor_direct_gpio_diag.stopped.gpio_moder&0x3ccc0000u)==0x14440000u);
    CHECK((g_motor_direct_gpio_diag.stopped.gpio_odr&0x6a00u)==0u);
    CHECK(g_motor_direct_gpio_diag.stop_ms-g_motor_direct_gpio_diag.start_ms==g_motor_direct_gpio_diag.elapsed_ms);
}
static void lockout(void) {
    pressed=0u;ticks(1100u);pressed=1u;ticks(1200u);pressed=0u;ticks(40u);
    CHECK(set_calls==1u && (GPIOE->ODR&0x6a00u)==0u);
}
static void normal_timeout(void) {
    motor_direct_gpio_snapshot_t kept;
    trigger_a();
    CHECK(g_motor_direct_gpio_diag.enable_count==1u && (GPIOE->ODR&0x6a00u)==TEST_PIN);
    CHECK((GPIOE->MODER&0x3ccc0000u)==0x14440000u && GPIOE->AFR[1]==0u);
    CHECK((GPIOE->ODR&8u)!=0u); /* 未选PE3不被四脚写入破坏。 */
    memcpy(&kept,(const void *)&g_motor_direct_gpio_diag.active,sizeof(kept));
    ticks(499u);CHECK(g_motor_direct.state==MOTOR_BENCH_RUNNING && set_calls==1u);
    CHECK((GPIOE->ODR&0x6a00u)==TEST_PIN);
    ticks(1u);stopped_ok(MOTOR_DIRECT_STOP_TIMEOUT);
    CHECK(g_motor_direct.state==MOTOR_BENCH_COMPLETE && g_motor_direct.step==0u);
    CHECK(g_motor_direct_gpio_diag.elapsed_ms==500u);
    CHECK(memcmp(&kept,(const void *)&g_motor_direct_gpio_diag.active,sizeof(kept))==0);
    lockout();CHECK(g_motor_direct.state==MOTOR_BENCH_COMPLETE);
}
static void key_stop(void) {
    trigger_a();pressed=1u;ticks(1u);stopped_ok(MOTOR_DIRECT_STOP_KEY);
    CHECK(g_motor_direct.state==MOTOR_BENCH_ABORTED && g_motor_direct_gpio_diag.elapsed_ms==1u);
    lockout();CHECK(g_motor_direct.state==MOTOR_BENCH_ABORTED);
}
static void fault_stop(void) {
    trigger_a();g_motor_direct_fault=8u;ticks(1u);stopped_ok(MOTOR_DIRECT_STOP_FAULT);
    CHECK(g_motor_direct.state==MOTOR_BENCH_ABORTED && g_motor_direct.output_mask==0u);
    CHECK(g_motor_direct_gpio_diag.stopped.fault==8u);lockout();
}
static void bad_step(void) {
    trigger_a();g_motor_direct.step=1u;ticks(1u);stopped_ok(MOTOR_DIRECT_STOP_LOGIC);
    CHECK(g_motor_direct.state==MOTOR_BENCH_ABORTED);lockout();
}
static void illegal_request(void) {
    trigger_a();g_motor_direct.output_mask=OTHER_MASK;ticks(1u);
    stopped_ok(MOTOR_DIRECT_STOP_INVALID_MASK);
    CHECK(g_motor_direct_fault==32u && g_motor_direct.output_mask==0u);
    CHECK(g_motor_direct.state==MOTOR_BENCH_ABORTED);lockout();
}
static void timeout_wrap(void) {
    ready();g_motor_direct_ms=0xfffffa00u;press_to_run();
    ticks(499u);CHECK(g_motor_direct.state==MOTOR_BENCH_RUNNING);
    ticks(1u);stopped_ok(MOTOR_DIRECT_STOP_TIMEOUT);
    CHECK(g_motor_direct_gpio_diag.stop_ms<g_motor_direct_gpio_diag.start_ms);
    CHECK(g_motor_direct_gpio_diag.elapsed_ms==500u);lockout();
}
static void no_auto_start(void) {
    pressed=1u;ticks(6100u);CHECK(set_calls==0u && g_motor_direct.state==MOTOR_BENCH_WAIT_RELEASE);
    pressed=0u;ready();pressed=1u;ticks(200u);pressed=0u;ticks(1200u);
    CHECK(g_motor_direct.state==MOTOR_BENCH_READY && set_calls==0u);
    pressed=1u;ticks(5100u);CHECK(g_motor_direct.state==MOTOR_BENCH_ABORTED && set_calls==0u);
    pressed=0u;ticks(1200u);CHECK(set_calls==0u && (GPIOE->ODR&0x6a00u)==0u);
    CHECK(g_motor_direct_gpio_diag.active.valid==0u && g_motor_direct_gpio_diag.stop_count==0u);
}
static void actual_readback(void) {
    disturb_set=1u;GPIOE->IDR=0x1234u;trigger_a();
    CHECK(g_motor_direct_gpio_diag.enable_calls==1u && g_motor_direct_gpio_diag.enable_count==0u);
    CHECK(g_motor_direct_gpio_diag.active.gpio_odr==GPIOE->ODR);
    CHECK(g_motor_direct_gpio_diag.active.gpio_idr==0x1234u);
    CHECK((g_motor_direct_gpio_diag.active.gpio_odr&TEST_PIN)==0u);
    ticks(500u);stopped_ok(MOTOR_DIRECT_STOP_TIMEOUT);
}
static void clock_fault(void) {
    CHECK(g_motor_direct_fault==3u && g_motor_direct.state==MOTOR_BENCH_ABORTED);
    CHECK(motor_direct_gpio_apply(TEST_MASK)==0); /* 模块自身也拒绝时钟失败后的误调用。 */
    pressed=1u;ticks(1500u);pressed=0u;ticks(40u);
    CHECK(set_calls==0u && (GPIOE->ODR&0x6a00u)==0u && watchdog_enabled==0u);
}
static void run(void (*test)(void),uint8_t clock_bad) {
    memset(&model_gpio_a,0,sizeof(model_gpio_a));memset(&model_gpio_b,0,sizeof(model_gpio_b));
    memset(&model_gpio_e,0,sizeof(model_gpio_e));memset(&model_tim1,0,sizeof(model_tim1));
    memset(&model_rcc,0,sizeof(model_rcc));memset((void *)&g_motor_direct_gpio_diag,0,sizeof(g_motor_direct_gpio_diag));
    GPIOE->ODR=8u; /* 无关PE3的已存在输出锁存值，检查适配器掩码边界。 */
    gpio_ready=output_ready=active_mask=requested_mask=startup_timer_clocked=0u;
    diagnostic_ms=diagnostic_state=diagnostic_fault=0u;diagnostic_reason=MOTOR_DIRECT_STOP_NONE;
    g_motor_direct_ms=g_motor_direct_fault=g_motor_direct_revision=0u;
    g_motor_direct_watchdog_started=g_motor_direct_watchdog_stage=0u;
    pressed=disturb_set=0u;bad_clock=clock_bad;set_calls=reloads=watchdog_enabled=0u;startup_counter=0u;
    scenario=test;
    if(setjmp(completed)==0) { SystemInit();(void)direct_application_main(); }
    CHECK(g_motor_direct_revision==TEST_REVISION);
    CHECK(memcmp(&model_tim1,&(model_tim_t){0},sizeof(model_tim1))==0);
    CHECK(RCC->APB2ENR==0u); /* GPIO置高、TIM5时基存在，TIM1／APB2始终不启用。 */
}
int main(void) {
    run(normal_timeout,0u);run(key_stop,0u);run(fault_stop,0u);run(bad_step,0u);
    run(illegal_request,0u);run(timeout_wrap,0u);run(no_auto_start,0u);
    run(actual_readback,0u);run(clock_fault,1u);
    printf("PASS MotorDirect GPIO: %u checks in 9 real-main/GPIO scenarios (single 500ms, lockout, fault, wrap, no TIM1/AF; no board)\n",checks);
    return 0;
}
