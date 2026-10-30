#ifndef YEYE_ENCODER_COUNTER_H
#define YEYE_ENCODER_COUNTER_H
#include <stdint.h>

/* 单位全部为解码后的counts、ms、counts/s；没有轮径、减速比或CPR常量。 */
#define ENCODER_MAX_DT_MS 100u
#define ENCODER_CONTINUITY_LOST 1u
#define ENCODER_TOTAL_SATURATED 2u
typedef enum {
    ENCODER_OK = 0, ENCODER_FIRST = 1, ENCODER_ZERO_DT = 2,
    ENCODER_LONG_DT = 3, ENCODER_HALF_RANGE = 4, ENCODER_OVERFLOW = 5
} encoder_status_t;

typedef struct {
    uint32_t raw_cnt;          /* 实际16位CNT零扩展，范围0..65535。 */
    int32_t delta;             /* 最近有效窗口的带符号净增量；无效窗口置0。 */
    int64_t total_count;       /* 自首样起有效窗口之和；有丢窗时不是完整里程。 */
    int32_t counts_per_s;      /* delta*1000/dt，整数向零截断；无效窗口置0。 */
    uint32_t dt_ms;            /* unsigned毫秒差；首样为0。 */
    uint32_t valid;            /* 1=本窗口增量／速率可用；不证明传感器有电。 */
    uint32_t status;           /* encoder_status_t：本窗口状态。 */
    uint32_t flags;            /* 粘性连续性／累计饱和标志，仅重新初始化清除。 */
} encoder_sample_t;

typedef struct {
    uint16_t previous_raw;
    uint32_t previous_ms;
    uint32_t initialized;
    encoder_sample_t sample;
} encoder_counter_t;

/** @brief 清除一通道历史；无硬件操作。c必须为有效对象，返回无。 */
void encoder_counter_init(encoder_counter_t *c);
/** @brief 输入实际CNT与采样时间，更新当前窗口；返回无。
 * raw为16位硬件读数，now_ms为uint32毫秒时基。首样只建立基线，不把当前CNT当位移。
 * 必须保证两次采样间真实净变化严格小于32768 counts，不能由16位数据检测多圈混叠。
 * 异常dt／半量程窗口丢弃并重建基线，flags锁存丢窗，禁止伪造跨长间隔累计。
 */
void encoder_counter_update(encoder_counter_t *c, uint16_t raw, uint32_t now_ms);
#endif
