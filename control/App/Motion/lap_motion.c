/** @file lap_motion.c
 * @brief 低速试跑应用策略。原目标逐轮校准；首弯／直道适配版沿用实证映射做双轮测试。
 * 校准结束后不让原共同目标／3秒策略参与巡航；左右独立PI仍用原数学模块。
 * 视觉偏差右正：右转时左轮更快、右轮减速，最大只前进不带电换向。
 */
#include "lap_motion.h"
#include <string.h>
#include <float.h>
#if defined(STRAIGHT_ASSIST_TARGET) || defined(RIGHT_ANGLE_TARGET)
#include "straight_guide.h"
#endif
#ifdef RIGHT_ANGLE_TARGET
#include "corner_guide.h"
/* 首弯快过弯候选：80RPM接近、满弯平均60RPM，默认12秒试跑窗口。
 * 限时只限制范围，不触发转弯；每个20ms目标均来自当前v5观测／预测路径。
 */
volatile lap_config_t g_lap_config = {80.0f, 12000u, 200.0f};
volatile corner_guide_t g_corner_guide;
#ifdef LAP_DUAL_STARTUP
volatile corner_startup_t g_corner_startup;
#endif
static uint32_t corner_pair_at;
static uint8_t corner_pair_seen;
#define LAP_MIN_CRUISE 40.0f
#define LAP_MAX_CRUISE 80.0f
#ifdef RIGHT_ANGLE_VOICE_TARGET
#define LAP_MAX_RUN_MS 12000u
#else
#define LAP_MAX_RUN_MS 15000u
#endif
#elif defined(STRAIGHT_ASSIST_TARGET)
/* 独立直道候选：2秒、80RPM；只改变本目标，不放宽旧循迹目标的参数边界。 */
volatile lap_config_t g_lap_config = {80.0f, 2000u, 200.0f};
volatile straight_guide_t g_straight_guide;
/* 独立Watch取证，不改变g_lap及原冻结环布局；单位分别RPM与PWM千分比。 */
volatile float g_straight_sync_error, g_straight_sync_adjustment;
#define LAP_MIN_CRUISE 40.0f
#define LAP_MAX_CRUISE 100.0f
#ifdef STRAIGHT_VOICE_TARGET
#define LAP_MAX_RUN_MS 2000u
#else
#define LAP_MAX_RUN_MS 3000u
#endif
#elif defined(LAP_TRACK_TARGET)
/* 只有GUI明确选择Track目标才默认允许最长5分钟；仍须逐轮悬空校准与人工启动。
 * 原LowSpeedLap目标继续3秒，避免断电后RAM设置丢失而无法识别实际运行期限。
 */
volatile lap_config_t g_lap_config = {40.0f, 300000u, 200.0f};
#else
volatile lap_config_t g_lap_config = {40.0f, 3000u, 200.0f};
#endif
#if !defined(STRAIGHT_ASSIST_TARGET) && !defined(RIGHT_ANGLE_TARGET)
#define LAP_MIN_CRUISE 10.0f
#define LAP_MAX_CRUISE 60.0f
#define LAP_MAX_RUN_MS 300000u
#endif
#ifdef STRAIGHT_DUAL_START_TARGET
/* 复用首弯已实现的双轮启动状态，独立于直道PI及视觉策略；不更改既有取证布局。 */
volatile corner_startup_t g_corner_startup;
#endif
volatile lap_view_t g_lap;
volatile lap_result_t g_lap_last;
volatile lap_diag_view_t g_lap_diag;
static speed_pi_t left_pi, right_pi;
static uint32_t state_at, raw_at, last_sample, quiet_ms, edge_at[2];
static uint32_t sequence_at[2];
static uint8_t raw_candidate, stable, seen[2], sequences[2], have_sample;
static uint8_t last_path_sequence;
static float previous_target[2];
/* 仅为静止起步提供短时已受限输出；不是轮速标定，也不放宽无反馈保护。
 * 50%沿用已确认逐轮500ms校准的上限；这里每次最多100ms，反馈一到即退出。
 */
#define LAP_START_BOOST_MS 100u
#define LAP_START_BOOST_DUTY 500u
static uint32_t boost_at[2], boost_samples[2];
static uint8_t boost_pending[2];
static float absf(float x) { return x < 0.0f ? -x : x; }
static int finitef(float x) { return x == x && x <= FLT_MAX && x >= -FLT_MAX; }
static void zero(void) {
    g_lap.left_pwm = g_lap.right_pwm = 0u;
    g_lap.left_target = g_lap.right_target = 0.0f;
    previous_target[0] = previous_target[1] = 0.0f;
    boost_pending[0] = boost_pending[1] = 0u;
    speed_pi_reset(&left_pi); speed_pi_reset(&right_pi);
#ifdef LAP_DUAL_STARTUP
    /* 被KEY／STOP／故障提前打断的双轮测试不能解锁上道；正常完成先置stage2。
     * 这里只复位测试阶段，保留净计数及停止快照供定位，不重置已核实通道。
     */
    if (g_corner_startup.stage == 1u && g_lap.state != LAP_RUNNING) g_corner_startup.stage = 0u;
#endif
#ifdef RIGHT_ANGLE_TARGET
    {
        corner_guide_t empty;
        corner_guide_reset(&empty); g_corner_guide = empty;
    }
#endif
#ifdef STRAIGHT_ASSIST_TARGET
    /* 所有停止路径都清直道滤波和斜坡；用局部副本避免volatile指针被强转。 */
    {
        straight_guide_t empty;
        straight_guide_reset(&empty); g_straight_guide = empty;
        g_straight_sync_error = g_straight_sync_adjustment = 0.0f;
    }
#endif
}
/** @brief 只在离开RUN时留存一次结果；必须在zero和状态切换之前调用。
 * 参数为本地ms与本次停止原因；后续待机、故障重复上报或K230清理STOP不覆盖。
 */
