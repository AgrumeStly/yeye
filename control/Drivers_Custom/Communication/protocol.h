#ifndef YEYE_PROTOCOL_H
#define YEYE_PROTOCOL_H
#include <stdint.h>
#define PROTOCOL_FRAME_SIZE 20u
#define PROTOCOL_PATH 1u
#define PROTOCOL_COMMAND 2u
#define PATH_VALID 1u
#define PATH_FINISH 2u
#define CMD_START 1u
#define CMD_STOP 2u
#define CMD_STATUS 3u
typedef struct {
    uint8_t type, sequence, flags, confidence;
    int16_t error, heading;
    uint16_t bend, processing_ms;
    uint8_t command;
} protocol_frame_t;
typedef struct {
    uint8_t bytes[PROTOCOL_FRAME_SIZE];
    uint8_t count;
    uint32_t accepted, rejected;
} protocol_parser_t;
uint16_t protocol_crc16(const uint8_t *data, uint16_t size);
int protocol_encode(const protocol_frame_t *frame, uint8_t *bytes);
void protocol_parser_init(protocol_parser_t *parser);
/* One byte per call; returns 1 only for a fully validated frame. */
int protocol_push(protocol_parser_t *parser, uint8_t byte, protocol_frame_t *frame);
#endif
