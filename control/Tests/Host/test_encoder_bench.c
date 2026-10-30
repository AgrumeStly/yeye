/* 编译真实Core入口、SPL适配、App及Algorithms；仅外设／内核边界为电脑模型。
 * 不模拟实际AB电气解码；输入CNT轨迹验证真实读取与调度，检查没有电机置高或TIM1操作。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#define main encoder_application_main
#include "../../Core/Src/encoder_bench_main.c"
#undef main
#include "../../Drivers_Custom/Encoder/encoder_hw.c"

test_scb_t test_scb;
model_gpio_t model_gpio_a, model_gpio_b, model_gpio_c, model_gpio_e;
model_tim_t model_tim1, model_tim3, model_tim4;
model_rcc_t model_rcc;
static jmp_buf exit_point;
typedef enum { NORMAL, LSI_STUCK, PVU_STUCK, RVU_STUCK, BOTH_STUCK,
               TIMER_STUCK, TIMER_STOPS, BAD_CLOCK, READ_FAIL, SYSTICK_FAIL } scenario_t;
static scenario_t scenario;
static unsigned checks, watchdog_enabled, reloads, polls, timer_reads, lsi_polls;
static unsigned timer_running, config_writes, systick_started, input_configured, af_calls;
static unsigned motor_clears, gpio_initialized;
static uint32_t startup_counter, expected_fault;
#define CHECK(e) do { ++checks; if (!(e)) { fprintf(stderr,"FAIL encoder main line %d: %s (case %d)\n",__LINE__,#e,(int)scenario); exit(1); } } while (0)

void RCC_HSICmd(FunctionalState s) { (void)s; }
FlagStatus RCC_GetFlagStatus(uint32_t flag) {
    if (flag == RCC_FLAG_LSIRDY) {
        if (++lsi_polls > 2u * STARTUP_POLL_LIMIT) longjmp(exit_point,2);
        if (scenario == LSI_STUCK) return RESET;
    }
    return SET;
}
void RCC_SYSCLKConfig(uint32_t s) { (void)s; }
uint8_t RCC_GetSYSCLKSource(void) { return 0u; }
void RCC_DeInit(void) { }
void NVIC_SetVectorTable(uint32_t t,uint32_t o) { (void)t; (void)o; }
void RCC_GetClocksFreq(RCC_ClocksTypeDef *c) {
    c->SYSCLK_Frequency=c->HCLK_Frequency=c->PCLK1_Frequency=c->PCLK2_Frequency=16000000u;
    if (scenario == BAD_CLOCK) c->HCLK_Frequency=c->PCLK1_Frequency=8000000u;
}
void RCC_AHB1PeriphClockCmd(uint32_t c,FunctionalState s) { CHECK(s==ENABLE); model_rcc.AHB1ENR|=c; }
void RCC_APB1PeriphClockCmd(uint32_t c,FunctionalState s) {
    CHECK(s==ENABLE && (c==RCC_APB1Periph_TIM5 || c==(RCC_APB1Periph_TIM3|RCC_APB1Periph_TIM4)));
}
void RCC_APB2PeriphClockCmd(uint32_t c,FunctionalState s) { (void)c; (void)s; CHECK(0); }
void GPIO_StructInit(GPIO_InitTypeDef *g) { memset(g,0,sizeof(*g)); }
void GPIO_Init(void *port,GPIO_InitTypeDef *g) {
    model_gpio_t *p=(model_gpio_t *)port;
    unsigned bit;
    if (port==GPIOE) CHECK(g->GPIO_Pin==MOTOR_ZERO_PINS && g->GPIO_Mode==GPIO_Mode_OUT && (p->ODR&MOTOR_ZERO_PINS)==0u);
    else if (port==GPIOC || (port==GPIOB && g->GPIO_Pin==(GPIO_Pin_6|GPIO_Pin_7)))
        CHECK(g->GPIO_Mode==GPIO_Mode_AF && g->GPIO_PuPd==GPIO_PuPd_UP);
    else CHECK((port==GPIOA && g->GPIO_Pin==GPIO_Pin_0) || (port==GPIOB && g->GPIO_Pin==GPIO_Pin_2));
    for (bit=0u;bit<16u;++bit) if ((g->GPIO_Pin&(1u<<bit))!=0u) {
        p->MODER=(p->MODER&~(3u<<(bit*2u))) | (g->GPIO_Mode<<(bit*2u));
        p->PUPDR=(p->PUPDR&~(3u<<(bit*2u))) | (g->GPIO_PuPd<<(bit*2u));
    }
    ++gpio_initialized;
}
void GPIO_ResetBits(void *port,uint16_t pins) {
    model_gpio_t *p=(model_gpio_t *)port;
    CHECK((port==GPIOE && pins==MOTOR_ZERO_PINS) || (port==GPIOB && pins==GPIO_Pin_2));
    p->ODR &= ~(uint32_t)pins;
    if (port==GPIOE) ++motor_clears;
}
uint8_t GPIO_ReadInputDataBit(void *port,uint16_t pin) {
    CHECK((port==GPIOC || port==GPIOB) && (pin==GPIO_Pin_6 || pin==GPIO_Pin_7));
    return (((model_gpio_t *)port)->IDR & pin)!=0u ? 1u:0u;
}
void GPIO_WriteBit(void *port,uint16_t pin,BitAction b) {
    CHECK(port==GPIOB && pin==GPIO_Pin_2); /* 任何电机写高操作都会失败。 */
    if (b==Bit_SET) ((model_gpio_t *)port)->ODR|=pin;
    else ((model_gpio_t *)port)->ODR&=~(uint32_t)pin;
}
void GPIO_PinAFConfig(void *port,uint16_t pin,uint8_t af) {
    CHECK((port==GPIOC || port==GPIOB) && (pin==6u || pin==7u) && af==2u);
    ((model_gpio_t *)port)->AFR[0]|=(uint32_t)af<<((uint32_t)pin*4u); ++af_calls;
}
void RCC_LSICmd(FunctionalState s) { CHECK(s==ENABLE); }
void IWDG_Enable(void) { watchdog_enabled=1u; }
void IWDG_WriteAccessCmd(uint16_t key) { CHECK(key==0x5555u && watchdog_enabled==1u); }
void IWDG_SetPrescaler(uint8_t p) { CHECK(p==IWDG_Prescaler_32); ++config_writes; }
void IWDG_SetReload(uint16_t r) { CHECK(r==249u); ++config_writes; }
FlagStatus IWDG_GetFlagStatus(uint16_t flag) {
    CHECK(watchdog_enabled==1u); if (++polls>2u*STARTUP_POLL_LIMIT+2000u) longjmp(exit_point,2);
    if (scenario==BOTH_STUCK || scenario==TIMER_STOPS) return SET;
    if (scenario==PVU_STUCK && flag==IWDG_FLAG_PVU) return SET;
    if (scenario==RVU_STUCK && flag==IWDG_FLAG_RVU) return SET;
    return polls<5u?SET:RESET;
}
void IWDG_ReloadCounter(void) { CHECK(watchdog_enabled==1u); ++reloads; }
void TIM_DeInit(void *t) {
    CHECK(t==TIM5 || t==TIM3 || t==TIM4);
    if (t!=TIM5) memset(t,0,sizeof(model_tim_t));
}
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef *b) { memset(b,0,sizeof(*b)); }
void TIM_TimeBaseInit(void *t,TIM_TimeBaseInitTypeDef *b) {
    CHECK(t==TIM5 || t==TIM3 || t==TIM4);
    if (t==TIM5) CHECK(b->TIM_Prescaler==15u && b->TIM_Period==0xffffffffu);
    else { CHECK(b->TIM_Prescaler==0u && b->TIM_Period==65535u); ((model_tim_t *)t)->ARR=b->TIM_Period; }
}
void TIM_GenerateEvent(void *t,uint16_t e) { CHECK(t==TIM5 && e==TIM_EventSource_Update); }
void TIM_Cmd(void *t,FunctionalState s) {
    CHECK(t==TIM5 || t==TIM3 || t==TIM4);
    if (t==TIM5) timer_running=s==ENABLE?1u:0u;
    else ((model_tim_t *)t)->CR1=s==ENABLE?1u:0u;
}
uint32_t TIM_GetCounter(void *t) {
    CHECK(t==TIM5 || t==TIM3 || t==TIM4);
    if (t!=TIM5) return ((model_tim_t *)t)->CNT;
    ++timer_reads;
    if (timer_running!=0u && scenario!=TIMER_STUCK && !(scenario==TIMER_STOPS && timer_reads>2u)) startup_counter+=25u;
    return startup_counter;
}
void TIM_EncoderInterfaceConfig(void *t,uint16_t mode,uint16_t p1,uint16_t p2) {
    CHECK((t==TIM3 || t==TIM4) && mode==TIM_EncoderMode_TI12 && p1==0u && p2==0u);
    ((model_tim_t *)t)->CCMR2=mode;
}
void TIM_ICStructInit(TIM_ICInitTypeDef *i) { memset(i,0,sizeof(*i)); }
void TIM_ICInit(void *t,TIM_ICInitTypeDef *i) {
    CHECK((t==TIM3 || t==TIM4) && (i->TIM_Channel==TIM_Channel_1 || i->TIM_Channel==TIM_Channel_2));
    CHECK(i->TIM_ICPolarity==0u && i->TIM_ICSelection==1u && i->TIM_ICPrescaler==0u && i->TIM_ICFilter==6u);
    ++input_configured;
}
void TIM_SetCounter(void *t,uint32_t count) { CHECK((t==TIM3 || t==TIM4) && count==0u); ((model_tim_t *)t)->CNT=count; }
uint32_t SysTick_Config(uint32_t ticks) {
    CHECK(g_encoder_bench_ms==0u && g_encoder_bench_fault==expected_fault && ticks==SystemCoreClock/1000u);
    CHECK(g_encoder_bench_motor_odr==0u && (model_gpio_e.ODR&MOTOR_ZERO_PINS)==0u);
    systick_started=1u; return scenario==SYSTICK_FAIL?1u:0u;
}
void NVIC_SetPriority(int irq,uint32_t priority) { CHECK(irq==SysTick_IRQn && priority==0u); }
void __disable_irq(void) {
    CHECK(scenario==SYSTICK_FAIL && (g_encoder_bench_fault&ENCODER_FAULT_SYSTICK)!=0u);
    CHECK((model_gpio_e.ODR&MOTOR_ZERO_PINS)==0u);
    longjmp(exit_point,1); /* 不执行永久异常循环；异常前已处于零输出。 */
}
void __WFI(void) {
    unsigned i;
    if (expected_fault==0u) {
        CHECK(g_encoder_bench.sample_count==1u && g_encoder_bench.a.status==ENCODER_FIRST);
        CHECK(input_configured==4u && af_calls==4u && gpio_initialized==5u);
        for (i=0u;i<9u;++i) SysTick_Handler();
        CHECK(g_encoder_bench.sample_count==1u); /* 前9ms没有伪造样本。 */
        model_tim3.CNT=7u; model_tim4.CNT=65533u;
        model_gpio_c.IDR=GPIO_Pin_6; model_gpio_b.IDR=GPIO_Pin_7;
        if (scenario==READ_FAIL) ready=0u;
        SysTick_Handler();
        if (scenario!=READ_FAIL) {
            CHECK(g_encoder_bench.a.delta==7 && g_encoder_bench.b.delta==-3);
            CHECK(g_encoder_bench.a.counts_per_s==700 && g_encoder_bench.b.counts_per_s==-300);
            CHECK(g_encoder_bench.a.dt_ms==10u && g_encoder_bench.pin_levels==9u);
            CHECK((g_encoder_bench.sequence&1u)==0u && g_encoder_bench.sample_ms==10u);
            model_tim3.CNT=10u; /* B静止，只让A新增3counts。 */
            for (i=0u;i<10u;++i) SysTick_Handler();
            CHECK(g_encoder_bench.a.total_count==10 && g_encoder_bench.b.total_count==-3);
            /* Core调度本身跨毫秒回绕，实际dt仍为10ms，异常窗由算法明确标记。 */
            g_encoder_bench_ms=0xfffffff8u; last_sample_ms=0xfffffff8u;
            CHECK(encoder_bench_sample(0xfffffff8u)==1);
            for (i=0u;i<10u;++i) SysTick_Handler();
            CHECK(g_encoder_bench_ms==2u && g_encoder_bench.a.dt_ms==10u);
        } else CHECK(g_encoder_bench_fault==ENCODER_FAULT_READ && g_encoder_bench_state==2u);
    }
    for (i=0u;i<1200u;++i) SysTick_Handler();
    CHECK((model_gpio_e.ODR&MOTOR_ZERO_PINS)==0u && model_gpio_e.ODR==8u); /* 不改PE3。 */
    CHECK(g_encoder_bench_motor_odr==0u && motor_clears>100u && model_rcc.APB2ENR==0u);
    CHECK(model_tim1.CR1==0u && timer_running==0u);
    longjmp(exit_point,1);
}

