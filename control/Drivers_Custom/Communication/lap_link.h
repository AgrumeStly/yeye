/** @file lap_link.h
 * @brief 按目标版本滑窗解析，首弯v5和语音首弯v7互斥，不改变v1。
 */
#ifndef YEYE_LAP_LINK_H
#define YEYE_LAP_LINK_H
#include <stdint.h>
typedef struct { uint8_t bytes[20], count; uint32_t accepted, rejected; } lap_parser_t;
void lap_link_init(lap_parser_t *parser);
/** @return 1=bytes内完整CRC／字段合法且版本匹配本目标的消息；随后交应用监督。 */
int lap_link_push(lap_parser_t *parser, uint8_t byte);
#endif