static void save_result(uint32_t now, lap_reason_t reason) {
    if (g_lap.state != LAP_RUNNING) return;
    /* 所有RUN退出共用同一冻结点；不得为了取证延后原有撤PWM／锁故障。
     * 非编码器采样触发的停车，末槽只是最近采样，不冒称故障字节的时刻。
     */
    g_lap_diag.stop_at_ms = now; g_lap_diag.stop_reason = (uint32_t)reason;
    g_lap_diag.frozen = 1u;
    g_lap_last.valid = 0u;
    g_lap_last.elapsed_ms = now - g_lap.run_since; g_lap_last.reason = reason;
    g_lap_last.left_target = g_lap.left_target; g_lap_last.right_target = g_lap.right_target;
    g_lap_last.left_rpm = g_lap.left_rpm; g_lap_last.right_rpm = g_lap.right_rpm;
    g_lap_last.left_pwm = g_lap.left_pwm; g_lap_last.right_pwm = g_lap.right_pwm;
    g_lap_last.left_boost_samples = boost_samples[0]; g_lap_last.right_boost_samples = boost_samples[1];
    g_lap_last.valid = 1u;
}
void lap_motion_fault(lap_reason_t reason, uint32_t now) {
    save_result(now, reason);
    if (g_lap.state != LAP_FAULT) g_lap.reason = reason;
    /* 连同复用校准器一起锁住，避免已撤驱动后仍保持CALIBRATING并累计计数。
     * 校准器自己的原始故障已存在时保留，新增策略原因以g_lap.reason为准。
     */
    if (g_speed_match.state != SPEED_FAULT) speed_match_fault(SPEED_ERROR_STATE, now);
    g_lap.state = LAP_FAULT; state_at = now; zero();
}
void lap_motion_init(uint32_t now) {
    lap_view_t empty;
    lap_result_t empty_result;
    memset(&empty, 0, sizeof(empty)); g_lap = empty;
    memset(&empty_result, 0, sizeof(empty_result)); g_lap_last = empty_result;
    memset((void *)&g_lap_diag, 0, sizeof(g_lap_diag));
    memset(boost_at, 0, sizeof(boost_at)); memset(boost_samples, 0, sizeof(boost_samples));
    g_lap.state = LAP_CALIBRATION;
    state_at = raw_at = last_sample = now; quiet_ms = 0u;
    raw_candidate = stable = have_sample = 0u;
    last_path_sequence = 0u;
    memset(seen, 0, sizeof(seen)); memset(sequences, 0, sizeof(sequences));
    memset(sequence_at, 0, sizeof(sequence_at));
    edge_at[0] = edge_at[1] = now;
#ifdef RIGHT_ANGLE_TARGET
    corner_pair_at = now; corner_pair_seen = 0u;
#endif
#ifdef LAP_DUAL_STARTUP
    memset((void *)&g_corner_startup, 0, sizeof(g_corner_startup));
#endif
    zero(); speed_match_init(now);
#if defined(LAP_DUAL_STARTUP) || defined(LAP_VOICE_START)
    /* 当前接线已在直道实跑确认，不再把首次KEY送进单轮校准器。
     * 双轮适配版仍做原KEY测试；语音版直接零输出等待路径和新语音指令。
     */
    if (!speed_match_use_verified_mapping()) { lap_motion_fault(LAP_CONFIG, now); return; }
    g_lap.state = LAP_WAIT;
#endif
}
/** @brief 锁定本次控制参数后进入RUN。now为本板毫秒，config为经启动门核对的参数。
 * 只重置诊断计数，旧采样槽随计数归零失效，避免在状态提交区清整块内存。
 */
