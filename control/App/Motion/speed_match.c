/** @file speed_match.c
 * @brief 双轮同速策略与台架安全监督；不直接访问GPIO、TIM或看门狗。
 * 通道配对由两次人工单轮500ms、50%输出识别，未成功前禁止双轮闭环。
 * CPR跟随当前物理轮组：左1058.6、右1060.8，来自旧5圈手转参考，非新实测。
 */
#include "speed_match.h"
#include <string.h>
#include <float.h>
/* 调试初值：共同目标60RPM，Kp=2千分比/RPM，Ki=4千分比/(RPM*s)，前馈30%。
 * 这些不是实车标定结果；停车时可用Keil Watch修改，下次KEY启动时统一锁定。
 * 前馈用于抵消常见静摩擦／基础驱动需求，左右PI分别修正动力差；不含D项。
 */
volatile speed_match_config_t g_speed_config = {60.0f, {2.0f, 4.0f, 300.0f}, 3000u};
volatile speed_match_view_t g_speed_match;
static speed_pi_t left_pi, right_pi;
static uint32_t state_since, raw_since, sample_since, quiet_ms;
static uint32_t last_edge[2];
static uint8_t candidate, stable, have_sample;
static int32_t cal_sum[2];
static uint32_t cal_abs[2];
static float magnitude(float x) { return x < 0.0f ? -x : x; }
static int finite_number(float x) { return x == x && x <= FLT_MAX && x >= -FLT_MAX; }
static int moving(void) { return g_speed_match.state == SPEED_RUNNING || g_speed_match.state == SPEED_CALIBRATING; }

/** @brief 撤驱动前保留最后一帧，便于3秒结束后仍可比较两轮转速。
 * 只记录闭环运行，不把校准／待机时的零速覆盖为“同速达标”。
 * Watch分项读取不是原子快照；应在停止后读取这些last字段作为同次结束事件。
 */
static void save_run_result(void) {
    if (g_speed_match.state != SPEED_RUNNING) return;
    g_speed_match.last_left_rpm = g_speed_match.left_rpm;
    g_speed_match.last_right_rpm = g_speed_match.right_rpm;
    g_speed_match.last_difference_rpm = g_speed_match.difference_rpm;
    g_speed_match.last_left_pwm = g_speed_match.left_pwm;
    g_speed_match.last_right_pwm = g_speed_match.right_pwm;
    g_speed_match.last_matched_ms = g_speed_match.matched_ms;
}

/** @brief 所有结束路径清PWM和积分，保留测量、开始时刻及结果供Watch读取。 */
static void zero_output(void) {
    g_speed_match.left_pwm = g_speed_match.right_pwm = 0u;
    g_speed_match.left_saturated = g_speed_match.right_saturated = 0u;
    speed_pi_reset(&left_pi); speed_pi_reset(&right_pi);
}
void speed_match_fault(speed_match_error_t error, uint32_t now) {
    if (g_speed_match.state != SPEED_FAULT) {
        g_speed_match.error = error; g_speed_match.stop_ms = now;
        save_run_result();
    }
    zero_output(); g_speed_match.state = SPEED_FAULT;
}
void speed_match_init(uint32_t now) {
    speed_match_view_t empty;
    memset(&empty, 0, sizeof(empty));
    g_speed_match = empty;
    g_speed_match.state = SPEED_WAIT_RELEASE;
    state_since = raw_since = sample_since = now;
    last_edge[0] = last_edge[1] = now;
    candidate = stable = have_sample = 0u;
    quiet_ms = 0u;
    memset(cal_sum, 0, sizeof(cal_sum)); memset(cal_abs, 0, sizeof(cal_abs));
    zero_output();
}

/** @brief 校准时仅一个编码器通道应有脉冲；至少20 counts且另一通道≤3。
 * 净变化须≥总变化90%，拒绝明显往复／噪声；这些是队内诊断阈值，不是官方规则。
 * 输出方向已由此前主控确认，本函数识别反馈符号，不能证明轮子实际朝车头。
 */
static int finish_calibration(void) {
    unsigned selected;
    int32_t sign;
    if (cal_abs[0] >= 20u && cal_abs[1] <= 3u) selected = 0u;
    else if (cal_abs[1] >= 20u && cal_abs[0] <= 3u) selected = 1u;
    else return 0;
    if ((uint32_t)(cal_sum[selected] < 0 ? -cal_sum[selected] : cal_sum[selected]) * 10u < cal_abs[selected] * 9u)
        return 0;
    sign = cal_sum[selected] > 0 ? 1 : -1;
    if (g_speed_match.phase == 0u) {
        g_speed_match.left_channel = selected + 1u; g_speed_match.left_sign = sign;
    } else {
        if (g_speed_match.left_channel == selected + 1u) return 0;
        g_speed_match.right_channel = selected + 1u; g_speed_match.right_sign = sign;
    }
    return 1;
}

/** @brief 启动只在长按后松开分支发生；样本新鲜、停稳、配置有效才接受。
 * 第0/1阶段固定单轮500ms；第2阶段用Watch配置但锁定时限500..3000ms。
 */
