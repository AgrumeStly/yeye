/**
 * @file motor_bench.h
 * @brief C-02B首次开环试转的纯逻辑接口，不访问寄存器，供板端与电脑测试共用。
 * A/B仅表示AT8236桥编号，不表示已标定的左右轮或车辆前进方向。
 */
#ifndef YEYE_MOTOR_BENCH_H
#define YEYE_MOTOR_BENCH_H
#include <stdint.h>

/* 全部时间单位为ms；每次都必须重新松键，再长按并松开，禁止自动连跑。 */
#define MOTOR_BENCH_RELEASE_MS 1000u
#define MOTOR_BENCH_DEBOUNCE_MS 30u
#define MOTOR_BENCH_HOLD_MS 1000u
#define MOTOR_BENCH_STUCK_MS 5000u
#define MOTOR_BENCH_RUN_MS 500u /* MotorBench／MotorDirect时限；MotorContinuous不使用。 */
#define MOTOR_BENCH_MASK_A 1u
#define MOTOR_BENCH_MASK_B 2u

typedef enum {
    MOTOR_BENCH_WAIT_RELEASE, /* 上电或阶段之间，连续松键1s后才接收新操作。 */
    MOTOR_BENCH_READY,        /* LED闪1/2/3次，提示下一次为A/B/AB。 */
    MOTOR_BENCH_HOLDING,      /* 已消抖按下，尚未长按满1s。 */
    MOTOR_BENCH_ARMED,        /* 长按达标，松开并消抖后才试转。 */
    MOTOR_BENCH_RUNNING,      /* 运行中原始按键高电平立即停止，不等待消抖。 */
    MOTOR_BENCH_COMPLETE,     /* MotorBench三次／MotorDirect一次结束，均禁止循环。 */
    MOTOR_BENCH_ABORTED       /* 手动停止、按键卡住或异常状态，复位才能重来。 */
} motor_bench_state_t;

typedef struct {
    motor_bench_state_t state;
    uint32_t state_since, raw_since, run_since;
    uint8_t step;             /* 0=A、1=B、2=AB；不用于推断左右轮。 */
    uint8_t raw_candidate;    /* 最新原始电平，1为按下。 */
    uint8_t stable_button;    /* 连续30ms稳定后的电平。 */
    uint8_t output_mask;      /* 0停止、1仅A、2仅B、3双桥。 */
} motor_bench_t;

/* 初始化只产生零输出；now为uint32毫秒时间，所有时间差支持回绕。 */
void motor_bench_init(motor_bench_t *bench, uint32_t now);
/* 每1ms调用；raw_pressed为PA0原始电平。函数无阻塞、无自动重试。 */
void motor_bench_tick(motor_bench_t *bench, uint32_t now, uint8_t raw_pressed);
/* 返回PB2用户灯的期望电平；只作操作提示，不作为实测转动反馈。 */
uint8_t motor_bench_led(const motor_bench_t *bench, uint32_t now);
#endif
