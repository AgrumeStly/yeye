#include "car.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CHECK(expr) do { ++checks; if (!(expr)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#expr); exit(1); } } while (0)
static protocol_frame_t path(uint8_t seq) {
    protocol_frame_t f;
    memset(&f,0,sizeof(f)); f.type=PROTOCOL_PATH; f.sequence=seq;
    f.flags=PATH_VALID; f.confidence=80; f.processing_ms=20;
    return f;
}
static protocol_frame_t command(uint8_t seq, uint8_t cmd) {
    protocol_frame_t f;
    memset(&f,0,sizeof(f)); f.type=PROTOCOL_COMMAND; f.sequence=seq; f.command=cmd;
    return f;
}
static unsigned push(protocol_parser_t *p, const uint8_t *bytes, unsigned n, protocol_frame_t *f) {
    unsigned i, count=0;
    for(i=0;i<n;++i) count+=(unsigned)protocol_push(p,bytes[i],f);
    return count;
}
static void parser_tests(void) {
    protocol_parser_t p;
    protocol_frame_t f=path(42),out;
    uint8_t bytes[20],bad[20],noise[3]={0xa5,0x00,0x5a};
    const uint8_t golden[20]={0xa5,0x5a,1,1,12,1,1,80,0,0,0,0,0,0,20,0,0,0,0x92,1};
    unsigned i;
    CHECK(protocol_crc16((const uint8_t *)"123456789",9)==0x29b1u);
    out=path(1); CHECK(protocol_encode(&out,bytes)); CHECK(memcmp(bytes,golden,20)==0);
    f.error=-1000; f.heading=-9000; f.bend=1000;
    CHECK(protocol_encode(&f,bytes));
    protocol_parser_init(&p);
    CHECK(push(&p,noise,3,&out)==0);
    CHECK(push(&p,bytes,7,&out)==0);
    CHECK(push(&p,bytes+7,13,&out)==1);
    CHECK(out.error==-1000 && out.heading==-9000 && out.bend==1000 && out.sequence==42);
    CHECK(push(&p,bytes,20,&out)==1);
    memcpy(bad,bytes,20); bad[8]^=1;
    CHECK(push(&p,bad,20,&out)==0);
    CHECK(push(&p,bytes,20,&out)==1);
    protocol_parser_init(&p);
    CHECK(push(&p,bytes,9,&out)==0); /* truncated frame followed by a full one */
    CHECK(push(&p,bytes,20,&out)==1);
    for(i=2;i<=4;++i) {
        memcpy(bad,bytes,20); bad[i]=0xff;
        { uint16_t crc=protocol_crc16(bad,18); bad[18]=(uint8_t)crc; bad[19]=(uint8_t)(crc>>8); }
        protocol_parser_init(&p);
        CHECK(push(&p,bad,20,&out)==0);
        CHECK(push(&p,bytes,20,&out)==1);
    }
    f.confidence=101; CHECK(!protocol_encode(&f,bytes));
    f.confidence=80; f.error=1001; CHECK(!protocol_encode(&f,bytes));
    f=command(1,CMD_STOP); CHECK(protocol_encode(&f,bytes));
    f.flags=PATH_VALID; CHECK(!protocol_encode(&f,bytes));
    puts("PASS parser: CRC, split/concatenated frames, noise, corruption, truncation, format/range checks");
}
static void state_tests(void) {
    car_t c;
    protocol_frame_t p=path(1),cmd=command(1,CMD_START);
    car_init(&c); car_tick(&c,0);
    CHECK(c.state==CAR_IDLE && c.left_request==0);
    car_receive(&c,&cmd,0); CHECK(c.state==CAR_IDLE && c.starts_rejected==1);
    car_receive(&c,&p,10); cmd.sequence=2; car_receive(&c,&cmd,11); car_tick(&c,11);
    CHECK(c.state==CAR_RUNNING && c.left_request==120 && c.right_request==120);
    p.error=600; p.sequence=2; car_receive(&c,&p,20); car_tick(&c,20);
    CHECK(c.left_request==150 && c.right_request==90);
    car_receive(&c,&p,190); CHECK(c.duplicates==1 && c.path_time==20);
    car_tick(&c,219); CHECK(c.state==CAR_RUNNING);
    car_tick(&c,220); CHECK(c.state==CAR_FAULT && c.left_request==0 && c.reason==STOP_LINK);
    p.sequence=3; car_receive(&c,&p,221); car_tick(&c,221);
    CHECK(c.state==CAR_FAULT); /* valid data never restarts automatically */
    cmd.sequence=3; car_receive(&c,&cmd,222); car_tick(&c,222); CHECK(c.state==CAR_RUNNING);
    cmd.sequence=5; cmd.command=CMD_STOP; car_receive(&c,&cmd,223); CHECK(c.state==CAR_STOPPED && c.left_request==0);
    cmd.sequence=4; cmd.command=CMD_START; car_receive(&c,&cmd,224); CHECK(c.state==CAR_STOPPED);
    cmd.sequence=6; car_receive(&c,&cmd,225); car_tick(&c,225); CHECK(c.state==CAR_RUNNING);
    cmd.sequence=1; cmd.command=CMD_STOP; car_receive(&c,&cmd,226); CHECK(c.state==CAR_STOPPED);
    cmd.sequence=7; cmd.command=CMD_START; car_receive(&c,&cmd,227);
    p.sequence=4; p.flags=0; car_receive(&c,&p,228); CHECK(c.state==CAR_FAULT && c.reason==STOP_PATH);
    p=path(5); p.confidence=39; car_receive(&c,&p,229);
    cmd.sequence=8; car_receive(&c,&cmd,230); CHECK(c.state==CAR_FAULT);
    p=path(6); p.processing_ms=101; car_receive(&c,&p,231);
    cmd.sequence=9; car_receive(&c,&cmd,232); CHECK(c.state==CAR_FAULT);
    p=path(7); car_receive(&c,&p,233); cmd.sequence=10; car_receive(&c,&cmd,234);
    car_transport_fault(&c); CHECK(c.state==CAR_FAULT && c.reason==STOP_TRANSPORT && c.have_path==0);
    car_receive(&c,&cmd,235); CHECK(c.state==CAR_FAULT);
    car_init(&c); p=path(255); car_receive(&c,&p,0xfffffff0u);
    cmd=command(255,CMD_START); car_receive(&c,&cmd,0xfffffff1u); car_tick(&c,10);
    CHECK(c.state==CAR_RUNNING); p.sequence=0; car_receive(&c,&p,11); CHECK(c.path.sequence==0);
    p.sequence=255; car_receive(&c,&p,12); CHECK(c.path.sequence==0);
    car_tick(&c,211); CHECK(c.state==CAR_FAULT);
    p.sequence=20; car_receive(&c,&p,212); CHECK(c.path.sequence==20 && c.state==CAR_FAULT);
    car_init(&c); p=path(1); car_receive(&c,&p,0); cmd=command(1,CMD_START); car_receive(&c,&cmd,1);
    p.sequence=2; car_receive(&c,&p,200); car_tick(&c,200);
    CHECK(c.state==CAR_FAULT && c.path.sequence==2 && c.left_request==0);
    puts("PASS state: explicit start/stop, demands, duplicate/old frames, timeout, no auto-restart, invalid path, delayed processing, transport error, counter wrap/reboot");
}
static void wire_state_test(void) {
    protocol_parser_t parser;
    car_t car;
    protocol_frame_t f=path(1),out;
    uint8_t bytes[20];
    protocol_parser_init(&parser); car_init(&car);
    CHECK(protocol_encode(&f,bytes)); CHECK(push(&parser,bytes,20,&out)==1); car_receive(&car,&out,0);
    f=command(1,CMD_START); CHECK(protocol_encode(&f,bytes));
    CHECK(push(&parser,bytes,20,&out)==1); car_receive(&car,&out,1); car_tick(&car,1); CHECK(car.state==CAR_RUNNING);
    f=path(2); CHECK(protocol_encode(&f,bytes)); bytes[9]^=0x80;
    CHECK(push(&parser,bytes,20,&out)==0); car_tick(&car,200); CHECK(car.state==CAR_FAULT && car.left_request==0);
    puts("PASS end-to-end: wire bytes -> parser -> state; corrupted updates cannot keep vehicle running");
}
int main(void) { parser_tests(); state_tests(); wire_state_test(); printf("PASS all %u checks\n",checks); return 0; }