static void start_run(uint32_t now) {
    speed_match_config_t config = g_speed_config;
    if (have_sample == 0u || (uint32_t)(now - sample_since) > 60u || quiet_ms < 500u) {
        speed_match_fault(SPEED_ERROR_SAMPLE, now); return;
    }
    zero_output();
    g_speed_match.run_since = now; g_speed_match.matched_ms = 0u;
    last_edge[0] = last_edge[1] = now;
    if (g_speed_match.phase < 2u) {
        memset(cal_sum, 0, sizeof(cal_sum)); memset(cal_abs, 0, sizeof(cal_abs));
        g_speed_match.state = SPEED_CALIBRATING;
        g_speed_match.left_pwm = g_speed_match.phase == 0u ? 500u : 0u;
        g_speed_match.right_pwm = g_speed_match.phase == 1u ? 500u : 0u;
        return;
    }
    if (g_speed_match.left_channel == 0u || g_speed_match.right_channel == 0u ||
        g_speed_match.left_channel == g_speed_match.right_channel) {
        speed_match_fault(SPEED_ERROR_MAPPING, now); return;
    }
    if (!finite_number(config.target_rpm) || config.target_rpm < 10.0f || config.target_rpm > 120.0f ||
        !speed_pi_config_valid(&config.pi) || config.run_ms < 500u || config.run_ms > 3000u) {
        speed_match_fault(SPEED_ERROR_CONFIG, now); return;
    }
    g_speed_match.active = config;
    g_speed_match.state = SPEED_RUNNING;
    ++g_speed_match.runs;
    /* 起步只使用已停止时测得的速度，初始PWM仍受0..500限制。 */
    {
        uint16_t left, right;
        if (!speed_pi_update(&left_pi, &config.pi, config.target_rpm, magnitude(g_speed_match.left_rpm), 20u, &left) ||
            !speed_pi_update(&right_pi, &config.pi, config.target_rpm, magnitude(g_speed_match.right_rpm), 20u, &right)) {
            speed_match_fault(SPEED_ERROR_CONFIG, now); return;
        }
        g_speed_match.left_pwm = left; g_speed_match.right_pwm = right;
    }
}

void speed_match_tick(uint32_t now, uint8_t raw_key) {
    uint32_t held;
    raw_key = raw_key != 0u ? 1u : 0u;
    if (raw_key != candidate) { candidate = raw_key; raw_since = now; }
    if ((uint32_t)(now - raw_since) >= 30u) stable = raw_key;
    if (moving()) {
        /* 原始KEY优先，停止不等消抖；运行中target=0是额外停止请求。
         * 其它参数变更只在下次人工启动采纳，绝不能中途延长本次时限。 */
        if (raw_key != 0u || (g_speed_match.state == SPEED_RUNNING && g_speed_config.target_rpm == 0.0f)) {
            speed_match_fault(SPEED_ERROR_KEY, now); return;
        }
        if ((uint32_t)(now - sample_since) > 60u) { speed_match_fault(SPEED_ERROR_TIMING, now); return; }
        if ((uint32_t)(now - g_speed_match.run_since) >=
            (g_speed_match.state == SPEED_CALIBRATING ? 500u : g_speed_match.active.run_ms)) {
            if (g_speed_match.state == SPEED_CALIBRATING) {
                if (!finish_calibration()) { speed_match_fault(SPEED_ERROR_MAPPING, now); return; }
                ++g_speed_match.phase;
            }
            g_speed_match.stop_ms = now;
            save_run_result();
            zero_output(); quiet_ms = 0u;
            g_speed_match.state = SPEED_SETTLING; state_since = now;
        }
        return;
    }
    switch (g_speed_match.state) {
    case SPEED_WAIT_RELEASE:
        if (raw_key != 0u) state_since = now;
        else if ((uint32_t)(now - state_since) >= 1000u && stable == 0u && quiet_ms >= 500u)
            g_speed_match.state = SPEED_READY;
        break;
    case SPEED_READY:
        if (stable != 0u) { g_speed_match.state = SPEED_HOLDING; state_since = now; }
        break;
    case SPEED_HOLDING:
    case SPEED_ARMED:
        if (stable == 0u) {
            held = raw_since - state_since;
            if (g_speed_match.state == SPEED_ARMED && held >= 1000u && held < 5000u) start_run(now);
            else { g_speed_match.state = SPEED_WAIT_RELEASE; state_since = now; }
        } else if ((uint32_t)(now - state_since) >= 5000u) speed_match_fault(SPEED_ERROR_STUCK_KEY, now);
        else if (raw_key != 0u && (uint32_t)(now - state_since) >= 1000u) g_speed_match.state = SPEED_ARMED;
        break;
    case SPEED_SETTLING:
        if (quiet_ms >= 500u) { g_speed_match.state = SPEED_WAIT_RELEASE; state_since = now; }
        break;
    case SPEED_FAULT: zero_output(); break;
    default: speed_match_fault(SPEED_ERROR_STATE, now); break;
    }
}

