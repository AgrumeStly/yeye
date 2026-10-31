/* 验证真实纯逻辑：边界时长、回绕、短按、卡键、停止与禁止重复。 */
#include "straight_test.h"
#include <assert.h>
#include <stdio.h>
static straight_test_t t;
static uint32_t now;
static int stopped(void) { return t.left_duty_permille == 0u && t.right_duty_permille == 0u; }
static void ticks(unsigned count, uint8_t raw) {
    while (count-- != 0u) straight_test_tick(&t, ++now, raw);
}
static void start(uint32_t initial) {
    now = initial;
    straight_test_init(&t, now);
    assert(stopped());
    ticks(1000u, 0u); assert(t.state == STRAIGHT_READY);
    ticks(1100u, 1u); assert(t.state == STRAIGHT_ARMED && stopped());
    ticks(31u, 0u); assert(t.state == STRAIGHT_RUNNING && t.run_since == now);
}
int main(void) {
    unsigned i;
    const int32_t trims[] = { 0, 20, -20, 500, -500, INT32_MAX, INT32_MIN };
    const uint16_t left[] = { 500u, 500u, 480u, 500u, 0u, 500u, 0u };
    const uint16_t right[] = { 500u, 480u, 500u, 0u, 500u, 0u, 500u };
    for (i = 0u; i < 2u; ++i) {
        g_straight_trim_permille = 20;
        start(i == 0u ? 0u : UINT32_MAX - 2500u);
        assert(t.left_duty_permille == 500u && t.right_duty_permille == 480u);
        g_straight_trim_permille = -100; /* 中途修改不改变本轮参数与3秒时限。 */
        ticks(1000u, 0u); assert(t.state == STRAIGHT_RUNNING);
        assert(t.left_duty_permille == 500u && t.right_duty_permille == 480u);
        ticks(1999u, 0u); assert(t.state == STRAIGHT_RUNNING);
        ticks(1u, 0u); assert(t.state == STRAIGHT_COMPLETE && stopped());
        assert((uint32_t)(t.stop_ms - t.run_since) == 3000u);
        ticks(1500u, 1u); ticks(1000u, 0u);
        assert(t.state == STRAIGHT_COMPLETE && stopped());
    }
    for (i = 0u; i < sizeof(trims) / sizeof(trims[0]); ++i) {
        g_straight_trim_permille = trims[i]; start(0u);
        assert(t.left_duty_permille == left[i] && t.right_duty_permille == right[i]);
        ticks(3000u, 0u); assert(t.state == STRAIGHT_COMPLETE && stopped());
    }
    for (i = 0u; i < 2u; ++i) {
        start(0u); ticks(i == 0u ? 100u : 1100u, 0u);
        ticks(1u, 1u); assert(t.state == STRAIGHT_ABORTED && stopped());
        ticks(1500u, 1u); ticks(1000u, 0u);
        assert(t.state == STRAIGHT_ABORTED && stopped());
    }
    now = 0u; straight_test_init(&t, now);
    ticks(6000u, 1u); assert(stopped());
    ticks(1000u, 0u); assert(t.state == STRAIGHT_READY);
    ticks(500u, 1u); ticks(31u, 0u);
    assert(t.state == STRAIGHT_WAIT_RELEASE && stopped());
    ticks(1000u, 0u); ticks(5100u, 1u); ticks(31u, 0u);
    assert(t.state == STRAIGHT_ABORTED && stopped());
    now = 0u; straight_test_init(&t, now); t.state = (straight_state_t)99;
    ticks(1u, 0u); assert(t.state == STRAIGHT_ABORTED && stopped());
    puts("StraightTest: 3s, signed trim/clamp/latch, wraparound, manual stop, short/stuck key, terminal lock PASS");
    return 0;
}
