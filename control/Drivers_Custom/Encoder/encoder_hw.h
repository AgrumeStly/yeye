#ifndef YEYE_ENCODER_HW_H
#define YEYE_ENCODER_HW_H
#include <stdint.h>
typedef struct { uint16_t a, b; uint32_t pin_levels; } encoder_raw_t;
/** @brief 初始化TIM3 PC6/7与TIM4 PB6/7的编码器模式；返回1成功、0时钟不符。
 * 不配置TIM1、TIM5、UART、SWD，不产生电机驱动；调用前由入口先保持四电机输入低。
 */
int encoder_hw_init(void);
/** @brief 按顺序读取两路CNT和四输入电平；不是两定时器硬件同时锁存。
 * out必须非空；pin_levels bit0..3分别PC6、PC7、PB6、PB7。未就绪返回0，不填假数据。
 */
int encoder_hw_read(encoder_raw_t *out);
#endif
