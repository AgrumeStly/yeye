/** @file lap_motion.h
 * @brief 独立低速循迹监督：复用SpeedMatch逐轮校准，校准后执行左右独立RPM。
 * 单位：时间ms、轮速RPM、PWM千分比；所有函数在统一1ms监督上下文调用。
 * 主循环提交通信结果时须用BASEPRI屏蔽SysTick状态写者，UART仅搬运字节可继续。
 */
#ifndef YEYE_LAP_MOTION_H
#define YEYE_LAP_MOTION_H
#include "speed_match.h"
/* 同一套控制策略可配两种启动入口。语音版复用轮位，直接等待地面路径与Go。 */
#if defined(RIGHT_ANGLE_VOICE_TARGET) || defined(STRAIGHT_VOICE_TARGET)
#define LAP_VOICE_START 1
#elif defined(RIGHT_ANGLE_TARGET) || defined(STRAIGHT_DUAL_START_TARGET)
#define LAP_DUAL_STARTUP 1
#endif
typedef enum { LAP_CALIBRATION, LAP_WAIT, LAP_HOLD, LAP_ARMED, LAP_RUNNING, LAP_STOPPED, LAP_FAULT } lap_state_t;
typedef enum { LAP_OK, LAP_KEY, LAP_LINK, LAP_PATH, LAP_ENCODER, LAP_REVERSE, LAP_OVERSPEED,
               LAP_NO_FEEDBACK, LAP_CONFIG, LAP_HARDWARE, LAP_TRANSPORT, LAP_LIMIT,
               LAP_VOICE_STOP } lap_reason_t;
typedef struct {
    float straight_rpm; /* 旧目标默认40、10..60；StraightAssist默认80、40..100；RightAngle默认60、40..80RPM。 */
    uint32_t run_ms; /* 单次运动上限ms。直道默认2000，首弯默认12000，联合弯默认40000。 */
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
    uint8_t path_valid, history, single; /* 首弯v5沿用布局：history=当前出口弱关联，single=当前L预测。
                                        * 其它旧目标仍按原历史／单边语义解码，协议版本互斥。
                                        */
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
/* 固定32个20ms窗口（约640ms）的只读取证环，不参与目标、PWM或故障判定。
 * total_samples表示本次RUN已记录数量；有效槽数为min(total_samples,32)，
 * 第k个样本在samples[k%32]。停止时先冻结，待机／后续相机包不覆盖。
 * 原始计数已按校准通道映射到物理左／右，但delta保留编码器原始符号；
 * raw_rpm才乘前进系数。PWM和目标是本次采样进入控制计算前的请求。
 */
#define LAP_DIAG_SAMPLES 32u
typedef struct {
    uint32_t at_ms, dt_ms, received, path_at;
    int32_t left_delta, right_delta, left_counts_per_s, right_counts_per_s;
    float left_raw_rpm, right_raw_rpm, left_target, right_target;
    uint16_t left_pwm, right_pwm;
    int16_t steering;
    uint16_t bend;
    uint8_t history, single, path_valid, path_sequence; /* 实际最后接受的PATH序号，0..255。 */
} lap_diag_sample_t;
typedef struct {
    uint32_t total_samples, frozen, stop_at_ms, stop_reason;
    uint32_t left_channel, right_channel;
    int32_t left_sign, right_sign;
    lap_diag_sample_t samples[LAP_DIAG_SAMPLES];
} lap_diag_view_t;
extern volatile lap_config_t g_lap_config;
extern volatile lap_view_t g_lap;
extern volatile lap_result_t g_lap_last;
extern volatile lap_diag_view_t g_lap_diag;
#ifdef LAP_DUAL_STARTUP
/** @brief 首弯／直道适配版共用启动监督，与g_lap既有布局独立，便于保留旧取证工具。
 * stage：0等首次双轮悬空测试，1正在测试，2测试完成可上道；所有时间ms。
 * completed只在两轮反馈及完整1秒测试均通过后置1；复位后须重新双轮测试。
 * blocked_reason是最近一次KEY被拒绝的lap_reason_t数值，不锁故障。
 * counts为按已核实前进符号换算的本次双轮测试净计数，不重新推断左右映射。
 */
typedef struct {
    uint32_t stage, bench_ms, completed, ground_runs;
    int32_t left_counts, right_counts;
    uint32_t starts_blocked, blocked_reason;
} corner_startup_t;
extern volatile corner_startup_t g_corner_startup;
#endif
void lap_motion_init(uint32_t now);
/** @brief 1ms监督KEY／200ms通信／运行上限；长按1..3秒后松开启动，5秒卡键故障。
 * 原目标前两次单轮配对；首弯／直道适配目标第一次KEY双轮悬空1秒，下一次KEY上道。
 * 首弯v5上道允许当前双侧或当前L形预测，弱关联不能冷启动；旧目标保持双边要求。
 * 首次双轮测试不依赖相机，不跟随弯道差速。
 * 语音目标只将KEY作为启动抑制及紧急停止输入。
 */
void lap_motion_tick(uint32_t now, uint8_t key);
/** @brief 每20ms输入真实原编码器样本；任何状态都检查样本连续性。
 * 目标为0的内轮允许无脉冲；目标由0变为正时重新计300ms无反馈时限。
 */
void lap_motion_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b);
/** @brief 20字节消息接收；bytes必须CRC／字段及目标版本已核实；arrival为最后字节ISR时间。
 * STOP始终生效；语音直道v6和语音首弯v9接纳与当前PATH序号绑定的START。
 */
void lap_motion_receive(const uint8_t *bytes, uint32_t arrival, uint32_t now);
void lap_motion_fault(lap_reason_t reason, uint32_t now);
#ifdef LAP_VOICE_START
void lap_motion_transport_fault(uint32_t now);
#endif
uint8_t lap_motion_led(uint32_t now);
#endif
