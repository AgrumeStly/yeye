/** @file encoder_bench_main.c
 * @brief C-02C独立EncoderBench：电机四输入始终为低，只手转轮读取TIM3/4。
 * Core负责HSI／R1启动监督、SysTick调度及异常衔接；App负责双路数据发布，
 * Drivers_Custom负责SPL编码器输入，Algorithms负责回绕／增量／时间换算。
 * TIM1不启动，TIM5仅用于既有启动限时等待，UART／SWD／PA0资源保留。
 */
#include "encoder_bench.h"
#include "encoder_hw.h"
#include "stm32f4xx.h"
#if !defined(ENCODER_BENCH_TARGET)
#error EncoderBench requires its independent target
#endif
uint32_t SystemCoreClock = HSI_VALUE;
volatile uint32_t g_encoder_bench_ms, g_encoder_bench_fault, g_encoder_bench_revision;
volatile uint32_t g_encoder_bench_watchdog_started, g_encoder_bench_watchdog_stage;
volatile uint32_t g_encoder_bench_state, g_encoder_bench_motor_odr;
#define ENCODER_FAULT_CLOCK 1u
#define ENCODER_FAULT_STARTUP_TIMER 2u
#define ENCODER_FAULT_LSI_TIMEOUT 4u
#define ENCODER_FAULT_IWDG_TIMEOUT 8u
#define ENCODER_FAULT_SYSTICK 16u
#define ENCODER_FAULT_READ 32u
#define STARTUP_WAIT_US 10000u
#define STARTUP_POLL_LIMIT 100000u
#define MOTOR_ZERO_PINS (GPIO_Pin_9 | GPIO_Pin_11 | GPIO_Pin_13 | GPIO_Pin_14)
static uint8_t startup_timer_clocked, motor_gpio_ready;
static uint32_t last_sample_ms;

/** @brief 初始化／滴答／异常共用的物理零输出；无参数／返回值，无等待。
 * 仅清PE9／11／13／14的输出锁存，不置高任何电机控制脚；先初始化GPIO才能调用。
 * ODR读回仅证明板内锁存，不冒充排针电压或驱动实际输出测量。
 */
static void motor_zero(void) {
    if (motor_gpio_ready != 0u) {
        GPIO_ResetBits(GPIOE, MOTOR_ZERO_PINS);
        g_encoder_bench_motor_odr = GPIOE->ODR & MOTOR_ZERO_PINS;
    }
}

/** @brief 第一个应用外设动作：先清锁存，再把四电机输入配置为推挽下拉输出。
 * 无TIM1／AF／PWM操作；复位最初高阻窗口仍依赖驱动默认下拉，不能靠软件证明。
 */
static void motor_zero_init(void) {
    GPIO_InitTypeDef gpio;
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOE, ENABLE);
    GPIO_ResetBits(GPIOE, MOTOR_ZERO_PINS);
    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = MOTOR_ZERO_PINS;
    gpio.GPIO_Mode = GPIO_Mode_OUT;
    gpio.GPIO_OType = GPIO_OType_PP;
    gpio.GPIO_PuPd = GPIO_PuPd_DOWN;
    gpio.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOE, &gpio);
    motor_gpio_ready = 1u;
    motor_zero();
}

/** @brief 启用HSI并复位时钟树；执行时编码器入口从不允许电机请求。
 * 无参数/返回值。使用SPL设置时钟，CMSIS负责中断向量和FPU内核许可。
 * 冷启动HSI是芯片复位时钟；随后驱动层还会核对各路实际时钟均为16MHz。
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
    return *polls >= STARTUP_POLL_LIMIT ? ENCODER_FAULT_STARTUP_TIMER : 0u;
}

/** @brief 启动IWDG并有限等待寄存器更新，约250ms为LSI名义值。
 * @return 0=就绪，其它为故障位。所有退出路径停止TIM5，失败保持零输出。
 * 先使能IWDG，再写PR/RLR并等待PVU/RVU；不能在尚未启动时无限等更新位。
 * 已启动的IWDG不能软件关闭；故障时滴答可喂狗保留灯态，CPU停滞则硬件复位。
 */
