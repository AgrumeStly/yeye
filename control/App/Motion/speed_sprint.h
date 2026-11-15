/** @file speed_sprint.h
 * @brief 比赛直线带载候选速度试验：人工逐次确认，不以轮速相同推定没有跑偏。
 * 只由SpeedSprint独立目标链接；复用speed_match的校准、闭环和故障监督。
 * 所有周期入口在同一SysTick内顺序调用，主循环不写控制状态。
 */
#ifndef YEYE_SPEED_SPRINT_H
#define YEYE_SPEED_SPRINT_H
#include "speed_match.h"
typedef struct {
    uint32_t distance_limit_mm; /* 默认1500，允许200..3000mm；只限制驱动轮程，不含滑行。 */
    float wheel_diameter_mm; /* 默认67.5mm，来自采购几何参考；应按实物轮胎校核。 */
    uint32_t search_enabled; /* 1=每档人工接受3次后建议+20RPM；0=保持当前目标。 */
} speed_sprint_config_t;
typedef enum {
    SPRINT_NO_RESULT, SPRINT_ENCODER_PASS, SPRINT_SATURATED,
    SPRINT_NOT_VERIFIED, SPRINT_FAULTED
} speed_sprint_result_t;
typedef struct {
    uint32_t result_id, reviewed_id;
    uint32_t last_result; /* 编码器结果不代表地面直行；见speed_sprint_result_t。 */
    uint32_t stop_reason; /* 0=无，1=时间到，2=轮程到，3=故障。 */
    uint32_t accepted_runs; /* 同一目标、同一设置下连续人工接受次数，满3记录候选。 */
    uint32_t review_error; /* 0=无；1=运行中命令；2=无可审结果；3=编码器未达标；4=无已确认速度。 */
    float best_rpm; /* 三次人工接受的最高地面候选，复位清零，不是物理极速／正式比赛速度。 */
    float next_rpm; /* 下一次KEY使用的目标镜像；真正配置仍为g_speed_config.target_rpm。 */
    float last_target_rpm;
    float left_distance_mm, right_distance_mm, last_distance_mm;
    uint32_t last_saturated_ms; /* 本次最长连续100%且欠速时间，不能据此唯一判断机械极限。 */
    uint32_t mismatch_ms; /* 起步500ms后，两轮差>20RPM的连续时间；达到200ms故障撤驱动。 */
    speed_sprint_config_t active; /* 启动时锁定距离、轮径和搜索模式。 */
} speed_sprint_view_t;
extern volatile speed_sprint_config_t g_sprint_config;
extern volatile speed_sprint_view_t g_sprint;
/** 停稳后写1=接受本次地面直行，2=拒绝／跑偏，3=选用best并停止自动升档。
 * 命令消费后归零；每个result_id只可接受一次；运行中命令丢弃并提示，不延后执行。
 * 这是赛前人工确认入口，正式比赛运行不得使用该方式遥控或调参。
 */
extern volatile uint32_t g_sprint_review;
/** @brief 上电初始化，now单位ms；清试验结果并复用原校准状态，不启动电机。 */
void speed_sprint_init(uint32_t now);
/** @brief 每1ms调用，raw_key为KEY原始电平；复用停止优先、长按松开与限时。 */
void speed_sprint_tick(uint32_t now, uint8_t raw_key);
/** @brief 每20ms输入原采样结果；先执行闭环与反馈保护，再核算轮程并按需撤驱动。
 * a/b须有效对象；无效窗口交由原状态机锁定，不用伪造0速继续控制。
 */
void speed_sprint_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b);
/** @brief Core外设故障入口：立即归零、锁定并保存本次失败，不能人工接受。 */
void speed_sprint_fault(speed_match_error_t error, uint32_t now);
/** @brief 返回绿灯0/1，无外设访问；校准／运动／故障沿用原指示。
 * 双轮待机：状态短闪后，三位十进制RPM报数，0为600ms长亮，1..9为相应次数短闪。
 * 1=待试，2=待人工确认的编码器达标，3=保持已确认档，4=未达标，5=按键命令未接受。
 * KEY短按约0.2..0.5秒接受地面结果；长按1..2秒松开启动；长按约3秒松开结束升档。
 * 仅待机受理确认手势；运行按KEY仍立即锁定停止，卡键5秒仍故障。
 */
uint8_t speed_sprint_led(uint32_t now);
#endif
