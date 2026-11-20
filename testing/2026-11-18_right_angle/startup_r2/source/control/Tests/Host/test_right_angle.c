/* 使用生产校准／编码器／PI／UART及监督，验证直角弯差速和停止边界。
 * 模型不包含车辆轮距／侧滑／相机时序，不能作为实际过弯证据。
 */
#define main old_lap_test_main
#include "test_lap_motion.c"
#undef main
#include "corner_guide.h"
static void corner_running(void) {
    init(0,0); g_lap_config.straight_rpm=60.0f;
    CHECK(g_lap.state==LAP_WAIT && g_speed_match.phase==2u);
    start(); CHECK(g_lap.state==LAP_RUNNING && g_corner_startup.stage==1u);
    ticks(1100,0); CHECK(g_corner_startup.completed && g_corner_startup.stage==2u);
    g_lap_config.run_ms=12000u; start(); CHECK(g_lap.state==LAP_RUNNING);
}
static void corner_startup_cases(void) {
    uint8_t p[20]; unsigned i;
    /* 刚上电第一次长按即启动双轮，不需要先完成一秒等待再重新计长按。
     * 不发视觉，两个目标均60RPM、时限1秒，不能进入原逐轮配对状态。
     */
    init(0,0); feed=0; ticks(1200,1); ticks(31,0);
    CHECK(g_lap.state==LAP_RUNNING && g_corner_startup.stage==1u);
    CHECK(g_speed_match.left_channel==1u && g_speed_match.right_channel==2u);
    CHECK(g_speed_match.left_sign==1 && g_speed_match.right_sign==-1);
    CHECK(g_speed_match.state!=SPEED_CALIBRATING && g_lap.active.run_ms==1000u);
    ticks(100,0); CHECK(g_lap.left_target==60.0f && g_lap.right_target==60.0f);
    packet(p); p[6]=0; put16(p+18,protocol_crc16(p,18)); submit(p,now);
    ticks(1000,0);
    CHECK(g_corner_startup.completed==1u && g_corner_startup.stage==2u);
    CHECK(g_corner_startup.bench_ms==1000u && g_lap_last.elapsed_ms==1000u);
    CHECK(g_corner_startup.left_counts>=20 && g_corner_startup.right_counts>=20);
    CHECK(g_lap.left_pwm==0 && g_lap.right_pwm==0 && g_corner_startup.ground_runs==0u);
    start(); CHECK(g_lap.state==LAP_WAIT && g_lap.starts_rejected==1u);
    CHECK(g_corner_startup.blocked_reason==LAP_PATH); /* 地面缺视觉不能启动，但也不快闪锁故障。 */
    feed=1; g_lap_config.straight_rpm=60; g_lap_config.run_ms=12000;
    start(); CHECK(g_lap.state==LAP_RUNNING && g_corner_startup.ground_runs==1u);
    CHECK(g_lap.active.run_ms==12000u); /* 第二次合法KEY就是上道，不再重复测试。 */
    for(i=1;i<=4;++i) {
        init(0,0); feed=0; start(); mode=(int)i; ticks(600,0);
        CHECK(g_lap.state==LAP_FAULT && !g_corner_startup.completed);
        CHECK(g_lap.left_pwm==0 && g_lap.right_pwm==0);
    }
    init(0,0); feed=0; start(); ticks(1,1);
    CHECK(g_lap.reason==LAP_KEY && !g_corner_startup.completed);
    init(0,0); feed=0; start(); packet(p); p[3]=2; memset(p+6,0,12);p[16]=2;
    put16(p+18,protocol_crc16(p,18)); submit(p,now);
    CHECK(g_lap.state==LAP_STOPPED && !g_corner_startup.completed);
    /* 被STOP打断的双轮测试必须回到待测试阶段，不能下一次直接上道。 */
    start(); CHECK(g_lap.state==LAP_RUNNING && g_corner_startup.stage==1u);
}
int main(void) {
    corner_guide_t guide;
    float left, right, previous;
    uint8_t p[20]; unsigned i;
    corner_guide_reset(&guide);
    for(i=0;i<50;++i) {
        CHECK(corner_guide_update(&guide,60.0f,0,0,20,&left,&right));
        CHECK(left==right && left>=35.0f && left<=60.0f);
    }
    for(i=0;i<60;++i) {
        previous=guide.correction;
        CHECK(corner_guide_update(&guide,60.0f,1000,1000,20,&left,&right));
        CHECK(left>=right && left<=90.001f && right>=0);
        CHECK(guide.correction-previous<=0.06001f);
    }
    CHECK(right==0 && fabs((double)left-70.0)<0.01);
    for(i=0;i<100;++i) {
        CHECK(corner_guide_update(&guide,60.0f,0,0,20,&left,&right));
        CHECK(left<=90.001f && right<=90.001f && left>=0 && right>=0);
    }
    CHECK(left==right && left==60.0f);
    CHECK(!corner_guide_update(&guide,(float)NAN,0,0,20,&left,&right) && left==0 && right==0);
    CHECK(!corner_guide_update(&guide,60,0,1001,20,&left,&right));
    CHECK(!corner_guide_update(&guide,60,0,0,61,&left,&right));
    parser_cases(); corner_startup_cases();
    corner_running(); ticks(700,0); CHECK(g_lap.left_target==g_lap.right_target);
    bend=1000; steer=1000; ticks(1000,0);
    CHECK(g_lap.state==LAP_RUNNING && g_lap.right_target==0 && g_lap.right_pwm==0);
    CHECK(g_lap.left_target>69.9f && g_lap.left_target<70.1f);
    /* 零目标允许无脉冲；出弯恢复正目标后重新开启300ms监督。 */
    bend=0; steer=0; ticks(2000,0);
    CHECK(g_lap.state==LAP_RUNNING && g_lap.left_target==g_lap.right_target);
    ticks(8500,0); CHECK(g_lap_last.reason==LAP_LIMIT && g_lap_last.elapsed_ms==12000u);
    for(i=0;i<3;++i) {
        corner_running(); packet(p); p[6]=(uint8_t)(i==0?0:(i==1?5:9));
        put16(p+18,protocol_crc16(p,18)); submit(p,now);
        CHECK(g_lap.state==LAP_FAULT && g_lap.reason==LAP_PATH && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    }
    corner_running(); bend=1000; steer=700; ticks(500,0); feed=0;
    /* 已有当前弯道双侧后，真实新单侧包只开放短租期；反复新包也不能续租双侧。 */
    for(i=0;i<55 && g_lap.state==LAP_RUNNING;++i) {
        packet(p); p[6]=9; put16(p+18,protocol_crc16(p,18)); submit(p,now); ticks(40,0);
    }
    CHECK(g_lap.state==LAP_FAULT && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    corner_running(); feed=0; ticks(201,0); CHECK(g_lap.reason==LAP_LINK);
    path(); CHECK(g_lap.state==LAP_FAULT);
    corner_running(); ticks(1,1); CHECK(g_lap.reason==LAP_KEY && g_lap.left_pwm==0);
    for(i=1;i<=4;++i) {
        corner_running(); mode=(int)i; ticks(600,0);
        CHECK(g_lap.state==LAP_FAULT);
        CHECK(g_lap.reason==(i<=2?LAP_NO_FEEDBACK:(i==3?LAP_REVERSE:LAP_OVERSPEED)));
    }
    for(i=2;i<=3;++i) {
        corner_running(); feed=0; packet(p); p[2]=(uint8_t)i;
        put16(p+18,protocol_crc16(p,18)); submit(p,now); ticks(201,0);
        CHECK(g_lap.reason==LAP_LINK);
    }
    corner_running(); packet(p); p[3]=2; memset(p+6,0,12); p[16]=2;
    put16(p+18,protocol_crc16(p,18)); submit(p,now-1000u);
    CHECK(g_lap.state==LAP_STOPPED && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    printf("RightAngle: %u assertions PASS; host models only\n",checks);
    return 0;
}
