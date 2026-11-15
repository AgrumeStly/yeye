/** @file oled_bench_main.c
 * @brief 独立无动力OLED点亮测试：零电机输出、地址应答、四种图样及秒计数。
 * 保留既有TIM5限时启动/IWDG保护；TIM3/TIM4和UART不初始化，KEY不触发动作。
 * SysTick只做毫秒、灯及电机零输出；显示在主循环按页传输，每页完成后喂狗。
 * 此入口不替代LowSpeedLap运动程序，下载前必须隔离动力电池。
 */
#include "stm32f4xx.h"
#include "stm32f4xx_tim.h"
#include "stm32f4xx_iwdg.h"
#include "oled_i2c.h"
#include "oled_pattern.h"
#ifndef OLED_BENCH_TARGET
#error This entry requires OledBench target
#endif
uint32_t SystemCoreClock = HSI_VALUE;
volatile uint32_t g_oled_ms, g_oled_fault, g_oled_revision;
volatile uint32_t g_oled_watchdog_started, g_oled_watchdog_stage;
volatile uint32_t g_oled_state, g_oled_motor_odr;
#define OLED_FAULT_CLOCK 1u
#define OLED_FAULT_STARTUP_TIMER 2u
#define OLED_FAULT_LSI_TIMEOUT 4u
#define OLED_FAULT_IWDG_TIMEOUT 8u
#define OLED_FAULT_SYSTICK 16u
#define OLED_FAULT_READ 32u
#define STARTUP_WAIT_US 10000u
#define STARTUP_POLL_LIMIT 100000u
#define MOTOR_ZERO_PINS (GPIO_Pin_9 | GPIO_Pin_11 | GPIO_Pin_13 | GPIO_Pin_14)
static uint8_t startup_timer_clocked, motor_gpio_ready;


/** @brief 初始化／滴答／异常共用的物理零输出；无参数／返回值，无等待。
 * 仅清PE9／11／13／14的输出锁存，不置高任何电机控制脚；先初始化GPIO才能调用。
 * ODR读回仅证明板内锁存，不冒充排针电压或驱动实际输出测量。
 */
