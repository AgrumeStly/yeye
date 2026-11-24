/* 生产v6解析器及应用状态机，编码器与电机仍沿用电脑替身。 */
#define main legacy_lap_test_main
#include "test_lap_motion.c"
#undef main

static uint8_t last_path(void) { return (uint8_t)(sequence - 1u); }

static void command(uint8_t *frame, uint8_t seq, uint8_t id, uint8_t path_seq) {
    const uint8_t header[] = {0xa5, 0x5a, 6, 2, 12, seq};
    memset(frame, 0, 20);
    memcpy(frame, header, sizeof(header));
    frame[8] = path_seq;
    frame[16] = id;
    put16(frame + 18, protocol_crc16(frame, 18));
}

static void voice_init(uint32_t start_at) {
    init(start_at, 0);
    g_lap_config.straight_rpm = 80.0f;
    g_lap_config.run_ms = 2000u;
    CHECK(g_lap.state == LAP_WAIT && g_speed_match.phase == 2u);
    CHECK(g_speed_match.left_channel == 1u && g_speed_match.right_channel == 2u);
    CHECK(g_speed_match.left_sign == 1 && g_speed_match.right_sign == -1);
    CHECK(g_lap.left_pwm == 0 && g_lap.right_pwm == 0);
}

static void go(void) {
    uint8_t frame[20];
    path();
    command(frame, 0, 1, last_path());
    submit(frame, now);
}

static void voice_run(uint32_t start_at) {
    voice_init(start_at);
    ticks(600, 0);
    go();
    CHECK(g_lap.state == LAP_RUNNING && g_lap.active.run_ms == 2000u);
    CHECK(g_lap.active.straight_rpm == 80.0f && g_lap.run_since == now);
}

static void start_guards(void) {
    uint8_t frame[20];
    unsigned version;
    voice_init(0);
    go();
    CHECK(g_lap.state == LAP_WAIT && g_lap.starts_rejected == 1u);
    ticks(610, 0);
    CHECK(g_lap.state == LAP_WAIT && g_lap.left_pwm == 0);
    start();
    CHECK(g_lap.state == LAP_WAIT && g_lap.right_pwm == 0);
    ticks(1, 1);
    go();
    CHECK(g_lap.state == LAP_WAIT && g_lap.starts_rejected == 2u);
    ticks(31, 0);
    feed = 0;
    ticks(300, 0);
    command(frame, 0, 1, last_path());
    submit(frame, now);
    CHECK(g_lap.state == LAP_WAIT && g_lap.starts_rejected == 3u);
    ticks(300, 0);
    path();
    command(frame, 0, 1, (uint8_t)(last_path() - 1u));
    submit(frame, now);
    CHECK(g_lap.state == LAP_WAIT && g_lap.starts_rejected == 4u);
    path();
    ticks(31, 0);
    command(frame, 1, 1, last_path());
    submit(frame, now);
    CHECK(g_lap.state == LAP_WAIT && g_lap.starts_rejected == 5u);
    path();
    command(frame, 2, 1, last_path());
    submit(frame, now - 100u);
    CHECK(g_lap.state == LAP_WAIT && g_lap.rejected == 1u);
    valid_path = 0;
    path();
    command(frame, 2, 1, last_path());
    submit(frame, now);
    CHECK(g_lap.state == LAP_WAIT && g_lap.starts_rejected == 6u);
    for (version = 1; version <= 5; ++version) {
        command(frame, 3, 1, last_path());
        frame[2] = (uint8_t)version;
        put16(frame + 18, protocol_crc16(frame, 18));
        submit(frame, now);
    }
    CHECK(parser.rejected >= 5u && g_lap.state == LAP_WAIT);
}

static void stop_guards(void) {
    uint8_t frame[20];
    unsigned fault;
    voice_run(0);
    ticks(100, 0);
    CHECK(g_lap.left_pwm > 0 && g_lap.right_pwm > 0);
    command(frame, 1, 1, last_path());
    submit(frame, now);
    CHECK(g_lap.starts_rejected == 1u && now - g_lap.run_since == 100u);
    command(frame, 0, 2, 0);
    submit(frame, now - 500u);
    CHECK(g_lap.state == LAP_STOPPED && g_lap_last.reason == LAP_VOICE_STOP);
    CHECK(g_lap_last.elapsed_ms == 100u && g_lap.left_pwm == 0 && g_lap.right_pwm == 0);
    submit(frame, now);
    ticks(300, 0);
    go();
    CHECK(g_lap.state == LAP_STOPPED);
    ticks(1000, 0);
    CHECK(g_lap.state == LAP_WAIT && g_lap.left_pwm == 0 && g_lap.right_pwm == 0);
    go();
    CHECK(g_lap.state == LAP_RUNNING);
    ticks(1, 1);
    CHECK(g_lap.reason == LAP_KEY && g_lap.state == LAP_FAULT);
    ticks(1100, 0);
    go();
    CHECK(g_lap.reason == LAP_KEY && g_lap.state == LAP_FAULT);

    voice_run(UINT32_MAX - 650u);
    ticks(2000, 0);
    CHECK(g_lap_last.reason == LAP_LIMIT && g_lap_last.elapsed_ms == 2000u);
    CHECK(g_lap.left_pwm == 0 && g_lap.right_pwm == 0);
    voice_run(0);
    feed = 0;
    ticks(201, 0);
    CHECK(g_lap.reason == LAP_LINK);
    voice_run(0);
    valid_path = 0;
    path();
    CHECK(g_lap.reason == LAP_PATH);
    for (fault = 1; fault <= 4; ++fault) {
        voice_run(0);
        mode = (int)fault;
        ticks(600, 0);
        CHECK(g_lap.state == LAP_FAULT && g_lap.left_pwm == 0 && g_lap.right_pwm == 0);
        CHECK(g_lap.reason == (fault <= 2 ? LAP_NO_FEEDBACK : (fault == 3 ? LAP_REVERSE : LAP_OVERSPEED)));
    }
}

static void boot_transport(void) {
    voice_init(0);
    lap_motion_transport_fault(now);
    CHECK(g_lap.state == LAP_WAIT);
    valid_path = 0;
    path();
    lap_motion_transport_fault(now);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_TRANSPORT);
    voice_run(0);
    lap_motion_transport_fault(now);
    CHECK(g_lap.state == LAP_FAULT && g_lap.reason == LAP_TRANSPORT);
}

int main(void) {
    parser_cases();
    start_guards();
    stop_guards();
    boot_transport();
    printf("StraightVoice: %u assertions PASS; software model only\n", checks);
    return 0;
}
