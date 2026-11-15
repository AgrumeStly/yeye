/** @file lap_motion.h
 * @brief 独立低速循迹监督：复用SpeedMatch逐轮校准，校准后执行左右独立RPM。
 * 单位：时间ms、轮速RPM、PWM千分比；所有函数在统一1ms监督上下文调用。
 * 主循环提交通信结果时须用BASEPRI屏蔽SysTick状态写者，UART仅搬运字节可继续。
 */
#ifndef YEYE_LAP_MOTION_H
#define YEYE_LAP_MOTION_H
#include "speed_match.h"
typedef enum { LAP_CALIBRATION, LAP_WAIT, LAP_HOLD, LAP_ARMED, LAP_RUNNING, LAP_STOPPED, LAP_FAULT } lap_state_t;
typedef enum { LAP_OK, LAP_KEY, LAP_LINK, LAP_PATH, LAP_ENCODER, LAP_REVERSE, LAP_OVERSPEED,
               LAP_NO_FEEDBACK, LAP_CONFIG, LAP_HARDWARE, LAP_TRANSPORT, LAP_LIMIT } lap_reason_t;
typedef struct {
    float straight_rpm; /* 默认40RPM，10..60；不是已地面标定值。 */
    uint32_t run_ms; /* 默认3000ms做悬空／短线；停止时可明确改到300000ms一圈上限。 */
    float min_feedforward; /* 正目标前馈下限，PWM千分比，默认200、允许0..300。
                            * 不是实际输出下限：PI仍可减到0，零目标始终停轮。
                            * 只在停稳时调整，下次人工启动锁定；不是实测电机阈值。
                            */
} lap_config_t;
typedef struct {
    lap_state_t state;
    lap_reason_t reason;
    uint32_t run_since, path_at, received, rejected, duplicates, starts_rejected;
    float left_target, right_target, left_rpm, right_rpm;
    uint16_t left_pwm, right_pwm;
    int16_t steering;
    uint16_t bend;
    uint8_t path_valid, history, single;
    lap_config_t active;
} lap_view_t;
/** @brief 最后一次真正进入RUN的停止快照；停车后不被实时零速或末尾STOP覆盖。
 * valid=1表示已有完整停止记录；elapsed_ms为从人工启动到撤驱动的本板时间。
 * 转速为最后20ms样本的滤波RPM，PWM为撤驱动前请求的千分比，不是地面测速。
 * boost_samples记录各轮本次实际使用起步补偿的20ms样本数，非实测扭矩。
 */
typedef struct {
    uint32_t valid, elapsed_ms;
    lap_reason_t reason;
    float left_target, right_target, left_rpm, right_rpm;
    uint16_t left_pwm, right_pwm;
    uint32_t left_boost_samples, right_boost_samples;
} lap_result_t;
extern volatile lap_config_t g_lap_config;
extern volatile lap_view_t g_lap;
extern volatile lap_result_t g_lap_last;
void lap_motion_init(uint32_t now);
/** @brief 1ms监督KEY／200ms通信／运行上限；长按1..3秒后松开启动，5秒卡键故障。
 * 前两次仍为单轮500ms校准；校准后的启动必须有当前双边新鲜路径，历史不能启动。
 */
void lap_motion_tick(uint32_t now, uint8_t key);
/** @brief 每20ms输入真实原编码器样本；任何状态都检查样本连续性。
 * 目标为0的内轮允许无脉冲；目标由0变为正时重新计300ms无反馈时限。
 */
void lap_motion_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b);
/** @brief 新版本20字节消息接收；bytes必须CRC／格式已核实；arrival为最后字节ISR时间。
 * STOP始终生效；不允许远程START，正式一键启动由车载KEY完成。
 */
void lap_motion_receive(const uint8_t *bytes, uint32_t arrival, uint32_t now);
void lap_motion_fault(lap_reason_t reason, uint32_t now);
uint8_t lap_motion_led(uint32_t now);
#endif
