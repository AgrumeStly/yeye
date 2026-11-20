/** @file speed_match.h
 * @brief 独立双轮同速台架：逐轮识别通道／方向，然后同目标RPM闭环。
 * 1ms调用按键／时限监督，20ms输入一次现有编码器算法结果；无UART依赖。
 */
#ifndef YEYE_SPEED_MATCH_H
#define YEYE_SPEED_MATCH_H
#include "encoder_counter.h"
#include "speed_pi.h"
#define SPEED_MATCH_SAMPLE_MS 20u
typedef enum {
    SPEED_WAIT_RELEASE, SPEED_READY, SPEED_HOLDING, SPEED_ARMED,
    SPEED_CALIBRATING, SPEED_RUNNING, SPEED_SETTLING, SPEED_FAULT
} speed_match_state_t;
typedef enum {
    SPEED_ERROR_NONE, SPEED_ERROR_KEY, SPEED_ERROR_STUCK_KEY, SPEED_ERROR_SAMPLE,
    SPEED_ERROR_MAPPING, SPEED_ERROR_CONFIG, SPEED_ERROR_NO_FEEDBACK,
    SPEED_ERROR_REVERSE, SPEED_ERROR_OVERSPEED, SPEED_ERROR_TIMING,
    SPEED_ERROR_HARDWARE, SPEED_ERROR_STATE, SPEED_ERROR_SYNC
} speed_match_error_t;
typedef struct {
    float target_rpm; /* 两轮共享10..SPEED_PI_MAX_TARGET_RPM；0可在运行中发停止请求。 */
    speed_pi_config_t pi;
    uint32_t run_ms; /* 500..3000，启动锁定，本轮不随Watch延长。 */
} speed_match_config_t;
typedef struct {
    speed_match_state_t state;
    speed_match_error_t error;
    uint32_t phase; /* 0=左轮500ms校准；1=右轮500ms；2=双轮同速。 */
    uint32_t run_since, stop_ms, sample_ms, sample_count, runs;
    uint32_t left_channel, right_channel; /* 0=未确认，1=软件a/TIM3，2=b/TIM4。 */
    int32_t left_sign, right_sign; /* 单轮校准所得前进系数，不修改底层AB相序。 */
    float left_rpm, right_rpm, difference_rpm;
    uint16_t left_pwm, right_pwm;
    uint32_t matched_ms; /* 当前持续满足两轮及目标误差各≤5RPM的时间，队内指标。 */
    uint32_t last_matched_ms; /* 上次运行结束时保留，不在待机中被0速覆盖。 */
    float last_left_rpm, last_right_rpm, last_difference_rpm; /* 停机前最后一帧滤波转速。 */
    uint16_t last_left_pwm, last_right_pwm; /* 同一停止事件保留的PWM，不表示当前仍输出。 */
    uint32_t left_saturated, right_saturated;
    speed_match_config_t active; /* 本轮锁定的目标、增益与时限。 */
#ifdef SPEED_SPRINT_TARGET
    float command_rpm; /* PI当前共同设定；SpeedMatch直接用目标，SpeedSprint按300RPM/s上升。 */
#endif
} speed_match_view_t;
extern volatile speed_match_config_t g_speed_config;
extern volatile speed_match_view_t g_speed_match;
/** @brief 清状态／PI及通道映射；上电不动。now单位ms，指针参数均须有效。 */
void speed_match_init(uint32_t now);
#ifdef RIGHT_ANGLE_TARGET
/** @brief 首弯专用：装载当前安装已实跑核实的映射，取消逐轮重新配对。
 * 无参数，返回1表示成功；只能在init后的零输出等待状态调用，否则返回0。
 * 依据2026-11-18 ground_03_capture：左TIM3/+1，右TIM4/-1。
 * 只安装已知配置，不把本次双轮测试称作重新识别左右通道；接线改变后须更新证据。
 */
int speed_match_use_verified_mapping(void);
#endif
/** @brief 每1ms调用；raw_key为KEY原始电平。先停机监督，再进行按键启动。 */
void speed_match_tick(uint32_t now, uint8_t raw_key);
/** @brief 复用现有encoder_counter结果；a/b为本次采样，必须每20ms调用。
 * invalid/status/flags异常、过期、反转／超速／无反馈均停止锁定，不以0伪装有效。
 */
void speed_match_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b);
/** @brief 外设／启动故障立即归零并锁定；由Core调用，无自动恢复。 */
void speed_match_fault(speed_match_error_t error, uint32_t now);
#ifdef SPEED_SPRINT_TARGET
/** @brief 仅结束正在进行的双轮闭环并保存结果，进入停稳等待；now单位ms。
 * 供直线试验距离限停使用；不会完成／跳过逐轮校准，也不会自动重新启动。
 */
void speed_match_finish(uint32_t now);
/** @brief 仅取消尚未松键的HOLDING／ARMED启动，退回松键等待；now单位ms。
 * 供SpeedSprint三秒按键“结束升档”手势使用；不结束运动，不跳过校准或解除故障。
 */
void speed_match_cancel_start(uint32_t now);
#endif
/** @brief 绿灯待机按阶段闪1/2/3次，运行常亮，故障快闪。 */
uint8_t speed_match_led(uint32_t now);
#endif