static void motor_zero(void) {
    if (motor_gpio_ready != 0u) {
        GPIO_ResetBits(GPIOE, MOTOR_ZERO_PINS);
        g_oled_motor_odr = GPIOE->ODR & MOTOR_ZERO_PINS;
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

/** @brief 启用HSI并复位时钟树；执行时本诊断入口从不允许电机请求。
 * 无参数/返回值。使用SPL设置时钟，CMSIS负责中断向量和FPU内核许可。
 * 冷启动HSI是芯片复位时钟；随后驱动层还会核对实际内核时钟为16MHz。
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
    return *polls >= STARTUP_POLL_LIMIT ? OLED_FAULT_STARTUP_TIMER : 0u;
}

/** @brief 启动IWDG并有限等待寄存器更新，约250ms为LSI名义值。
 * @return 0=就绪，其它为故障位。所有退出路径停止TIM5，失败保持零输出。
 * 先使能IWDG，再写PR/RLR并等待PVU/RVU；不能在尚未启动时无限等更新位。
 * 已启动的IWDG不能软件关闭；故障时滴答可喂狗保留灯态，CPU停滞则硬件复位。
 */
static uint32_t watchdog_init(void) {
    uint32_t started, polls = 0u, fault = 0u;
    if (!startup_timer_init()) { fault = OLED_FAULT_STARTUP_TIMER; goto done; }
    g_oled_watchdog_stage = 1u;
    RCC_LSICmd(ENABLE);
    started = TIM_GetCounter(TIM5);
    while (RCC_GetFlagStatus(RCC_FLAG_LSIRDY) == RESET) {
        fault = startup_wait_fault(started, &polls, OLED_FAULT_LSI_TIMEOUT);
        if (fault != 0u) goto done;
    }
    g_oled_watchdog_stage = 2u;
    IWDG_Enable();
    g_oled_watchdog_started = 1u;
    g_oled_watchdog_stage = 3u;
    IWDG_WriteAccessCmd(IWDG_WriteAccess_Enable);
    IWDG_SetPrescaler(IWDG_Prescaler_32);
    IWDG_SetReload(249u);
    started = TIM_GetCounter(TIM5);
    polls = 0u;
    while (IWDG_GetFlagStatus(IWDG_FLAG_PVU) != RESET || IWDG_GetFlagStatus(IWDG_FLAG_RVU) != RESET) {
        fault = startup_wait_fault(started, &polls, OLED_FAULT_IWDG_TIMEOUT);
        if (fault != 0u) goto done;
    }
    IWDG_ReloadCounter();
    g_oled_watchdog_stage = 4u;
done:
    if (startup_timer_clocked != 0u) TIM_Cmd(TIM5, DISABLE);
    if (fault != 0u) motor_zero();
    return fault;
}


/* Watch可读诊断：版本、启动故障、实际7位地址、两个候选应答掩码和成功整帧数。
 * ack_mask bit0=0x3C应答、bit1=0x3D应答，不是控制芯片身份识别。
 * stage 1启动、2总线、3探测、4初始化、5图样刷新、6稳定计数、255故障。
 */
volatile uint32_t g_oled_stage, g_oled_address, g_oled_ack_mask;
volatile uint32_t g_oled_frames, g_oled_phase, g_oled_seconds;
static uint8_t frame[1024];

/** @brief 1ms中断只维护心跳和物理零输出，不做I2C或喂看门狗。
 * 看门狗只由主循环/每页完成后喂，显示驱动若意外卡死会触发复位。
 */
void SysTick_Handler(void) {
    uint32_t now=++g_oled_ms;
    motor_zero();
    GPIO_WriteBit(GPIOB,GPIO_Pin_2,
        (now/(g_oled_fault==0u ? 500u : 100u))%2u!=0u ? Bit_SET : Bit_RESET);
}
/** @brief 异常先撤所有电机输入，再等IWDG复位；不在异常中调用显示或等待总线。 */
static void fatal_stop(void) {
    __disable_irq(); motor_zero();
    g_oled_state=2u; g_oled_stage=255u;
    for (;;) { }
}
void NMI_Handler(void) { fatal_stop(); }
void HardFault_Handler(void) { fatal_stop(); }
void MemManage_Handler(void) { fatal_stop(); }
void BusFault_Handler(void) { fatal_stop(); }
void UsageFault_Handler(void) { fatal_stop(); }

/** @brief 显示故障锁存后保留Watch和快闪，不反复重初始化屏幕或驱动电机。 */
static void diagnostic_stop(void) {
    g_oled_fault |= OLED_FAULT_READ;
    g_oled_stage=255u; g_oled_state=2u;
    for (;;) { motor_zero(); IWDG_ReloadCounter(); __WFI(); }
}
/** @brief 无动力测试入口；无参数，不返回。
 * 上电等200ms后，探测3C/3D，优先3C；初始化失败锁存错误。
 * 前约3.2秒依次白/黑/两个互补棋盘格，之后显示边框/引脚/地址/运行秒数。
 * 每个128字节页完成后喂狗，失败立即停止后续传输；不声称ACK等于肉眼显示正常。
 */
int main(void) {
    uint32_t phase,seconds,page,last_phase=0xffffffffu,last_seconds=0xffffffffu;
    motor_zero_init(); controls_init(); SystemCoreClockUpdate();
    g_oled_revision=0x02120001u; g_oled_stage=1u;
    if (SystemCoreClock!=16000000u) g_oled_fault|=OLED_FAULT_CLOCK;
    g_oled_fault|=watchdog_init();
    if (SysTick_Config(SystemCoreClock/1000u)!=0u) {
        g_oled_fault|=OLED_FAULT_SYSTICK; fatal_stop();
    }
    NVIC_SetPriority(SysTick_IRQn,0u);
    if (g_oled_fault!=0u) diagnostic_stop();
    while (g_oled_ms<200u) { IWDG_ReloadCounter(); __WFI(); }
    g_oled_stage=2u;
    if (!oled_i2c_init()) diagnostic_stop();
    g_oled_stage=3u;
    if (oled_i2c_probe(0x3cu)) g_oled_ack_mask|=1u;
    if (oled_i2c_probe(0x3du)) g_oled_ack_mask|=2u;
    if (g_oled_ack_mask==0u) diagnostic_stop();
    g_oled_address=(g_oled_ack_mask & 1u)!=0u ? 0x3cu : 0x3du;
    g_oled_stage=4u;
    if (!oled_ssd1306_init((uint8_t)g_oled_address)) diagnostic_stop();
    g_oled_state=1u;
    for (;;) {
        seconds=g_oled_ms/1000u;
        phase=(g_oled_ms-200u)/800u;
        if (phase>4u) phase=4u;
        if (phase!=last_phase || (phase==4u && seconds!=last_seconds)) {
            g_oled_stage=5u;
            oled_pattern_build(frame,phase,seconds,(uint8_t)g_oled_address);
            for (page=0u;page<8u;++page) {
                IWDG_ReloadCounter();
                if (!oled_i2c_page((uint8_t)g_oled_address,(uint8_t)page,&frame[page*128u]))
                    diagnostic_stop();
            }
            ++g_oled_frames; g_oled_phase=phase; g_oled_seconds=seconds;
            last_phase=phase; last_seconds=seconds;
            if (phase==4u) g_oled_stage=6u;
        }
        IWDG_ReloadCounter(); __WFI();
    }
}
