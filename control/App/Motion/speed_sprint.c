/** @file speed_sprint.c
 * @brief 在已验证的同速闭环外增加地面提速试验策略，不直接访问外设。
 * 编码器只能确认轮侧转速／轮程；地面不跑偏、无触边、能在弯前停稳由主控确认。
 * 每个目标需3次独立人工接受才记为best；没有自动连跑，也不宣称已找到绝对极速。
 */
#include "speed_sprint.h"
#include <string.h>
#include <float.h>
#ifndef SPEED_SPRINT_TARGET
#error speed_sprint.c must only be linked in the SpeedSprint profile
#endif
volatile speed_sprint_config_t g_sprint_config = {1500u, 67.5f, 1u};
volatile speed_sprint_view_t g_sprint;
volatile uint32_t g_sprint_review;
static uint8_t trial_active, have_accepted, have_best;
static uint32_t saturated_ms, peak_saturated_ms;
static speed_match_config_t accepted_control;
static speed_sprint_config_t accepted_extra;
static speed_match_config_t best_control;
static speed_sprint_config_t best_extra;
static uint32_t ui_press_since, display_since;
static uint8_t ui_press_eligible;

/** @brief 配置边界不是官方赛道保证；主控须依据可用直线和停车空间缩短距离。
 * 轮径20..200mm仅用于拒绝明显错误输入，默认值并非本车受载滚动周长标定。
 */
static int valid_config(const speed_sprint_config_t *c) {
    return c->distance_limit_mm >= 200u && c->distance_limit_mm <= 3000u &&
           c->wheel_diameter_mm == c->wheel_diameter_mm && c->wheel_diameter_mm <= FLT_MAX &&
           c->wheel_diameter_mm >= 20.0f && c->wheel_diameter_mm <= 200.0f && c->search_enabled <= 1u;
}

/** @brief 判断重复试验设置是否相同；防止更换PI、轮径／距离后继承旧的连续3次。
 * 浮点来自同一份启动快照，直接比较用于设置身份，不用于测量容差判定。
 */
static int same_context(const speed_match_config_t *c, const speed_sprint_config_t *e,
                        const speed_match_config_t *other, const speed_sprint_config_t *extra) {
    return c->pi.kp == other->pi.kp && c->pi.ki == other->pi.ki &&
           c->pi.feedforward == other->pi.feedforward && c->run_ms == other->run_ms &&
           e->distance_limit_mm == extra->distance_limit_mm && e->wheel_diameter_mm == extra->wheel_diameter_mm;
}
static int same_settings(const speed_match_config_t *c, const speed_sprint_config_t *e) {
    return have_accepted != 0u && c->target_rpm == accepted_control.target_rpm &&
           same_context(c, e, &accepted_control, &accepted_extra) && e->search_enabled == accepted_extra.search_enabled;
}

/** @brief 每次双轮结束只保存一次，故障永远不能被后来的待机0速覆盖为成功。
 * 未达标且最长持续饱和>=500ms标为饱和；其它未达标保留为窗口／调参待核。
 * 时间／距离限制下未验证，不等于电机已达到物理极限。
 */
static void capture_result(void) {
    float distance;
    if (trial_active == 0u || g_speed_match.state == SPEED_RUNNING) return;
    trial_active = 0u;
    ++g_sprint.result_id;
    g_sprint.last_target_rpm = g_speed_match.active.target_rpm;
    distance = g_sprint.left_distance_mm > g_sprint.right_distance_mm ?
               g_sprint.left_distance_mm : g_sprint.right_distance_mm;
    g_sprint.last_distance_mm = distance;
    g_sprint.last_saturated_ms = peak_saturated_ms;
    if (g_speed_match.state == SPEED_FAULT) {
        g_sprint.stop_reason = 3u; g_sprint.last_result = SPRINT_FAULTED;
    } else {
        if (g_sprint.stop_reason == 0u) g_sprint.stop_reason = 1u;
        g_sprint.last_result = g_speed_match.last_matched_ms >= 500u ? SPRINT_ENCODER_PASS :
                               (peak_saturated_ms >= 500u ? SPRINT_SATURATED : SPRINT_NOT_VERIFIED);
    }
    if (g_sprint.last_result != SPRINT_ENCODER_PASS) {
        g_sprint.accepted_runs = 0u; have_accepted = 0u;
        /* 已确认档位在当前条件下重新失效时，不再把更高旧值推荐为当前可用速度。 */
        if (g_sprint.last_target_rpm <= g_sprint.best_rpm) { g_sprint.best_rpm = 0.0f; have_best = 0u; }
    }
}

