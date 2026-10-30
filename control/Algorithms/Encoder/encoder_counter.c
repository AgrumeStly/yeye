/** @file encoder_counter.c
 * @brief 与SPL无关的16位编码器增量／时间换算，供双通道独立复用。
 * 回绕先按模65536求差，再用明确减65536得到负数，避免依赖超范围强转int16的实现行为。
 */
#include "encoder_counter.h"
#include <string.h>
#include <limits.h>

void encoder_counter_init(encoder_counter_t *c) {
    memset(c, 0, sizeof(*c));
    c->sample.status = ENCODER_FIRST;
}

void encoder_counter_update(encoder_counter_t *c, uint16_t raw, uint32_t now_ms) {
    encoder_sample_t *s = &c->sample;
    uint32_t difference;
    int32_t delta;
    s->raw_cnt = raw;
    s->delta = 0;
    s->counts_per_s = 0;
    s->valid = 0u;
    if (c->initialized == 0u) {
        c->initialized = 1u;
        s->dt_ms = 0u;
        s->status = ENCODER_FIRST;
        c->previous_raw = raw;
        c->previous_ms = now_ms;
        return;
    }
    s->dt_ms = now_ms - c->previous_ms; /* 支持一次uint32毫秒回绕；不处理停采约49.7天。 */
    difference = ((uint32_t)raw + 65536u - (uint32_t)c->previous_raw) & 0xffffu;
    /* 每次输入都重建下一窗口基线，包括无效窗口；不能把丢失计数混进下一窗。 */
    c->previous_raw = raw;
    c->previous_ms = now_ms;
    if (s->dt_ms == 0u || s->dt_ms > ENCODER_MAX_DT_MS || difference == 32768u) {
        s->status = s->dt_ms == 0u ? ENCODER_ZERO_DT :
                    (s->dt_ms > ENCODER_MAX_DT_MS ? ENCODER_LONG_DT : ENCODER_HALF_RANGE);
        s->flags |= ENCODER_CONTINUITY_LOST;
        return;
    }
    delta = difference < 32768u ? (int32_t)difference : (int32_t)difference - 65536;
    /* 64位累计有明确界限。达到饱和后永久冻结，不能反转几次就伪装恢复准确累计。 */
    if ((s->flags & ENCODER_TOTAL_SATURATED) != 0u ||
        (delta > 0 && s->total_count > INT64_MAX - (int64_t)delta) ||
        (delta < 0 && s->total_count < INT64_MIN - (int64_t)delta)) {
        if ((s->flags & ENCODER_TOTAL_SATURATED) == 0u)
            s->total_count = delta > 0 ? INT64_MAX : INT64_MIN;
        s->flags |= ENCODER_TOTAL_SATURATED | ENCODER_CONTINUITY_LOST;
        s->status = ENCODER_OVERFLOW;
        return;
    }
    s->total_count += delta;
    s->delta = delta;
    /* |delta|<=32767，乘1000不会超出int32；dt先限为1..100才转换后除，避免除零。 */
    s->counts_per_s = (delta * 1000) / (int32_t)s->dt_ms;
    s->valid = 1u;
    s->status = ENCODER_OK;
}
