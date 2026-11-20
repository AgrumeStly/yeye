/** @file low_speed_lap_main.c
 * @brief 低速循迹／独立直道的编译期入口，复用原PWM、编码器采集及计数算法。
 * HSI16MHz、TIM1输出、TIM3/4编码器、TIM5启动限时、IWDG及KEY停止均保留。
 * 原目标前两次KEY逐轮校准；RightAngle R2首次KEY双轮悬空1秒，下一次上道。
 * 地面UART断流仍由1ms监督撤驱动，悬空仅豁免视觉许可，不豁免电机保护。
 */
#include "lap_motion.h"
#include "lap_link.h"
#include "lap_uart.h"
#include "encoder_hw.h"
#include "straight_pwm.h"
#include "stm32f4xx.h"

uint32_t SystemCoreClock = HSI_VALUE;
encoder_counter_t g_speed_encoder_a, g_speed_encoder_b;
volatile uint32_t g_speed_ms, g_speed_fault, g_speed_revision;
lap_parser_t g_lap_parser;
volatile uint32_t g_speed_watchdog_started, g_speed_watchdog_stage;
#define MOTOR_BENCH_FAULT_PWM_CLOCK 1u
#define MOTOR_BENCH_FAULT_STARTUP_TIMER 2u
#define MOTOR_BENCH_FAULT_LSI_TIMEOUT 4u
#define MOTOR_BENCH_FAULT_IWDG_TIMEOUT 8u
#define MOTOR_BENCH_FAULT_SYSTICK 16u
#define MOTOR_BENCH_FAULT_PWM_REQUEST 32u
#define STARTUP_WAIT_US 10000u
#define STARTUP_POLL_LIMIT 100000u
static uint8_t startup_timer_clocked;
static uint32_t last_sample_at;
/** @brief 本板执行时序诊断；周期数除以16为当前16MHz下的微秒数。
 * SysTick最大值包含UART抢占，motion_lock最大值包含主循环的状态提交。
 * UART自身用g_lap_uart_diag.isr_max_cycles记录；计时不代替实测停车验收。
 */
typedef struct {
    uint32_t counter_ready, clock_hz, systick_max_cycles, motion_lock_max_cycles;
} lap_timing_t;
volatile lap_timing_t g_lap_timing;
static uint32_t motion_irq_mask;

/** @brief 屏蔽运动状态的SysTick写者，同时保留UART优先级0接收。
 * 返回原BASEPRI，解锁时原样恢复；MAX形式不放宽调用方已有的屏蔽级别。
 * UART只写接收环，不写g_lap/校准器/解析器，因此允许在状态提交期间抢占。
 * 禁止改成全局关中断：115200/8N1连续字节间隔约86.8us，长计算会丢字节。
 */
static uint32_t motion_lock(void) {
    uint32_t previous = __get_BASEPRI();
    __set_BASEPRI_MAX(motion_irq_mask); __DSB(); __ISB();
    return previous;
}
/** @brief 更新最长提交周期数，再恢复调用方BASEPRI；started为DWT起始周期数。 */
static void motion_unlock(uint32_t previous, uint32_t started) {
    uint32_t elapsed = DWT->CYCCNT - started;
    if (elapsed > g_lap_timing.motion_lock_max_cycles) g_lap_timing.motion_lock_max_cycles = elapsed;
    __DMB(); __set_BASEPRI(previous); __ISB();
}

/** @brief 只启用CMSIS内核周期计数器，不改SPL时钟、外设或控制周期。
 * 64次有界NOP检查计数器是否前进；不支持时ready为0，不能声称计时已通过。
 * CYCCNT允许自然回绕，短区间用无符号减法求周期差。
 */
static void timing_init(void) {
    uint32_t before, i;
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    before = DWT->CYCCNT;
    for (i = 0u; i < 64u; ++i) __NOP();
    g_lap_timing.counter_ready = DWT->CYCCNT != before ? 1u : 0u;
    g_lap_timing.clock_hz = SystemCoreClock;
}

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
    g_speed_watchdog_stage = 1u;
    RCC_LSICmd(ENABLE);
    started = TIM_GetCounter(TIM5);
    while (RCC_GetFlagStatus(RCC_FLAG_LSIRDY) == RESET) {
        fault = startup_wait_fault(started, &polls, MOTOR_BENCH_FAULT_LSI_TIMEOUT);
        if (fault != 0u) goto done;
    }
    g_speed_watchdog_stage = 2u;
    IWDG_Enable();
    g_speed_watchdog_started = 1u;
    g_speed_watchdog_stage = 3u;
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
    g_speed_watchdog_stage = 4u;
done:
    if (startup_timer_clocked != 0u) TIM_Cmd(TIM5, DISABLE);
    if (fault != 0u) straight_pwm_stop();
    return fault;
}

/** @brief 每1ms监督停止，每20ms复用原采集／回绕算法并计算轮速。
 * 先采样再进行按键／时限监督，最后应用输出与喂狗；整个中断不阻塞。
 * 原始a/b数据供校准和Watch，控制层自行保存识别后的物理左右映射。
 */
