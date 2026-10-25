#include "protocol.h"
#include <string.h>
static uint16_t read_u16(const uint8_t *p) { return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8)); }
static int16_t read_i16(const uint8_t *p) {
    uint16_t value = read_u16(p);
    return (int16_t)(value < 32768u ? (int32_t)value : (int32_t)value - 65536);
}
static void write_u16(uint8_t *p, uint16_t value) { p[0] = (uint8_t)value; p[1] = (uint8_t)(value >> 8); }
uint16_t protocol_crc16(const uint8_t *data, uint16_t size) {
    uint16_t crc = 0xffffu, i;
    uint8_t bit;
    for (i = 0; i < size; ++i) {
        crc ^= (uint16_t)((uint16_t)data[i] << 8);
        for (bit = 0; bit < 8; ++bit)
            crc = (uint16_t)((crc & 0x8000u) ? ((uint32_t)crc << 1) ^ 0x1021u : (uint32_t)crc << 1);
    }
    return crc;
}
static int valid(const protocol_frame_t *f) {
    if (f->type == PROTOCOL_PATH)
        return (f->flags & (uint8_t)~3u) == 0u && f->confidence <= 100u &&
               f->error >= -1000 && f->error <= 1000 && f->heading >= -9000 && f->heading <= 9000 &&
               f->bend <= 1000u && f->processing_ms <= 1000u && f->command == 0u;
    if (f->type == PROTOCOL_COMMAND)
        return f->command >= CMD_START && f->command <= CMD_STATUS && f->flags == 0u &&
               f->confidence == 0u && f->error == 0 && f->heading == 0 && f->bend == 0u && f->processing_ms == 0u;
    return 0;
}
int protocol_encode(const protocol_frame_t *f, uint8_t *b) {
    if (!valid(f)) return 0;
    memset(b, 0, PROTOCOL_FRAME_SIZE);
    b[0] = 0xa5u; b[1] = 0x5au; b[2] = 1u; b[3] = f->type; b[4] = 12u; b[5] = f->sequence;
    b[6] = f->flags; b[7] = f->confidence;
    write_u16(b+8, (uint16_t)f->error); write_u16(b+10, (uint16_t)f->heading);
    write_u16(b+12, f->bend); write_u16(b+14, f->processing_ms); b[16] = f->command;
    write_u16(b+18, protocol_crc16(b, 18));
    return 1;
}
static int decode(const uint8_t *b, protocol_frame_t *f) {
    if (b[0] != 0xa5u || b[1] != 0x5au || b[2] != 1u || b[4] != 12u || b[17] != 0u ||
        read_u16(b+18) != protocol_crc16(b, 18)) return 0;
    f->type=b[3]; f->sequence=b[5]; f->flags=b[6]; f->confidence=b[7];
    f->error=read_i16(b+8); f->heading=read_i16(b+10); f->bend=read_u16(b+12);
    f->processing_ms=read_u16(b+14); f->command=b[16];
    return valid(f);
}
void protocol_parser_init(protocol_parser_t *p) { memset(p, 0, sizeof(*p)); }
int protocol_push(protocol_parser_t *p, uint8_t byte, protocol_frame_t *f) {
    p->bytes[p->count++] = byte;
    /* A sliding window also recovers when a corrupt frame contains the next header. */
    if (p->count < PROTOCOL_FRAME_SIZE) return 0;
    if (decode(p->bytes, f)) { p->count=0; ++p->accepted; return 1; }
    if (p->bytes[0] == 0xa5u && p->bytes[1] == 0x5au) ++p->rejected;
    memmove(p->bytes, p->bytes+1, PROTOCOL_FRAME_SIZE-1u);
    p->count = PROTOCOL_FRAME_SIZE-1u;
    return 0;
}
