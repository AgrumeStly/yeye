/**
 * @file motor_direct_main.c
 * @brief 独立MotorDirect入口：普通GPIO固定电平，只A桥人工一次500ms。
 *
 * 本目标不链接PWM／board／UART，不启动TIM1，不把GPIO当电机电源。
 * PE9高、PE11／13／14低使AT8236 A桥满导通，强于原30%PWM；
 * 仅KEY长按达标再松开才发出一次500ms请求，超时完成或人工停止均锁定。
 * 沿用R1已修复的IWDG顺序、TIM5独立启动超时和SysTick监督；
 * TIM5只用于初始化等待，并非电机PWM，不能为了“不要PWM”删除看门狗时基。
 * 复位／异常先四脚低，复位后仍需重新人工触发，不恢复旧请求。
 */
#include "motor_bench.h"
#include "motor_direct_gpio.h"
#include "stm32f4xx.h"
#if !defined(MOTOR_DIRECT_A_TARGET) || defined(MOTOR_CONTINUOUS_A_TARGET)
#error MotorDirect requires its own single-shot target macro
#endif

uint32_t SystemCoreClock = HSI_VALUE;
/* Watch仅供可用SWD场景观察；USB DFU没有运行中Watch功能。 */
motor_bench_t g_motor_direct;
volatile uint32_t g_motor_direct_ms;
volatile uint32_t g_motor_direct_fault;
/* 故障位可组合且运行中不自动清除；非零时不调用试转逻辑，只保持零驱动。 */
#define MOTOR_DIRECT_FAULT_GPIO_CLOCK 1u
#define MOTOR_DIRECT_FAULT_GPIO_REQUEST 32u /* 非法桥请求／GPIO未初始化，锁存且禁止重启。 */
#define MOTOR_DIRECT_FAULT_STARTUP_TIMER 2u
#define MOTOR_DIRECT_FAULT_LSI_TIMEOUT 4u
#define MOTOR_DIRECT_FAULT_IWDG_TIMEOUT 8u
#define MOTOR_DIRECT_FAULT_SYSTICK 16u
#define STARTUP_WAIT_US 10000u       /* LSI及寄存器更新各最多等待10ms。 */
#define STARTUP_POLL_LIMIT 100000u   /* 定时器异常停滞时的第二道有限循环保护。 */

volatile uint32_t g_motor_direct_revision;
volatile uint32_t g_motor_direct_watchdog_started;
/* 0=未开始，1=启动时基就绪，2=LSI就绪，3=IWDG已启动，4=配置更新完成。 */
volatile uint32_t g_motor_direct_watchdog_stage;
static uint8_t startup_timer_clocked;

/** @brief 启动阶段使用HSI，不依赖8MHz外部晶振或PLL；尚不允许电机GPIO置高。 */
void SystemInit(void) {
    RCC_HSICmd(ENABLE);
    while (RCC_GetFlagStatus(RCC_FLAG_HSIRDY) == RESET) { }
    RCC_SYSCLKConfig(RCC_SYSCLKSource_HSI);
    while (RCC_GetSYSCLKSource() != 0x00u) { }
    RCC_DeInit();
    NVIC_SetVectorTable(NVIC_VectTab_FLASH, 0u);
    SCB->CPACR |= 0x00f00000u; /* CMSIS内核FPU访问许可，与原工程相同。 */
}

/** @brief 读取实际RCC配置更新Hz变量；本目标只接受16MHz配置。 */
void SystemCoreClockUpdate(void) {
    RCC_ClocksTypeDef clocks;
    RCC_GetClocksFreq(&clocks);
    SystemCoreClock = clocks.SYSCLK_Frequency;
}

/** @brief 配置WKUP/PA0为输入下拉、PB2为先灭后输出，保留SWD与其他针脚。 */
static void controls_init(void) {
    GPIO_InitTypeDef gpio;
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA | RCC_AHB1Periph_GPIOB, ENABLE);
    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = GPIO_Pin_0;
    gpio.GPIO_Mode = GPIO_Mode_IN;
    gpio.GPIO_PuPd = GPIO_PuPd_DOWN;
    GPIO_Init(GPIOA, &gpio);
    GPIO_ResetBits(GPIOB, GPIO_Pin_2);
    gpio.GPIO_Pin = GPIO_Pin_2;
    gpio.GPIO_Mode = GPIO_Mode_OUT;
    gpio.GPIO_OType = GPIO_OType_PP;
    gpio.GPIO_Speed = GPIO_Speed_2MHz;
    gpio.GPIO_PuPd = GPIO_PuPd_NOPULL;
    GPIO_Init(GPIOB, &gpio);
}

/**
 * @brief 建立只供初始化等待使用的TIM5：16MHz/16=1MHz，1计数=1us。
 * @return 1为时钟及计数递增检查通过，0为不支持的时钟配置或计数器未运行。
 * 不启用TIM5中断、DMA或GPIO，独占TIM5的CNT/PSC/ARR，初始化结束即停止。
 * 本目标不使用TIM1，TIM3/4保留编码器，不与本时基共享计数器；不依赖调试器或SysTick。
 */
