/** @file lap_link.c
 * @brief v2与v1物理帧长相同，但version必须为2；误接v1不会产生运动许可。
 * CRC继续复用原生产实现。当前只允许当前几何／短历史两种来源，无终点自动停车。
 */
#include "lap_link.h"
#include "protocol.h"
#include <string.h>
static uint16_t u16(const uint8_t *p) { return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8)); }
static int valid(const uint8_t *b) {
    uint16_t error = u16(b + 8);
    int32_t steering = error < 32768u ? (int32_t)error : (int32_t)error - 65536;
    if (b[0] != 0xa5u || b[1] != 0x5au || b[2] != 2u || b[4] != 12u || b[17] != 0u ||
        u16(b + 18) != protocol_crc16(b, 18u)) return 0;
    if (b[3] == 1u) return (b[6] & (uint8_t)~13u) == 0u && (b[6] & 12u) != 12u && b[7] <= 100u &&
        steering >= -1000 && steering <= 1000 && u16(b + 10) <= 1000u &&
        u16(b + 12) <= 1000u && u16(b + 14) <= 1000u && b[16] == 0u;
    if (b[3] == 2u) return b[6] == 0u && b[7] == 0u && u16(b+8) == 0u && u16(b+10) == 0u &&
        u16(b+12) == 0u && u16(b+14) == 0u && b[16] >= 1u && b[16] <= 3u;
    return 0;
}
void lap_link_init(lap_parser_t *p) { memset(p, 0, sizeof(*p)); }
int lap_link_push(lap_parser_t *p, uint8_t byte) {
    p->bytes[p->count++] = byte;
    if (p->count < 20u) return 0;
    if (valid(p->bytes)) { p->count = 0u; ++p->accepted; return 1; }
    if (p->bytes[0] == 0xa5u && p->bytes[1] == 0x5au) ++p->rejected;
    memmove(p->bytes, p->bytes + 1, 19u); p->count = 19u; return 0;
}
