/* 使用真实PI、编码器算法与状态机；机械模型只用于检查控制方向和收敛逻辑。 */
#include "speed_match.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
static encoder_counter_t a, b;
static uint16_t raw_a, raw_b;
static uint32_t now, last_sample;
static int wiring, moving_mode;
static float left_speed, right_speed, fraction_a, fraction_b;
static float absf(float x) { return x < 0.0f ? -x : x; }
static void init(uint32_t initial, int reversed_wiring) {
    now=last_sample=initial; raw_a=raw_b=0u; wiring=reversed_wiring; moving_mode=0;
    left_speed=right_speed=fraction_a=fraction_b=0.0f;
    encoder_counter_init(&a); encoder_counter_init(&b); speed_match_init(now);
    g_speed_config.target_rpm=60.0f; g_speed_config.pi.kp=2.0f;
    g_speed_config.pi.ki=4.0f; g_speed_config.pi.feedforward=300.0f;
    g_speed_config.run_ms=3000u;
}
static void sample(void) {
    float left_goal=(float)g_speed_match.left_pwm * 0.25f;
    float right_goal=(float)g_speed_match.right_pwm * 0.32f;
    float ca,cb;
    int da,db;
    if (moving_mode==1) left_goal=right_goal=0.0f; /* 断反馈／堵转模型。 */
    left_speed+=(left_goal-left_speed)*0.25f;
    right_speed+=(right_goal-right_speed)*0.25f;
    if (moving_mode==1) left_speed=right_speed=0.0f;
    ca=left_speed*1058.6f/3000.0f;
    cb=right_speed*1060.8f/3000.0f;
    if (wiring==0) { fraction_a+=ca; fraction_b-=cb; }
    else { fraction_a-=cb; fraction_b+=ca; }
    da=(int)fraction_a; db=(int)fraction_b;
    fraction_a-=(float)da; fraction_b-=(float)db;
    if (moving_mode==2 && g_speed_match.state==SPEED_RUNNING) { da=-da; db=-db; }
    if (moving_mode==3 && g_speed_match.state==SPEED_RUNNING) { da=300; db=-300; }
    if (moving_mode==4) db=da; /* 单轮动作造成两通道联动，拒绝配对。 */
    raw_a=(uint16_t)((uint32_t)raw_a+(uint32_t)da);
    raw_b=(uint16_t)((uint32_t)raw_b+(uint32_t)db);
    encoder_counter_update(&a,raw_a,now); encoder_counter_update(&b,raw_b,now);
    speed_match_sample(now,&a.sample,&b.sample);
}
static void ticks(unsigned count, uint8_t key) {
    while (count-- != 0u) {
        ++now;
        if ((uint32_t)(now-last_sample)>=20u) { sample(); last_sample=now; }
        speed_match_tick(now,key);
        assert(g_speed_match.left_pwm<=500u && g_speed_match.right_pwm<=500u);
        if (g_speed_match.state==SPEED_FAULT) assert(g_speed_match.left_pwm==0u && g_speed_match.right_pwm==0u);
    }
}
static void wait_ready(void) {
    unsigned i;
    for (i=0u;i<4000u && g_speed_match.state!=SPEED_READY;++i) ticks(1u,0u);
    assert(g_speed_match.state==SPEED_READY);
}
static void trigger(void) {
    wait_ready(); ticks(1100u,1u); assert(g_speed_match.state==SPEED_ARMED);
    ticks(31u,0u);
}
static void calibrate(void) {
    trigger(); assert(g_speed_match.state==SPEED_CALIBRATING && g_speed_match.left_pwm==500u && g_speed_match.right_pwm==0u);
    ticks(499u,0u); assert(g_speed_match.state==SPEED_CALIBRATING);
    ticks(1u,0u); assert(g_speed_match.state==SPEED_SETTLING && g_speed_match.phase==1u);
    trigger(); assert(g_speed_match.state==SPEED_CALIBRATING && g_speed_match.right_pwm==500u && g_speed_match.left_pwm==0u);
    ticks(500u,0u); assert(g_speed_match.state==SPEED_SETTLING && g_speed_match.phase==2u);
    assert(g_speed_match.left_channel==(wiring==0?1u:2u) && g_speed_match.left_sign==1);
    assert(g_speed_match.right_channel==(wiring==0?2u:1u) && g_speed_match.right_sign==-1);
}
static void normal_and_repeat(int reverse, uint32_t initial) {
    uint32_t begin;
    init(initial,reverse); calibrate(); trigger(); begin=now;
    assert(g_speed_match.state==SPEED_RUNNING);
    g_speed_config.target_rpm=100.0f; g_speed_config.run_ms=500u; /* 本轮仍锁定60/3000。 */
    ticks(2500u,0u);
    assert(g_speed_match.state==SPEED_RUNNING && g_speed_match.active.target_rpm==60.0f);
    printf("model mapping %d: left %.2f right %.2f diff %.2f PWM %u/%u matched %u ms\n",reverse,
           (double)g_speed_match.left_rpm,(double)g_speed_match.right_rpm,(double)g_speed_match.difference_rpm,
           (unsigned)g_speed_match.left_pwm,(unsigned)g_speed_match.right_pwm,(unsigned)g_speed_match.matched_ms);
    assert(absf(g_speed_match.left_rpm-60.0f)<5.0f && absf(g_speed_match.right_rpm-60.0f)<5.0f);
    assert(absf(g_speed_match.difference_rpm)<5.0f && g_speed_match.left_pwm>g_speed_match.right_pwm);
    ticks(499u,0u); assert(g_speed_match.state==SPEED_RUNNING);
    ticks(1u,0u); assert(g_speed_match.state==SPEED_SETTLING && g_speed_match.stop_ms-begin==3000u);
    assert(g_speed_match.left_pwm==0u && g_speed_match.right_pwm==0u);
    assert(g_speed_match.last_matched_ms>=500u && absf(g_speed_match.last_difference_rpm)<5.0f);
    assert(g_speed_match.last_left_pwm>0u && g_speed_match.last_right_pwm>0u);
    {
        float saved=g_speed_match.last_left_rpm;
        ticks(1000u,0u); assert(g_speed_match.last_left_rpm==saved);
    }
    g_speed_config.target_rpm=60.0f; trigger();
    assert(g_speed_match.state==SPEED_RUNNING && g_speed_match.runs==2u);
    ticks(500u,0u); assert(g_speed_match.state==SPEED_SETTLING);
}
static void fault_cases(void) {
    unsigned mode;
    for(mode=1u;mode<=3u;++mode) {
        init(0u,0); calibrate(); trigger(); moving_mode=(int)mode;
        ticks(400u,0u);
        assert(g_speed_match.state==SPEED_FAULT);
        assert(g_speed_match.error==(mode==1u?SPEED_ERROR_NO_FEEDBACK:(mode==2u?SPEED_ERROR_REVERSE:SPEED_ERROR_OVERSPEED)));
        ticks(1500u,1u); ticks(1500u,0u); assert(g_speed_match.state==SPEED_FAULT);
    }
    init(0u,0); moving_mode=4; trigger(); ticks(500u,0u);
    assert(g_speed_match.state==SPEED_FAULT && g_speed_match.error==SPEED_ERROR_MAPPING);
    init(0u,0); moving_mode=1; trigger(); ticks(500u,0u);
    assert(g_speed_match.error==SPEED_ERROR_MAPPING);
    init(0u,0); calibrate(); trigger(); ticks(1u,1u);
    assert(g_speed_match.error==SPEED_ERROR_KEY);
    init(0u,0); calibrate(); trigger(); g_speed_config.target_rpm=0.0f; ticks(1u,0u);
    assert(g_speed_match.error==SPEED_ERROR_KEY);
    init(0u,0); calibrate(); trigger();
    now+=61u; speed_match_tick(now,0u); assert(g_speed_match.error==SPEED_ERROR_TIMING);
    init(0u,0); calibrate(); a.sample.flags=ENCODER_CONTINUITY_LOST;
    now+=20u; a.sample.dt_ms=b.sample.dt_ms=20u; speed_match_sample(now,&a.sample,&b.sample);
    assert(g_speed_match.error==SPEED_ERROR_SAMPLE);
    init(0u,0); calibrate(); g_speed_config.target_rpm=(float)NAN; trigger(); assert(g_speed_match.error==SPEED_ERROR_CONFIG);
    init(0u,0); calibrate(); g_speed_config.run_ms=3001u; trigger(); assert(g_speed_match.error==SPEED_ERROR_CONFIG);
    init(0u,0); wait_ready(); ticks(5100u,1u); assert(g_speed_match.error==SPEED_ERROR_STUCK_KEY);
    init(0u,0); wait_ready(); ticks(300u,1u); ticks(31u,0u); assert(g_speed_match.left_pwm==0u && g_speed_match.right_pwm==0u);
}
static void pi_cases(void) {
    speed_pi_t pi; speed_pi_config_t c={10.0f,20.0f,500.0f}; uint16_t duty;
    unsigned i; speed_pi_reset(&pi);
    for(i=0u;i<1000u;++i) assert(speed_pi_update(&pi,&c,120.0f,0.0f,20u,&duty) && duty==500u);
    assert(pi.integral==0.0f);
    assert(speed_pi_update(&pi,&c,10.0f,120.0f,20u,&duty) && duty==0u);
    assert(!speed_pi_update(&pi,&c,60.0f,NAN,20u,&duty) && duty==0u && pi.integral==0.0f);
    assert(!speed_pi_update(&pi,&c,-1.0f,0.0f,20u,&duty));
    assert(!speed_pi_update(&pi,&c,60.0f,0.0f,0u,&duty));
    assert(!speed_pi_update(&pi,&c,60.0f,0.0f,101u,&duty));
    assert(speed_pi_update(&pi,&c,0.0f,60.0f,20u,&duty) && duty==0u);
    c.kp=(float)INFINITY; assert(!speed_pi_config_valid(&c));
}
int main(void) {
    pi_cases(); normal_and_repeat(0,0u); normal_and_repeat(1,UINT32_MAX-6000u); fault_cases();
    puts("SpeedMatch: real PI + encoder + state-machine tests PASS (model only)");
    return 0;
}
