/* 使用真实编码器、PI、SpeedMatch校准、v2解析和循迹监督。
 * 虚拟电机只提供计数反馈；不得将此程序结果写成地面速度／跑圈证据。
 */
#include "lap_motion.h"
#include "lap_link.h"
#include "protocol.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#undef assert
#define assert(e) do { if (!(e)) { fprintf(stderr,"FAIL line %u: %s\n",(unsigned)__LINE__,#e); exit(1); } } while (0)
static encoder_counter_t a, b;
static lap_parser_t parser;
static uint32_t now, sampled;
static uint16_t raw_a, raw_b;
static float ls, rs, fa, fb;
static uint8_t sequence;
static int feed, valid_path, steer, bend, history, mode, reverse_mapping;
static unsigned checks;
#define CHECK(e) do { ++checks; assert(e); } while (0)
static void put16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); }
static void packet(uint8_t *p) {
    memset(p,0,20); p[0]=0xa5; p[1]=0x5a; p[2]=2; p[3]=1; p[4]=12; p[5]=sequence++;
    p[6]=(uint8_t)((valid_path?1:0)|(history?4:0)); p[7]=80;
    put16(p+8,(uint16_t)steer); put16(p+12,(uint16_t)bend); put16(p+14,20);
    put16(p+18,protocol_crc16(p,18));
}
static void submit(uint8_t *p, uint32_t arrival) {
    unsigned i;
    for(i=0;i<20;++i) if(lap_link_push(&parser,p[i])) lap_motion_receive(parser.bytes,arrival,now);
}
static void path(void) { uint8_t p[20]; packet(p); submit(p,now); }
static void sample(void) {
    int da,db;
    ls+=((float)g_lap.left_pwm*.25f-ls)*.25f;
    rs+=((float)g_lap.right_pwm*.32f-rs)*.25f;
    if(mode==1) ls=rs=0;
    if(mode==2) rs=0;
    fa+=ls*1058.6f/3000.0f; fb+=rs*1060.8f/3000.0f;
    da=(int)fa; db=(int)fb; fa-=(float)da; fb-=(float)db;
    if(mode==3) { da=-da; db=-db; }
    if(mode==4) { da=300; db=300; }
    raw_a=(uint16_t)((int32_t)raw_a+(reverse_mapping?-db:da));
    raw_b=(uint16_t)((int32_t)raw_b+(reverse_mapping?da:-db));
    encoder_counter_update(&a,raw_a,now); encoder_counter_update(&b,raw_b,now);
    lap_motion_sample(now,&a.sample,&b.sample);
}
static void ticks(unsigned n, uint8_t key) {
    while(n--) {
        ++now;
        if(feed && now%40u==0u) path();
        if((uint32_t)(now-sampled)>=20u) { sample(); sampled=now; }
        lap_motion_tick(now,key);
        assert(g_lap.left_pwm<=500u && g_lap.right_pwm<=500u);
        if(g_lap.state==LAP_FAULT) assert(g_lap.left_pwm==0 && g_lap.right_pwm==0);
    }
}
static void init(uint32_t start, int mapping) {
    now=sampled=start; reverse_mapping=mapping; raw_a=raw_b=0; ls=rs=fa=fb=0;
    feed=1; valid_path=1; steer=bend=history=mode=0; sequence=0;
    encoder_counter_init(&a); encoder_counter_init(&b); lap_link_init(&parser); lap_motion_init(now);
    g_lap_config.straight_rpm=40; g_lap_config.run_ms=3000;
}
static void cal_trigger(void) {
    unsigned i;
    for(i=0;i<5000 && g_speed_match.state!=SPEED_READY;++i) ticks(1,0);
    CHECK(g_speed_match.state==SPEED_READY);
    ticks(1200,1); ticks(31,0); CHECK(g_speed_match.state==SPEED_CALIBRATING);
    ticks(500,0);
}
static void calibrated(void) {
    cal_trigger(); CHECK(g_speed_match.phase==1);
    cal_trigger(); CHECK(g_speed_match.phase==2 && g_lap.state==LAP_WAIT);
}
static void start(void) { ticks(1800,0); ticks(1200,1); ticks(31,0); }
static void running(void) { init(0,0); calibrated(); start(); CHECK(g_lap.state==LAP_RUNNING); }
static void parser_cases(void) {
    uint8_t p[20], q[20]; unsigned i;
    init(0,0); packet(p);
    p[2]=1; put16(p+18,protocol_crc16(p,18)); submit(p,now); CHECK(parser.accepted==0);
    packet(p); p[8]^=1; submit(p,now); CHECK(parser.accepted==0);
    packet(p); memcpy(q,p,20); q[17]=1; put16(q+18,protocol_crc16(q,18)); submit(q,now);
    CHECK(parser.accepted==0);
    for(i=0;i<7;++i) (void)lap_link_push(&parser,0x11);
    submit(p,now); CHECK(parser.accepted==1 && g_lap.received==1);
    submit(p,now); CHECK(g_lap.duplicates==1);
}
static void fault_cases(void) {
    uint8_t p[20]; unsigned m;
    running(); ticks(1,1); CHECK(g_lap.reason==LAP_KEY); ticks(2000,0); CHECK(g_lap.state==LAP_FAULT);
    running(); feed=0; ticks(201,0); CHECK(g_lap.reason==LAP_LINK);
    valid_path=1; path(); CHECK(g_lap.state==LAP_FAULT);
    running(); valid_path=0; path(); CHECK(g_lap.reason==LAP_PATH);
    for(m=1;m<=4;++m) {
        running(); mode=(int)m; ticks(600,0);
        CHECK(g_lap.state==LAP_FAULT);
        CHECK(g_lap.reason==(m<=2?LAP_NO_FEEDBACK:(m==3?LAP_REVERSE:LAP_OVERSPEED)));
    }
    running(); packet(p); feed=0; now+=101; submit(p,now-101); CHECK(g_lap.reason==LAP_LINK);
    running(); now+=61; lap_motion_tick(now,0); CHECK(g_lap.reason==LAP_ENCODER);
    running(); lap_motion_fault(LAP_TRANSPORT,now); CHECK(g_lap.state==LAP_FAULT && g_lap.left_pwm==0);
    running(); packet(p); p[3]=2; memset(p+6,0,12); p[16]=2;
    put16(p+18,protocol_crc16(p,18)); submit(p,now-1000);
    CHECK(g_lap.state==LAP_STOPPED && !g_lap.path_valid && g_lap.left_pwm==0);
    init(0,0); calibrated(); history=1; start(); CHECK(g_lap.state==LAP_WAIT && g_lap.starts_rejected==1);
    init(0,0); calibrated(); g_lap_config.straight_rpm=(float)NAN; start(); CHECK(g_lap.reason==LAP_CONFIG);
    /* 发送端报告的源年龄必须进入接收端200ms监督，不能仅按串口到达计时。 */
    running(); packet(p); put16(p+10,190u); put16(p+18,protocol_crc16(p,18)); submit(p,now);
    feed=0; ticks(9,0); CHECK(g_lap.reason==LAP_LINK);
    running(); packet(p); p[7]=39; put16(p+18,protocol_crc16(p,18)); submit(p,now); CHECK(g_lap.reason==LAP_PATH);
    running(); packet(p); put16(p+14,101u); put16(p+18,protocol_crc16(p,18)); submit(p,now); CHECK(g_lap.reason==LAP_PATH);
    init(0,0); packet(p); p[3]=2; memset(p+6,0,12); p[16]=2; put16(p+18,protocol_crc16(p,18));
    submit(p,now); CHECK(g_lap.state==LAP_CALIBRATION && g_speed_match.state!=SPEED_FAULT);
    ticks(1007,0); submit(p,now); ticks(33,0);
    CHECK(g_lap.state==LAP_CALIBRATION && g_speed_match.state!=SPEED_FAULT);
    /* 单轮校准正在动作时收到STOP，必须真归零且锁住，不能继续500ms。 */
    ticks(2000,0); ticks(1200,1); ticks(31,0); CHECK(g_speed_match.state==SPEED_CALIBRATING);
    submit(p,now); CHECK(g_lap.state==LAP_FAULT && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    init(0,0); calibrated(); packet(p); p[6]=9u; put16(p+18,protocol_crc16(p,18));
    feed=0; submit(p,now); ticks(100,0); CHECK(g_lap.single!=0u);
    running(); packet(p); p[6]=5u; put16(p+10,100u); put16(p+18,protocol_crc16(p,18));
    submit(p,now); feed=0; ticks(19,0); CHECK(g_lap.reason==LAP_LINK);
}
static void differential_case(int mapping, uint32_t initial) {
    init(initial,mapping); calibrated(); g_lap_config.run_ms=20000; start();
    CHECK(g_lap.state==LAP_RUNNING);
    ticks(1500,0); CHECK(fabs((double)g_lap.left_rpm-40)<6 && fabs((double)g_lap.right_rpm-40)<6);
    steer=1000; bend=1000; ticks(1200,0);
    CHECK(g_lap.state==LAP_RUNNING && g_lap.left_target>0 && g_lap.right_target==0 && g_lap.right_pwm==0);
    /* 合法内轮停转超过300ms不会故障；恢复直行时重新监督右轮反馈。 */
    steer=0; bend=0; ticks(1500,0); CHECK(g_lap.state==LAP_RUNNING && g_lap.right_pwm>0);
    steer=-1000; path(); ticks(500,0); CHECK(g_lap.left_target==0 && g_lap.right_target>0);
    steer=0; mode=2; ticks(500,0); CHECK(g_lap.reason==LAP_NO_FEEDBACK);
}
int main(void) {
    parser_cases(); fault_cases(); differential_case(0,0); differential_case(1,UINT32_MAX-8000u);
    running(); ticks(3000,0); CHECK(g_lap.state!=LAP_RUNNING && g_lap.left_pwm==0);
    printf("LowSpeedLap: %u scenario assertions PASS; real PI/encoder/link/calibration; model only\n",checks);
    return 0;
}