static void run(scenario_t s,uint32_t initial_counter,uint32_t fault) {
    scenario=s; expected_fault=fault;
    memset(&model_gpio_a,0,sizeof(model_gpio_a)); memset(&model_gpio_b,0,sizeof(model_gpio_b));
    memset(&model_gpio_c,0,sizeof(model_gpio_c)); memset(&model_gpio_e,0,sizeof(model_gpio_e));
    memset(&model_rcc,0,sizeof(model_rcc)); model_gpio_e.ODR=MOTOR_ZERO_PINS|8u;
    watchdog_enabled=reloads=polls=timer_reads=lsi_polls=timer_running=config_writes=systick_started=0u;
    input_configured=af_calls=motor_clears=gpio_initialized=0u;
    startup_counter=initial_counter;
    g_encoder_bench_ms=g_encoder_bench_fault=g_encoder_bench_revision=0u;
    g_encoder_bench_watchdog_started=g_encoder_bench_watchdog_stage=0u;
    startup_timer_clocked=motor_gpio_ready=0u; last_sample_ms=0u; ready=0u;
    {
        int result=setjmp(exit_point);
        if (result==0) { SystemInit(); (void)encoder_application_main(); }
        CHECK(result!=2);
    }
    CHECK(g_encoder_bench_revision==0x020c0001u && systick_started==1u);
    if (s==READ_FAIL) CHECK(g_encoder_bench_fault==32u);
    else if (s==SYSTICK_FAIL) CHECK(g_encoder_bench_fault==16u);
    else CHECK(g_encoder_bench_fault==fault);
    if (fault==0u) CHECK(g_encoder_bench_watchdog_stage==4u && config_writes==2u && watchdog_enabled==1u);
    if (s==LSI_STUCK || s==TIMER_STUCK || s==BAD_CLOCK) CHECK(watchdog_enabled==0u && reloads==0u);
    CHECK((model_gpio_e.ODR&MOTOR_ZERO_PINS)==0u);
}
int main(void) {
    run(NORMAL,0u,0u); run(NORMAL,0xfffffff0u,0u);
    run(LSI_STUCK,0u,4u); run(LSI_STUCK,0xfffffff0u,4u);
    run(PVU_STUCK,0u,8u); run(RVU_STUCK,0u,8u); run(BOTH_STUCK,0xfffffff0u,8u);
    run(TIMER_STUCK,0u,2u); run(TIMER_STOPS,0u,2u); run(BAD_CLOCK,0u,3u);
    run(READ_FAIL,0u,0u); run(SYSTICK_FAIL,0u,0u);
    printf("PASS EncoderBench: %u assertions in 12 real-main/SPL scenarios (R1, 10ms, dual reads, zero motor; no board)\n",checks);
    return 0;
}