void SysTick_Handler(void) {
    uint32_t started = DWT->CYCCNT, elapsed;
    uint32_t now = ++g_speed_ms;
    lap_uart_tick(now);
    if (g_speed_fault == 0u) {
        if ((uint32_t)(now - last_sample_at) >= SPEED_MATCH_SAMPLE_MS) {
            encoder_raw_t raw;
            last_sample_at = now;
            if (!encoder_hw_read(&raw)) g_speed_fault |= 64u;
            else {
                encoder_counter_update(&g_speed_encoder_a, raw.a, now);
                encoder_counter_update(&g_speed_encoder_b, raw.b, now);
                lap_motion_sample(now, &g_speed_encoder_a.sample, &g_speed_encoder_b.sample);
            }
        }
        lap_motion_tick(now, GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0));
        if (!straight_pwm_apply(g_lap.left_pwm, g_lap.right_pwm))
            g_speed_fault |= MOTOR_BENCH_FAULT_PWM_REQUEST;
    }
    if (g_speed_fault != 0u) {
        lap_motion_fault(LAP_HARDWARE, now);
        straight_pwm_stop();
    }
    GPIO_WriteBit(GPIOB, GPIO_Pin_2, lap_motion_led(now) != 0u ? Bit_SET : Bit_RESET);
    if (g_speed_watchdog_started != 0u) IWDG_ReloadCounter();
    elapsed = DWT->CYCCNT - started;
    if (elapsed > g_lap_timing.systick_max_cycles) g_lap_timing.systick_max_cycles = elapsed;
}

/** @brief CPU异常先撤四脚驱动再等待IWDG，绝不从异常返回继续试转。 */
static void fatal_stop(void) {
    __disable_irq();
    straight_pwm_stop();
    for (;;) { }
}
void NMI_Handler(void) { fatal_stop(); }
void HardFault_Handler(void) { fatal_stop(); }
void MemManage_Handler(void) { fatal_stop(); }
void BusFault_Handler(void) { fatal_stop(); }
void UsageFault_Handler(void) { fatal_stop(); }

/** @brief 先撤PWM，再初始化编码器／状态与启动监督；默认只读采集，不自启。 */
int main(void) {
#ifdef RIGHT_ANGLE_TARGET
    g_speed_revision = 0x02120012u; /* 首弯R4/v5：当前L形预测可启动，大半径前进圆弧。 */
#elif defined(STRAIGHT_ASSIST_TARGET)
    g_speed_revision = 0x02120002u; /* 独立直道v3：加入编码器差速补偿，减轻快轮超调。 */
#elif defined(LAP_TRACK_TARGET)
    g_speed_revision = 0x0211000Cu; /* Track诊断版：保持300000ms上限，未放行实车。 */
#else
    g_speed_revision = 0x0211000Bu; /* 三秒诊断版：增加停车前原始编码器取证环。 */
#endif
    g_speed_fault = straight_pwm_init() ? 0u : MOTOR_BENCH_FAULT_PWM_CLOCK;
    if (!encoder_hw_init()) g_speed_fault |= 64u;
    controls_init();
    SystemCoreClockUpdate();
    timing_init();
    encoder_counter_init(&g_speed_encoder_a);
    encoder_counter_init(&g_speed_encoder_b);
    lap_motion_init(0u);
    lap_link_init(&g_lap_parser);
    lap_uart_init();
    g_speed_fault |= watchdog_init();
    if (g_speed_fault != 0u) lap_motion_fault(LAP_HARDWARE, 0u);
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        g_speed_fault |= MOTOR_BENCH_FAULT_SYSTICK;
        fatal_stop();
    }
    /* 优先级分组由UART初始化设定。通过CMSIS编码“抢占级1、子优先级0”，
     * 不能直接写逻辑优先级1：Group2下它只是同抢占级的不同子优先级。
     */
    NVIC_SetPriority(SysTick_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(), LAP_SAFETY_PREEMPT_PRIORITY, 0u));
    motion_irq_mask = NVIC_GetPriority(SysTick_IRQn) << (8u - __NVIC_PRIO_BITS);
    /* 协议解析留在主循环；停止／轮速／看门狗仍由1ms滴答执行。
     * UART的单字节搬运可抢占滴答与状态提交，避免20ms计算阻塞接收。
     * BASEPRI只屏蔽状态写者，不屏蔽UART；CRC／串口等待不放入提交区。
     * 每次循环先处理传输错误，绝不从已溢出的缓冲恢复运动许可。
     */
    for (;;) {
        uint8_t byte; uint32_t arrival, mask, started;
        if (lap_uart_fault()) {
            started = DWT->CYCCNT; mask = motion_lock();
            lap_motion_fault(LAP_TRANSPORT, g_speed_ms); lap_link_init(&g_lap_parser);
            motion_unlock(mask, started);
        }
        while (lap_uart_read(&byte, &arrival)) {
            if (lap_link_push(&g_lap_parser, byte)) {
                started = DWT->CYCCNT; mask = motion_lock();
                lap_motion_receive(g_lap_parser.bytes, arrival, g_speed_ms);
                motion_unlock(mask, started);
            }
        }
        /* 不在这里WFI：包到达与睡眠之间的竞争可能把解析延迟一拍。
         * 低功耗不是本试跑的目标，主循环无等待，ISR只维护接收环。
         */
    }
}
