/** @file straight_guide.h
 * @brief 直道轮速目标生成：与外设无关，不直接输出PWM。
 * 编码器PI负责跟踪这里的左右目标；视觉误差只改变小比例差速。
 */
#ifndef YEYE_STRAIGHT_GUIDE_H
#define YEYE_STRAIGHT_GUIDE_H
#include <stdint.h>
typedef struct {
    float command_rpm;       /* 共同速度RPM，从40RPM向巡航目标爬升。 */
    float filtered_error;    /* 视觉组合误差，归一化-1..1，右正。 */
    float correction;        /* 左加／右减的比例，绝对值不超过0.12。 */
    uint8_t correcting;     /* 滞回状态：0.08进入，0.04退出。 */
} straight_guide_t;
/** @brief 清除上一趟误差与差速；新人工启动后的第一样本从40RPM开始。 */
void straight_guide_reset(straight_guide_t *guide);
/** @brief 生成左右RPM目标，成功返回1；无效参数返回0并清状态／输出。
 * cruise单位RPM，范围40..100；error为视觉有符号千分量-1000..1000；
 * dt_ms必须1..60ms，与真实编码器窗口相同。输出不含轮径物理标定。
 * 共同速度斜率100RPM/s，误差低通80ms，差速比例变化不超过0.6/s。
 * 左右始终前进，最低35.2RPM、最高112RPM；近边界／失线停车由应用监督。
 */
int straight_guide_update(straight_guide_t *guide, float cruise, int16_t error,
                          uint32_t dt_ms, float *left, float *right);
#endif
