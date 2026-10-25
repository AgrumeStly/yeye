/**
 * @file motor_direct_gpio.h
 * @brief MotorDirect独立GPIO满导通接口：编译时选A或B单桥、人工一次500ms。
 *
 * MCU只提供3.3V逻辑，电机电流仍由AT8236及动力电池承担。
 * 不得把此接口理解为GPIO直接给电机供电；未选中的桥始终保持00。
 */
#ifndef YEYE_MOTOR_DIRECT_GPIO_H
#define YEYE_MOTOR_DIRECT_GPIO_H
#include <stdint.h>

/* 原因仅解释真实停止事件，不决定时间／是否允许驱动；单位无。 */
typedef enum {
    MOTOR_DIRECT_STOP_NONE = 0,
    MOTOR_DIRECT_STOP_TIMEOUT = 1,
    MOTOR_DIRECT_STOP_KEY = 2,
    MOTOR_DIRECT_STOP_FAULT = 3,
    MOTOR_DIRECT_STOP_LOGIC = 4,
    MOTOR_DIRECT_STOP_DIRECT = 6,
    MOTOR_DIRECT_STOP_EXCEPTION = 7,
    MOTOR_DIRECT_STOP_INVALID_MASK = 8
} motor_direct_stop_reason_t;

/** @brief GPIO真实寄存器快照，valid最后写1；不是实际电压／转动反馈。
 * ms单位ms，其余软件字段记录调用上下文；gpio_*与rcc_*直接读取MMIO。
 * 没有TIM1字段，因为本目标不启动TIM1；AFRH保留值也不代表GPIO模式下启用AF。
 */
typedef struct {
    uint32_t valid, run_id, ms, state, fault, mask;
    uint32_t gpio_moder, gpio_afrh, gpio_otyper, gpio_pupdr;
    uint32_t gpio_odr, gpio_idr, rcc_ahb1enr;
} motor_direct_gpio_snapshot_t;

/** @brief Keil保留诊断，复位清零，不写Flash。
 * enable_calls计GPIO置高调用完成次数；enable_count只在快照ODR四位与选定桥匹配时加1，
 * A目标为0x0200，B目标为0x2000；不能据此证明排针电压、H桥或电机正常。
 * elapsed_ms只在停止时写实际滴答差；初始化／重复停止不伪造事件或覆盖活动帧。
 */
typedef struct {
    uint32_t request_count, enable_calls, enable_count, stop_count, last_mask;
    uint32_t start_ms, stop_ms, elapsed_ms, stop_reason;
    motor_direct_gpio_snapshot_t active, stopped;
} motor_direct_gpio_diag_t;
extern volatile motor_direct_gpio_diag_t g_motor_direct_gpio_diag;

/* 先四脚GPIO低，再核对固定16MHz时钟；成功返回1，否则返回0且不允许试转。 */
int motor_direct_gpio_init(void);
/* mask单位无：0停止，A目标只接受1／PE9，B目标只接受2／PE13；其他值拒绝并停止。 */
int motor_direct_gpio_apply(uint8_t mask);
/* 立即写四脚低并恢复GPIO输出模式；初始化未开GPIO时不访问外设。 */
void motor_direct_gpio_stop(void);
/* 只保存真实软件上下文，无等待、无输出；由1ms监督在apply／stop之前调用。 */
void motor_direct_gpio_diag_context(uint32_t now, uint32_t state, uint32_t fault,
                                    motor_direct_stop_reason_t reason);
#endif