static int startup_timer_init(void) {
    RCC_ClocksTypeDef clocks;
    TIM_TimeBaseInitTypeDef timebase;
    uint32_t first, probes;
    RCC_GetClocksFreq(&clocks);
    if (clocks.HCLK_Frequency != 16000000u || clocks.PCLK1_Frequency != 16000000u)
        return 0; /* APB1不分频，TIM5时钟才是16MHz；拒绝错误的微秒单位。 */
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM5, ENABLE);
    startup_timer_clocked = 1u;
    TIM_DeInit(TIM5);
    TIM_TimeBaseStructInit(&timebase);
    timebase.TIM_Prescaler = 15u;
    timebase.TIM_Period = 0xffffffffu;
    timebase.TIM_CounterMode = TIM_CounterMode_Up;
    timebase.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInit(TIM5, &timebase);
    TIM_GenerateEvent(TIM5, TIM_EventSource_Update);
    TIM_Cmd(TIM5, ENABLE);
    first = TIM_GetCounter(TIM5);
    /* 此检查本身也有次数上限，避免定时器没启动时卡死在“检查时基”。 */
    for (probes = 0u; probes < 1024u; ++probes)
        if (TIM_GetCounter(TIM5) != first) return 1;
    return 0;
}

/**
 * @brief 检查一次启动等待的边界；started为TIM5起始us，polls为本等待轮询数。
 * @return 0继续等待；否则为应锁存的故障位。无符号减法处理32位计数回绕。
 * 正常超时依据硬件计时，不用g_motor_direct_ms；次数保护只处理时基失效，
 * 不是精确毫秒定时，也不能代替独立看门狗对CPU停滞的保护。
 */
static uint32_t startup_wait_fault(uint32_t started, uint32_t *polls, uint32_t timeout_fault) {
    if ((uint32_t)(TIM_GetCounter(TIM5) - started) >= STARTUP_WAIT_US)
        return timeout_fault;
    ++*polls;
    return *polls >= STARTUP_POLL_LIMIT ? MOTOR_DIRECT_FAULT_STARTUP_TIMER : 0u;
}

/**
 * @brief 启动并配置IWDG，返回0成功或明确故障位；所有退出路径维持电机零驱动。
 * 顺序：验证TIM5→限时等待LSI→先Enable→解锁→写PR/RLR→限时等PVU/RVU→Reload。
 * 旧版先等更新再Enable，现场PVU不清，使SysTick永远无法启动。
 * F407 RM0090 21.4.4给出更新最多5个LSI周期，本版各留10ms窗口；
 * 先启动时计数从复位值0xFFF倒数，不提前Reload较短的249，避免压缩配置预算。
 * 启动后硬件不能软件关闭：失败只锁存错误、停止电机，后续SysTick喂狗保留诊断；
 * 若CPU/滴答也停滞，仍由IWDG复位。失败不会被当作正常启动，不允许人工试转。
 */
static uint32_t watchdog_init(void) {
    uint32_t started, polls = 0u, fault = 0u;
    if (!startup_timer_init()) {
        fault = MOTOR_DIRECT_FAULT_STARTUP_TIMER;
        goto finished;
    }
    g_motor_direct_watchdog_stage = 1u;
    RCC_LSICmd(ENABLE);
    started = TIM_GetCounter(TIM5);
    while (RCC_GetFlagStatus(RCC_FLAG_LSIRDY) == RESET) {
        fault = startup_wait_fault(started, &polls, MOTOR_DIRECT_FAULT_LSI_TIMEOUT);
        if (fault != 0u) goto finished;
    }
    g_motor_direct_watchdog_stage = 2u;
    IWDG_Enable(); /* 必须在等待状态位之前启动，继续使用原厂SPL接口。 */
    g_motor_direct_watchdog_started = 1u;
    g_motor_direct_watchdog_stage = 3u;
    IWDG_WriteAccessCmd(IWDG_WriteAccess_Enable);
    IWDG_SetPrescaler(IWDG_Prescaler_32);
    IWDG_SetReload(249u);
    started = TIM_GetCounter(TIM5);
    polls = 0u;
    while (IWDG_GetFlagStatus(IWDG_FLAG_PVU) != RESET ||
           IWDG_GetFlagStatus(IWDG_FLAG_RVU) != RESET) {
        fault = startup_wait_fault(started, &polls, MOTOR_DIRECT_FAULT_IWDG_TIMEOUT);
        if (fault != 0u) goto finished;
    }
    IWDG_ReloadCounter();
    g_motor_direct_watchdog_stage = 4u;
finished:
    if (startup_timer_clocked != 0u) TIM_Cmd(TIM5, DISABLE);
    if (fault != 0u) motor_direct_gpio_stop();
    return fault;
}

/**
 * @brief 每1ms读取按键并完成停止/超时、输出和LED；结束后才喂独立看门狗。
 * 中断中不延时、不串口打印、不调用阻塞操作；原始按键停止优先于消抖。
 * 请求停止延迟通常为0–1ms加本中断执行时间，机械停稳时间必须另外测量。
 */
