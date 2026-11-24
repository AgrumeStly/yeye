/* 语音首弯运行生产v8解析与分档预测，电机替身不代表实际过弯。 */
#define main legacy_lap_test_main
#include "test_lap_motion.c"
#undef main

static void cmd(uint8_t version, uint8_t seq, uint8_t path_seq, uint8_t kind, uint32_t arrival) {
    uint8_t frame[20] = {0xa5, 0x5a, version, 2, 12, seq};
    frame[8] = path_seq;
    frame[16] = kind;
    put16(frame + 18, protocol_crc16(frame, 18));
    submit(frame, arrival);
}

static void go(uint8_t seq) {
    path();
    cmd(8, seq, (uint8_t)(sequence - 1u), 1, now);
}

static void setup(void) {
    init(0, 0);
    g_lap_config.straight_rpm = 80.0f;
    g_lap_config.run_ms = 12000u;
    CHECK(g_lap.state == LAP_WAIT && g_speed_match.phase == 2u);
    CHECK(g_speed_match.left_channel == 1u && g_speed_match.right_channel == 2u);
    CHECK(g_speed_match.left_sign == 1 && g_speed_match.right_sign == -1);
    CHECK(g_lap.left_pwm == 0u && g_lap.right_pwm == 0u);
}

int main(void) {
    uint8_t seq;
    unsigned fault;
    parser_cases();
    setup();
    go(0);
    CHECK(g_lap.starts_rejected == 1u && g_lap.state == LAP_WAIT);
    start();
    CHECK(g_lap.state == LAP_WAIT && g_lap.left_pwm == 0u && g_lap.right_pwm == 0u);
    feed = 0;
    path();
    seq = (uint8_t)(sequence - 1u);
    cmd(5, 1, seq, 1, now);
    cmd(6, 1, seq, 1, now);
    cmd(7, 1, seq, 1, now);
    CHECK(parser.rejected == 3u && g_lap.state == LAP_WAIT);
    cmd(8, 1, (uint8_t)(seq - 1u), 1, now);
    ticks(31, 0);
    cmd(8, 2, seq, 1, now);
    CHECK(g_lap.starts_rejected == 3u && g_lap.state == LAP_WAIT);
    ticks(1, 1);
    go(3);
    CHECK(g_lap.starts_rejected == 4u && g_lap.state == LAP_WAIT);
    ticks(31, 0);
    corner_flags = 8; bend = 1000; steer = 550; feed = 1;
    ticks(2000u - (now % 2000u) + 100u, 0);
    CHECK(lap_motion_led(now) == 1u && g_lap.single);
    corner_flags = 4; path_quality = 55;
    go(4);
    CHECK(g_lap.path_valid && g_lap.history && g_lap.starts_rejected == 5u);
    CHECK(g_lap.state == LAP_WAIT && lap_motion_led(now) == 0u);
    corner_flags = 8; path_quality = 60;
    go(5);
    CHECK(g_lap.state == LAP_RUNNING && g_lap.active.run_ms == 12000u);
    ticks(500, 0);
    CHECK(g_lap.left_target > g_lap.right_target && g_lap.right_target > 0.0f);
    go(6);
    CHECK(g_lap.starts_rejected == 6u && now - g_lap.run_since == 500u);
    corner_flags = 4; path_quality = 55;
    ticks(600, 0);
    CHECK(g_lap.state == LAP_RUNNING);
    CHECK((g_lap.left_target + g_lap.right_target) / 2.0f <= 50.01f);
    path_quality = 45;
    ticks(200, 0);
    CHECK(g_lap.state == LAP_RUNNING);
    CHECK((g_lap.left_target + g_lap.right_target) / 2.0f <= 40.01f);
    corner_flags = 0; path_quality = 75; bend = steer = 0;
    path();
    ticks(1000, 0);
    CHECK(g_lap.state == LAP_RUNNING && g_lap.left_target == g_lap.right_target);
    cmd(8, 0, 0, 2, now - 500u);
    CHECK(g_lap.state == LAP_STOPPED && g_lap_last.reason == LAP_VOICE_STOP);
    CHECK(g_lap.left_pwm == 0u && g_lap.right_pwm == 0u);

    setup(); ticks(600, 0); go(0); ticks(12000, 0);
    CHECK(g_lap_last.reason == LAP_LIMIT && g_lap_last.elapsed_ms == 12000u);
    setup(); ticks(600, 0); go(0); ticks(1, 1);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_KEY);
    setup(); ticks(600, 0); go(0); feed = 0; ticks(200, 0);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_LINK);
    path(); go(1);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_LINK);
    setup(); ticks(600, 0); go(0); valid_path = 0; path();
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_PATH);
    setup(); ticks(600, 0); go(0); corner_flags = 4; path_quality = 45;
    ticks(250, 0);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_LINK);
    setup(); ticks(600, 0); go(0); corner_flags = 4; path_quality = 55;
    ticks(1205, 0);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_LINK);
    for (fault = 1; fault <= 4; ++fault) {
        setup(); ticks(600, 0); go(0);
        mode = (int)fault;
        ticks(600, 0);
        CHECK(g_lap.state == LAP_FAULT);
        CHECK(g_lap.reason == (fault <= 2u ? LAP_NO_FEEDBACK : (fault == 3u ? LAP_REVERSE : LAP_OVERSPEED)));
    }
    setup(); lap_motion_transport_fault(now);
    CHECK(g_lap.state == LAP_WAIT);
    path(); lap_motion_transport_fault(now);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_TRANSPORT);
    printf("RightAngleVoice: %u assertions PASS; software model only\n", checks);
    return 0;
}
