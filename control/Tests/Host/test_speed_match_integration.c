/* Integration model: real entry, SysTick, state machine and PWM; SPL boundary reused from test_motor_bench_pwm_diag.c. No physical waveform or motor simulation. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include "../../Drivers_Custom/Motor/straight_pwm.c"
#include "../../Drivers_Custom/Encoder/encoder_hw.c"
#define main bench_application_main
#include "../../Core/Src/speed_match_main.c"
#undef main

model_gpio_t model_gpio_a, model_gpio_b, model_gpio_c, model_gpio_e;
model_tim_t model_tim1, model_tim3, model_tim4;
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
void TIM_DeInit(void *t) { if (t != TIM5) memset(t,0,sizeof(model_tim_t)); }
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef *t) { memset(t,0,sizeof(*t)); }
void TIM_TimeBaseInit(void *t, TIM_TimeBaseInitTypeDef *b) {
    if (t != TIM5) { ((model_tim_t *)t)->PSC=b->TIM_Prescaler; ((model_tim_t *)t)->ARR=b->TIM_Period; }
}
void TIM_GenerateEvent(void *t, uint16_t e) { (void)t; (void)e; }
void TIM_Cmd(void *t, FunctionalState s) { if (t == TIM1 && s == ENABLE) TIM1->CR1 |= 1u; }
uint32_t TIM_GetCounter(void *t) { if (t != TIM5) return ((model_tim_t *)t)->CNT; startup_counter+=25u; return startup_counter; }
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

void TIM_EncoderInterfaceConfig(void *t,uint16_t mode,uint16_t p1,uint16_t p2) {
    CHECK((t==TIM3 || t==TIM4) && mode==TIM_EncoderMode_TI12 && p1==0u && p2==0u);
}
void TIM_ICStructInit(TIM_ICInitTypeDef *i) { memset(i,0,sizeof(*i)); }
void TIM_ICInit(void *t,TIM_ICInitTypeDef *i) { CHECK((t==TIM3 || t==TIM4) && i->TIM_ICFilter==6u); }
void TIM_SetCounter(void *t,uint32_t count) { ((model_tim_t *)t)->CNT=count; }
static void ticks(unsigned n) {
    while (n-- != 0u) {
        if ((g_speed_ms+1u)%20u==0u && (TIM1->BDTR & TIM_BDTR_MOE)!=0u) {
            TIM3->CNT=(TIM3->CNT+TIM1->CCR1/400u)&65535u;
            TIM4->CNT=(TIM4->CNT-TIM1->CCR4/300u)&65535u;
        }
        SysTick_Handler();
    }
}
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