void SysTick_Handler(void) {
    uint32_t now = ++g_motor_direct_ms;
    uint8_t raw = GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_0);
    motor_bench_state_t previous = g_motor_direct.state;
    motor_direct_stop_reason_t reason = MOTOR_DIRECT_STOP_NONE;
    if (g_motor_direct_fault != 0u) {
        /* 故障为粘性状态；软件状态和请求也归零，不能让Watch仍显示RUNNING。
         * 真正的安全动作仍由下面GPIO stop立即执行，不依赖灯态或诊断判断。
         */
        g_motor_direct.output_mask = 0u;
        g_motor_direct.state = MOTOR_BENCH_ABORTED;
        motor_direct_gpio_diag_context(now, (uint32_t)g_motor_direct.state,
                                    g_motor_direct_fault, MOTOR_DIRECT_STOP_FAULT);
        motor_direct_gpio_stop();
        GPIO_WriteBit(GPIOB, GPIO_Pin_2, (now / 100u) % 2u != 0u ? Bit_SET : Bit_RESET);
    } else {
        motor_bench_tick(&g_motor_direct, now, raw);
        /* 先按真实状态转换确定事件原因，再由GPIO层在置高／清零后读回。
         * 诊断不参与控制；没有TIM1／PWM字段，不把软件请求冒充排针电压。
         */
        if (g_motor_direct.state == MOTOR_BENCH_ABORTED)
            reason = previous == MOTOR_BENCH_RUNNING && raw != 0u ?
                     MOTOR_DIRECT_STOP_KEY : MOTOR_DIRECT_STOP_LOGIC;
        else if (previous == MOTOR_BENCH_RUNNING && g_motor_direct.state != MOTOR_BENCH_RUNNING)
            reason = MOTOR_DIRECT_STOP_TIMEOUT;
        motor_direct_gpio_diag_context(now, (uint32_t)g_motor_direct.state, 0u, reason);
        if (motor_direct_gpio_apply(g_motor_direct.output_mask) == 0) {
            /* GPIO适配层拒绝B／AB／未初始化请求；先撤输出，再锁存故障。
             * 后续滴答只走故障停止分支，不能因按键松开而重新启用。
             */
            g_motor_direct_fault |= MOTOR_DIRECT_FAULT_GPIO_REQUEST;
            g_motor_direct.output_mask = 0u;
            g_motor_direct.state = MOTOR_BENCH_ABORTED;
            motor_direct_gpio_diag_context(now, (uint32_t)g_motor_direct.state,
                                           g_motor_direct_fault, MOTOR_DIRECT_STOP_FAULT);
            motor_direct_gpio_stop();
        }
        GPIO_WriteBit(GPIOB, GPIO_Pin_2,
                      (g_motor_direct_fault != 0u ? (now / 100u) % 2u :
                       motor_bench_led(&g_motor_direct, now)) != 0u ? Bit_SET : Bit_RESET);
    }
    /* LSI或启动时基失败时IWDG尚未启动，不能伪装成正常看门狗服务。 */
    if (g_motor_direct_watchdog_started != 0u) IWDG_ReloadCounter();
}

/** @brief CPU异常先关闭驱动，再等待IWDG复位；绝不从异常返回继续旧试转。 */
static void fatal_stop(void) {
    __disable_irq();
    motor_direct_gpio_diag_context(g_motor_direct_ms, (uint32_t)g_motor_direct.state,
                                g_motor_direct_fault, MOTOR_DIRECT_STOP_EXCEPTION);
    motor_direct_gpio_stop();
    for (;;) { } /* 已启用IWDG时将复位；启用前异常则永久保持停止。 */
}
void NMI_Handler(void) { fatal_stop(); }
void HardFault_Handler(void) { fatal_stop(); }
void MemManage_Handler(void) { fatal_stop(); }
void BusFault_Handler(void) { fatal_stop(); }
void UsageFault_Handler(void) { fatal_stop(); }

int main(void) {
    /* 电机GPIO低电平的建立优先于按键、LED和滴答，初始化中没有非零请求。 */
    g_motor_direct_revision = 0x020b2001u; /* 独立GPIO满导通单次版本，不是PWM持续版。 */
    g_motor_direct_fault = motor_direct_gpio_init() != 0 ? 0u : MOTOR_DIRECT_FAULT_GPIO_CLOCK;
    controls_init();
    SystemCoreClockUpdate();
    motor_bench_init(&g_motor_direct, 0u);
    g_motor_direct_fault |= watchdog_init();
    if (g_motor_direct_fault != 0u) {
        motor_direct_gpio_stop();
        g_motor_direct.output_mask = 0u;
        g_motor_direct.state = MOTOR_BENCH_ABORTED;
    }
    /* 初始化失败也启动可用的滴答显示故障；不清故障、不进入READY、不允许试转。 */
    if (SysTick_Config(SystemCoreClock / 1000u) != 0u) {
        g_motor_direct_fault |= MOTOR_DIRECT_FAULT_SYSTICK;
        fatal_stop();
    }
    NVIC_SetPriority(SysTick_IRQn, 0u); /* 本目标没有其他外设中断，监督优先。 */
    for (;;) __WFI();
}