/** @brief 消费停机后的人工判定；接受只代表主控确认本轮地面现象。
 * 连续3次通过才建议下一档，建议本身不启动；到450上限后保持该档供重复验证。
 * 拒绝时退回已确认档或60RPM；若本轮不低于先前已确认值，则保留低档候选。
 */
static void consume_review(void) {
    uint32_t command = g_sprint_review;
    speed_match_config_t control;
    speed_sprint_config_t extra;
    float next;
    if (command == 0u) return;
    g_sprint_review = 0u; g_sprint.review_error = 0u;
    if (g_speed_match.state == SPEED_RUNNING || g_speed_match.state == SPEED_CALIBRATING ||
        g_speed_match.state == SPEED_HOLDING || g_speed_match.state == SPEED_ARMED ||
        g_speed_match.state == SPEED_SETTLING) {
        g_sprint.review_error = 1u; return;
    }
    if (g_speed_match.state == SPEED_FAULT) { g_sprint.review_error = 2u; return; }
    if (command == 3u) {
        control = g_speed_config; extra = g_sprint_config;
        /* 旧速度对应旧增益／距离／轮径，改设置后必须重新验证，不能直接套用。 */
        if (have_best != 0u && !same_context(&control, &extra, &best_control, &best_extra)) {
            g_sprint.best_rpm = 0.0f; have_best = 0u;
        }
        if (g_sprint.best_rpm < 10.0f) { g_sprint.review_error = 4u; return; }
        g_speed_config.target_rpm = g_sprint.best_rpm;
        g_sprint_config.search_enabled = 0u;
        g_sprint.accepted_runs = 0u; have_accepted = 0u; return;
    }
    if ((command != 1u && command != 2u) || g_sprint.result_id == 0u ||
        g_sprint.reviewed_id == g_sprint.result_id) {
        g_sprint.review_error = 2u; return;
    }
    g_sprint.reviewed_id = g_sprint.result_id;
    if (command == 2u) {
        g_sprint.accepted_runs = 0u; have_accepted = 0u;
        if (g_sprint.last_target_rpm <= g_sprint.best_rpm) { g_sprint.best_rpm = 0.0f; have_best = 0u; }
        g_speed_config.target_rpm = g_sprint.best_rpm >= 10.0f ? g_sprint.best_rpm : 60.0f;
        return;
    }
    if (g_sprint.last_result != SPRINT_ENCODER_PASS) { g_sprint.review_error = 3u; return; }
    control = g_speed_match.active; extra = g_sprint.active;
    if (!same_settings(&control, &extra)) g_sprint.accepted_runs = 0u;
    accepted_control = control; accepted_extra = extra; have_accepted = 1u;
    if (g_sprint.accepted_runs < 3u) ++g_sprint.accepted_runs;
    if (g_sprint.accepted_runs < 3u) return;
    if (control.target_rpm > g_sprint.best_rpm) {
        g_sprint.best_rpm = control.target_rpm;
        best_control = control; best_extra = extra; have_best = 1u;
    }
    if (extra.search_enabled == 0u) return;
    next = control.target_rpm + 20.0f;
    if (next > SPEED_PI_MAX_TARGET_RPM) next = SPEED_PI_MAX_TARGET_RPM;
    g_speed_config.target_rpm = next;
}

void speed_sprint_init(uint32_t now) {
    speed_sprint_view_t empty;
    memset(&empty, 0, sizeof(empty)); g_sprint = empty;
    g_sprint_review = 0u; trial_active = have_accepted = have_best = 0u;
    saturated_ms = peak_saturated_ms = 0u;
    ui_press_since = display_since = now; ui_press_eligible = 0u;
    speed_match_init(now);
    g_sprint.next_rpm = g_speed_config.target_rpm;
}

