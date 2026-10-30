#ifndef YEYE_ENCODER_BENCH_H
#define YEYE_ENCODER_BENCH_H
#include "encoder_counter.h"
#define ENCODER_BENCH_PERIOD_MS 10u
typedef struct {
    uint32_t sequence; /* 奇数=正在发布；偶数=写完。Watch分项读仍非原子快照。 */
    uint32_t sample_ms, sample_count, pin_levels;
    encoder_sample_t a, b;
} encoder_bench_view_t;
extern volatile encoder_bench_view_t g_encoder_bench;
/** @brief 清除两路软件历史，不重配置硬件；返回无。 */
void encoder_bench_init(void);
/** @brief 读取真实硬件、更新两路并发布Watch；now_ms单位ms，返回1成功／0未就绪。
 * 由Core在首次及每10ms调用；不是在此隐式延时。两路对象独立，不改左右映射或计数符号。
 */
int encoder_bench_sample(uint32_t now_ms);
#endif
