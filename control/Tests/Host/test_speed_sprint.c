/* 真实计数／PI／校准状态机与试验策略；机械响应仅是测试模型，不是实车极速证据。 */
#include "speed_sprint.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
static encoder_counter_t a, b;
static uint16_t raw_a, raw_b;
static uint32_t now, last_sample;
static int wiring, mode;
static float left_speed, right_speed, fraction_a, fraction_b;
static float left_gain, right_gain;
static float absf(float x) { return x < 0.0f ? -x : x; }
static void init(uint32_t initial, int reverse) {
    now = last_sample = initial; raw_a = raw_b = 0u; wiring = reverse; mode = 0;
    left_speed = right_speed = fraction_a = fraction_b = 0.0f;
    left_gain = 0.25f; right_gain = 0.32f;
    encoder_counter_init(&a); encoder_counter_init(&b);
    g_speed_config.target_rpm = 60.0f; g_speed_config.run_ms = 3000u;
    g_speed_config.pi.kp = 2.0f; g_speed_config.pi.ki = 4.0f; g_speed_config.pi.feedforward = 300.0f;
    g_sprint_config.distance_limit_mm = 3000u; g_sprint_config.wheel_diameter_mm = 67.5f;
    g_sprint_config.search_enabled = 1u;
    speed_sprint_init(now);
}
static void sample(void) {
    float ca, cb;
    int da, db;
    left_speed += ((float)g_speed_match.left_pwm * left_gain - left_speed) * 0.25f;
    right_speed += ((float)g_speed_match.right_pwm * right_gain - right_speed) * 0.25f;
    if (mode == 1) left_speed = right_speed = 0.0f;
    ca = left_speed * 1058.6f / 3000.0f; cb = right_speed * 1060.8f / 3000.0f;
    if (wiring == 0) { fraction_a += ca; fraction_b -= cb; }
    else { fraction_a -= cb; fraction_b += ca; }
    da = (int)fraction_a; db = (int)fraction_b;
    fraction_a -= (float)da; fraction_b -= (float)db;
    if (mode == 2 && g_speed_match.state == SPEED_RUNNING) { da = -da; db = -db; }
    if (mode == 3 && g_speed_match.state == SPEED_RUNNING) { da = 300; db = -300; }
    raw_a = (uint16_t)((uint32_t)raw_a + (uint32_t)da);
    raw_b = (uint16_t)((uint32_t)raw_b + (uint32_t)db);
    encoder_counter_update(&a, raw_a, now); encoder_counter_update(&b, raw_b, now);
    speed_sprint_sample(now, &a.sample, &b.sample);
}
static void ticks(unsigned n, uint8_t key) {
    while (n-- != 0u) {
        ++now;
        if ((uint32_t)(now - last_sample) >= 20u) { sample(); last_sample = now; }
        speed_sprint_tick(now, key);
        assert(g_speed_match.left_pwm <= 1000u && g_speed_match.right_pwm <= 1000u);
        if (g_speed_match.state == SPEED_FAULT)
            assert(g_speed_match.left_pwm == 0u && g_speed_match.right_pwm == 0u);
    }
}
static void wait_ready(void) {
    unsigned i;
    for (i = 0u; i < 5000u && g_speed_match.state != SPEED_READY; ++i) ticks(1u, 0u);
    assert(g_speed_match.state == SPEED_READY);
}
static void trigger(void) {
    wait_ready(); ticks(1100u, 1u); assert(g_speed_match.state == SPEED_ARMED);
    ticks(31u, 0u);
}
static void calibrate(void) {
    trigger(); assert(g_speed_match.left_pwm == 500u && g_speed_match.right_pwm == 0u);
    ticks(499u, 0u); assert(g_speed_match.state == SPEED_CALIBRATING);
    ticks(1u, 0u); assert(g_speed_match.phase == 1u);
    trigger(); assert(g_speed_match.left_pwm == 0u && g_speed_match.right_pwm == 500u);
    ticks(500u, 0u); assert(g_speed_match.phase == 2u && g_sprint.result_id == 0u);
    assert(g_speed_match.left_channel == (wiring == 0 ? 1u : 2u));
    assert(g_speed_match.right_channel == (wiring == 0 ? 2u : 1u));
    assert(g_speed_match.left_sign == 1 && g_speed_match.right_sign == -1);
}
static void trial(void) {
    uint32_t start, run_ms;
    trigger(); start = now; run_ms = g_speed_match.active.run_ms;
    assert(g_speed_match.state == SPEED_RUNNING && g_speed_match.command_rpm == 10.0f);
    while (g_speed_match.state == SPEED_RUNNING && (uint32_t)(now - start) < run_ms) ticks(1u, 0u);
    assert(g_speed_match.state == SPEED_SETTLING);
    assert(g_speed_match.left_pwm == 0u && g_speed_match.right_pwm == 0u);
    assert(g_sprint.result_id > 0u);
}
static void review(uint32_t command) {
    wait_ready(); g_sprint_review = command; ticks(1u, 0u); assert(g_sprint_review == 0u);
}
static void pass_and_accept(void) {
    trial();
    if (g_sprint.last_result != SPRINT_ENCODER_PASS)
        fprintf(stderr, "not verified: target %.1f left %.2f right %.2f matched %u distance %.1f reason %u result %u\n",
                (double)g_sprint.last_target_rpm, (double)g_speed_match.last_left_rpm,
                (double)g_speed_match.last_right_rpm, (unsigned)g_speed_match.last_matched_ms,
                (double)g_sprint.last_distance_mm, (unsigned)g_sprint.stop_reason, (unsigned)g_sprint.last_result);
    assert(g_sprint.last_result == SPRINT_ENCODER_PASS && g_speed_match.last_matched_ms >= 500u);
    assert(absf(g_speed_match.last_left_rpm - g_sprint.last_target_rpm) <= 5.0f);
    assert(absf(g_speed_match.last_right_rpm - g_sprint.last_target_rpm) <= 5.0f);
    assert(absf(g_speed_match.last_difference_rpm) <= 5.0f);
    review(1u); assert(g_sprint.review_error == 0u);
}
static void search_cases(int reverse, uint32_t initial) {
    unsigned i;
    init(initial, reverse); calibrate();
    for (i = 0u; i < 3u; ++i) {
        pass_and_accept(); assert(g_sprint.accepted_runs == i + 1u);
        if (i < 2u) assert(g_sprint.best_rpm == 0.0f && g_speed_config.target_rpm == 60.0f);
    }
    assert(g_sprint.best_rpm == 60.0f && g_speed_config.target_rpm == 80.0f);
    review(1u); assert(g_sprint.review_error == 2u && g_sprint.accepted_runs == 3u);
    ticks(1000u, 0u); assert(g_speed_match.state == SPEED_READY); /* 建议升档不会自启。 */
    for (i = 0u; i < 3u; ++i) pass_and_accept();
    assert(g_sprint.best_rpm == 80.0f && g_speed_config.target_rpm == 100.0f);
    printf("Sprint model mapping %d: last %.2f/%.2f RPM, matched %u ms, accepted best %.0f RPM\n",
           reverse, (double)g_speed_match.last_left_rpm, (double)g_speed_match.last_right_rpm,
           (unsigned)g_speed_match.last_matched_ms, (double)g_sprint.best_rpm);
    review(3u); assert(g_speed_config.target_rpm == 80.0f && g_sprint_config.search_enabled == 0u);
    for (i = 0u; i < 3u; ++i) pass_and_accept();
    assert(g_speed_config.target_rpm == 80.0f); /* 选用best模式保持目标，不继续升档。 */
    review(1u); assert(g_sprint.review_error == 2u);
    trial(); review(2u); assert(g_sprint.best_rpm == 0.0f && g_speed_config.target_rpm == 60.0f);
}
static void limited_cases(void) {
    uint32_t begin;
    float saved;
    init(0u, 0); calibrate(); g_sprint_config.distance_limit_mm = 200u;
    trigger(); begin = now; g_sprint_config.distance_limit_mm = 3000u;
    while (g_speed_match.state == SPEED_RUNNING) ticks(1u, 0u);
    assert(g_sprint.active.distance_limit_mm == 200u && g_sprint.stop_reason == 2u);
    assert(now - begin < 3000u && g_sprint.last_distance_mm >= 200.0f && g_sprint.last_distance_mm < 230.0f);
    saved = g_sprint.last_distance_mm; ticks(2000u, 0u); assert(g_sprint.last_distance_mm == saved);
    init(0u, 0); calibrate(); g_speed_config.target_rpm = 300.0f;
    right_gain = left_gain; /* 两轮都到输出上限，仍同速但共同欠速，区分于明显轮速分离。 */
    g_speed_config.pi.kp = 10.0f; g_speed_config.pi.ki = 20.0f;
    trial();
    printf("Sprint saturation model: left %.2f right %.2f, saturated %u ms, result %u\n",
           (double)g_speed_match.last_left_rpm, (double)g_speed_match.last_right_rpm,
           (unsigned)g_sprint.last_saturated_ms, (unsigned)g_sprint.last_result);
    assert(g_sprint.last_result == SPRINT_SATURATED && g_sprint.last_saturated_ms >= 500u);
    assert(g_speed_match.last_left_pwm == 1000u && g_sprint.best_rpm == 0.0f);
    review(1u); assert(g_sprint.review_error == 3u && g_sprint.best_rpm == 0.0f);
    init(0u, 0); calibrate(); g_speed_config.target_rpm = 300.0f; g_speed_config.run_ms = 500u;
    trial(); assert(g_sprint.last_result == SPRINT_NOT_VERIFIED && g_sprint.stop_reason == 1u);
    assert(g_speed_match.command_rpm < 300.0f && g_speed_match.last_matched_ms == 0u);
    init(0u, 0); calibrate(); trigger(); begin = now;
    g_speed_config.target_rpm = 450.0f; g_speed_config.run_ms = 500u;
    ticks(2999u, 0u); assert(g_speed_match.state == SPEED_RUNNING && g_speed_match.active.target_rpm == 60.0f);
    ticks(1u, 0u); assert(g_speed_match.stop_ms - begin == 3000u);
}
static void review_cases(void) {
    init(0u, 0); calibrate(); review(3u); assert(g_sprint.review_error == 4u);
    review(1u); assert(g_sprint.review_error == 2u);
    pass_and_accept(); assert(g_sprint.accepted_runs == 1u);
    g_speed_config.pi.kp = 2.1f; pass_and_accept(); assert(g_sprint.accepted_runs == 1u);
    trigger(); g_sprint_review = 1u; ticks(1u, 0u);
    assert(g_sprint.review_error == 1u && g_sprint_review == 0u);
    ticks(3000u, 0u); assert(g_sprint.accepted_runs == 1u); /* 未延后消费运行中命令。 */
    review(2u); assert(g_sprint.accepted_runs == 0u && g_sprint.best_rpm == 0.0f);
}
static void cap_and_context_cases(void) {
    unsigned i;
    init(0u, 0); calibrate();
    /* 搜索软件上限使用另一组响应更快的假想电机；不把本模型450当成本车能力。 */
    left_gain = 1.0f; right_gain = 1.1f;
    g_speed_config.pi.kp = 1.0f; g_speed_config.pi.ki = 12.0f;
    g_speed_config.target_rpm = 450.0f;
    for (i = 0u; i < 3u; ++i) pass_and_accept();
    assert(g_sprint.best_rpm == 450.0f && g_speed_config.target_rpm == 450.0f);
    g_speed_config.pi.kp = 1.1f;
    review(3u); assert(g_sprint.review_error == 4u && g_sprint.best_rpm == 0.0f);
    init(0u, 0); calibrate();
    for (i = 0u; i < 3u; ++i) pass_and_accept();
    g_sprint_config.wheel_diameter_mm = 68.0f;
    trigger(); assert(g_sprint.best_rpm == 0.0f && g_sprint.accepted_runs == 0u);
    ticks(1u, 1u);
}
static void fault_cases(void) {
    int m;
    for (m = 1; m <= 3; ++m) {
        init(0u, 0); calibrate(); trigger(); mode = m; ticks(400u, 0u);
        assert(g_speed_match.state == SPEED_FAULT && g_sprint.last_result == SPRINT_FAULTED);
        assert(g_speed_match.error == (m == 1 ? SPEED_ERROR_NO_FEEDBACK :
                                     (m == 2 ? SPEED_ERROR_REVERSE : SPEED_ERROR_OVERSPEED)));
        g_sprint_review = 1u; ticks(1500u, 0u); assert(g_sprint.best_rpm == 0.0f);
    }
    init(0u, 0); calibrate(); trigger(); ticks(1u, 1u);
    assert(g_speed_match.error == SPEED_ERROR_KEY && g_sprint.stop_reason == 3u);
    init(0u, 0); calibrate(); trigger(); now += 61u; speed_sprint_tick(now, 0u);
    assert(g_speed_match.error == SPEED_ERROR_TIMING && g_sprint.last_result == SPRINT_FAULTED);
    init(0u, 0); calibrate(); trigger(); g_speed_config.target_rpm = 0.0f; ticks(1u, 0u);
    assert(g_speed_match.error == SPEED_ERROR_KEY);
    init(0u, 0); calibrate(); g_sprint_config.wheel_diameter_mm = (float)NAN; trigger();
    assert(g_speed_match.error == SPEED_ERROR_CONFIG);
    init(0u, 0); calibrate(); g_sprint_config.distance_limit_mm = 0u; trigger();
    assert(g_speed_match.error == SPEED_ERROR_CONFIG);
    init(0u, 0); calibrate(); g_speed_config.target_rpm = 451.0f; trigger();
    assert(g_speed_match.error == SPEED_ERROR_CONFIG);
    init(0u, 0); calibrate(); trigger(); speed_sprint_fault(SPEED_ERROR_HARDWARE, now);
    assert(g_sprint.last_result == SPRINT_FAULTED && g_speed_match.left_pwm == 0u);
    init(0u, 0); calibrate(); trigger(); g_speed_match.left_channel = 0u; ticks(20u, 0u);
    assert(g_speed_match.error == SPEED_ERROR_MAPPING);
    init(0u, 0); calibrate(); trigger(); g_speed_match.left_sign = 0; ticks(20u, 0u);
    assert(g_speed_match.error == SPEED_ERROR_MAPPING);
    init(0u, 0); calibrate(); g_speed_config.target_rpm = 300.0f;
    g_speed_config.pi.kp = 10.0f; g_speed_config.pi.ki = 20.0f;
    trigger(); ticks(2000u, 0u);
    assert(g_speed_match.error == SPEED_ERROR_SYNC && g_sprint.last_result == SPRINT_FAULTED);
    assert(g_sprint.mismatch_ms >= 200u && g_sprint.best_rpm == 0.0f);
}
static void pi_boundaries(void) {
    speed_pi_t pi; speed_pi_config_t c = {10.0f, 20.0f, 300.0f}; uint16_t duty;
    unsigned i; speed_pi_reset(&pi);
    for (i = 0u; i < 1000u; ++i)
        assert(speed_pi_update(&pi, &c, 450.0f, 0.0f, 20u, &duty) && duty == 1000u);
    assert(pi.integral == 0.0f); /* 饱和方向不积累。 */
    assert(!speed_pi_update(&pi, &c, 451.0f, 0.0f, 20u, &duty) && duty == 0u);
    assert(!speed_pi_update(&pi, &c, 60.0f, NAN, 20u, &duty) && duty == 0u);
}
static void short_accept(void) {
    wait_ready(); ticks(250u, 1u); ticks(31u, 0u);
    assert(g_speed_match.state == SPEED_WAIT_RELEASE);
    assert(g_speed_match.left_pwm == 0u && g_speed_match.right_pwm == 0u);
}
static void end_search_key(void) {
    wait_ready(); ticks(3000u, 1u);
    assert(g_speed_match.state == SPEED_ARMED);
    ticks(31u, 0u);
    assert(g_speed_match.state == SPEED_WAIT_RELEASE && g_speed_match.runs > 0u);
    assert(g_speed_match.left_pwm == 0u && g_speed_match.right_pwm == 0u);
}
static void offline_key_cases(void) {
    unsigned i;
    uint32_t runs;
    init(0u, 0); calibrate();
    for (i = 0u; i < 3u; ++i) {
        trial(); assert(g_sprint.last_result == SPRINT_ENCODER_PASS);
        short_accept(); assert(g_sprint.accepted_runs == i + 1u && g_sprint.review_error == 0u);
    }
    assert(g_sprint.best_rpm == 60.0f && g_speed_config.target_rpm == 80.0f);
    runs = g_speed_match.runs; end_search_key();
    assert(g_speed_match.runs == runs && g_sprint_config.search_enabled == 0u);
    assert(g_speed_config.target_rpm == 60.0f && g_sprint.best_rpm == 60.0f);
    for (i = 0u; i < 3u; ++i) { trial(); short_accept(); }
    assert(g_speed_config.target_rpm == 60.0f); /* 脱线选择已确认档后不再自动升档。 */
    init(0u, 0); calibrate(); trial(); short_accept();
    trial(); /* 地面现象没有接受，直接重复试验会打断连续通过计数。 */
    trial(); short_accept(); assert(g_sprint.accepted_runs == 1u);
    init(0u, 0); calibrate(); trial(); end_search_key();
    assert(g_sprint.best_rpm == 0.0f && g_speed_config.target_rpm == 60.0f && g_sprint.review_error == 4u);
    init(0u, 0); calibrate(); wait_ready();
    ticks(10u, 1u); ticks(50u, 0u); assert(g_sprint.result_id == 0u && g_speed_match.runs == 0u);
    trigger(); ticks(1u, 1u); ticks(400u, 1u); ticks(31u, 0u);
    assert(g_speed_match.error == SPEED_ERROR_KEY && g_sprint.best_rpm == 0.0f);
    init(0u, 0); calibrate(); wait_ready(); ticks(5100u, 1u); ticks(31u, 0u);
    assert(g_speed_match.error == SPEED_ERROR_STUCK_KEY && g_speed_match.runs == 0u);
    /* 供电切换会重新进入程序，源码默认值重建，旧best和通道不能当作仍在RAM。 */
    init(now + 1000u, 0);
    assert(g_sprint.best_rpm == 0.0f && g_speed_config.target_rpm == 60.0f);
    assert(g_speed_match.phase == 0u && g_speed_match.left_channel == 0u && g_speed_match.runs == 0u);
}
static void offline_led_cases(void) {
    uint32_t ready_at, t, duration = 0u, short_pulses = 0u, long_pulses = 0u;
    uint8_t previous = 0u, current;
    init(0u, 0); calibrate(); wait_ready(); ready_at = now;
    /* 初始待试60RPM：1次状态短闪，然后数字0／6／0。
     * 检查一帧的实际脉冲数量与宽度；不使用Watch也能读出完整十进制数。
     */
    for (t = 0u; t < 7100u; ++t) {
        current = speed_sprint_led(ready_at + t);
        if (current != 0u) ++duration;
        if (current == 0u && previous != 0u) {
            if (duration == 100u) ++short_pulses;
            else { assert(duration == 600u); ++long_pulses; }
            duration = 0u;
        }
        previous = current;
    }
    assert(short_pulses == 7u && long_pulses == 2u);
    trial(); wait_ready(); ready_at = now;
    assert(speed_sprint_led(ready_at) == 1u && speed_sprint_led(ready_at + 300u) == 1u);
    assert(speed_sprint_led(ready_at + 600u) == 0u); /* 待确认结果以2次短闪开头。 */
}
int main(void) {
    pi_boundaries(); search_cases(0, 0u); search_cases(1, UINT32_MAX - 6000u);
    limited_cases(); review_cases(); cap_and_context_cases(); fault_cases();
    offline_key_cases(); offline_led_cases();
    puts("SpeedSprint policy + real PI/encoder/state-machine PASS (model only)");
    return 0;
}
