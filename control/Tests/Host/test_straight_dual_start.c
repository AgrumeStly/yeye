/* 复用真实直道算法及原编码器／UART／电机模型，验证新双轮启动的状态边界。
 * 所有运动由模拟KEY触发；这些检查只证明软件逻辑，不替代悬空／地面人工验证。
 */
#define main legacy_lap_test_main
#include "test_lap_motion.c"
#undef main

/** @brief 初始化固定实证映射及原直道默认值；不进行逐轮校准。 */
static void dual_init(uint32_t initial) {
    init(initial, 0);
    g_lap_config.straight_rpm = 80.0f; g_lap_config.run_ms = 2000u;
    CHECK(g_lap.state == LAP_WAIT && g_speed_match.phase == 2u);
    CHECK(g_speed_match.left_channel == 1u && g_speed_match.right_channel == 2u);
    CHECK(g_speed_match.left_sign == 1 && g_speed_match.right_sign == -1);
    CHECK(!g_corner_startup.completed && !g_corner_startup.stage);
    CHECK(!g_lap.left_pwm && !g_lap.right_pwm);
}
/** @brief 完成一次无视觉的双轮测试，再以当前有效直道许可启动原2秒控制。 */
static void dual_ground(uint32_t initial) {
    dual_init(initial); feed = 0; start(); ticks(1100, 0);
    CHECK(g_corner_startup.completed && g_corner_startup.bench_ms == 1000u);
    CHECK(g_lap_config.straight_rpm == 80.0f && g_lap_config.run_ms == 2000u);
    feed = 1; start();
    CHECK(g_lap.state == LAP_RUNNING && g_corner_startup.ground_runs == 1u);
    CHECK(g_lap.active.straight_rpm == 80.0f && g_lap.active.run_ms == 2000u);
}
static void dual_startup_cases(void) {
    unsigned i; uint8_t p[20];
    dual_init(0); feed = 0;
    /* 上电首次长按即可接受；无相机、无效PATH及大转向均不改变悬空同速目标。 */
    ticks(1200, 1); ticks(31, 0);
    CHECK(g_lap.state == LAP_RUNNING && g_corner_startup.stage == 1u);
    CHECK(g_speed_match.state != SPEED_CALIBRATING && g_lap.active.run_ms == 1000u);
    steer = 1000; valid_path = 0; path(); ticks(100, 0);
    CHECK(g_lap.left_target == 60.0f && g_lap.right_target == 60.0f);
    ticks(1000, 0);
    CHECK(g_corner_startup.completed && g_corner_startup.stage == 2u);
    CHECK(g_corner_startup.left_counts >= 20 && g_corner_startup.right_counts >= 20);
    CHECK(g_lap_last.elapsed_ms == 1000u && g_lap_last.reason == LAP_LIMIT);
    CHECK(!g_lap.left_pwm && !g_lap.right_pwm && !g_corner_startup.ground_runs);
    start(); CHECK(g_lap.state == LAP_WAIT && g_corner_startup.blocked_reason == LAP_PATH);
    /* 缺左／右反馈、反向及超速均不得获得上道资格。 */
    for (i = 1; i <= 4; ++i) {
        dual_init(0); feed = 0; start(); mode = (int)i; ticks(600, 0);
        CHECK(g_lap.state == LAP_FAULT && !g_corner_startup.completed);
        CHECK(g_lap.reason == (i <= 2 ? LAP_NO_FEEDBACK : (i == 3 ? LAP_REVERSE : LAP_OVERSPEED)));
    }
    dual_init(0); feed = 0; start(); ticks(1, 1);
    CHECK(g_lap.reason == LAP_KEY && !g_corner_startup.completed);
    dual_init(0); feed = 0; start();
    packet(p); p[3] = 2; memset(p + 6, 0, 12); p[16] = 2;
    put16(p + 18, protocol_crc16(p, 18)); submit(p, now);
    CHECK(g_lap.state == LAP_STOPPED && !g_corner_startup.completed);
    start(); CHECK(g_lap.state == LAP_RUNNING && g_corner_startup.stage == 1u);
    /* 物理映射与归档不符时只能停止，绝不能用双轮脉冲重新猜测左右。 */
    dual_init(0); reverse_mapping = 1; feed = 0; start(); ticks(600, 0);
    CHECK(g_lap.state == LAP_FAULT && !g_corner_startup.completed);
    dual_init(0); ticks(5100, 1);
    CHECK(g_lap.state == LAP_FAULT && !g_corner_startup.completed);
    /* 人工复位后资格清零；相机STOP不能伪造一次已完成的双轮测试。 */
    dual_ground(0); lap_motion_init(now);
    CHECK(!g_corner_startup.completed && !g_corner_startup.stage && !g_lap.left_pwm);
}
static void dual_ground_cases(void) {
    unsigned i; uint8_t p[20];
    for (i = 0; i < 2; ++i) {
        dual_ground(i ? UINT32_MAX - 5000u : 0u);
        ticks(2100, 0);
        CHECK(g_lap_last.elapsed_ms == 2000u && g_lap_last.reason == LAP_LIMIT);
        CHECK(g_corner_startup.completed && !g_lap.left_pwm && !g_lap.right_pwm);
    }
    dual_ground(0); steer = 1000; ticks(800, 0);
    CHECK(g_lap.left_target > g_lap.right_target && g_lap.right_target >= 70.39f);
    dual_ground(0); feed = 0; ticks(201, 0);
    CHECK(g_lap.reason == LAP_LINK && !g_lap.left_pwm && !g_lap.right_pwm);
    path(); CHECK(g_lap.state == LAP_FAULT);
    for (i = 0; i < 4; ++i) {
        dual_ground(0); packet(p);
        if (i == 0) p[6] = 0;
        if (i == 1) p[6] = 5;
        if (i == 2) p[6] = 9;
        if (i == 3) put16(p + 12, 1);
        put16(p + 18, protocol_crc16(p, 18)); submit(p, now);
        CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_PATH);
    }
    dual_ground(0); ticks(1, 1); CHECK(g_lap.reason == LAP_KEY && !g_lap.left_pwm);
    for (i = 1; i <= 4; ++i) {
        dual_ground(0); mode = (int)i; ticks(600, 0);
        CHECK(g_lap.state == LAP_FAULT);
    }
    /* 仅允许v3直道帧；首弯v5或旧v2不能给新目标运动许可。 */
    for (i = 2; i <= 5; ++i) {
        if (i == 3) continue;
        dual_ground(0); feed = 0; packet(p); p[2] = (uint8_t)i;
        put16(p + 18, protocol_crc16(p, 18)); submit(p, now); ticks(201, 0);
        CHECK(g_lap.reason == LAP_LINK);
    }
}
int main(void) {
    parser_cases(); dual_startup_cases(); dual_ground_cases();
    printf("StraightDualStart: %u assertions PASS; software model only\n", checks);
    return 0;
}
