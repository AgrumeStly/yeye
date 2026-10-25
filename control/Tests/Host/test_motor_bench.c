/* C-02B电脑测试：直接运行板端相同的按键/超时逻辑，不模拟PWM寄存器或机械运动。 */
#include "motor_bench.h"
#include <stdio.h>
#include <stdlib.h>

static unsigned checks;
#define CHECK(e) do { ++checks; if (!(e)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #e); exit(1); } } while (0)

static void advance(motor_bench_t *b, uint32_t *now, uint8_t pressed, uint32_t duration) {
    uint32_t i;
    for (i = 0u; i < duration; ++i) {
        ++*now;
        motor_bench_tick(b, *now, pressed);
    }
}

static void ready(motor_bench_t *b, uint32_t *now) {
    advance(b, now, 0u, MOTOR_BENCH_RELEASE_MS + MOTOR_BENCH_DEBOUNCE_MS + 1u);
    CHECK(b->state == MOTOR_BENCH_READY && b->output_mask == 0u);
}

static void trigger(motor_bench_t *b, uint32_t *now, uint8_t expected) {
    advance(b, now, 1u, MOTOR_BENCH_DEBOUNCE_MS + MOTOR_BENCH_HOLD_MS + 1u);
    CHECK(b->state == MOTOR_BENCH_ARMED && b->output_mask == 0u);
    advance(b, now, 0u, MOTOR_BENCH_DEBOUNCE_MS + 1u);
    CHECK(b->state == MOTOR_BENCH_RUNNING && b->output_mask == expected);
}

static void sequence_test(uint32_t start) {
    motor_bench_t b;
    uint32_t now = start, began;
    unsigned step;
    const uint8_t masks[3] = {1u, 2u, 3u};
    motor_bench_init(&b, now);
    CHECK(b.output_mask == 0u && b.state == MOTOR_BENCH_WAIT_RELEASE);
    for (step = 0u; step < 3u; ++step) {
        ready(&b, &now);
        CHECK(b.step == step);
        trigger(&b, &now, masks[step]);
        began = b.run_since;
        motor_bench_tick(&b, began + MOTOR_BENCH_RUN_MS - 1u, 0u);
        CHECK(b.state == MOTOR_BENCH_RUNNING && b.output_mask == masks[step]);
        now = began + MOTOR_BENCH_RUN_MS;
        motor_bench_tick(&b, now, 0u);
        CHECK(b.output_mask == 0u);
        if (step < 2u) {
            CHECK(b.state == MOTOR_BENCH_WAIT_RELEASE && b.step == step + 1u);
            /* 无论等待多久，下一步都不能自行启动。 */
            advance(&b, &now, 0u, 10000u);
            CHECK(b.output_mask == 0u && b.state == MOTOR_BENCH_READY);
        } else CHECK(b.state == MOTOR_BENCH_COMPLETE);
    }
    advance(&b, &now, 1u, 2000u);
    advance(&b, &now, 0u, 2000u);
    CHECK(b.state == MOTOR_BENCH_COMPLETE && b.output_mask == 0u);
}

static void input_and_stop_test(void) {
    motor_bench_t b;
    uint32_t now = 0u, i;
    motor_bench_init(&b, now);
    advance(&b, &now, 1u, 10000u);
    CHECK(b.state == MOTOR_BENCH_WAIT_RELEASE && b.output_mask == 0u);
    ready(&b, &now);
    /* 反复5ms抖动不能变成有效启动操作。 */
    for (i = 0u; i < 10u; ++i) {
        advance(&b, &now, 1u, 5u); advance(&b, &now, 0u, 5u);
    }
    CHECK(b.state == MOTOR_BENCH_READY && b.output_mask == 0u);
    advance(&b, &now, 1u, 200u); advance(&b, &now, 0u, 31u);
    CHECK(b.state == MOTOR_BENCH_WAIT_RELEASE && b.step == 0u && b.output_mask == 0u);
    ready(&b, &now);
    /* 总按下1s但消抖后长按不足1s：不能借松键消抖时间补足。 */
    advance(&b, &now, 1u, 1000u); advance(&b, &now, 0u, 31u);
    CHECK(b.state == MOTOR_BENCH_WAIT_RELEASE && b.output_mask == 0u);
    ready(&b, &now);
    trigger(&b, &now, 1u);
    motor_bench_tick(&b, ++now, 1u); /* 只一个原始高电平，不满30ms也应停。 */
    CHECK(b.state == MOTOR_BENCH_ABORTED && b.output_mask == 0u && b.step == 0u);
    advance(&b, &now, 0u, 10000u);
    advance(&b, &now, 1u, 2000u); advance(&b, &now, 0u, 100u);
    CHECK(b.state == MOTOR_BENCH_ABORTED && b.output_mask == 0u);
    /* 复位时仍按住：不能沿用刚才的操作，必须先释放后再重新长按。 */
    motor_bench_init(&b, now);
    advance(&b, &now, 1u, 2000u);
    CHECK(b.state == MOTOR_BENCH_WAIT_RELEASE && b.output_mask == 0u);
    ready(&b, &now);
    advance(&b, &now, 1u, MOTOR_BENCH_STUCK_MS + 100u);
    CHECK(b.state == MOTOR_BENCH_ABORTED && b.output_mask == 0u);
    advance(&b, &now, 0u, 100u);
    CHECK(b.output_mask == 0u && b.state == MOTOR_BENCH_ABORTED);
}

static void delayed_and_invalid_test(void) {
    motor_bench_t b;
    uint32_t now = 0u;
    motor_bench_init(&b, now); ready(&b, &now); trigger(&b, &now, 1u);
    motor_bench_tick(&b, now + 50000u, 0u);
    CHECK(b.output_mask == 0u && b.step == 1u);
    b.state = (motor_bench_state_t)99;
    motor_bench_tick(&b, now + 50001u, 0u);
    CHECK(b.state == MOTOR_BENCH_ABORTED && b.output_mask == 0u);
    b.step = 3u; b.state = MOTOR_BENCH_READY;
    motor_bench_tick(&b, now + 50002u, 1u);
    CHECK(b.state == MOTOR_BENCH_ABORTED && b.output_mask == 0u);
    b.step = 0u; b.state = MOTOR_BENCH_READY;
    CHECK(motor_bench_led(&b, 0u) == 1u && motor_bench_led(&b, 300u) == 0u);
    b.step = 2u;
    CHECK(motor_bench_led(&b, 300u) == 1u && motor_bench_led(&b, 600u) == 1u);
}

int main(void) {
    sequence_test(0u);
    sequence_test(0xfffffff0u); /* 序列跨uint32毫秒回绕。 */
    input_and_stop_test();
    delayed_and_invalid_test();
    printf("PASS motor bench: %u checks (manual sequence, debounce, stop, timeout, wrap, lockout)\n", checks);
    return 0;
}
