/** @file oled_i2c.h
 * @brief PB8/SCL、PB9/SDA的开漏软件I2C与SSD1306候选驱动。
 * 仅供无动力点亮诊断，不在中断调用；每页传输之间由应用喂看门狗。
 */
#ifndef YEYE_OLED_I2C_H
#define YEYE_OLED_I2C_H
#include <stdint.h>
enum { OLED_BUS_OK=0, OLED_BUS_NACK=1, OLED_BUS_SCL=2,
       OLED_BUS_SDA=3, OLED_BUS_CLOCK=4, OLED_BUS_ARGUMENT=5 };
typedef struct {
    uint32_t error;       /* 最近一次操作错误码；探测未接地址的NACK属于预期。 */
    uint32_t ack_bytes;   /* 实际采到低电平ACK的累计字节数，不证明芯片型号。 */
    uint32_t nack_bytes;  /* 含地址探测的NACK累计数。 */
    uint32_t recoveries;  /* 上电发现SDA被拉低时，尝试九脉冲恢复的次数。 */
    uint32_t idle_pins;   /* 初始化后PB8/PB9输入电平掩码，正常为0x300。 */
} oled_bus_status_t;
extern volatile oled_bus_status_t g_oled_bus;
/** @return 1=16MHz时钟和空闲总线就绪，0=限时失败；只配置PB8/PB9。 */
int oled_i2c_init(void);
/** @param address 7位地址，仅接受0x3C或0x3D；只发地址，不写命令。 */
int oled_i2c_probe(uint8_t address);
/** @brief 发送SSD1306 128x64内部电荷泵初始化；成功返回1，不能鉴定芯片。 */
int oled_ssd1306_init(uint8_t address);
/** @brief 以页寻址写128字节；page范围0..7，data必须指向完整128字节。 */
int oled_i2c_page(uint8_t address, uint8_t page, const uint8_t *data);
#endif
