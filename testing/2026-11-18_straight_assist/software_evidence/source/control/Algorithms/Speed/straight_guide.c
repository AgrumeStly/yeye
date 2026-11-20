/** @file straight_guide.c
 * @brief 让直道小误差不触发明显左右摆动，同时保持必要的缓慢纠偏。
 * 固定初值为开发候选，必须用真实横向偏移／摆动／用时验证，不能声称最优。
 */
#include "straight_guide.h"
static float absolute(float x) { return x < 0.0f ? -x : x; }
static float limit(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }
void straight_guide_reset(straight_guide_t *g) {
    g->command_rpm = g->filtered_error = g->correction = 0.0f;
    g->correcting = 0u;
}
int straight_guide_update(straight_guide_t *g, float cruise, int16_t error,
                          uint32_t dt_ms, float *left, float *right) {
    float dt, desired, step;
    *left = *right = 0.0f;
    if (!(cruise >= 40.0f && cruise <= 100.0f) || error < -1000 || error > 1000 ||
        dt_ms == 0u || dt_ms > 60u || !(g->command_rpm >= 0.0f && g->command_rpm <= 100.0f) ||
        !(g->filtered_error >= -1.0f && g->filtered_error <= 1.0f) ||
        !(g->correction >= -0.12f && g->correction <= 0.12f)) {
        straight_guide_reset(g); return 0;
    }
    dt = (float)dt_ms / 1000.0f;
    if (g->command_rpm == 0.0f) g->command_rpm = 40.0f;
    else g->command_rpm += limit(cruise - g->command_rpm, -100.0f * dt, 100.0f * dt);
    /* 一阶低通的系数随真实dt变化；死区只用于纠偏，不遮蔽应用的失线停车。 */
    g->filtered_error += ((float)error / 1000.0f - g->filtered_error) * (float)dt_ms / (80.0f + (float)dt_ms);
    if (absolute(g->filtered_error) >= 0.08f) g->correcting = 1u;
    else if (absolute(g->filtered_error) <= 0.04f) g->correcting = 0u;
    desired = g->correcting != 0u ?
        (g->filtered_error > 0.0f ? 1.0f : -1.0f) * 0.35f * (absolute(g->filtered_error) - 0.04f) : 0.0f;
    desired = limit(desired, -0.12f, 0.12f);
    step = 0.6f * dt;
    g->correction += limit(desired - g->correction, -step, step);
    g->correction = limit(g->correction, -0.12f, 0.12f);
    *left = g->command_rpm * (1.0f + g->correction);
    *right = g->command_rpm * (1.0f - g->correction);
    return 1;
}
