#include "board.h"
#include "car.h"
car_t g_car;
protocol_parser_t g_parser;
volatile uint32_t g_control_ticks;
int main(void) {
    uint32_t now, last_tick=0;
    uint8_t byte;
    protocol_frame_t frame;
    car_init(&g_car); protocol_parser_init(&g_parser); board_init();
    for (;;) {
        now=board_millis();
        if (board_uart_fault()) { protocol_parser_init(&g_parser); car_transport_fault(&g_car); }
        while (board_uart_read(&byte)) {
            if (protocol_push(&g_parser, byte, &frame)) car_receive(&g_car, &frame, board_millis());
        }
        now=board_millis();
        if ((uint32_t)(now-last_tick) >= 5u) {
            last_tick=now; car_tick(&g_car, now); ++g_control_ticks;
            board_apply_requests(g_car.left_request, g_car.right_request);
        }
    }
}
