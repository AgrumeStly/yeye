#include "car.h"
#include <string.h>
car_t g_car;
protocol_parser_t g_parser;
volatile uint32_t g_demo_checks, g_demo_failures, g_demo_complete;
/* LogicDemo deliberately avoids RCC, GPIO, UART and SysTick registers. */
void SystemInit(void) { }
static void check(int condition) { ++g_demo_checks; if (!condition) ++g_demo_failures; }
static void inject(protocol_frame_t *frame, uint32_t now, int corrupt) {
    uint8_t bytes[PROTOCOL_FRAME_SIZE], i;
    protocol_frame_t decoded;
    check(protocol_encode(frame, bytes));
    if (corrupt) bytes[8]^=1u;
    for (i=0; i<PROTOCOL_FRAME_SIZE; ++i)
        if (protocol_push(&g_parser, bytes[i], &decoded)) car_receive(&g_car, &decoded, now);
}
void demo_done(void) { g_demo_complete=1u; }
int main(void) {
    protocol_frame_t path, cmd;
    car_init(&g_car); protocol_parser_init(&g_parser);
    memset(&path,0,sizeof(path)); memset(&cmd,0,sizeof(cmd));
    path.type=PROTOCOL_PATH; path.sequence=1; path.flags=PATH_VALID; path.confidence=80; path.processing_ms=20;
    cmd.type=PROTOCOL_COMMAND; cmd.sequence=1; cmd.command=CMD_START;
    inject(&cmd,0,0); check(g_car.state==CAR_IDLE);
    inject(&path,10,0); cmd.sequence=2; inject(&cmd,11,0); car_tick(&g_car,11);
    check(g_car.state==CAR_RUNNING && g_car.left_request==120);
    inject(&path,150,0); car_tick(&g_car,210);
    check(g_car.state==CAR_FAULT && g_car.left_request==0);
    path.sequence=2; inject(&path,211,0); check(g_car.state==CAR_FAULT);
    cmd.sequence=3; inject(&cmd,212,0); car_tick(&g_car,212); check(g_car.state==CAR_RUNNING);
    path.sequence=3; inject(&path,250,1); car_tick(&g_car,411);
    check(g_car.state==CAR_FAULT && g_car.reason==STOP_LINK);
    cmd.sequence=4; cmd.command=CMD_STOP; inject(&cmd,412,0); check(g_car.state==CAR_STOPPED);
    demo_done();
    for (;;) { }
}
