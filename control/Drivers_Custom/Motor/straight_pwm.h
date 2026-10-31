/** @file straight_pwm.h
 * @brief 独立StraightTest驱动；A/B是固定驱动桥名，不随物理命名自动变化。
 */
#ifndef YEYE_STRAIGHT_PWM_H
#define YEYE_STRAIGHT_PWM_H
#include <stdint.h>
/* 2026-10-30主控反馈：MotorPwm先转的A为左轮朝前，后转的B为右轮朝后。
 * 因而A沿用IN1 PWM，B改用IN2 PWM。此处不是编码器方向系数。
 * +1=IN1 PWM/IN2低；-1=IN1低/IN2 PWM；只在断动力后改配置并重新编译。
 */
#define STRAIGHT_BRIDGE_A_FORWARD 1
#define STRAIGHT_BRIDGE_B_FORWARD (-1)
/** @return 1=HSI16MHz及TIM1就绪；0=失败，四脚保持GPIO低。 */
int straight_pwm_init(void);
/** @brief 同时设置左右轮；left/right单位千分比，分别允许0..500。
 * 左轮固定对应A桥，右轮对应B桥；任一越界先同时停止并返回0。
 * 单轮0表示该桥PWM为0，两轮均0关闭MOE并将四脚切为GPIO低。
 * 运行时仅改变占空比，禁止带动力切换方向；返回1表示寄存器配置成功。
 */
int straight_pwm_apply(uint16_t left_duty, uint16_t right_duty);
/** @brief 关闭MOE、清四CCR、四脚GPIO低；00为滑行，机械停稳仍有惯性。 */
void straight_pwm_stop(void);
#endif