void speed_sprint_tick(uint32_t now, uint8_t raw_key) {
    speed_sprint_config_t extra = g_sprint_config;
    speed_match_state_t before = g_speed_match.state;
    uint32_t held = now - ui_press_since;
    uint8_t finish_search = 0u;
    capture_result();
    if (g_sprint_review != 0u) display_since = now;
    consume_review();
    /* 三秒松键代表结束升档，必须在原状态机将松键解释为启动之前取消ARMED。
     * 仅接受从双轮待机开始的按压；校准和运动时不重定义KEY，5秒卡键仍锁故障。
     * 首次松开使用原始电平抢先取消启动，即使有回弹也只能延迟待机，不能误起跑。
     */
    if (ui_press_eligible != 0u && raw_key == 0u && held >= 2500u && held < 5000u &&
        (before == SPEED_HOLDING || before == SPEED_ARMED)) {
        speed_match_cancel_start(now); ui_press_eligible = 0u; finish_search = 1u;
    }
    /* 只在双轮启动前锁定额外配置；校准保持原50%／500ms，不受距离参数影响。 */
    if (g_speed_match.phase == 2u && g_speed_match.state == SPEED_ARMED && raw_key == 0u) {
        if (!valid_config(&extra)) speed_match_fault(SPEED_ERROR_CONFIG, now);
        else g_sprint.active = extra;
    }
    speed_match_tick(now, raw_key);
    if (before == SPEED_READY && g_speed_match.state == SPEED_HOLDING) {
        ui_press_since = now;
        ui_press_eligible = g_speed_match.phase == 2u ? 1u : 0u;
    }
    if (finish_search != 0u) {
        /* 新结果尚未接受时先拒绝，防止把一次跑偏计入最高档；再选用已确认较低档。
         * 无best时保持60RPM搜索并报命令4，避免宣称一个从未地面确认的速度已通过。
         */
        if (g_sprint.result_id != 0u && g_sprint.result_id != g_sprint.reviewed_id) {
            g_sprint_review = 2u; consume_review();
        }
        if (g_sprint.best_rpm >= 10.0f) { g_sprint_review = 3u; consume_review(); }
        else {
            g_speed_config.target_rpm = 60.0f; g_sprint_config.search_enabled = 1u;
            g_sprint.accepted_runs = 0u; have_accepted = 0u; g_sprint.review_error = 4u;
        }
        display_since = now;
    } else if (ui_press_eligible != 0u && g_speed_match.state == SPEED_WAIT_RELEASE &&
               (before == SPEED_HOLDING || before == SPEED_ARMED)) {
        /* 短按必须通过原30ms消抖并真正进入过HOLDING；30ms以内毛刺不会形成确认。
         * 只写一次原有审查入口，因此重复确认、未达标或故障同样不能绕过。
         */
        if (held >= 100u && held <= 600u) { g_sprint_review = 1u; consume_review(); display_since = now; }
        ui_press_eligible = 0u;
    }
    if (g_speed_match.state == SPEED_RUNNING && trial_active == 0u) {
        speed_match_config_t control = g_speed_match.active;
        extra = g_sprint.active;
        if (!same_settings(&control, &extra) || g_sprint.result_id != g_sprint.reviewed_id) {
            g_sprint.accepted_runs = 0u; have_accepted = 0u;
        }
        /* 未确认上一轮就再次启动，不把该轮跳过后仍拼出“连续3次地面通过”。 */
        if (g_sprint.result_id != g_sprint.reviewed_id && g_sprint.last_target_rpm <= g_sprint.best_rpm) {
            g_sprint.best_rpm = 0.0f; have_best = 0u;
        }
        if (have_best != 0u && !same_context(&control, &extra, &best_control, &best_extra)) {
            g_sprint.best_rpm = 0.0f; have_best = 0u;
        }
        trial_active = 1u;
        g_sprint.stop_reason = 0u;
        g_sprint.left_distance_mm = g_sprint.right_distance_mm = 0.0f;
        g_sprint.mismatch_ms = 0u;
        saturated_ms = peak_saturated_ms = 0u;
        ui_press_eligible = 0u; g_sprint.review_error = 0u;
    }
    capture_result();
    g_sprint.next_rpm = g_speed_config.target_rpm;
    if (g_speed_match.state == SPEED_FAULT) ui_press_eligible = 0u;
    if (g_speed_match.state == SPEED_READY && before != SPEED_READY) display_since = now;
}

