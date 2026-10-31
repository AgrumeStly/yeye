/** @file straight_test.h
 * @brief 双轮开环直行测试：人工启动，固定输出3秒、锁定停车。
 * 占空比不是实际轮速；没有编码器修正，不保证车身一定走直。
 */
#ifndef YEYE_STRAIGHT_TEST_H
#define YEYE_STRAIGHT_TEST_H
#include <stdint.h>
#define STRAIGHT_RUN_MS 3000u
#define STRAIGHT_BASE_PERMILLE 500u /* 基准50%，不得超过驱动层的50%上限。 */
/* 单位为PWM占空比千分点：+20使右轮少2个百分点，-20使左轮少2个百分点。
 * 变量定义及默认值在straight_test.c；启动时读取一次并限幅，运行中不跟随修改。
 */
extern volatile int32_t g_straight_trim_permille;
typedef enum {
    STRAIGHT_WAIT_RELEASE, STRAIGHT_READY, STRAIGHT_HOLDING,
    STRAIGHT_ARMED, STRAIGHT_RUNNING,
    STRAIGHT_COMPLETE, STRAIGHT_ABORTED
} straight_state_t;
typedef struct {
    straight_state_t state;
    uint32_t state_since, raw_since, run_since, stop_ms;
    int32_t trim_applied_permille; /* 本次启动锁定的限幅后修正量。 */
    uint16_t left_duty_permille, right_duty_permille; /* 0..500，均为0时撤驱动。 */
    uint8_t candidate, stable;
} straight_test_t;
/** @brief 清零并等待松键；now单位ms，复位后不恢复上次运动。 */
void straight_test_init(straight_test_t *test, uint32_t now);
/** @brief 每1ms调用；raw为KEY原始电平，高=按下；无阻塞，时间差支持回绕。 */
void straight_test_tick(straight_test_t *test, uint32_t now, uint8_t raw);
/** @brief 返回绿灯电平；只提示状态，不表示实测转速或车辆位置。 */
uint8_t straight_test_led(const straight_test_t *test, uint32_t now);
#endif
