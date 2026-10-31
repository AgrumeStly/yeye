/** @file speed_pi.c
 * @brief 不用D项，避免20ms计数差分噪声放大；实际增益需实车验收。
 */
#include "speed_pi.h"
#include <float.h>
static int finite_number(float x) { return x == x && x <= FLT_MAX && x >= -FLT_MAX; }
static float clamp(float x, float low, float high) { return x < low ? low : (x > high ? high : x); }
void speed_pi_reset(speed_pi_t *pi) { pi->integral = 0.0f; }
int speed_pi_config_valid(const speed_pi_config_t *c) {
    return finite_number(c->kp) && finite_number(c->ki) && finite_number(c->feedforward) &&
           c->kp >= 0.0f && c->kp <= 10.0f && c->ki >= 0.0f && c->ki <= 20.0f &&
           c->feedforward >= 0.0f && c->feedforward <= 500.0f;
}
int speed_pi_update(speed_pi_t *pi, const speed_pi_config_t *c,
                    float target, float measured, uint32_t dt_ms, uint16_t *duty) {
    float error, trial, output;
    *duty = 0u;
    if (!speed_pi_config_valid(c) || !finite_number(target) || !finite_number(measured) ||
        !finite_number(pi->integral) || target < 0.0f || target > 120.0f ||
        measured < 0.0f || measured > 600.0f || dt_ms == 0u || dt_ms > 100u) {
        speed_pi_reset(pi); return 0;
    }
    if (target == 0.0f) { speed_pi_reset(pi); return 1; }
    error = target - measured;
    trial = clamp(pi->integral + c->ki * error * ((float)dt_ms / 1000.0f), -500.0f, 500.0f);
    output = c->feedforward + c->kp * error + trial;
    /* 在饱和方向不再积累；误差反向时允许积分退出饱和。 */
    if (!((output > 500.0f && error > 0.0f) || (output < 0.0f && error < 0.0f)))
        pi->integral = trial;
    output = clamp(c->feedforward + c->kp * error + pi->integral, 0.0f, 500.0f);
    *duty = (uint16_t)(output + 0.5f);
    return 1;
}
