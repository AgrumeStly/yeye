/** @file encoder_hw.c
 * @brief 双AB相硬件计数：TIM3/TIM4独占各自16位CNT，SPL V1.3.0。
 * TI12模式在两相的上升／下降沿计数（x4），Polarity_Rising在此选择不反相，
 * 不表示只计上升沿；不通过交换A/B或改极性预先猜测“车辆前进”。
 */
#include "encoder_hw.h"
#include "stm32f4xx.h"
static uint32_t ready;

/** @brief 配置一个16位计数器；timer仅允许本文件传入TIM3/TIM4。
 * PSC0、ARR65535、CKD1；IC1/2直连TI1/2、输入分频DIV1。
 * ICFilter=6对应fDTS/4、连续6次采样；当前16MHz名义时钟下约1.5us抗毛刺窗口，
 * 不是去机械抖动或最高速度保证，真实线束／脉宽仍须实测。不开中断／DMA，不需溢出ISR。
 */
static void configure(TIM_TypeDef *timer) {
    TIM_TimeBaseInitTypeDef base;
    TIM_ICInitTypeDef input;
    TIM_DeInit(timer);
    TIM_TimeBaseStructInit(&base);
    base.TIM_Prescaler = 0u;
    base.TIM_Period = 65535u;
    base.TIM_CounterMode = TIM_CounterMode_Up;
    base.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInit(timer, &base);
    TIM_EncoderInterfaceConfig(timer, TIM_EncoderMode_TI12,
                               TIM_ICPolarity_Rising, TIM_ICPolarity_Rising);
    TIM_ICStructInit(&input);
    input.TIM_ICPolarity = TIM_ICPolarity_Rising;
    input.TIM_ICSelection = TIM_ICSelection_DirectTI;
    input.TIM_ICPrescaler = TIM_ICPSC_DIV1;
    input.TIM_ICFilter = 6u;
    input.TIM_Channel = TIM_Channel_1;
    TIM_ICInit(timer, &input);
    input.TIM_Channel = TIM_Channel_2;
    TIM_ICInit(timer, &input);
    TIM_SetCounter(timer, 0u); /* 只在初始化清零；采样时绝不清CNT，避免边沿丢失。 */
    TIM_Cmd(timer, ENABLE);
}

int encoder_hw_init(void) {
    RCC_ClocksTypeDef clocks;
    GPIO_InitTypeDef input;
    ready = 0u;
    RCC_GetClocksFreq(&clocks);
    if (clocks.SYSCLK_Frequency != 16000000u || clocks.HCLK_Frequency != 16000000u ||
        clocks.PCLK1_Frequency != 16000000u || clocks.PCLK2_Frequency != 16000000u) return 0;
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB | RCC_AHB1Periph_GPIOC, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3 | RCC_APB1Periph_TIM4, ENABLE);
    GPIO_StructInit(&input);
    input.GPIO_Mode = GPIO_Mode_AF;
    input.GPIO_OType = GPIO_OType_PP;
    input.GPIO_Speed = GPIO_Speed_2MHz; /* 输入无输出频率意义，不是采样周期。 */
    /* MD310资料含上拉整形，采用3.3V供电；内部弱上拉只补确定的空闲态。
     * 无电时上拉也可能读高，禁止将IDR高或CNT不变当作编码器有电／正常的证明。
     */
    input.GPIO_PuPd = GPIO_PuPd_UP;
    input.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
    GPIO_Init(GPIOC, &input);
    GPIO_Init(GPIOB, &input);
    GPIO_PinAFConfig(GPIOC, GPIO_PinSource6, GPIO_AF_TIM3);
    GPIO_PinAFConfig(GPIOC, GPIO_PinSource7, GPIO_AF_TIM3);
    GPIO_PinAFConfig(GPIOB, GPIO_PinSource6, GPIO_AF_TIM4);
    GPIO_PinAFConfig(GPIOB, GPIO_PinSource7, GPIO_AF_TIM4);
    configure(TIM3);
    configure(TIM4);
    ready = 1u;
    return 1;
}

int encoder_hw_read(encoder_raw_t *out) {
    if (ready == 0u) return 0;
    out->a = (uint16_t)TIM_GetCounter(TIM3);
    out->b = (uint16_t)TIM_GetCounter(TIM4);
    out->pin_levels = (uint32_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_6) |
                     ((uint32_t)GPIO_ReadInputDataBit(GPIOC, GPIO_Pin_7) << 1) |
                     ((uint32_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_6) << 2) |
                     ((uint32_t)GPIO_ReadInputDataBit(GPIOB, GPIO_Pin_7) << 3);
    return 1;
}
