/* 给Python逐字节喂入真实C滑窗解析器；stdin为原始字节，stdout为字段行。 */
#include "lap_link.h"
#include <stdio.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
int main(void) {
    lap_parser_t parser; int byte;
#ifdef _WIN32
    (void)_setmode(0, _O_BINARY); /* Windows标准输入描述符固定为0，避免非标准fileno声明差异。 */
#endif
    lap_link_init(&parser);
    while ((byte=getchar())!=EOF) if (lap_link_push(&parser,(uint8_t)byte))
        printf("%u %u %u %u %u\n", (unsigned)parser.bytes[3],(unsigned)parser.bytes[5],
               (unsigned)parser.bytes[6],(unsigned)parser.bytes[8],(unsigned)parser.bytes[9]);
    return 0;
}
