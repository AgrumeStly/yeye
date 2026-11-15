/** @file oled_pattern.h @brief 纯图样生成，不访问硬件；buffer须提供1024字节。 */
#ifndef YEYE_OLED_PATTERN_H
#define YEYE_OLED_PATTERN_H
#include <stdint.h>
/** @param phase 0全亮、1全黑、2/3互补棋盘格、4文字计数页。
 * @param seconds 运行秒数，显示末四位；address为实际应答的7位地址。
 * @return 无；空buffer不写入。此函数不鉴定屏幕显示效果。
 */
void oled_pattern_build(uint8_t *buffer,uint32_t phase,uint32_t seconds,uint8_t address);
#endif
