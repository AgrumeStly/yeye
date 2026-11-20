/** @file corner_guide.c
 * @brief 直角弯减速与差速斜坡。20ms调用，左右独立编码器PI负责实际跟踪。
 * 参数为开发候选；控制边界通过模型检查，实际转弯半径与车体余量须实跑留证。
 */
#include "corner_guide.h"
static float clip(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }
void corner_guide_reset(corner_guide_t *g) { g->command_rpm = g->correction = 0.0f; }
int corner_guide_update(corner_guide_t *g, float cruise, int16_t steering,
                        uint16_t bend, uint32_t dt_ms, float *left, float *right) {
    float risk, dt, speed, desired, maximum, step;
    *left = *right = 0.0f;
    if (!(cruise >= 40.0f && cruise <= 80.0f) || steering < -1000 || steering > 1000 ||
        bend > 1000u || dt_ms == 0u || dt_ms > 60u ||
        !(g->command_rpm >= 0.0f && g->command_rpm <= 80.0f) ||
        !(g->correction >= -1.0f && g->correction <= 1.0f)) {
        corner_guide_reset(g); return 0;
    }
    dt = (float)dt_ms / 1000.0f; risk = (float)bend / 1000.0f;
    speed = cruise + (35.0f - cruise) * risk;
    if (g->command_rpm == 0.0f) g->command_rpm = 35.0f;
    g->command_rpm += clip(speed - g->command_rpm, -240.0f * dt, 80.0f * dt);
    maximum = 0.12f + 0.88f * risk;
    desired = (float)steering / 1000.0f;
    if (bend == 0u) {
        /* 直道继续抑制小抖动；大转向只有当前弯道证据才能取得。 */
        if (desired > -0.08f && desired < 0.08f) desired = 0.0f;
        else desired *= 0.35f;
    }
    desired = clip(desired, -maximum, maximum);
    step = (bend == 0u ? 0.6f : 3.0f) * dt;
    g->correction += clip(desired - g->correction, -step, step);
    /* 风险骤降时只沿斜坡回正，避免出弯两轮目标瞬间跳变。
     * 共同速度受当前差速反向约束，任一外轮始终不超过90RPM。
     */
    speed = g->command_rpm;
    if (speed * (1.0f + (g->correction < 0.0f ? -g->correction : g->correction)) > 90.0f)
        speed = 90.0f / (1.0f + (g->correction < 0.0f ? -g->correction : g->correction));
    *left = speed * (1.0f + g->correction); *right = speed * (1.0f - g->correction);
    if (*left < 5.0f) *left = 0.0f;
    if (*right < 5.0f) *right = 0.0f;
    return 1;
}