void speed_match_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b) {
    const encoder_sample_t *channels[2];
    const encoder_sample_t *left, *right;
    float left_raw, right_raw;
    uint32_t dt = now - sample_since;
    channels[0] = a; channels[1] = b;
    if (have_sample == 0u && a->status == ENCODER_FIRST && b->status == ENCODER_FIRST) {
        sample_since = now; return;
    }
    if (dt == 0u || dt > 60u || !a->valid || !b->valid || a->status != ENCODER_OK || b->status != ENCODER_OK ||
        a->flags != 0u || b->flags != 0u || a->dt_ms != dt || b->dt_ms != dt) {
        speed_match_fault(SPEED_ERROR_SAMPLE, now); return;
    }
    sample_since = now; have_sample = 1u;
    g_speed_match.sample_ms = now; ++g_speed_match.sample_count;
    if (a->delta == 0 && b->delta == 0) { if (quiet_ms < 1000u) quiet_ms += dt; }
    else quiet_ms = 0u;
    if (g_speed_match.state == SPEED_CALIBRATING) {
        unsigned i;
        for (i = 0u; i < 2u; ++i) {
            int32_t d = channels[i]->delta;
            cal_sum[i] += d; cal_abs[i] += (uint32_t)(d < 0 ? -d : d);
        }
    }
    if (g_speed_match.left_channel == 0u || g_speed_match.right_channel == 0u) return;
    if (g_speed_match.left_channel > 2u || g_speed_match.right_channel > 2u ||
        g_speed_match.left_channel == g_speed_match.right_channel) {
        speed_match_fault(SPEED_ERROR_MAPPING, now); return;
    }
    left = channels[g_speed_match.left_channel - 1u];
    right = channels[g_speed_match.right_channel - 1u];
    /* counts/s由原算法使用真实dt得到；CPR随物理轮组，不随软件a/b换位。 */
    left_raw = (float)left->counts_per_s * (float)g_speed_match.left_sign * 60.0f / 1058.6f;
    right_raw = (float)right->counts_per_s * (float)g_speed_match.right_sign * 60.0f / 1060.8f;
    if (g_speed_match.state == SPEED_RUNNING && (magnitude(left_raw) > 600.0f || magnitude(right_raw) > 600.0f)) {
        speed_match_fault(SPEED_ERROR_OVERSPEED, now); return;
    }
    if (g_speed_match.state == SPEED_RUNNING && (left_raw < -5.0f || right_raw < -5.0f)) {
        speed_match_fault(SPEED_ERROR_REVERSE, now); return;
    }
    /* 一阶低通alpha=1/4，20ms采样时减少量化抖动，响应有约数十ms延迟。 */
    g_speed_match.left_rpm += (left_raw - g_speed_match.left_rpm) * 0.25f;
    g_speed_match.right_rpm += (right_raw - g_speed_match.right_rpm) * 0.25f;
    g_speed_match.difference_rpm = g_speed_match.left_rpm - g_speed_match.right_rpm;
    if (g_speed_match.state != SPEED_RUNNING) return;
    if (left->delta != 0) last_edge[0] = now;
    if (right->delta != 0) last_edge[1] = now;
    if ((uint32_t)(now - last_edge[0]) >= 300u || (uint32_t)(now - last_edge[1]) >= 300u) {
        speed_match_fault(SPEED_ERROR_NO_FEEDBACK, now); return;
    }
    {
        uint16_t l, r;
        speed_match_config_t config = g_speed_match.active;
        if (!speed_pi_update(&left_pi, &config.pi, config.target_rpm, magnitude(g_speed_match.left_rpm), dt, &l) ||
            !speed_pi_update(&right_pi, &config.pi, config.target_rpm, magnitude(g_speed_match.right_rpm), dt, &r)) {
            speed_match_fault(SPEED_ERROR_CONFIG, now); return;
        }
        g_speed_match.left_pwm = l; g_speed_match.right_pwm = r;
        g_speed_match.left_saturated = l == 500u ? 1u : 0u;
        g_speed_match.right_saturated = r == 500u ? 1u : 0u;
        if (magnitude(g_speed_match.difference_rpm) <= 5.0f &&
            magnitude(g_speed_match.left_rpm - config.target_rpm) <= 5.0f &&
            magnitude(g_speed_match.right_rpm - config.target_rpm) <= 5.0f)
            g_speed_match.matched_ms += dt;
        else g_speed_match.matched_ms = 0u;
    }
}
uint8_t speed_match_led(uint32_t now) {
    uint32_t phase;
    if (g_speed_match.state == SPEED_FAULT) return (uint8_t)((now / 100u) % 2u);
    if (moving() || g_speed_match.state == SPEED_ARMED) return 1u;
    if (g_speed_match.state == SPEED_HOLDING) return (uint8_t)((now / 100u) % 2u);
    if (g_speed_match.state == SPEED_READY) {
        phase = now % 2500u;
        return (uint8_t)(phase / 300u <= g_speed_match.phase && phase % 300u < 100u);
    }
    return 0u;
}
