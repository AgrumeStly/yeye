/** @file straight_test.c
 * @brief 纯逻辑状态机，所有运行与停止判定由板端1ms中断调用。
 * 长按至少1秒后松开才启动；固定占空比前进3秒，不作快慢切换。
 * 原始KEY停止优先于计时，结束后禁止自动重复；重测须断动力再复位。
 */
#include "straight_test.h"
#include <string.h>

/* ===== 主控调直线只需修改这一行 =====
 * 单位：PWM占空比的千分点，10=1个百分点；这是开环输出修正，不是RPM。
 * 正数降低右轮：20→左50%/右48%，30→左50%/右47%。
 * 负数降低左轮：-20→左48%/右50%；0→左右均50%。
 * 默认20是针对“右轮偏快”的试调起点，未经实车标定，不保证刚好走直。
 * 修改源码后重新编译下载；如用Keil Watch改RAM，须断动力且在启动之前改，
 * 不在动力接入时暂停CPU。复位会恢复本行初值，启动后本轮参数保持不变。
 */

 //数越大，左轮快，数小，右轮快
volatile int32_t g_straight_trim_permille = 12;

/** @brief 将本轮修正量换算为左右占空比；无返回值，不提高任一轮超过基准。
 * 修正量先限到±基准，避免极端输入溢出或产生负PWM；最大修正会令一轮为0，
 * 仅是输入边界保护，实际调直建议每次只改5~10（0.5~1个百分点）。
 */
static void set_run_output(straight_test_t *t) {
    int32_t trim = t->trim_applied_permille;
    if (trim > (int32_t)STRAIGHT_BASE_PERMILLE) trim = (int32_t)STRAIGHT_BASE_PERMILLE;
    if (trim < -(int32_t)STRAIGHT_BASE_PERMILLE) trim = -(int32_t)STRAIGHT_BASE_PERMILLE;
    t->trim_applied_permille = trim;
    t->left_duty_permille = (uint16_t)((int32_t)STRAIGHT_BASE_PERMILLE + (trim < 0 ? trim : 0));
    t->right_duty_permille = (uint16_t)((int32_t)STRAIGHT_BASE_PERMILLE - (trim > 0 ? trim : 0));
}

void straight_test_init(straight_test_t *t, uint32_t now) {
    memset(t, 0, sizeof(*t));
    t->state = STRAIGHT_WAIT_RELEASE;
    t->state_since = t->raw_since = now;
}

void straight_test_tick(straight_test_t *t, uint32_t now, uint8_t raw) {
    uint32_t held, elapsed;
    raw = raw != 0u ? 1u : 0u;
    if (raw != t->candidate) { t->candidate = raw; t->raw_since = now; }
    if ((uint32_t)(now - t->raw_since) >= 30u) t->stable = raw;
    t->left_duty_permille = t->right_duty_permille = 0u;
    if (t->state == STRAIGHT_RUNNING) {
        elapsed = now - t->run_since;
        if (raw != 0u) { t->state = STRAIGHT_ABORTED; t->stop_ms = now; }
        else if (elapsed >= STRAIGHT_RUN_MS) {
            t->state = STRAIGHT_COMPLETE; t->stop_ms = now;
        } else set_run_output(t);
        return;
    }
    switch (t->state) {
    case STRAIGHT_WAIT_RELEASE:
        /* 上电必须连续松键1秒，避免复位时持键导致自动起跑。 */
        if (raw != 0u) t->state_since = now;
        else if (t->stable == 0u && (uint32_t)(now - t->state_since) >= 1000u)
            t->state = STRAIGHT_READY;
        break;
    case STRAIGHT_READY:
        if (t->stable != 0u) { t->state = STRAIGHT_HOLDING; t->state_since = now; }
        break;
    case STRAIGHT_HOLDING:
    case STRAIGHT_ARMED:
        if (t->stable == 0u) {
            /* 松键消抖的30ms不能补进实际长按时间。 */
            held = t->raw_since - t->state_since;
            if (t->state == STRAIGHT_ARMED && held >= 1000u && held < 5000u) {
                t->state = STRAIGHT_RUNNING; t->run_since = now;
                /* 32位对齐变量读取一次：本轮运行不接受中途参数变更。 */
                t->trim_applied_permille = g_straight_trim_permille;
                set_run_output(t);
            } else { t->state = STRAIGHT_WAIT_RELEASE; t->state_since = now; }
        } else if ((uint32_t)(now - t->state_since) >= 5000u)
            t->state = STRAIGHT_ABORTED; /* 卡键锁定，不在松开后补跑。 */
        else if (raw != 0u && (uint32_t)(now - t->state_since) >= 1000u)
            t->state = STRAIGHT_ARMED;
        break;
    case STRAIGHT_COMPLETE:
    case STRAIGHT_ABORTED: break;
    default: t->state = STRAIGHT_ABORTED; break;
    }
}

uint8_t straight_test_led(const straight_test_t *t, uint32_t now) {
    switch (t->state) {
    case STRAIGHT_READY: return (uint8_t)(now % 2500u < 100u);
    case STRAIGHT_ARMED:
    case STRAIGHT_RUNNING: return 1u;
    case STRAIGHT_COMPLETE: return (uint8_t)((now / 500u) % 2u);
    case STRAIGHT_HOLDING:
    case STRAIGHT_ABORTED: return (uint8_t)((now / 100u) % 2u);
    default: return 0u;
    }
}
