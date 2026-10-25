/**
 * @file motor_bench_main.c
 * @brief 重写PWM测试入口：先四脚低，完成启动监督，再接受KEY长按松开。
 *
 * 单次目标1kHz/50%，每阶段500ms；持续A目标保留20kHz/30%与人工停止语义。
 * 复用与Direct共用的纯按键状态机，不改已验证的Direct A/B代码及其参数。
 * TIM1负责PWM，TIM5只为启动等待计时；SysTick每1ms推进按键和超时，最后喂IWDG。
 * 无编码器/电流/温度反馈，所有试转须悬空；复位后必须重新人工触发。
 */
#include "motor_bench.h"
#include "motor_bench_pwm.h"
#include "stm32f4xx.h"

uint32_t SystemCoreClock = HSI_VALUE;
motor_bench_t g_motor_bench;
volatile uint32_t g_motor_bench_ms, g_motor_bench_fault, g_motor_bench_revision;
volatile uint32_t g_motor_bench_watchdog_started, g_motor_bench_watchdog_stage;
#define MOTOR_BENCH_FAULT_PWM_CLOCK 1u
#define MOTOR_BENCH_FAULT_STARTUP_TIMER 2u
#define MOTOR_BENCH_FAULT_LSI_TIMEOUT 4u
#define MOTOR_BENCH_FAULT_IWDG_TIMEOUT 8u
#define MOTOR_BENCH_FAULT_SYSTICK 16u
#define MOTOR_BENCH_FAULT_PWM_REQUEST 32u
#define STARTUP_WAIT_US 10000u
#define STARTUP_POLL_LIMIT 100000u
static uint8_t startup_timer_clocked;

/** @brief 启用HSI并复位时钟树；执行时应用尚未允许任何PWM请求。
 * 无参数/返回值。使用SPL设置时钟，CMSIS负责中断向量和FPU内核许可。
 * 冷启动HSI是芯片复位时钟；随后驱动层还会核对四路实际时钟均为16MHz。
 */
void SystemInit(void) {
    RCC_HSICmd(ENABLE);
    while (RCC_GetFlagStatus(RCC_FLAG_HSIRDY) == RESET) { }
    RCC_SYSCLKConfig(RCC_SYSCLKSource_HSI);
    while (RCC_GetSYSCLKSource() != 0u) { }
    RCC_DeInit();
    NVIC_SetVectorTable(NVIC_VectTab_FLASH, 0u);
    SCB->CPACR |= 0x00f00000u;
}

/** @brief 读取RCC实际配置并更新Hz单位的内核时钟变量；不假定外部晶振存在。 */
void SystemCoreClockUpdate(void) {
    RCC_ClocksTypeDef clocks;
    RCC_GetClocksFreq(&clocks);
    SystemCoreClock = clocks.SYSCLK_Frequency;
}

/** @brief KEY为PA0/WKUP输入下拉，PB2绿灯先灭再配置输出；不影响SWD。 */
static void controls_init(void) {
    GPIO_InitTypeDef config;
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA | RCC_AHB1Periph_GPIOB, ENABLE);
    GPIO_StructInit(&config);
    config.GPIO_Pin = GPIO_Pin_0;
    config.GPIO_Mode = GPIO_Mode_IN;
    config.GPIO_PuPd = GPIO_PuPd_DOWN;
    GPIO_Init(GPIOA, &config);
    GPIO_ResetBits(GPIOB, GPIO_Pin_2);
    config.GPIO_Pin = GPIO_Pin_2;
    config.GPIO_Mode = GPIO_Mode_OUT;
    config.GPIO_OType = GPIO_OType_PP;
    config.GPIO_PuPd = GPIO_PuPd_NOPULL;
    config.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOB, &config);
}

/** @brief 建立独立TIM5启动时基，1计数=1us；不使用其中断或GPIO。
 * @return 1=16MHz APB1且CNT实际递增，0=不支持的时钟/停滞。
 * 首次检查也有1024次上限，防止为了建立超时机制而无限等待。
 */
