/**
 * @file motor_bench.c
 * @brief 按键驱动的一次性A→B→AB试转序列，输出只允许固定掩码。
 *
 * 控制逻辑在SysTick中每1ms执行，电脑测试直接调用同一实现。
 * 长按不直接起转：必须松开后才运行，便于运行中用同一按键发停止请求。
 * 正常超时才推进下一阶段；人工停止立即锁定，防止误将异常测试继续为双桥。
 * 2026-10-24新增独立MotorContinuous目标：只允许A桥，人工启动后持续输出，
 * KEY停止／故障／复位仍撤驱动；宏只在该目标定义，原MotorBench仍为500ms三步序列。
 * MotorDirect使用同一人工触发逻辑，但只允许A桥一次500ms，结束后锁定；
 * 真正的高低电平由独立GPIO适配器生成，不使用原PWM适配器。
 */
#include "motor_bench.h"
#include <string.h>

/** @brief 进入等待松键状态；now单位ms，阶段编号保留，输出立即归零。 */
static void wait_release(motor_bench_t *b, uint32_t now) {
    b->state = MOTOR_BENCH_WAIT_RELEASE;
    b->state_since = now;
    b->output_mask = 0u;
}

void motor_bench_init(motor_bench_t *b, uint32_t now) {
    /* 不从之前的RAM值恢复进度；复位后重新从A开始且必须重新人工触发。 */
    memset(b, 0, sizeof(*b));
    b->raw_since = now;
    wait_release(b, now);
}

void motor_bench_tick(motor_bench_t *b, uint32_t now, uint8_t raw_pressed) {
    uint8_t raw = raw_pressed != 0u ? 1u : 0u;
    uint32_t held;

    /* 消抖只用于启动操作；停止检查直接使用raw，宁可误停也不延后停止。 */
    if (raw != b->raw_candidate) {
        b->raw_candidate = raw;
        b->raw_since = now;
    }
    if ((uint32_t)(now - b->raw_since) >= MOTOR_BENCH_DEBOUNCE_MS)
        b->stable_button = raw;

#if defined(MOTOR_CONTINUOUS_A_TARGET) || defined(MOTOR_DIRECT_A_TARGET)
    /* 两种单A诊断都只允许step=0；禁止错误阶段值切到B或双桥。 */
    if (b->step != 0u) {
#else
    if (b->step > 2u) {
#endif
        b->state = MOTOR_BENCH_ABORTED;
        b->output_mask = 0u;
        return;
    }
    if (b->state == MOTOR_BENCH_RUNNING) {
        if (raw != 0u) {
            b->output_mask = 0u;
            b->state = MOTOR_BENCH_ABORTED;
        }
#ifndef MOTOR_CONTINUOUS_A_TARGET
        /* MotorBench及MotorDirect启用500ms超时。持续目标按本轮要求等人工停止，
         * 不靠改写run_since或反复重启500ms窗口伪装连续，按键检查始终优先。
         */
        else if ((uint32_t)(now - b->run_since) >= MOTOR_BENCH_RUN_MS) {
            b->output_mask = 0u;
#ifdef MOTOR_DIRECT_A_TARGET
            /* 固定高低电平相当于满导通，只允许一次短时诊断；超时立即锁定，
             * 不进入B／AB，也不能在松键后重复触发，复测必须先断动力再复位。
             */
            b->state = MOTOR_BENCH_COMPLETE;
#else
            if (b->step == 2u) b->state = MOTOR_BENCH_COMPLETE;
            else { ++b->step; wait_release(b, now); }
#endif
        }
#endif
        return;
    }

    /* 只有下方已完成长按+松开的分支能设置非零输出，其他路径一律停止。 */
    b->output_mask = 0u;
    switch (b->state) {
    case MOTOR_BENCH_WAIT_RELEASE:
        if (raw != 0u) b->state_since = now;
        else if (b->stable_button == 0u &&
                 (uint32_t)(now - b->state_since) >= MOTOR_BENCH_RELEASE_MS)
            b->state = MOTOR_BENCH_READY;
        break;
    case MOTOR_BENCH_READY:
        if (b->stable_button != 0u) {
            b->state = MOTOR_BENCH_HOLDING;
            b->state_since = now;
        }
        break;
    case MOTOR_BENCH_HOLDING:
    case MOTOR_BENCH_ARMED:
        if (b->stable_button == 0u) {
            /* 用原始松键时刻计算持续时间，不能把松键消抖30ms算进长按。 */
            held = (uint32_t)(b->raw_since - b->state_since);
            if (b->state == MOTOR_BENCH_ARMED && held >= MOTOR_BENCH_HOLD_MS &&
                held < MOTOR_BENCH_STUCK_MS) {
                b->output_mask = b->step == 0u ? MOTOR_BENCH_MASK_A :
                    (b->step == 1u ? MOTOR_BENCH_MASK_B :
                     (MOTOR_BENCH_MASK_A | MOTOR_BENCH_MASK_B));
                b->run_since = now;
                b->state = MOTOR_BENCH_RUNNING;
            } else wait_release(b, now);
        } else if ((uint32_t)(now - b->state_since) >= MOTOR_BENCH_STUCK_MS) {
            b->state = MOTOR_BENCH_ABORTED; /* 连续按住5s视为卡键，不在松开时补跑。 */
        } else if (raw != 0u && (uint32_t)(now - b->state_since) >= MOTOR_BENCH_HOLD_MS) {
            b->state = MOTOR_BENCH_ARMED;
        }
        break;
    case MOTOR_BENCH_COMPLETE:
    case MOTOR_BENCH_ABORTED:
        break; /* 终态保持，释放或再按都不能重新运行；重新测试需RESET。 */
    default:
        b->state = MOTOR_BENCH_ABORTED;
        break;
    }
}

uint8_t motor_bench_led(const motor_bench_t *b, uint32_t now) {
    uint32_t phase;
    switch (b->state) {
    case MOTOR_BENCH_READY:
        /* 每2.5s提示一组：每次亮100ms、间隔200ms，组内闪step+1次。 */
        phase = now % 2500u;
        return (uint8_t)(phase / 300u <= (uint32_t)b->step && phase % 300u < 100u);
    case MOTOR_BENCH_HOLDING: return (uint8_t)((now / 100u) % 2u);
    case MOTOR_BENCH_ARMED:
    case MOTOR_BENCH_RUNNING: return 1u;
    case MOTOR_BENCH_COMPLETE: return (uint8_t)((now / 500u) % 2u);
    case MOTOR_BENCH_ABORTED: return (uint8_t)((now / 100u) % 2u);
    default: return 0u;
    }
}
