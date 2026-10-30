/** @file encoder_bench.c
 * @brief 无动力手转诊断：把硬件读数送入真实数学算法，再保留Watch可见数据。
 * 未知CPR时只给counts、counts/s。没有PID、PWM、串口或自动运动请求。
 */
#include "encoder_bench.h"
#include "encoder_hw.h"
static encoder_counter_t counter_a, counter_b;
volatile encoder_bench_view_t g_encoder_bench;

void encoder_bench_init(void) {
    encoder_bench_view_t empty = {0};
    encoder_counter_init(&counter_a);
    encoder_counter_init(&counter_b);
    empty.a.status = empty.b.status = ENCODER_FIRST;
    g_encoder_bench = empty;
}

int encoder_bench_sample(uint32_t now_ms) {
    encoder_raw_t raw;
    if (!encoder_hw_read(&raw)) return 0;
    encoder_counter_update(&counter_a, raw.a, now_ms);
    encoder_counter_update(&counter_b, raw.b, now_ms);
    ++g_encoder_bench.sequence;
    g_encoder_bench.sample_ms = now_ms;
    g_encoder_bench.pin_levels = raw.pin_levels;
    g_encoder_bench.a = counter_a.sample;
    g_encoder_bench.b = counter_b.sample;
    ++g_encoder_bench.sample_count;
    ++g_encoder_bench.sequence;
    return 1;
}