static uint32_t watchdog_init(void) {
    uint32_t started, polls = 0u, fault = 0u;
    if (!startup_timer_init()) { fault = ENCODER_FAULT_STARTUP_TIMER; goto done; }
    g_encoder_bench_watchdog_stage = 1u;
    RCC_LSICmd(ENABLE);
    started = TIM_GetCounter(TIM5);
    while (RCC_GetFlagStatus(RCC_FLAG_LSIRDY) == RESET) {
        fault = startup_wait_fault(started, &polls, ENCODER_FAULT_LSI_TIMEOUT);
        if (fault != 0u) goto done;
    }
    g_encoder_bench_watchdog_stage = 2u;
    IWDG_Enable();
    g_encoder_bench_watchdog_started = 1u;
    g_encoder_bench_watchdog_stage = 3u;
    IWDG_WriteAccessCmd(IWDG_WriteAccess_Enable);
    IWDG_SetPrescaler(IWDG_Prescaler_32);
    IWDG_SetReload(249u);
    started = TIM_GetCounter(TIM5);
    polls = 0u;
    while (IWDG_GetFlagStatus(IWDG_FLAG_PVU) != RESET || IWDG_GetFlagStatus(IWDG_FLAG_RVU) != RESET) {
        fault = startup_wait_fault(started, &polls, ENCODER_FAULT_IWDG_TIMEOUT);
        if (fault != 0u) goto done;
    }
    IWDG_ReloadCounter();
    g_encoder_bench_watchdog_stage = 4u;
done:
    if (startup_timer_clocked != 0u) TIM_Cmd(TIM5, DISABLE);
    if (fault != 0u) motor_zero();
    return fault;
}

/** @brief 1ms滴答仅维护时间／灯／零输出，每10ms读取两路CNT。
 * 使用实际now-last进行调度和dt计算，不用循环补造多个相同时间的样本；
 * 毫秒回绕用无符号差处理。ISR无打印、无延时，处理结束才喂看门狗。
 * KEY没有任何启动动作，按多久也不会使电机置高；它仍保留为板载输入。
 */
void SysTick_Handler(void) {
    uint32_t now = ++g_encoder_bench_ms;
    motor_zero();
    if (g_encoder_bench_fault == 0u && (uint32_t)(now - last_sample_ms) >= ENCODER_BENCH_PERIOD_MS) {
        last_sample_ms = now;
        if (!encoder_bench_sample(now)) g_encoder_bench_fault |= ENCODER_FAULT_READ;
    }
    g_encoder_bench_state = g_encoder_bench_fault == 0u ? 1u : 2u;
    GPIO_WriteBit(GPIOB, GPIO_Pin_2,
        (now / (g_encoder_bench_fault == 0u ? 500u : 100u)) % 2u != 0u ? Bit_SET : Bit_RESET);
    if (g_encoder_bench_watchdog_started != 0u) IWDG_ReloadCounter();
}

/** @brief 异常锁定为fault态并先拉低电机脚，再等已启动的IWDG复位。
 * 异常发生在初始化前时不访问未开时钟的GPIO；复位后也不会进入任何运动状态。
 */
static void fatal_stop(void) {
    __disable_irq();
    g_encoder_bench_state = 2u;
    motor_zero();
    for (;;) { }
}
void NMI_Handler(void) { fatal_stop(); }
void HardFault_Handler(void) { fatal_stop(); }
void MemManage_Handler(void) { fatal_stop(); }
void BusFault_Handler(void) { fatal_stop(); }
void UsageFault_Handler(void) { fatal_stop(); }

int main(void) {
    /* 无动力诊断的第一步永远是四脚低，不调用已验收电机驱动的任何启用路径。 */
    motor_zero_init();
    g_encoder_bench_revision = 0x020c0001u;
    controls_init();
    SystemCoreClockUpdate();
    encoder_bench_init();
    g_encoder_bench_fault = encoder_hw_init() ? 0u : ENCODER_FAULT_CLOCK;
    g_encoder_bench_fault |= watchdog_init();
    if (g_encoder_bench_fault == 0u && !encoder_bench_sample(0u))
        g_encoder_bench_fault |= ENCODER_FAULT_READ;
    g_encoder_bench_state = g_encoder_bench_fault == 0u ? 1u : 2u;
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        g_encoder_bench_fault |= ENCODER_FAULT_SYSTICK;
        fatal_stop();
    }
    NVIC_SetPriority(SysTick_IRQn, 0u);
    for (;;) __WFI();
}
