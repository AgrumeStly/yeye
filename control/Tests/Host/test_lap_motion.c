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
#ifdef RIGHT_ANGLE_TARGET
static int corner_flags;
#endif
#ifdef RIGHT_ANGLE_VOICE_TARGET
static uint8_t path_quality;
#endif
static unsigned checks;
#define CHECK(e) do { ++checks; assert(e); } while (0)
static void put16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); }
static void packet(uint8_t *p) {
    memset(p,0,20); p[0]=0xa5; p[1]=0x5a; p[2]=2; p[3]=1; p[4]=12; p[5]=sequence++;
#ifdef STRAIGHT_ASSIST_TARGET
    p[2]=3; /* 同一真实编码器／电机替身可复用于直道v3的独立检查入口。 */
#endif
#ifdef STRAIGHT_VOICE_TARGET
    p[2]=6;
#endif
#ifdef RIGHT_ANGLE_VOICE_TARGET
    p[2]=8;
#elif defined(RIGHT_ANGLE_TARGET)
    p[2]=5; /* 首弯v5：当前L形预测，保留其它旧目标原封包。 */
#endif
    p[6]=(uint8_t)((valid_path?1:0)|(history?4:0)); p[7]=80;
#ifdef RIGHT_ANGLE_TARGET
    if (corner_flags) p[6]=(uint8_t)((valid_path?1:0)|corner_flags);
#endif
#ifdef RIGHT_ANGLE_VOICE_TARGET
    p[7]=path_quality;
#endif
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
    float previous_left=ls, previous_right=rs;
    ls+=((float)g_lap.left_pwm*.25f-ls)*.25f;
    rs+=((float)g_lap.right_pwm*.32f-rs)*.25f;
    /* 假设性静摩擦模型：静止时需42%才起转，动起来后维持原模型。
     * 仅用于暴露“低PWM永远起不来”的控制缺口，不是本车实测起转阈值。
     */
    if(mode==5) {
        if(fabs((double)previous_left)<.1 && g_lap.left_pwm<420u) ls=0;
        if(fabs((double)previous_right)<.1 && g_lap.right_pwm<420u) rs=0;
    }
    /* 假设性持续低速死区模型：18%以下快速停转，正转时转速随超额PWM增加；
     * 静止另需42%起步。参数只用于比较前馈下限策略，不是本车电机标定。
     */
    if(mode==6) {
        float demand_left=(float)g_lap.left_pwm>180.0f ? ((float)g_lap.left_pwm-180.0f)*.9f : 0.0f;
        float demand_right=(float)g_lap.right_pwm>180.0f ? ((float)g_lap.right_pwm-180.0f)*.9f : 0.0f;
        if(fabs((double)previous_left)<.1 && g_lap.left_pwm<420u) demand_left=0;
        if(fabs((double)previous_right)<.1 && g_lap.right_pwm<420u) demand_right=0;
        ls=previous_left+(demand_left-previous_left)*.25f;
        rs=previous_right+(demand_right-previous_right)*.25f;
        if(g_lap.left_pwm<=180u) ls=previous_left>10.0f ? previous_left-10.0f : 0.0f;
        if(g_lap.right_pwm<=180u) rs=previous_right>10.0f ? previous_right-10.0f : 0.0f;
    }
    if(mode==1) ls=rs=0;
    if(mode==2) rs=0;
#ifdef STRAIGHT_ASSIST_TARGET
    if(mode==7) {
        /* 仅为早期带载瞬态的近似模型，系数来自ground_02的137..557ms原始记录。
         * 该短段拟合不能外推为稳态电机参数或实测性能；用于暴露左右增益／惯性
         * 不同的起步偏航风险。旧目标及原有电机替身完全不使用此分支。
         */
        ls=0.97566627f*previous_left+0.04646166f*(float)g_lap.left_pwm-14.25056101f;
        rs=0.94432472f*previous_right+0.06451199f*(float)g_lap.right_pwm-24.95763819f;
        if(ls<0.0f) ls=0.0f;
        if(rs<0.0f) rs=0.0f;
    }
#endif
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
#ifdef RIGHT_ANGLE_TARGET
    corner_flags=0;
#endif
#ifdef RIGHT_ANGLE_VOICE_TARGET
    path_quality=80;
#endif
    encoder_counter_init(&a); encoder_counter_init(&b); lap_link_init(&parser); lap_motion_init(now);
    g_lap_config.straight_rpm=40; g_lap_config.run_ms=3000;
    g_lap_config.min_feedforward=200;
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
static void startup_cases(void) {
    uint8_t p[20]; uint32_t elapsed;
    /* 双轮完全无反馈：补偿仅5个20ms样本，300ms保护仍锁定且保留结果。 */
    init(0,0); calibrated(); mode=1; start(); ticks(400,0);
    CHECK(g_lap.state==LAP_FAULT && g_lap.reason==LAP_NO_FEEDBACK);
    CHECK(g_lap_last.valid && g_lap_last.reason==LAP_NO_FEEDBACK);
    CHECK(g_lap_last.elapsed_ms>=300u && g_lap_last.elapsed_ms<=320u);
    CHECK(g_lap_last.left_boost_samples==5u && g_lap_last.right_boost_samples==5u);
    CHECK(g_lap_last.left_pwm<500u && g_lap_last.right_pwm<500u);
    CHECK(g_lap_last.left_target==40.0f && g_lap_last.right_target==40.0f);
    elapsed=g_lap_last.elapsed_ms; ticks(500,0);
    CHECK(g_lap_last.reason==LAP_NO_FEEDBACK && g_lap_last.elapsed_ms==elapsed);
    /* 单轮堵转不能带着另一轮继续跑；有反馈轮立即退出起步补偿。 */
    init(0,0); calibrated(); mode=2; start(); ticks(400,0);
    CHECK(g_lap.reason==LAP_NO_FEEDBACK);
    CHECK(g_lap_last.left_boost_samples<5u && g_lap_last.right_boost_samples==5u);
    /* 人工KEY在补偿期间仍立即撤输出。 */
    init(0,0); calibrated(); mode=1; start(); ticks(25,0);
    CHECK(g_lap.left_pwm==500u && g_lap.right_pwm==500u);
    ticks(1,1); CHECK(g_lap.reason==LAP_KEY && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    /* 零目标内轮绝不获得补偿。 */
    init(0,0); calibrated(); steer=1000; start(); ticks(100,0); ticks(1,1);
    CHECK(g_lap_last.right_target==0.0f && g_lap_last.right_pwm==0u);
    CHECK(g_lap_last.right_boost_samples==0u);
    /* 具有静摩擦的模型能够起步，补偿后回到真实PI；正常3秒结果保留。 */
    init(0,0); calibrated(); mode=5; start(); ticks(1000,0);
    CHECK(g_lap.state==LAP_RUNNING && g_lap.left_rpm>10.0f && g_lap.right_rpm>10.0f);
    ticks(2100,0);
    CHECK(g_lap_last.valid && g_lap_last.reason==LAP_LIMIT && g_lap_last.elapsed_ms==3000u);
    CHECK(g_lap_last.left_boost_samples>0u && g_lap_last.left_boost_samples<=5u);
    CHECK(g_lap_last.right_boost_samples>0u && g_lap_last.right_boost_samples<=5u);
    CHECK(g_lap_last.left_rpm>10.0f && g_lap_last.right_rpm>10.0f);
    /* 后续远程清理STOP不覆盖正常时限原因和运行中的最后转速。 */
    packet(p); p[3]=2; memset(p+6,0,12); p[16]=2;
    put16(p+18,protocol_crc16(p,18)); submit(p,now);
    CHECK(g_lap_last.reason==LAP_LIMIT && g_lap_last.elapsed_ms==3000u);
}
static void low_speed_cases(void) {
    const float invalid_values[3]={-1.0f,301.0f,(float)NAN};
    int s; unsigned i;
    /* 同一假设性低速死区：旧的线性前馈会在内轮20RPM处无反馈停车。 */
    init(0,0); calibrated(); mode=6; steer=500; g_lap_config.min_feedforward=0;
    start(); ticks(1500,0); CHECK(g_lap.state==LAP_FAULT && g_lap.reason==LAP_NO_FEEDBACK);
    /* 前馈下限应支持两种差速及直行，仍按3秒结束，不能把目标20直接钳成40。 */
    for(s=-500;s<=500;s+=500) {
        init(0,0); calibrated(); mode=6; steer=s; start(); ticks(1000,0);
        CHECK(g_lap.state==LAP_RUNNING && g_lap.left_rpm>5.0f && g_lap.right_rpm>5.0f);
        CHECK(g_lap.left_target==(s<0?20.0f:(s>0?60.0f:40.0f)));
        CHECK(g_lap.right_target==(s<0?60.0f:(s>0?20.0f:40.0f)));
        ticks(2100,0);
        CHECK(g_lap_last.reason==LAP_LIMIT && g_lap_last.elapsed_ms==3000u);
        CHECK(fabs((double)(g_lap_last.left_rpm-g_lap_last.left_target))<6.0);
        CHECK(fabs((double)(g_lap_last.right_rpm-g_lap_last.right_target))<6.0);
    }
    /* 拒绝非法下限，并在每次人工启动锁定，运行中改Watch不影响当前控制。 */
    for(i=0u;i<3u;++i) {
        init(0,0); calibrated(); g_lap_config.min_feedforward=invalid_values[i]; start();
        CHECK(g_lap.reason==LAP_CONFIG && g_lap.left_pwm==0 && g_lap.right_pwm==0);
    }
    running(); g_lap_config.min_feedforward=(float)NAN; ticks(500,0);
    CHECK(g_lap.state==LAP_RUNNING && g_lap.active.min_feedforward==200.0f);
    /* 前馈下限不能变成实际输出下限：反馈高于目标时PI仍允许给0。 */
    init(0,0); calibrated(); mode=1; start(); ticks(160,0);
    g_speed_match.left_rpm=300.0f; ticks(20,0);
    CHECK(g_lap.state==LAP_RUNNING && g_lap.left_target==40.0f && g_lap.left_pwm==0u);
}
/* 排障记录必须包含导致保护的原始负采样、保持既有保护立即撤驱动，
 * 并且在后续待机收包／采样中不被覆盖；模型负向反馈不是实物回退证据。
 */
static void diagnostic_cases(void) {
    lap_diag_view_t saved;
    lap_diag_sample_t last;
    uint32_t count, slot;
    CHECK(sizeof(lap_diag_sample_t)==60u && sizeof(lap_diag_view_t)==1952u);
    running(); ticks(1000,0);
    count=g_lap_diag.total_samples;
    CHECK(count>LAP_DIAG_SAMPLES && !g_lap_diag.frozen);
    slot=(count-1u)%LAP_DIAG_SAMPLES;
    CHECK(g_lap_diag.samples[slot].at_ms==sampled);
    CHECK(g_lap_diag.samples[slot].dt_ms==20u);
    mode=3; ticks(20,0);
    CHECK(g_lap.reason==LAP_REVERSE && g_lap_diag.frozen==1u);
    CHECK(g_lap_diag.stop_reason==(uint32_t)LAP_REVERSE);
    last=g_lap_diag.samples[(g_lap_diag.total_samples-1u)%LAP_DIAG_SAMPLES];
    CHECK(last.at_ms==g_lap_diag.stop_at_ms);
    CHECK(last.path_sequence==(uint8_t)((last.received-1u)%256u));
    CHECK(last.left_raw_rpm < -5.0f || last.right_raw_rpm < -5.0f);
    CHECK((last.left_counts_per_s*g_lap_diag.left_sign)<0 ||
          (last.right_counts_per_s*g_lap_diag.right_sign)<0);
    CHECK(g_lap.left_pwm==0u && g_lap.right_pwm==0u);
    saved=g_lap_diag; ticks(2000,0);
    CHECK(memcmp(&saved,(const void *)&g_lap_diag,sizeof(saved))==0);
    init(0,1); calibrated(); start(); ticks(3001,0);
    CHECK(g_lap_diag.frozen && g_lap_diag.stop_reason==(uint32_t)LAP_LIMIT);
    CHECK(g_lap_diag.left_channel==g_speed_match.left_channel &&
          g_lap_diag.right_channel==g_speed_match.right_channel);
    CHECK(g_lap_diag.left_sign==g_speed_match.left_sign &&
          g_lap_diag.right_sign==g_speed_match.right_sign);
    last=g_lap_diag.samples[(g_lap_diag.total_samples-1u)%LAP_DIAG_SAMPLES];
    CHECK((uint32_t)(g_lap_diag.stop_at_ms-last.at_ms)<20u);
    start();
    CHECK(g_lap.state==LAP_RUNNING && !g_lap_diag.frozen && g_lap_diag.total_samples<2u);
    init(0,0); CHECK(g_lap_diag.total_samples==0u && !g_lap_diag.frozen);
}

int main(void) {
    parser_cases(); fault_cases(); differential_case(0,0); differential_case(1,UINT32_MAX-8000u);
    startup_cases();
    low_speed_cases();
    diagnostic_cases();
    running(); ticks(3000,0); CHECK(g_lap.state!=LAP_RUNNING && g_lap.left_pwm==0);
    printf("LowSpeedLap: %u scenario assertions PASS; real PI/encoder/link/calibration; model only\n",checks);
    return 0;
}
