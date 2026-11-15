/** @file lap_link.h
 * @brief 试跑v2局部转向消息独立滑窗解析，不改变原v1固定y120协议。
 */
#ifndef YEYE_LAP_LINK_H
#define YEYE_LAP_LINK_H
#include <stdint.h>
typedef struct { uint8_t bytes[20], count; uint32_t accepted, rejected; } lap_parser_t;
void lap_link_init(lap_parser_t *parser);
/** @return 1=bytes内完整CRC／字段合法的v2消息；可随后传给lap_motion_receive。 */
int lap_link_push(lap_parser_t *parser, uint8_t byte);
#endif
