/** @file speed_pi.h
 * @brief 轮速PI纯数学：RPM输入、千分比PWM输出，与STM32硬件无关。
 */
#ifndef YEYE_SPEED_PI_H
#define YEYE_SPEED_PI_H
#include <stdint.h>
typedef struct { float integral; } speed_pi_t;
typedef struct {
    float kp; /* permille/RPM */
    float ki; /* permille/(RPM*s) */
    float feedforward; /* permille，前进运动时固定前馈。 */
} speed_pi_config_t;
/** @brief 清积分，停机／故障／新启动都调用；pi非空，无返回值。 */
void speed_pi_reset(speed_pi_t *pi);
/** @brief 检查有限值及调试边界：kp0..10、ki0..20、前馈0..500，返回1有效。 */
int speed_pi_config_valid(const speed_pi_config_t *config);
/** @brief 更新PI；target/measured单位RPM，dt_ms为实际周期1..100ms。
 * 输出限制0..500，不生成倒车；条件积分防饱和，积分本身限制±500。
 * 参数／数值无效返回0并清积分；成功返回1，*duty为四舍五入的千分比。
 */
int speed_pi_update(speed_pi_t *pi, const speed_pi_config_t *config,
                    float target, float measured, uint32_t dt_ms, uint16_t *duty);
#endif
