/* 仅MotorDirect电脑测试：复用GPIO寄存器模型，加普通GPIO置高声明。
 * 此目录不进Keil，不代表实际电压、驱动板或电机响应。
 */
#ifndef YEYE_TEST_MOTOR_DIRECT_STM32_H
#define YEYE_TEST_MOTOR_DIRECT_STM32_H
#include "../motor_bench_pwm/stm32f4xx.h"
void GPIO_SetBits(void *port, uint16_t pins);
#endif