void speed_sprint_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b) {
    const encoder_sample_t *channels[2];
    const encoder_sample_t *left, *right;
    float left_counts, right_counts, circumference;
    speed_match_sample(now, a, b);
    if (trial_active == 0u || g_speed_match.state != SPEED_RUNNING) return;
    if (g_speed_match.left_channel < 1u || g_speed_match.left_channel > 2u ||
        g_speed_match.right_channel < 1u || g_speed_match.right_channel > 2u ||
        g_speed_match.left_channel == g_speed_match.right_channel ||
        (g_speed_match.left_sign != 1 && g_speed_match.left_sign != -1) ||
        (g_speed_match.right_sign != 1 && g_speed_match.right_sign != -1)) {
        speed_sprint_fault(SPEED_ERROR_MAPPING, now); return;
    }
    channels[0] = a; channels[1] = b;
    left = channels[g_speed_match.left_channel - 1u];
    right = channels[g_speed_match.right_channel - 1u];
    left_counts = (float)left->delta * (float)g_speed_match.left_sign;
    right_counts = (float)right->delta * (float)g_speed_match.right_sign;
    circumference = 3.14159265358979323846f * g_sprint.active.wheel_diameter_mm;
    /* 小反向抖动不抵消已累计的前进轮程，使距离限停偏向提前而不是延后。
     * 两轮取较大轮程；打滑或编码器误差仍可能使车体真实位移不同。
     */
    if (left_counts > 0.0f) g_sprint.left_distance_mm += left_counts * circumference / 1058.6f;
    if (right_counts > 0.0f) g_sprint.right_distance_mm += right_counts * circumference / 1060.8f;
    if (g_speed_match.command_rpm == g_speed_match.active.target_rpm &&
        ((g_speed_match.left_saturated != 0u && g_speed_match.left_rpm < g_speed_match.active.target_rpm - 5.0f) ||
         (g_speed_match.right_saturated != 0u && g_speed_match.right_rpm < g_speed_match.active.target_rpm - 5.0f))) {
        saturated_ms += left->dt_ms;
        if (saturated_ms > peak_saturated_ms) peak_saturated_ms = saturated_ms;
    } else saturated_ms = 0u;
    /* 起步500ms后，明显轮速分离不能继续维持到3秒结束，斜坡中也监督。
     * 20RPM／200ms是队内试验保护阈值，不是车道偏移检测，也不保证不会触边。
     * 允许初始短暂动态差；KEY、反向、无反馈等原停止监督始终有效，不等500ms。
     */
    if ((uint32_t)(now - g_speed_match.run_since) >= 500u &&
        (g_speed_match.difference_rpm > 20.0f || g_speed_match.difference_rpm < -20.0f)) {
        g_sprint.mismatch_ms += left->dt_ms;
        if (g_sprint.mismatch_ms >= 200u) { speed_sprint_fault(SPEED_ERROR_SYNC, now); return; }
    } else g_sprint.mismatch_ms = 0u;
    if (g_sprint.left_distance_mm >= (float)g_sprint.active.distance_limit_mm ||
        g_sprint.right_distance_mm >= (float)g_sprint.active.distance_limit_mm) {
        g_sprint.stop_reason = 2u;
        speed_match_finish(now);
    }
    capture_result();
}

void speed_sprint_fault(speed_match_error_t error, uint32_t now) {
    speed_match_fault(error, now); capture_result();
}

/** @brief 一个十进制数字的显示长度，单位ms；额外800ms灭灯分隔相邻数字。 */
static uint32_t digit_length(uint32_t digit) { return (digit == 0u ? 600u : digit * 200u) + 800u; }

uint8_t speed_sprint_led(uint32_t now) {
    uint32_t status, value, digits[3], frame_ms, phase, i, length;
    float rpm = g_sprint.next_rpm;
    if (ui_press_eligible != 0u && (uint32_t)(now - ui_press_since) >= 2500u &&
        (g_speed_match.state == SPEED_HOLDING || g_speed_match.state == SPEED_ARMED))
        return (uint8_t)((now / 100u) % 2u); /* 三秒手势提示：松开只结束升档，不会启动。 */
    if (g_speed_match.phase != 2u || g_speed_match.state != SPEED_READY) return speed_match_led(now);
    if (g_sprint.review_error != 0u) {
        status = 5u; if (g_sprint.review_error == 4u) rpm = 0.0f;
    } else if (g_sprint.result_id != g_sprint.reviewed_id) {
        status = g_sprint.last_result == SPRINT_ENCODER_PASS ? 2u : 4u;
    } else status = g_sprint_config.search_enabled == 0u ? 3u : 1u;
    /* 防止Watch输入NaN／越界后浮点到整数转换无定义；真正启动仍由配置检查拒绝。 */
    value = rpm >= 0.0f && rpm <= SPEED_PI_MAX_TARGET_RPM ? (uint32_t)(rpm + 0.5f) : 0u;
    digits[0] = value / 100u; digits[1] = value / 10u % 10u; digits[2] = value % 10u;
    frame_ms = status * 300u + 1000u;
    for (i = 0u; i < 3u; ++i) frame_ms += digit_length(digits[i]);
    frame_ms += 1000u; /* 一帧末尾再留1秒灭灯，报数循环不影响任何运动控制。 */
    phase = (now - display_since) % frame_ms;
    length = status * 300u + 1000u;
    if (phase < length) return (uint8_t)(phase < status * 300u && phase % 300u < 100u);
    phase -= length;
    for (i = 0u; i < 3u; ++i) {
        length = digit_length(digits[i]);
        if (phase < length) return (uint8_t)(digits[i] == 0u ? phase < 600u :
                                           (phase < digits[i] * 200u && phase % 200u < 100u));
        phase -= length;
    }
    return 0u;
}