static void begin_run(uint32_t now, lap_config_t config) {
    g_lap.active = config; g_lap.state = LAP_RUNNING; g_lap.reason = LAP_OK;
    g_lap.run_since = now; edge_at[0] = edge_at[1] = now;
    g_lap_diag.total_samples = 0u; g_lap_diag.frozen = 0u;
    g_lap_diag.stop_at_ms = 0u; g_lap_diag.stop_reason = 0u;
    g_lap_last.valid = 0u; boost_samples[0] = boost_samples[1] = 0u;
}
/** @brief 检查RPM、运行毫秒及PWM千分比参数是否可用于本目标。 */
static int config_valid(lap_config_t config) {
    return finitef(config.straight_rpm) && config.straight_rpm >= LAP_MIN_CRUISE &&
           config.straight_rpm <= LAP_MAX_CRUISE && config.run_ms >= 500u &&
           config.run_ms <= LAP_MAX_RUN_MS && finitef(config.min_feedforward) &&
           config.min_feedforward >= 0.0f && config.min_feedforward <= 300.0f;
}
#ifdef LAP_VOICE_START
/** @brief 冷启动时K230 UART引脚尚未就绪，允许清空残字节和解析器后继续零输出等待。
 * 第一帧校验通过、时序可用的PATH（即便路径无效）即结束启动阶段。之后任一
 * 传输错误都和旧目标一样锁故障。驱动错误计数由UART中断保存，等待时也不清零。
 */
void lap_motion_transport_fault(uint32_t now) {
    if (seen[0] != 0u || g_lap.state != LAP_WAIT) lap_motion_fault(LAP_TRANSPORT, now);
}
#endif
static int fresh(uint32_t now) {
#ifdef RIGHT_ANGLE_TARGET
    /* v5：bit3为当前左纵／前横L，按当前证据200ms监督，不等左右双边。
     * bit2为仍有当前出口边支持的短关联；700ms只从最近确认L起计，不能续租。
     */
    return g_lap.path_valid != 0u && (uint32_t)(now-g_lap.path_at)<200u &&
        (g_lap.history == 0u || (corner_pair_seen != 0u && (uint32_t)(now-corner_pair_at)<700u));
#else
    return g_lap.path_valid != 0u && (uint32_t)(now - g_lap.path_at) < (g_lap.history ? 120u : 200u);
#endif
}
#ifdef LAP_VOICE_START
static int voice_path_ready(uint32_t now) {
    return fresh(now) && g_lap.history == 0u
#ifndef RIGHT_ANGLE_VOICE_TARGET
        && g_lap.single == 0u
#endif
        ;
}
/** @brief 处理一次Go。path_sequence是发令时刚发送的PATH序号，now为本地毫秒。
 * 必须处于待机、KEY松开、双轮停稳500ms、反馈仍新鲜。直道要求当前双边；
 * 首弯还允许已经通过当前像素门限的L形，出口弱关联只能续行。指令不排队。
 */
static void voice_start(uint8_t path_sequence, uint32_t arrival, uint32_t now) {
    lap_config_t config;
    if (g_lap.state != LAP_WAIT || raw_candidate != 0u || stable != 0u ||
        have_sample == 0u || quiet_ms < 500u || (uint32_t)(now - last_sample) > 60u ||
        path_sequence != last_path_sequence || (uint32_t)(arrival - sequence_at[0]) > 30u ||
        !voice_path_ready(now)) {
        ++g_lap.starts_rejected;
        return;
    }
    config = g_lap_config;
    if (!config_valid(config)) { lap_motion_fault(LAP_CONFIG, now); return; }
    quiet_ms = 0u;
    begin_run(now, config);
}
#endif
/** @brief 悬空双轮测试与地面循迹分别监督；原目标始终返回0。
 * 双轮测试只豁免视觉许可，KEY、编码器、方向、过速、无反馈及硬件保护不变。
 */
