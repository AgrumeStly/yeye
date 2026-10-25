/** @file motor_bench_pwm.h
 * @brief MotorBench/MotorContinuous固定PWM适配层，与整车board_apply_requests无连接。
 */
#ifndef YEYE_MOTOR_BENCH_PWM_H
#define YEYE_MOTOR_BENCH_PWM_H
#include <stdint.h>
#ifdef MOTOR_CONTINUOUS_A_TARGET
#define MOTOR_BENCH_PWM_PERIOD 800u  /* 持续目标仍为20kHz、30%。 */
#define MOTOR_BENCH_DUTY_PERMILLE 300u
#else
/* 重写单次测试：16MHz/16000=1kHz，8000/16000=50%，不是转速设定。
 * 仅悬空开环起转，500ms与KEY停止由应用层监督；无自动加功率。
 */
#define MOTOR_BENCH_PWM_PERIOD 16000u
#define MOTOR_BENCH_DUTY_PERMILLE 500u
#endif

/* 停止原因只解释已有控制分支，不参与是否驱动的决定。0表示尚无结束事件。
 * KEY=运行中原始按键停止；LOGIC=卡键／状态异常；DIRECT=无专用上下文的停止。
 */
typedef enum {
    MOTOR_BENCH_STOP_NONE = 0,
    MOTOR_BENCH_STOP_TIMEOUT = 1,
    MOTOR_BENCH_STOP_KEY = 2,
    MOTOR_BENCH_STOP_FAULT = 3,
    MOTOR_BENCH_STOP_LOGIC = 4,
    MOTOR_BENCH_STOP_MASK_CHANGE = 5,
    MOTOR_BENCH_STOP_DIRECT = 6,
    MOTOR_BENCH_STOP_EXCEPTION = 7,
    MOTOR_BENCH_STOP_INVALID_MASK = 8
} motor_bench_stop_reason_t;

/** @brief 一次实际寄存器读取；valid最后写1，0表示尚未采集完整。
 * ms/state/fault/mask/run_id是采集时的软件上下文，其余字段直接读硬件寄存器。
 * TIM/GPIO寄存器逐项读取，并非同一CPU周期的原子快照；CNT/IDR仅为瞬时读数，
 * 不用于声称测得频率、电压或完整波形。停止后读取，避免在捕获期间混读字段。
 */
typedef struct {
    uint32_t valid, run_id, ms, state, fault, mask;
    uint32_t tim_cr1, tim_psc, tim_arr, tim_cnt, tim_ccer, tim_bdtr;
    uint32_t tim_ccmr1, tim_ccmr2, tim_ccr1, tim_ccr2, tim_ccr3, tim_ccr4;
    uint32_t gpio_moder, gpio_afrh, gpio_otyper, gpio_pupdr, gpio_odr, gpio_idr;
    uint32_t rcc_ahb1enr, rcc_apb2enr;
} motor_bench_pwm_snapshot_t;

/** @brief Keil Watch保留诊断，复位清零；后一次启用替换上一组，不写Flash。
 * request_count只计新的非零mask请求，1ms重复调用不累加；非法非零mask也计请求。
 * enable_calls计真正执行并返回的MOE启用调用；enable_count仅在活动快照读回MOE=1时增加。
 * 这两个计数均不代表电机转动；若MOE未置位，仍保留valid活动读数以便定位。
 * stop_count只计启用调用后的一次停止，初始化与重复停止不覆盖已保留证据。
 * start_ms/stop_ms/elapsed_ms单位ms，elapsed为实际滴答差（支持uint32回绕），不是500常量。
 */
typedef struct {
    uint32_t request_count, enable_calls, enable_count, stop_count, last_mask;
    uint32_t start_ms, stop_ms, elapsed_ms, stop_reason;
    motor_bench_pwm_snapshot_t active, stopped;
} motor_bench_pwm_diag_t;
extern volatile motor_bench_pwm_diag_t g_motor_bench_pwm_diag;

/* 只更新诊断上下文，不读写硬件、不触发输出；在原控制逻辑决定后、apply/stop前调用。
 * now单位ms；state为motor_bench_state_t的数值；fault为粘性故障位；reason仅解释停止。
 */
void motor_bench_pwm_diag_context(uint32_t now, uint32_t state, uint32_t fault,
                                  motor_bench_stop_reason_t reason);

/* 初始化为四路GPIO低电平；返回1表示16MHz时钟配置及PWM准备通过，否则保持停止。 */
int motor_bench_pwm_init(void);
/* mask只接受0/1/2/3；1=A的IN1 PWM，2=B的IN1 PWM；IN2始终GPIO低。
 * 返回1成功；0为非法请求/未初始化/MOE读回失败，入口须锁存故障并停止。
 */
int motor_bench_pwm_apply(uint8_t mask);
/* 取消MOE并把四根脚改为主动低GPIO，形成00滑行；不代表机械瞬时停稳。 */
void motor_bench_pwm_stop(void);
#endif
