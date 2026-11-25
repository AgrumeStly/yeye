/** @file corner_guide.h
 * @brief 首个直角弯的轮速目标生成；纯数学，不访问硬件。
 * 输入右正转向千分量、弯道风险千分量、真实采样间隔ms，输出左右RPM。
 * 近弯使用外入切弯圆弧的差速，内轮保持正转，禁止负目标及带电换向。
 */
#ifndef YEYE_CORNER_GUIDE_H
#define YEYE_CORNER_GUIDE_H
#include <stdint.h>
#ifdef JOINT_ANGLE_VOICE_TARGET
#define CORNER_CRUISE_MAX_RPM 100.0f
#else
#define CORNER_CRUISE_MAX_RPM 80.0f
#endif
typedef struct {
    float command_rpm; /* 平均目标RPM；满弯最高60RPM，过渡外轮最高112RPM。 */
    float correction;  /* 右正的差速比例，应用限制在-0.65..0.65。 */
} corner_guide_t;
/** @brief 停车／新趟清状态；无返回值，不保存上一趟转弯指令。 */
void corner_guide_reset(corner_guide_t *guide);
/** @brief 成功返回1；参数／状态非有限或越界时清状态／输出并返回0。
 * cruise允许40到本目标巡航上限RPM；steering=-1000..1000，bend=0..1000；dt_ms=1..60。
 * 直道最大差速12%，弯道逐步开放至65%；平均速度降至min(巡航,60RPM)。
 * 加速100RPM/s，减速240RPM/s；差速变化率直道0.6/s、弯道2/s。
 * 目标小于5RPM归零，避免内轮长期处于不能维持转动的极低速区。
 * 此函数没有角度／距离标定；不按固定时间盲转，视觉必须持续提供当前路径。
 */
int corner_guide_update(corner_guide_t *guide, float cruise, int16_t steering,
                        uint16_t bend, uint32_t dt_ms, float *left, float *right);
#endif