#ifdef LAP_DUAL_STARTUP
static int bench_running(void) {
    return g_lap.state == LAP_RUNNING && g_corner_startup.stage == 1u;
}
#endif
static int16_t signed16(const uint8_t *p) {
    uint16_t value = (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
    return (int16_t)(value < 32768u ? (int32_t)value : (int32_t)value - 65536);
}
void lap_motion_receive(const uint8_t *b, uint32_t arrival, uint32_t now) {
    uint8_t type = b[3], index = (uint8_t)(type - 1u), delta;
#ifdef LAP_DUAL_STARTUP
    if (g_lap.state == LAP_RUNNING && !bench_running() && !fresh(now)) lap_motion_fault(LAP_LINK, now);
#else
    if (g_lap.state == LAP_RUNNING && !fresh(now)) lap_motion_fault(LAP_LINK, now);
#endif
    /* 停止优先于年龄／重复号；恢复图像不能自行恢复车辆。 */
    if (type == 2u && b[16] == 2u) {
#ifdef LAP_VOICE_START
        save_result(now, LAP_VOICE_STOP);
        if (g_lap.state != LAP_FAULT) {
            g_lap.state = LAP_STOPPED; g_lap.reason = LAP_VOICE_STOP; state_at = now;
        }
        g_lap.path_valid = 0u; zero(); return;
#else
        save_result(now, LAP_KEY);
        if (g_lap.state == LAP_CALIBRATION) {
            /* 相机入口先发STOP时，静止校准待机只清除待启动手势／映射。
             * 正在单轮校准则锁故障，不能在STOP后继续剩余脉冲。
             */
            if (g_speed_match.state == SPEED_CALIBRATING) lap_motion_fault(LAP_KEY, now);
            else {
                /* 只能沿用上一真实采样时刻重置校准状态；UART可能在任意毫秒
                 * 到达，若用now重置，下一20ms编码器样本会因dt不一致误锁故障。
                 * 不重置原硬件计数／回绕算法，只撤消尚未执行的按键手势。
                 */
                speed_match_init(last_sample);
            }
            g_lap.path_valid = 0u; zero(); return;
        }
        if (g_lap.state != LAP_FAULT) { g_lap.state = LAP_STOPPED; g_lap.reason = LAP_KEY; }
        zero();
        /* 停止后清路径许可，必须收到新的当前双边再进行人工启动。 */
        g_lap.path_valid = 0u; return;
#endif
    }
    if ((uint32_t)(now - arrival) >= 100u) {
        ++g_lap.rejected;
        if (g_lap.state == LAP_RUNNING) lap_motion_fault(LAP_LINK, now);
        return;
    }
    if (seen[index] != 0u && (uint32_t)(arrival - sequence_at[index]) < 200u) {
        delta = (uint8_t)(b[5] - sequences[index]);
        if (delta == 0u || delta >= 128u) { ++g_lap.duplicates; return; }
    }
    seen[index] = 1u; sequences[index] = b[5]; sequence_at[index] = arrival;
    ++g_lap.received;
    if (type == 2u) {
        if (b[16] == 1u) {
#ifdef LAP_VOICE_START
            voice_start(b[8], arrival, now);
#else
            ++g_lap.starts_rejected;
#endif
        }
        return;
    }
    last_path_sequence = b[5]; /* 与K230逐帧日志对照，不用累计received猜发送序号。 */
    /* v2的offset10是采集软件边界到封包的年龄ms，非v1航向。
     * 再扣2ms名义占线时间，使200ms监督包含发送端已报告的图像年龄。
     */
    g_lap.path_at = arrival - (uint32_t)((uint16_t)b[10] | ((uint16_t)b[11] << 8)) - 2u;
    g_lap.steering = signed16(b + 8);
    g_lap.bend = (uint16_t)((uint16_t)b[12] | ((uint16_t)b[13] << 8));
    g_lap.history = (uint8_t)((b[6] & 4u) != 0u);
    g_lap.single = (uint8_t)((b[6] & 8u) != 0u);
#ifdef RIGHT_ANGLE_TARGET
    g_lap.path_valid = (uint8_t)((b[6] & 1u) != 0u && b[7] >= 40u && b[15] == 0u && b[14] <= 100u &&
                               (uint32_t)(now - g_lap.path_at) < 200u);
#else
    g_lap.path_valid = (uint8_t)((b[6] & 1u) != 0u && b[7] >= 40u && b[15] == 0u && b[14] <= 100u &&
                               (uint32_t)(now - g_lap.path_at) < (g_lap.history ? 120u : 200u));
#endif
#ifdef STRAIGHT_ASSIST_TARGET
    /* v3直道只接纳当前双边、零bend；不靠历史或单边继续高速直走。 */
    if (g_lap.history != 0u || g_lap.single != 0u || g_lap.bend != 0u) g_lap.path_valid = 0u;
#endif
#ifdef RIGHT_ANGLE_TARGET
    /* v5当前L形可以独立启动／持续右转，不能再等右侧黑边或旧双侧租期。
     * 当前L必须置信度>=60、满弯风险、右转请求；只有一根直带不能取得该标志。
     * 当前出口边的弱关联(bit2)不能冷启动，最多沿用已确认L的700ms角色。
     */
    if (g_lap.history != 0u) {
        if (corner_pair_seen == 0u || (uint32_t)(now-corner_pair_at)>=700u ||
            g_lap.bend!=1000u || g_lap.steering<0 || b[7]<45u) g_lap.path_valid=0u;
    } else if (g_lap.single != 0u) {
        if (g_lap.bend!=1000u || g_lap.steering<0 || b[7]<60u) g_lap.path_valid=0u;
        if (g_lap.path_valid != 0u) { corner_pair_seen=1u; corner_pair_at=now; }
    } else if (g_lap.path_valid != 0u) {
        /* 当前双侧近弯也可作为出口关联的锚点；普通直道清除旧弯道角色。 */
        corner_pair_seen = (uint8_t)(g_lap.bend>=200u);
        corner_pair_at = now;
    }
    if (g_lap.path_valid == 0u) corner_pair_seen = 0u;
#endif
#ifdef LAP_DUAL_STARTUP
    if (g_lap.state == LAP_RUNNING && !bench_running() && g_lap.path_valid == 0u) lap_motion_fault(LAP_PATH, now);
#else
    if (g_lap.state == LAP_RUNNING && g_lap.path_valid == 0u) lap_motion_fault(LAP_PATH, now);
#endif
}
void lap_motion_tick(uint32_t now, uint8_t key) {
#ifndef LAP_VOICE_START
    uint32_t held;
#endif
    key = key != 0u ? 1u : 0u;
    if (g_lap.state == LAP_CALIBRATION) {
        speed_match_tick(now, key);
        g_lap.left_pwm = g_speed_match.left_pwm; g_lap.right_pwm = g_speed_match.right_pwm;
        if (g_speed_match.state == SPEED_FAULT) lap_motion_fault(LAP_ENCODER, now);
        else if (g_speed_match.phase == 2u) {
            g_lap.state = LAP_WAIT; state_at = raw_at = now;
            raw_candidate = stable = 0u; zero();
        }
        return;
    }
    if (key != raw_candidate) { raw_candidate = key; raw_at = now; }
    if ((uint32_t)(now - raw_at) >= 30u) stable = key;
    if (g_lap.state == LAP_RUNNING) {
        if (key != 0u) { lap_motion_fault(LAP_KEY, now); return; }
#ifdef LAP_DUAL_STARTUP
        if (!bench_running() && !fresh(now)) { lap_motion_fault(LAP_LINK, now); return; }
#else
        if (!fresh(now)) { lap_motion_fault(LAP_LINK, now); return; }
#endif
        if (!have_sample || (uint32_t)(now - last_sample) > 60u) { lap_motion_fault(LAP_ENCODER, now); return; }
        if ((uint32_t)(now - g_lap.run_since) >= g_lap.active.run_ms) {
#ifdef LAP_DUAL_STARTUP
            if (bench_running()) {
                /* 完整1秒后再核对两轮确实均有正反馈；零转、反向及异常已更早被保护。
                 * 不用相机有效／按键次数代替电机反馈，也不在测试结束时自动上道。
                 */
                if (g_corner_startup.left_counts < 20 || g_corner_startup.right_counts < 20 ||
                    g_lap.left_rpm < 10.0f || g_lap.right_rpm < 10.0f) {
                    lap_motion_fault(LAP_NO_FEEDBACK, now); return;
                }
                g_corner_startup.bench_ms = now - g_lap.run_since;
                g_corner_startup.completed = 1u; g_corner_startup.stage = 2u;
            }
#endif
            save_result(now, LAP_LIMIT);
            g_lap.state = LAP_STOPPED; g_lap.reason = LAP_LIMIT; state_at = now; zero();
        }
        return;
    }
    zero();
    if (g_lap.state == LAP_FAULT) return;
    if (g_lap.state == LAP_STOPPED) {
        /* 正常时限／远程STOP后需松键停稳再重新发令；故障必须复位。 */
        if (key == 0u && quiet_ms >= 500u
#ifdef LAP_VOICE_START
            && (uint32_t)(now - state_at) >= 500u
#endif
            ) { g_lap.state = LAP_WAIT; state_at = now; }
#ifdef LAP_VOICE_START
    } else if (key != 0u && (uint32_t)(now - raw_at) >= 5000u) {
        /* KEY不再进入启动手势。待机卡住仍锁故障，运行中则由上方原保护立即撤驱动。 */
        lap_motion_fault(LAP_KEY, now);
#else
    } else if (g_lap.state == LAP_WAIT) {
#ifdef LAP_DUAL_STARTUP
        /* 按下即可计长按时长，启动资格在松开时统一检查。
         * 避免上电后先等待1秒再开始计长按，使第一次正常手势被静默吃掉。
         * 上电按住超过5秒仍由下方卡键保护锁定，绝不自动运行。
         */
        if (stable != 0u) { g_lap.state = LAP_HOLD; state_at = raw_at; }
#else
        if (key != 0u) {
            if ((uint32_t)(now - state_at) >= 1000u && quiet_ms >= 500u && stable != 0u) {
                g_lap.state = LAP_HOLD; state_at = now;
            }
        }
#endif
    } else if (g_lap.state == LAP_HOLD || g_lap.state == LAP_ARMED) {
        if (key == 0u && stable == 0u) {
            held = raw_at - state_at;
            if (g_lap.state == LAP_ARMED && held >= 1000u && held < 5000u) {
                lap_config_t config = g_lap_config;
#ifdef LAP_DUAL_STARTUP
                int is_bench = g_corner_startup.stage == 0u;
                if (!have_sample || quiet_ms < 500u ||
                    (!is_bench && (!fresh(now) || g_lap.history != 0u
#ifdef STRAIGHT_DUAL_START_TARGET
                        || g_lap.single != 0u
#endif
                        ))) {
                    ++g_lap.starts_rejected; ++g_corner_startup.starts_blocked;
                    g_corner_startup.blocked_reason = !have_sample || quiet_ms < 500u ? LAP_ENCODER : LAP_PATH;
                    g_lap.state = LAP_WAIT; state_at = now; return;
                }
#else
                if (!fresh(now) || g_lap.history != 0u || g_lap.single != 0u || !have_sample || quiet_ms < 500u) {
                    ++g_lap.starts_rejected; g_lap.state = LAP_WAIT; state_at = now; return;
                }
#endif
                if (!config_valid(config)) { lap_motion_fault(LAP_CONFIG, now); return; }
#ifdef LAP_DUAL_STARTUP
                if (is_bench) {
                    /* 首次只运行1秒、两轮同目标60RPM，不读取视觉转向；须由主控悬空。
                     * 后续启动才使用目标原地面配置：直道80RPM／2秒、首弯80RPM／12秒。
                     */
                    config.straight_rpm = 60.0f; config.run_ms = 1000u;
                    g_corner_startup.stage = 1u;
                    g_corner_startup.left_counts = g_corner_startup.right_counts = 0;
                } else ++g_corner_startup.ground_runs;
                g_corner_startup.blocked_reason = LAP_OK;
#endif
                begin_run(now, config);
            } else { g_lap.state = LAP_WAIT; state_at = now; }
        } else if ((uint32_t)(now - state_at) >= 5000u) lap_motion_fault(LAP_KEY, now);
        else if (key != 0u && (uint32_t)(now - state_at) >= 1000u) g_lap.state = LAP_ARMED;
#endif
    }
}
/** @brief 每轮独立处理“目标由0变为正”的一次起步补偿，返回受限PWM。
 * 参数：wheel为0左/1右；target单位RPM；delta为本20ms编码器增量；now为ms；
 * pi_duty为已由真实PI算出的0..500输出。正目标但尚无反馈时最多给100ms的
 * 500/1000输出；任一真实增量即退出，超时后也不反复补偿，仍由300ms监督停机。
 * 目标0绝不补偿；中途堵转不会因“又没脉冲”自动重新给补偿，须先合法停轮。
 * 只在既有新鲜路径、编码器、方向、超速等检查之后执行，不绕过任何保护。
 */
static uint16_t startup_output(unsigned wheel, float target, int32_t delta, uint32_t now, uint16_t pi_duty) {
    if (target > 0.0f && previous_target[wheel] == 0.0f) {
        boost_at[wheel] = now; boost_pending[wheel] = 1u;
    }
    if (target == 0.0f || delta != 0 || (uint32_t)(now - boost_at[wheel]) >= LAP_START_BOOST_MS)
        boost_pending[wheel] = 0u;
    if (boost_pending[wheel] != 0u) {
        ++boost_samples[wheel]; return LAP_START_BOOST_DUTY;
    }
    return pi_duty;
}
/** @brief 记录进入本次保护／PI前的真实采样，单位ms、counts、counts/s、RPM。
 * 只由统一20ms采样上下文写入。固定内存、无串口／SD／动态分配，UART仍可抢占。
 * 反向／超速检查在此函数之后执行，因此触发保护的原始采样也会留下；
 * 数据只供事后排障，不反馈到控制，不改变任何保护阈值或判定时序。
 */
static void diag_sample(uint32_t now, uint32_t dt, const encoder_sample_t *left,
                        const encoder_sample_t *right, float raw_left, float raw_right) {
    volatile lap_diag_sample_t *entry;
    if (g_lap_diag.frozen != 0u) return;
    entry = &g_lap_diag.samples[g_lap_diag.total_samples % LAP_DIAG_SAMPLES];
    entry->at_ms = now; entry->dt_ms = dt;
    entry->received = g_lap.received; entry->path_at = g_lap.path_at;
    entry->left_delta = left->delta; entry->right_delta = right->delta;
    entry->left_counts_per_s = left->counts_per_s; entry->right_counts_per_s = right->counts_per_s;
    entry->left_raw_rpm = raw_left; entry->right_raw_rpm = raw_right;
    entry->left_target = g_lap.left_target; entry->right_target = g_lap.right_target;
    entry->left_pwm = g_lap.left_pwm; entry->right_pwm = g_lap.right_pwm;
    entry->steering = g_lap.steering; entry->bend = g_lap.bend;
    entry->history = g_lap.history; entry->single = g_lap.single;
    entry->path_valid = g_lap.path_valid; entry->path_sequence = last_path_sequence;
    g_lap_diag.left_channel = g_speed_match.left_channel;
    g_lap_diag.right_channel = g_speed_match.right_channel;
    g_lap_diag.left_sign = g_speed_match.left_sign;
    g_lap_diag.right_sign = g_speed_match.right_sign;
    ++g_lap_diag.total_samples; /* 最后提交计数；运行中SWD读取仍不是原子快照。 */
}

void lap_motion_sample(uint32_t now, const encoder_sample_t *a, const encoder_sample_t *b) {
    const encoder_sample_t *channels[2], *left, *right;
#if defined(STRAIGHT_ASSIST_TARGET) || defined(RIGHT_ANGLE_TARGET)
    float raw_left, raw_right, targets[2];
#else
    float raw_left, raw_right, base, steer, targets[2];
#endif
    uint32_t dt = now - last_sample;
    uint16_t lp, rp;
#if defined(STRAIGHT_ASSIST_TARGET) || defined(RIGHT_ANGLE_TARGET)
    /* 563ms地面失败中左轮已超目标约40RPM，旧低比例／高积分仍输出较大PWM。
     * 本独立目标改为Kp6、Ki8：更及时减小快轮驱动，减少起步积分积累。
     * 配合较快的编码器滤波和下方差速补偿；原低速目标及50%上限不变。
     */
    speed_pi_config_t pi = {6.0f, 8.0f, 300.0f};
#else
    speed_pi_config_t pi = {2.0f, 4.0f, 300.0f};
#endif
    /* 原算法负责FIRST／标志／真实dt与校准；其phase2保持非运行状态，不参与目标计算。 */
    speed_match_sample(now, a, b);
    if (g_speed_match.state == SPEED_FAULT) { lap_motion_fault(LAP_ENCODER, now); return; }
    if (a->status == ENCODER_FIRST && b->status == ENCODER_FIRST) { last_sample = now; return; }
    if (dt == 0u || dt > 60u || !a->valid || !b->valid) { lap_motion_fault(LAP_ENCODER, now); return; }
    last_sample = now; have_sample = 1u;
    if (a->delta == 0 && b->delta == 0) { if (quiet_ms < 1000u) quiet_ms += dt; } else quiet_ms = 0u;
    if (g_lap.state == LAP_CALIBRATION) return;
    channels[0] = a; channels[1] = b;
    if (g_speed_match.left_channel < 1u || g_speed_match.left_channel > 2u ||
        g_speed_match.right_channel < 1u || g_speed_match.right_channel > 2u ||
        g_speed_match.left_channel == g_speed_match.right_channel) { lap_motion_fault(LAP_ENCODER, now); return; }
    left = channels[g_speed_match.left_channel - 1u]; right = channels[g_speed_match.right_channel - 1u];
    raw_left = (float)left->counts_per_s * (float)g_speed_match.left_sign * 60.0f / 1058.6f;
    raw_right = (float)right->counts_per_s * (float)g_speed_match.right_sign * 60.0f / 1060.8f;
    g_lap.left_rpm = g_speed_match.left_rpm; g_lap.right_rpm = g_speed_match.right_rpm;
    if (g_lap.state != LAP_RUNNING) return;
    diag_sample(now, dt, left, right, raw_left, raw_right);
    if (absf(raw_left) > 600.0f || absf(raw_right) > 600.0f) { lap_motion_fault(LAP_OVERSPEED, now); return; }
    if (raw_left < -5.0f || raw_right < -5.0f) { lap_motion_fault(LAP_REVERSE, now); return; }
#ifdef LAP_DUAL_STARTUP
    if (!bench_running() && !fresh(now)) { lap_motion_fault(LAP_LINK, now); return; }
#else
    if (!fresh(now)) { lap_motion_fault(LAP_LINK, now); return; }
#endif
#ifdef LAP_DUAL_STARTUP
    if (bench_running()) {
        /* 固定已知左右映射，累计正向净计数；反向／过速检查已在上面执行。
         * 相机抖动、无路径或弯道大差速不应影响悬空双轮同速测试。
         */
        g_corner_startup.left_counts += left->delta * g_speed_match.left_sign;
        g_corner_startup.right_counts += right->delta * g_speed_match.right_sign;
        targets[0] = targets[1] = 60.0f;
    } else
#endif
#ifdef RIGHT_ANGLE_TARGET
    {
        corner_guide_t guide = g_corner_guide;
        if (!corner_guide_update(&guide, g_lap.active.straight_rpm, g_lap.steering,
                                 g_lap.bend, dt, &targets[0], &targets[1])) {
            lap_motion_fault(LAP_CONFIG, now); return;
        }
        g_corner_guide = guide;
    }
#elif defined(STRAIGHT_ASSIST_TARGET)
    {
        straight_guide_t guide = g_straight_guide;
        /* 小幅差速只生成RPM，真实编码器PI继续分别追踪两轮，而非直接改PWM。
         * 正目标不会因视觉噪声被压到0..20RPM；弯道识别由相机撤销许可停车。
         */
        if (!straight_guide_update(&guide, g_lap.active.straight_rpm, g_lap.steering,
                                   dt, &targets[0], &targets[1])) {
            lap_motion_fault(LAP_CONFIG, now); return;
        }
        g_straight_guide = guide;
    }
#else
    /* 右转时左外轮较快；大转向只把内轮降到0，不使用负RPM或反转。
     * base随弯道风险降至原值55%，每轮不超过60RPM／50%PWM。
     */
    steer = (float)g_lap.steering / 1000.0f;
    base = g_lap.active.straight_rpm * (1.0f - 0.45f * (float)g_lap.bend / 1000.0f);
    if (g_lap.history != 0u || g_lap.single != 0u) base *= 0.6f;
    targets[0] = base * (1.0f + steer); targets[1] = base * (1.0f - steer);
    if (targets[0] > 60.0f) targets[0] = 60.0f;
    if (targets[1] > 60.0f) targets[1] = 60.0f;
    if (targets[0] < 5.0f) targets[0] = 0.0f;
    if (targets[1] < 5.0f) targets[1] = 0.0f;
#endif
    if (left->delta != 0 || targets[0] == 0.0f || previous_target[0] == 0.0f) edge_at[0] = now;
    if (right->delta != 0 || targets[1] == 0.0f || previous_target[1] == 0.0f) edge_at[1] = now;
    if ((uint32_t)(now - edge_at[0]) >= 300u || (uint32_t)(now - edge_at[1]) >= 300u) {
        lap_motion_fault(LAP_NO_FEEDBACK, now); return;
    }
    g_lap.left_target = targets[0]; g_lap.right_target = targets[1];
    /* 原线性前馈在20RPM仅10%，实物出现起步后内轮无法维持、无反馈停车。
     * 正目标使用本次启动锁定的候选前馈下限（默认20%），40/60RPM参考不变；
     * 这只是PI的基础项，反馈超目标时仍可减到0，绝不是强制最低PWM。
     * 零目标不加下限，PI原有分支立即归零；不得为保持内轮而让零目标转动。
     * 该下限尚需差速实物验收，不当作已标定静摩擦或地面保证。
     */
    pi.feedforward = 300.0f * targets[0] / 60.0f;
#if defined(STRAIGHT_ASSIST_TARGET) || defined(RIGHT_ANGLE_TARGET)
    if (pi.feedforward > 500.0f) pi.feedforward = 500.0f;
#endif
    if (targets[0] > 0.0f && pi.feedforward < g_lap.active.min_feedforward)
        pi.feedforward = g_lap.active.min_feedforward;
    if (!speed_pi_update(&left_pi, &pi, targets[0], absf(g_lap.left_rpm), dt, &lp)) {
        lap_motion_fault(LAP_CONFIG, now); return;
    }
    pi.feedforward = 300.0f * targets[1] / 60.0f;
#if defined(STRAIGHT_ASSIST_TARGET) || defined(RIGHT_ANGLE_TARGET)
    if (pi.feedforward > 500.0f) pi.feedforward = 500.0f;
#endif
    if (targets[1] > 0.0f && pi.feedforward < g_lap.active.min_feedforward)
        pi.feedforward = g_lap.active.min_feedforward;
    if (!speed_pi_update(&right_pi, &pi, targets[1], absf(g_lap.right_rpm), dt, &rp)) {
        lap_motion_fault(LAP_CONFIG, now); return;
    }
#ifdef STRAIGHT_ASSIST_TARGET
    /* 直接按编码器实测差速纠偏：左实际过快则左减右加。
     * 减去目标差速，避免把视觉有意安排的70/90RPM强行拉回相同速度。
     * 本补偿仍在起步补偿之前；首次无脉冲的100ms受限起步机制继续保留。
     */
    {
        float adjustment;
        g_straight_sync_error = (absf(g_lap.left_rpm) - absf(g_lap.right_rpm)) - (targets[0] - targets[1]);
        if (!straight_balance_update(targets[0], targets[1], absf(g_lap.left_rpm),
                                     absf(g_lap.right_rpm), &lp, &rp, &adjustment)) {
            lap_motion_fault(LAP_CONFIG, now); return;
        }
        g_straight_sync_adjustment = adjustment;
    }
#endif
#ifdef RIGHT_ANGLE_TARGET
    {
        float adjustment;
        /* 保留直道实跑使用的编码器差速补偿，减去有意安排的弯道目标差。
         * 内轮目标0时复用函数立即撤该轮输出，不因交叉补偿重新驱动内轮。
         */
        if (!straight_balance_update(targets[0], targets[1], absf(g_lap.left_rpm),
                                     absf(g_lap.right_rpm), &lp, &rp, &adjustment)) {
            lap_motion_fault(LAP_CONFIG, now); return;
        }
    }
#endif
    g_lap.left_pwm = startup_output(0u, targets[0], left->delta, now, lp);
    g_lap.right_pwm = startup_output(1u, targets[1], right->delta, now, rp);
    previous_target[0] = targets[0]; previous_target[1] = targets[1];
}
uint8_t lap_motion_led(uint32_t now) {
    if (g_lap.state == LAP_CALIBRATION) return speed_match_led(now);
    if (g_lap.state == LAP_FAULT) return (uint8_t)((now / 100u) % 2u);
    if (g_lap.state == LAP_RUNNING || g_lap.state == LAP_ARMED) return 1u;
#ifdef RIGHT_ANGLE_VOICE_TARGET
    /* 当前L也可正式起步。用同一许可判定提示主控，出口弱关联仍显示短闪。 */
    return (uint8_t)((now % 2000u) < (g_lap.state == LAP_WAIT && voice_path_ready(now) ? 400u : 80u));
#else
    return (uint8_t)((now % 2000u) < (fresh(now) && !g_lap.history && !g_lap.single ? 400u : 80u));
#endif
}
