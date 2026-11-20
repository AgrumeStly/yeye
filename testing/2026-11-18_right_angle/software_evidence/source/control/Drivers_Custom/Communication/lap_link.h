/** @file lap_link.h
 * @brief 滑窗解析：普通目标v2、直道目标v3、RIGHT_ANGLE_TARGET首弯v4互斥，不改变v1。
 */
#ifndef YEYE_LAP_LINK_H
#define YEYE_LAP_LINK_H
#include <stdint.h>
typedef struct { uint8_t bytes[20], count; uint32_t accepted, rejected; } lap_parser_t;
void lap_link_init(lap_parser_t *parser);
/** @return 1=bytes内完整CRC／字段合法且版本匹配本目标的消息；随后交应用监督。 */
int lap_link_push(lap_parser_t *parser, uint8_t byte);
#endif