static int startup_timer_init(void) {
    RCC_ClocksTypeDef clocks;
    TIM_TimeBaseInitTypeDef base;
    uint32_t first, attempt;
    RCC_GetClocksFreq(&clocks);
    if (clocks.HCLK_Frequency != 16000000u || clocks.PCLK1_Frequency != 16000000u) return 0;
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM5, ENABLE);
    startup_timer_clocked = 1u;
    TIM_DeInit(TIM5);
    TIM_TimeBaseStructInit(&base);
    base.TIM_Prescaler = 15u;
    base.TIM_Period = 0xffffffffu;
    base.TIM_CounterMode = TIM_CounterMode_Up;
    base.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInit(TIM5, &base);
    TIM_GenerateEvent(TIM5, TIM_EventSource_Update);
    TIM_Cmd(TIM5, ENABLE);
    first = TIM_GetCounter(TIM5);
    for (attempt = 0u; attempt < 1024u; ++attempt)
        if (TIM_GetCounter(TIM5) != first) return 1;
    return 0;
}

/** @brief 启动等待限时判断；started单位us，polls为次数，fault为超时原因。
 * @return 0=仍可等待，非零=锁存故障。无符号差支持计数回绕。
 * 10ms硬件超时与次数上限同时使用，TIM5意外停滞也能退出。
 */
static uint32_t startup_wait_fault(uint32_t started, uint32_t *polls, uint32_t fault) {
    if ((uint32_t)(TIM_GetCounter(TIM5) - started) >= STARTUP_WAIT_US) return fault;
    ++*polls;
    return *polls >= STARTUP_POLL_LIMIT ? MOTOR_BENCH_FAULT_STARTUP_TIMER : 0u;
}

/** @brief 启动IWDG并有限等待寄存器更新，约250ms为LSI名义值。
 * @return 0=就绪，其它为故障位。所有退出路径停止TIM5，失败保持零输出。
 * 先使能IWDG，再写PR/RLR并等待PVU/RVU；不能在尚未启动时无限等更新位。
 * 已启动的IWDG不能软件关闭；故障时滴答可喂狗保留灯态，CPU停滞则硬件复位。
 */
static uint32_t watchdog_init(void) {
    uint32_t started, polls = 0u, fault = 0u;
    if (!startup_timer_init()) { fault = MOTOR_BENCH_FAULT_STARTUP_TIMER; goto done; }
    g_motor_bench_watchdog_stage = 1u;
    RCC_LSICmd(ENABLE);
    started = TIM_GetCounter(TIM5);
    while (RCC_GetFlagStatus(RCC_FLAG_LSIRDY) == RESET) {
        fault = startup_wait_fault(started, &polls, MOTOR_BENCH_FAULT_LSI_TIMEOUT);
        if (fault != 0u) goto done;
    }
    g_motor_bench_watchdog_stage = 2u;
    IWDG_Enable();
    g_motor_bench_watchdog_started = 1u;
    g_motor_bench_watchdog_stage = 3u;
    IWDG_WriteAccessCmd(IWDG_WriteAccess_Enable);
    IWDG_SetPrescaler(IWDG_Prescaler_32);
    IWDG_SetReload(249u);
    started = TIM_GetCounter(TIM5);
    polls = 0u;
    while (IWDG_GetFlagStatus(IWDG_FLAG_PVU) != RESET || IWDG_GetFlagStatus(IWDG_FLAG_RVU) != RESET) {
        fault = startup_wait_fault(started, &polls, MOTOR_BENCH_FAULT_IWDG_TIMEOUT);
        if (fault != 0u) goto done;
    }
    IWDG_ReloadCounter();
    g_motor_bench_watchdog_stage = 4u;
done:
    if (startup_timer_clocked != 0u) TIM_Cmd(TIM5, DISABLE);
    if (fault != 0u) motor_bench_pwm_stop();
    return fault;
}

/** @brief 粘性故障统一锁定状态和真实输出；now单位ms，无返回值。
 * 每次复用此路径都保持零请求，诊断帧不会因重复停止被覆盖。
 */
