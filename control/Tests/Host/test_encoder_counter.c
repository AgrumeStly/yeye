/* 测试真实数学模块：输入轨迹独立给定，不能用另一份模差实现当作正确答案。 */
#include "encoder_counter.h"
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
static unsigned checks;
#define CHECK(e) do { ++checks; if (!(e)) { fprintf(stderr,"FAIL %s:%d %s\n",__FILE__,__LINE__,#e); exit(1); } } while (0)
int main(void) {
    encoder_counter_t a, b;
    uint32_t now, random = 12345u;
    int64_t expected_a = 0, expected_b = 0;
    uint16_t raw_a = 65530u, raw_b = 100u;
    unsigned i;
    encoder_counter_init(&a);
    encoder_counter_update(&a, 12000u, 100u);
    CHECK(a.sample.status == ENCODER_FIRST && a.sample.valid == 0u && a.sample.total_count == 0 && a.sample.dt_ms == 0u);
    encoder_counter_update(&a, 12000u, 110u);
    CHECK(a.sample.valid == 1u && a.sample.delta == 0 && a.sample.counts_per_s == 0);
    encoder_counter_update(&a, 12025u, 120u);
    CHECK(a.sample.delta == 25 && a.sample.counts_per_s == 2500 && a.sample.total_count == 25);
    encoder_counter_update(&a, 12018u, 140u);
    CHECK(a.sample.delta == -7 && a.sample.counts_per_s == -350 && a.sample.total_count == 18);
    encoder_counter_init(&a);
    encoder_counter_update(&a, 65530u, 0u);
    encoder_counter_update(&a, 5u, 10u);
    CHECK(a.sample.delta == 11 && a.sample.total_count == 11);
    encoder_counter_update(&a, 65530u, 20u);
    CHECK(a.sample.delta == -11 && a.sample.total_count == 0);
    encoder_counter_update(&a, 32760u, 30u); /* 跨回绕净增32766，仍在允许窗口。 */
    encoder_counter_update(&a, 32780u, 40u);
    CHECK(a.sample.delta == 20);
    encoder_counter_update(&a, 32760u, 50u);
    CHECK(a.sample.delta == -20);
    encoder_counter_update(&a, 65528u, 60u);
    CHECK(a.sample.status == ENCODER_HALF_RANGE && a.sample.valid == 0u && a.sample.flags == ENCODER_CONTINUITY_LOST);
    expected_a = a.sample.total_count;
    encoder_counter_update(&a, 65529u, 70u);
    CHECK(a.sample.valid == 1u && a.sample.delta == 1 && a.sample.total_count == expected_a + 1 && a.sample.flags == 1u);
    encoder_counter_update(&a, 65530u, 70u);
    CHECK(a.sample.status == ENCODER_ZERO_DT && a.sample.delta == 0 && a.sample.counts_per_s == 0);
    encoder_counter_update(&a, 10u, 171u);
    CHECK(a.sample.status == ENCODER_LONG_DT && a.sample.dt_ms == 101u && a.sample.valid == 0u);
    encoder_counter_update(&a, 12u, 271u);
    CHECK(a.sample.valid == 1u && a.sample.delta == 2 && a.sample.counts_per_s == 20);
    encoder_counter_init(&a);
    encoder_counter_update(&a, 0u, 0xfffffff8u);
    encoder_counter_update(&a, 3u, 2u);
    CHECK(a.sample.dt_ms == 10u && a.sample.counts_per_s == 300);
    encoder_counter_update(&a, 32770u, 3u);
    CHECK(a.sample.delta == 32767 && a.sample.counts_per_s == 32767000);
    encoder_counter_update(&a, 3u, 4u);
    CHECK(a.sample.delta == -32767 && a.sample.counts_per_s == -32767000);
    encoder_counter_update(&a, 2u, 7u);
    CHECK(a.sample.counts_per_s == -333); /* 负数向零截断，不向负无穷取整。 */
    a.sample.total_count = INT64_MAX - 1;
    encoder_counter_update(&a, 4u, 17u);
    CHECK(a.sample.status == ENCODER_OVERFLOW && a.sample.total_count == INT64_MAX && a.sample.flags == 3u && a.sample.valid == 0u);
    encoder_counter_update(&a, 3u, 27u);
    CHECK(a.sample.total_count == INT64_MAX && a.sample.status == ENCODER_OVERFLOW);
    encoder_counter_init(&a);
    encoder_counter_update(&a, 4u, 0u);
    a.sample.total_count = INT64_MIN + 1;
    encoder_counter_update(&a, 2u, 10u);
    CHECK(a.sample.total_count == INT64_MIN && a.sample.status == ENCODER_OVERFLOW);
    encoder_counter_init(&a);
    encoder_counter_update(&a, 0u, 0u);
    a.sample.total_count = INT64_MAX - 1;
    encoder_counter_update(&a, 1u, 10u);
    CHECK(a.sample.total_count == INT64_MAX && a.sample.flags == 0u && a.sample.valid == 1u);
    encoder_counter_update(&a, 1u, 20u);
    CHECK(a.sample.valid == 1u && a.sample.total_count == INT64_MAX);

    /* 已知独立正反步长随机轨迹，覆盖多次16位CNT与32位毫秒回绕及两路互不污染。 */
    encoder_counter_init(&a); encoder_counter_init(&b);
    now = 0xfffffff0u; expected_a = expected_b = 0;
    encoder_counter_update(&a, raw_a, now); encoder_counter_update(&b, raw_b, now);
    for (i = 0u; i < 2000u; ++i) {
        int32_t da, db;
        uint32_t dt;
        random = random * 1664525u + 1013904223u;
        da = (int32_t)(random % 60001u) - 30000;
        random = random * 1664525u + 1013904223u;
        db = (int32_t)(random % 60001u) - 30000;
        dt = random % 100u + 1u; now += dt;
        raw_a = (uint16_t)((int32_t)raw_a + da);
        raw_b = (uint16_t)((int32_t)raw_b + db);
        expected_a += da; expected_b += db;
        encoder_counter_update(&a, raw_a, now); encoder_counter_update(&b, raw_b, now);
        CHECK(a.sample.delta == da && b.sample.delta == db);
        CHECK(a.sample.total_count == expected_a && b.sample.total_count == expected_b);
        CHECK(a.sample.counts_per_s == da * 1000 / (int32_t)dt && b.sample.counts_per_s == db * 1000 / (int32_t)dt);
        CHECK(a.sample.flags == 0u && b.sample.flags == 0u);
    }
    printf("PASS encoder counter: %u assertions (first, stationary, signs, wrap, dt, ambiguity, saturation, 2000 dual trajectories)\n", checks);
    return 0;
}
