/** @file lap_motion.c
 * @brief 低速试跑应用策略。保留原SpeedMatch文件：只复用其两次人工单轮校准。
 * 校准结束后不让原共同目标／3秒策略参与巡航；左右独立PI仍用原数学模块。
 * 视觉偏差右正：右转时左轮更快、右轮减速，最大只前进不带电换向。
 */
#include "lap_motion.h"
#include <string.h>
#include <float.h>
#ifdef LAP_TRACK_TARGET
/* 只有GUI明确选择Track目标才默认允许最长5分钟；仍须逐轮悬空校准与人工启动。
 * 原LowSpeedLap目标继续3秒，避免断电后RAM设置丢失而无法识别实际运行期限。
 */
volatile lap_config_t g_lap_config = {40.0f, 300000u};
#else
volatile lap_config_t g_lap_config = {40.0f, 3000u};
#endif
volatile lap_view_t g_lap;
static speed_pi_t left_pi, right_pi;
static uint32_t state_at, raw_at, last_sample, quiet_ms, edge_at[2];
static uint32_t sequence_at[2];
static uint8_t raw_candidate, stable, seen[2], sequences[2], have_sample;
static float previous_target[2];
static float absf(float x) { return x < 0.0f ? -x : x; }
static int finitef(float x) { return x == x && x <= FLT_MAX && x >= -FLT_MAX; }
static void zero(void) {
    g_lap.left_pwm = g_lap.right_pwm = 0u;
    g_lap.left_target = g_lap.right_target = 0.0f;
    previous_target[0] = previous_target[1] = 0.0f;
    speed_pi_reset(&left_pi); speed_pi_reset(&right_pi);
}
void lap_motion_fault(lap_reason_t reason, uint32_t now) {
    if (g_lap.state != LAP_FAULT) g_lap.reason = reason;
    /* 连同复用校准器一起锁住，避免已撤驱动后仍保持CALIBRATING并累计计数。
     * 校准器自己的原始故障已存在时保留，新增策略原因以g_lap.reason为准。
     */
    if (g_speed_match.state != SPEED_FAULT) speed_match_fault(SPEED_ERROR_STATE, now);
    g_lap.state = LAP_FAULT; state_at = now; zero();
}
void lap_motion_init(uint32_t now) {
    lap_view_t empty;
    memset(&empty, 0, sizeof(empty)); g_lap = empty;
    g_lap.state = LAP_CALIBRATION;
    state_at = raw_at = last_sample = now; quiet_ms = 0u;
    raw_candidate = stable = have_sample = 0u;
    memset(seen, 0, sizeof(seen)); memset(sequences, 0, sizeof(sequences));
    memset(sequence_at, 0, sizeof(sequence_at));
    edge_at[0] = edge_at[1] = now;
    zero(); speed_match_init(now);
}
static int fresh(uint32_t now) {
    return g_lap.path_valid != 0u && (uint32_t)(now - g_lap.path_at) < (g_lap.history ? 120u : 200u);
}
static int16_t signed16(const uint8_t *p) {
    uint16_t value = (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
    return (int16_t)(value < 32768u ? (int32_t)value : (int32_t)value - 65536);
}
void lap_motion_receive(const uint8_t *b, uint32_t arrival, uint32_t now) {
    uint8_t type = b[3], index = (uint8_t)(type - 1u), delta;
    if (g_lap.state == LAP_RUNNING && !fresh(now)) lap_motion_fault(LAP_LINK, now);
    /* 停止优先于年龄／重复号；恢复图像和远程START均不能自行恢复车辆。 */
    if (type == 2u && b[16] == 2u) {
        if (g_lap.state == LAP_CALIBRATION) {
            /* 相机入口先发STOP时，静止校准待机只清除待启动手势／映射。
             * 正在单轮校准则锁故障，不能在STOP后继续剩余脉冲。
             */
            if (g_speed_match.state == SPEED_CALIBRATING) lap_motion_fault(LAP_KEY, now);
            else {
                /* 只能沿用上一真实采样时刻重置校准状态；UART可能在任意毫秒
                 * 到达，若用now重置，下一20ms编码器样本会因dt不一致误锁故障。
                 * 不重置原硬件计数／回绕算法，只撤消尚未执行的按键手势。
                 */
                speed_match_init(last_sample);
            }
            g_lap.path_valid = 0u; zero(); return;
        }
        if (g_lap.state != LAP_FAULT) { g_lap.state = LAP_STOPPED; g_lap.reason = LAP_KEY; }
        zero();
        /* 停止后清路径许可，必须收到新的当前双边再进行人工启动。 */
        g_lap.path_valid = 0u; return;
    }
    if ((uint32_t)(now - arrival) >= 100u) {
        ++g_lap.rejected;
        if (g_lap.state == LAP_RUNNING) lap_motion_fault(LAP_LINK, now);
        return;
    }
    if (seen[index] != 0u && (uint32_t)(arrival - sequence_at[index]) < 200u) {
        delta = (uint8_t)(b[5] - sequences[index]);
        if (delta == 0u || delta >= 128u) { ++g_lap.duplicates; return; }
    }
    seen[index] = 1u; sequences[index] = b[5]; sequence_at[index] = arrival;
    ++g_lap.received;
    if (type == 2u) { if (b[16] == 1u) ++g_lap.starts_rejected; return; }
    /* v2的offset10是采集软件边界到封包的年龄ms，非v1航向。
     * 再扣2ms名义占线时间，使200ms监督包含发送端已报告的图像年龄。
     */
    g_lap.path_at = arrival - (uint32_t)((uint16_t)b[10] | ((uint16_t)b[11] << 8)) - 2u;
    g_lap.steering = signed16(b + 8);
    g_lap.bend = (uint16_t)((uint16_t)b[12] | ((uint16_t)b[13] << 8));
    g_lap.history = (uint8_t)((b[6] & 4u) != 0u);
    g_lap.single = (uint8_t)((b[6] & 8u) != 0u);
    g_lap.path_valid = (uint8_t)((b[6] & 1u) != 0u && b[7] >= 40u && b[15] == 0u && b[14] <= 100u &&
                               (uint32_t)(now - g_lap.path_at) < (g_lap.history ? 120u : 200u));
    if (g_lap.state == LAP_RUNNING && g_lap.path_valid == 0u) lap_motion_fault(LAP_PATH, now);
}
void lap_motion_tick(uint32_t now, uint8_t key) {
    uint32_t held;
    key = key != 0u ? 1u : 0u;
    if (g_lap.state == LAP_CALIBRATION) {
        speed_match_tick(now, key);
        g_lap.left_pwm = g_speed_match.left_pwm; g_lap.right_pwm = g_speed_match.right_pwm;
        if (g_speed_match.state == SPEED_FAULT) lap_motion_fault(LAP_ENCODER, now);
        else if (g_speed_match.phase == 2u) {
            g_lap.state = LAP_WAIT; state_at = raw_at = now;
            raw_candidate = stable = 0u; zero();
        }
        return;
    }
    if (key != raw_candidate) { raw_candidate = key; raw_at = now; }
    if ((uint32_t)(now - raw_at) >= 30u) stable = key;
    if (g_lap.state == LAP_RUNNING) {
        if (key != 0u) { lap_motion_fault(LAP_KEY, now); return; }
        if (!fresh(now)) { lap_motion_fault(LAP_LINK, now); return; }
        if (!have_sample || (uint32_t)(now - last_sample) > 60u) { lap_motion_fault(LAP_ENCODER, now); return; }
        if ((uint32_t)(now - g_lap.run_since) >= g_lap.active.run_ms) {
            g_lap.state = LAP_STOPPED; g_lap.reason = LAP_LIMIT; state_at = now; zero();
        }
        return;
    }
    zero();
    if (g_lap.state == LAP_FAULT) return;
    if (g_lap.state == LAP_STOPPED) {
        /* 正常时限／远程STOP后需松键停稳再重新人工触发；故障必须复位。 */
        if (key == 0u && quiet_ms >= 500u) { g_lap.state = LAP_WAIT; state_at = now; }
    } else if (g_lap.state == LAP_WAIT) {
        if (key != 0u) {
            if ((uint32_t)(now - state_at) >= 1000u && quiet_ms >= 500u && stable != 0u) {
                g_lap.state = LAP_HOLD; state_at = now;
            }
        }
    } else if (g_lap.state == LAP_HOLD || g_lap.state == LAP_ARMED) {
        if (key == 0u && stable == 0u) {
            held = raw_at - state_at;
            if (g_lap.state == LAP_ARMED && held >= 1000u && held < 5000u) {
                lap_config_t config = g_lap_config;
                if (!fresh(now) || g_lap.history != 0u || g_lap.single != 0u || !have_sample || quiet_ms < 500u) {
                    ++g_lap.starts_rejected; g_lap.state = LAP_WAIT; state_at = now; return;
                }
                if (!finitef(config.straight_rpm) || config.straight_rpm < 10.0f || config.straight_rpm > 60.0f ||
                    config.run_ms < 500u || config.run_ms > 300000u) { lap_motion_fault(LAP_CONFIG, now); return; }
                g_lap.active = config; g_lap.state = LAP_RUNNING; g_lap.reason = LAP_OK;
                g_lap.run_since = now; edge_at[0] = edge_at[1] = now;
            } else { g_lap.state = LAP_WAIT; state_at = now; }
        } else if ((uint32_t)(now - state_at) >= 5000u) lap_motion_fault(LAP_KEY, now);
        else if (key != 0u && (uint32_t)(now - state_at) >= 1000u) g_lap.state = LAP_ARMED;
    }
}
void lap_motion_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b) {
    const encoder_sample_t *channels[2], *left, *right;
    float raw_left, raw_right, base, steer, targets[2];
    uint32_t dt = now - last_sample;
    uint16_t lp, rp;
    speed_pi_config_t pi = {2.0f, 4.0f, 300.0f};
    /* 原算法负责FIRST／标志／真实dt与校准；其phase2保持非运行状态，不参与目标计算。 */
    speed_match_sample(now, a, b);
    if (g_speed_match.state == SPEED_FAULT) { lap_motion_fault(LAP_ENCODER, now); return; }
    if (a->status == ENCODER_FIRST && b->status == ENCODER_FIRST) { last_sample = now; return; }
    if (dt == 0u || dt > 60u || !a->valid || !b->valid) { lap_motion_fault(LAP_ENCODER, now); return; }
    last_sample = now; have_sample = 1u;
    if (a->delta == 0 && b->delta == 0) { if (quiet_ms < 1000u) quiet_ms += dt; } else quiet_ms = 0u;
    if (g_lap.state == LAP_CALIBRATION) return;
    channels[0] = a; channels[1] = b;
    if (g_speed_match.left_channel < 1u || g_speed_match.left_channel > 2u ||
        g_speed_match.right_channel < 1u || g_speed_match.right_channel > 2u ||
        g_speed_match.left_channel == g_speed_match.right_channel) { lap_motion_fault(LAP_ENCODER, now); return; }
    left = channels[g_speed_match.left_channel - 1u]; right = channels[g_speed_match.right_channel - 1u];
    raw_left = (float)left->counts_per_s * (float)g_speed_match.left_sign * 60.0f / 1058.6f;
    raw_right = (float)right->counts_per_s * (float)g_speed_match.right_sign * 60.0f / 1060.8f;
    g_lap.left_rpm = g_speed_match.left_rpm; g_lap.right_rpm = g_speed_match.right_rpm;
    if (g_lap.state != LAP_RUNNING) return;
    if (absf(raw_left) > 600.0f || absf(raw_right) > 600.0f) { lap_motion_fault(LAP_OVERSPEED, now); return; }
    if (raw_left < -5.0f || raw_right < -5.0f) { lap_motion_fault(LAP_REVERSE, now); return; }
    if (!fresh(now)) { lap_motion_fault(LAP_LINK, now); return; }
    /* 右转时左外轮较快；大转向只把内轮降到0，不使用负RPM或反转。
     * base随弯道风险降至原值55%，每轮不超过60RPM／50%PWM。
     */
    steer = (float)g_lap.steering / 1000.0f;
    base = g_lap.active.straight_rpm * (1.0f - 0.45f * (float)g_lap.bend / 1000.0f);
    if (g_lap.history != 0u || g_lap.single != 0u) base *= 0.6f;
    targets[0] = base * (1.0f + steer); targets[1] = base * (1.0f - steer);
    if (targets[0] > 60.0f) targets[0] = 60.0f;
    if (targets[1] > 60.0f) targets[1] = 60.0f;
    if (targets[0] < 5.0f) targets[0] = 0.0f;
    if (targets[1] < 5.0f) targets[1] = 0.0f;
    if (left->delta != 0 || targets[0] == 0.0f || previous_target[0] == 0.0f) edge_at[0] = now;
    if (right->delta != 0 || targets[1] == 0.0f || previous_target[1] == 0.0f) edge_at[1] = now;
    previous_target[0] = targets[0]; previous_target[1] = targets[1];
    if ((uint32_t)(now - edge_at[0]) >= 300u || (uint32_t)(now - edge_at[1]) >= 300u) {
        lap_motion_fault(LAP_NO_FEEDBACK, now); return;
    }
    g_lap.left_target = targets[0]; g_lap.right_target = targets[1];
    /* 60RPM保留原30%参考前馈，低目标按比例缩小，避免慢速／内轮仍先给30%。
     * 这只是试跑初值，左右PI分别补偿真实电机差异，不能当电机标定曲线。
     */
    pi.feedforward = 300.0f * targets[0] / 60.0f;
    if (!speed_pi_update(&left_pi, &pi, targets[0], absf(g_lap.left_rpm), dt, &lp)) {
        lap_motion_fault(LAP_CONFIG, now); return;
    }
    pi.feedforward = 300.0f * targets[1] / 60.0f;
    if (!speed_pi_update(&right_pi, &pi, targets[1], absf(g_lap.right_rpm), dt, &rp)) {
        lap_motion_fault(LAP_CONFIG, now); return;
    }
    g_lap.left_pwm = lp; g_lap.right_pwm = rp;
}
uint8_t lap_motion_led(uint32_t now) {
    if (g_lap.state == LAP_CALIBRATION) return speed_match_led(now);
    if (g_lap.state == LAP_FAULT) return (uint8_t)((now / 100u) % 2u);
    if (g_lap.state == LAP_RUNNING || g_lap.state == LAP_ARMED) return 1u;
    return (uint8_t)((now % 2000u) < (fresh(now) && !g_lap.history && !g_lap.single ? 400u : 80u));
}