static void lock_fault(uint32_t now) {
    g_motor_bench.output_mask = 0u;
    g_motor_bench.state = MOTOR_BENCH_ABORTED;
    motor_bench_pwm_diag_context(now, (uint32_t)g_motor_bench.state,
                                 g_motor_bench_fault, MOTOR_BENCH_STOP_FAULT);
    motor_bench_pwm_stop();
}

/** @brief 每1ms先处理KEY/500ms到期，再应用输出，最后喂狗；无阻塞操作。
 * 停止读取原始KEY，通常0至1ms内撤驱动，不等待启动所用的30ms消抖。
 * PWM适配器拒绝请求时新增故障位32并锁定，避免状态仍显示RUNNING。
 */
void SysTick_Handler(void) {
    uint32_t now = ++g_motor_bench_ms;
    uint8_t raw = GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0);
    motor_bench_state_t previous = g_motor_bench.state;
    motor_bench_stop_reason_t reason = MOTOR_BENCH_STOP_NONE;
    if (g_motor_bench_fault == 0u) {
        motor_bench_tick(&g_motor_bench, now, raw);
        if (g_motor_bench.state == MOTOR_BENCH_ABORTED)
            reason = previous == MOTOR_BENCH_RUNNING && raw != 0u ? MOTOR_BENCH_STOP_KEY : MOTOR_BENCH_STOP_LOGIC;
        else if (previous == MOTOR_BENCH_RUNNING && g_motor_bench.state != MOTOR_BENCH_RUNNING)
            reason = MOTOR_BENCH_STOP_TIMEOUT;
        motor_bench_pwm_diag_context(now, (uint32_t)g_motor_bench.state, 0u, reason);
        if (!motor_bench_pwm_apply(g_motor_bench.output_mask)) g_motor_bench_fault |= MOTOR_BENCH_FAULT_PWM_REQUEST;
    }
    if (g_motor_bench_fault != 0u) lock_fault(now);
    GPIO_WriteBit(GPIOB, GPIO_Pin_2,
        (g_motor_bench_fault != 0u ? (now / 100u) % 2u : motor_bench_led(&g_motor_bench, now)) != 0u ? Bit_SET : Bit_RESET);
    if (g_motor_bench_watchdog_started != 0u) IWDG_ReloadCounter();
}

/** @brief CPU异常先撤四脚驱动再等待IWDG，绝不从异常返回继续试转。 */
static void fatal_stop(void) {
    __disable_irq();
    motor_bench_pwm_diag_context(g_motor_bench_ms, (uint32_t)g_motor_bench.state,
                                 g_motor_bench_fault, MOTOR_BENCH_STOP_EXCEPTION);
    motor_bench_pwm_stop();
    for (;;) { }
}
void NMI_Handler(void) { fatal_stop(); }
void HardFault_Handler(void) { fatal_stop(); }
void MemManage_Handler(void) { fatal_stop(); }
void BusFault_Handler(void) { fatal_stop(); }
void UsageFault_Handler(void) { fatal_stop(); }

int main(void) {
#ifdef MOTOR_CONTINUOUS_A_TARGET
    g_motor_bench_revision = 0x020b1002u; /* 参数/持续语义保留，驱动重写故升级版本。 */
#else
    g_motor_bench_revision = 0x020b0004u; /* 新PWM：1kHz/50%，区别旧R3。 */
#endif
    /* 第一个外设初始化就是四脚主动低；按键、LED与看门狗在其后建立。 */
    g_motor_bench_fault = motor_bench_pwm_init() ? 0u : MOTOR_BENCH_FAULT_PWM_CLOCK;
    controls_init();
    SystemCoreClockUpdate();
    motor_bench_init(&g_motor_bench, 0u);
    g_motor_bench_fault |= watchdog_init();
    if (g_motor_bench_fault != 0u) lock_fault(0u);
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        g_motor_bench_fault |= MOTOR_BENCH_FAULT_SYSTICK;
        fatal_stop();
    }
    NVIC_SetPriority(SysTick_IRQn, 0u);
    for (;;) __WFI();
}
