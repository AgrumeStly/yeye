/**
 * @file board_self_test.c
 * @brief 主控板首次上电测试：标准库点灯、内核滴答及小块RAM读写自检。
 *
 * 目标板为天空星STM32F407VET6。官方资料中的用户LED连接PB2，高电平点亮。
 * 本目标不初始化电机、编码器、视觉串口或USB应用，不输出电机控制信号。
 * Type-C用于供电和进入ROM DFU烧录；程序运行后不会提供USB串口。
 * 自检仅检查专用缓冲区，不代表已经覆盖整片RAM或全部外设。
 */
#include "board.h"
#include "stm32f4xx.h"

/* 可通过SWD的Watch读取这些变量；USB DFU本身不提供运行中调试。 */
volatile uint32_t g_self_test_failures;
volatile uint32_t g_self_test_heartbeat;
volatile uint32_t g_self_test_clock_hz;
volatile uint32_t g_self_test_ram_words;
static volatile uint32_t ram_probe[32];

/**
 * @brief 初始化PB2板载用户灯，先写入灭灯状态，再切换引脚为输出。
 * @param 无。
 * @return 无。
 * GPIO_Speed是输出驱动速度等级，不是LED闪烁频率；点灯选择低速即可。
 * 仅配置PB2，保持USB、SWD和其他排针的原状态。
 */
static void led_init(void) {
    GPIO_InitTypeDef gpio;
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);
    GPIO_ResetBits(GPIOB, GPIO_Pin_2);
    GPIO_StructInit(&gpio);
    gpio.GPIO_Pin = GPIO_Pin_2;
    gpio.GPIO_Mode = GPIO_Mode_OUT;
    gpio.GPIO_OType = GPIO_OType_PP;
    gpio.GPIO_Speed = GPIO_Speed_2MHz;
    gpio.GPIO_PuPd = GPIO_PuPd_NOPULL;
    GPIO_Init(GPIOB, &gpio);
}

/**
 * @brief 在专用128字节RAM缓冲区执行两种交替位图样与地址相关读写检查。
 * @param 无。
 * @return 无；失败次数累计到g_self_test_failures。
 * volatile强制实际读写内存，防止编译器将测试优化成常量结果。
 * 不测试堆栈、程序数据或整片RAM，避免破坏运行环境。
 */
static void ram_check(void) {
    uint32_t pass, index, pattern;
    for (pass = 0u; pass < 2u; ++pass) {
        pattern = pass == 0u ? 0xaaaaaaaaUL : 0x55555555UL;
        for (index = 0u; index < 32u; ++index) ram_probe[index] = pattern ^ index;
        for (index = 0u; index < 32u; ++index) {
            if (ram_probe[index] != (pattern ^ index)) ++g_self_test_failures;
        }
    }
    g_self_test_ram_words = 32u;
}

/**
 * @brief 标准库板级测试入口：通过LED节奏显示程序与SysTick正在运行。
 * @return 不返回，持续执行测试心跳。
 * 正常：亮200ms、灭200ms、亮200ms、灭1400ms，循环显示双闪。
 * 自检失败：每100ms翻转一次LED，表示快速持续闪烁。
 * 时间差使用无符号减法，能够处理毫秒计数回绕。
 */
int main(void) {
    static const uint32_t periods[4] = {200u, 200u, 200u, 1400u};
    uint32_t previous, now, stage = 0u, interval;
    board_init();
    led_init();
    g_self_test_clock_hz = SystemCoreClock;
    if (SystemCoreClock != 16000000u) ++g_self_test_failures;
    ram_check();
    previous = board_millis();
    GPIO_SetBits(GPIOB, GPIO_Pin_2);
    for (;;) {
        now = board_millis();
        interval = g_self_test_failures == 0u ? periods[stage] : 100u;
        if ((uint32_t)(now - previous) >= interval) {
            previous = now;
            stage = (stage + 1u) & 3u;
            ++g_self_test_heartbeat;
            GPIO_WriteBit(GPIOB, GPIO_Pin_2, (stage & 1u) == 0u ? Bit_SET : Bit_RESET);
        }
    }
}
