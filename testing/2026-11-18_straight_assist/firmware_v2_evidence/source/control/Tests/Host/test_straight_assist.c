/* 复用真实编码器采样、校准、PI、帧解析和1ms监督的既有主机夹具。
 * 原测试入口保留但不执行旧弯道／低速策略场景；下方单独验收直道行为。
 * 电机替身不包含真实地面侧滑，不把这些断言当现场直行或速度证据。
 */
#define main old_lap_test_main
#include "test_lap_motion.c"
#undef main
#include "straight_guide.h"

static void straight_running(float cruise, int mapping, uint32_t initial) {
    init(initial,mapping); calibrated(); g_lap_config.straight_rpm=cruise;
    g_lap_config.run_ms=2000u; start(); CHECK(g_lap.state==LAP_RUNNING);
}
static void guide_cases(void) {
    straight_guide_t guide;
    float left, right, previous, prior_command;
    unsigned i;
    straight_guide_reset(&guide);
    /* +/-60千分量的交替小波动始终处于滤波死区，不产生左右差速。 */
    for(i=0u;i<100u;++i) {
        CHECK(straight_guide_update(&guide,80.0f,(int16_t)(i%2u?60:-60),20u,&left,&right));
        CHECK(left==right && guide.correction==0.0f);
        CHECK(guide.command_rpm>=40.0f && guide.command_rpm<=80.0f);
    }
    CHECK(guide.command_rpm==80.0f);
    for(i=0u;i<50u;++i) {
        previous=guide.correction; prior_command=guide.command_rpm;
        CHECK(straight_guide_update(&guide,100.0f,1000,20u,&left,&right));
        CHECK(fabs((double)(guide.correction-previous))<=0.012001);
        CHECK(guide.command_rpm-prior_command<=2.0001f);
        CHECK(left>=35.19f && right>=35.19f && left<=112.001f && right<=112.001f);
    }
    CHECK(guide.correction>0.119f && left>right);
    for(i=0u;i<70u;++i) {
        previous=guide.correction;
        CHECK(straight_guide_update(&guide,80.0f,-1000,20u,&left,&right));
        CHECK(fabs((double)(guide.correction-previous))<=0.012001);
    }
    CHECK(guide.correction < -0.119f && right>left);
    CHECK(!straight_guide_update(&guide,(float)NAN,0,20u,&left,&right) && left==0 && right==0);
    CHECK(!straight_guide_update(&guide,101.0f,0,20u,&left,&right));
    CHECK(!straight_guide_update(&guide,80.0f,1001,20u,&left,&right));
    CHECK(!straight_guide_update(&guide,80.0f,0,61u,&left,&right));
    guide.filtered_error=(float)NAN;
    CHECK(!straight_guide_update(&guide,80.0f,0,20u,&left,&right));
}
static void motion_cases(void) {
    unsigned i;
    uint8_t p[20];
    straight_running(80.0f,0,0u);
    for(i=0u;i<30u;++i) {
        steer=i%2u?60:-60; ticks(40,0);
        CHECK(g_lap.state==LAP_RUNNING && g_lap.left_target==g_lap.right_target);
    }
    printf("model at 1.2s: measured %.2f / %.2f RPM, targets %.2f / %.2f RPM\n",
        (double)g_lap.left_rpm,(double)g_lap.right_rpm,(double)g_lap.left_target,(double)g_lap.right_target);
    CHECK(fabs((double)g_lap.left_rpm-80.0)<7.0 && fabs((double)g_lap.right_rpm-80.0)<7.0);
    CHECK(g_lap.left_pwm!=g_lap.right_pwm); /* 不同电机增益由编码器PI补偿。 */
    ticks(900,0);
    CHECK(g_lap_last.reason==LAP_LIMIT && g_lap_last.elapsed_ms==2000u);
    CHECK(g_lap_diag.frozen && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    for(i=0u;i<2u;++i) {
        straight_running(80.0f,(int)i,i?UINT32_MAX-8000u:0u);
        steer=i?-1000:1000; ticks(800,0);
        CHECK(g_lap.state==LAP_RUNNING);
        CHECK(g_lap.left_target>=70.39f && g_lap.right_target>=70.39f);
        CHECK(i?(g_lap.right_target>g_lap.left_target):(g_lap.left_target>g_lap.right_target));
    }
    /* 巡航／时限只在启动锁定；运行中Watch修改不能延长本次或骤然提速。 */
    straight_running(80.0f,0,0u); g_lap_config.straight_rpm=100.0f; g_lap_config.run_ms=3000u;
    ticks(700,0); CHECK(g_lap.active.straight_rpm==80.0f && g_lap.active.run_ms==2000u);
    /* 无效／单边／历史／非直道请求立即撤输出。 */
    for(i=0u;i<4u;++i) {
        straight_running(80.0f,0,0u); packet(p);
        if(i==0u) p[6]=0u;
        if(i==1u) p[6]=9u;
        if(i==2u) p[6]=5u;
        if(i==3u) put16(p+12,1u);
        put16(p+18,protocol_crc16(p,18)); submit(p,now);
        CHECK(g_lap.state==LAP_FAULT && g_lap.reason==LAP_PATH && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    }
    straight_running(80.0f,0,0u); feed=0; ticks(201,0);
    CHECK(g_lap.reason==LAP_LINK && g_lap_last.valid);
    path(); CHECK(g_lap.state==LAP_FAULT); /* 恢复画面不能自动重启。 */
    straight_running(80.0f,0,0u); ticks(1,1); CHECK(g_lap.reason==LAP_KEY && g_lap.left_pwm==0);
    for(i=1u;i<=4u;++i) {
        straight_running(80.0f,0,0u); mode=(int)i; ticks(600,0);
        CHECK(g_lap.state==LAP_FAULT);
        CHECK(g_lap.reason==(i<=2u?LAP_NO_FEEDBACK:(i==3u?LAP_REVERSE:LAP_OVERSPEED)));
    }
    straight_running(80.0f,0,0u); packet(p); p[3]=2; memset(p+6,0,12); p[16]=2;
    put16(p+18,protocol_crc16(p,18)); submit(p,now-1000u);
    CHECK(g_lap.state==LAP_STOPPED && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    /* v2包即使CRC正确也不能取得v3许可；错配后保持原断流保护。 */
    straight_running(80.0f,0,0u); feed=0; packet(p); p[2]=2;
    put16(p+18,protocol_crc16(p,18)); submit(p,now); ticks(201,0); CHECK(g_lap.reason==LAP_LINK);
    for(i=0u;i<3u;++i) {
        init(0,0); calibrated();
        if(i==0u) g_lap_config.straight_rpm=39.0f;
        if(i==1u) g_lap_config.straight_rpm=101.0f;
        if(i==2u) g_lap_config.run_ms=3001u;
        start(); CHECK(g_lap.reason==LAP_CONFIG && g_lap.left_pwm==0);
    }
}
static void balance_cases(void) {
    uint16_t left=335u, right=500u;
    float adjustment;
    unsigned i;
    float integral_difference=0.0f, maximum_difference=0.0f;
    /* 复现真实563ms停车快照：视觉已要求左慢右快，实测却左快。
     * 同步补偿必须继续减左，不因右轮已达50%就放弃纠偏或提高限幅。
     */
    CHECK(straight_balance_update(70.4f,89.6f,110.77f,82.51f,&left,&right,&adjustment));
    CHECK(adjustment==100.0f && left==235u && right==500u);
    left=400u; right=400u;
    CHECK(straight_balance_update(70.4f,89.6f,70.4f,89.6f,&left,&right,&adjustment));
    CHECK(fabs((double)adjustment)<0.001 && left==400u && right==400u);
    CHECK(straight_balance_update(80.0f,80.0f,60.0f,90.0f,&left,&right,&adjustment));
    CHECK(adjustment==-100.0f && left==500u && right==300u);
    CHECK(!straight_balance_update(80.0f,80.0f,(float)NAN,90.0f,&left,&right,&adjustment));
    CHECK(left==0u && right==0u);
    init(0,0); calibrated(); g_lap_config.straight_rpm=80.0f; g_lap_config.run_ms=2000u;
    mode=7; start(); CHECK(g_lap.state==LAP_RUNNING);
    for(i=0u;i<30u;++i) {
        float difference;
        ticks(20,0); CHECK(g_lap.state==LAP_RUNNING);
        difference=(float)fabs((double)(ls-rs));
        integral_difference+=difference*0.02f;
        if(difference>maximum_difference) maximum_difference=difference;
    }
    printf("loaded transient model first 600ms: max wheel difference %.2f RPM, integrated difference %.2f RPM*s\n",
        (double)maximum_difference,(double)integral_difference);
    CHECK(maximum_difference<12.0f && integral_difference<5.0f);
    ticks(900,0); CHECK(g_lap.state==LAP_RUNNING);
    CHECK(fabs((double)g_lap.left_rpm-80.0)<10.0 && fabs((double)g_lap.right_rpm-80.0)<10.0);
    ticks(600,0); CHECK(g_lap_last.reason==LAP_LIMIT && g_lap_last.elapsed_ms==2000u);
}
int main(void) {
    guide_cases(); parser_cases(); motion_cases(); balance_cases();
    printf("StraightAssist: %u scenario assertions PASS; real PI/encoder/link/calibration; model only\n",checks);
    return 0;
}
