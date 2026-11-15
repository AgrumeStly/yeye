/** @file oled_i2c.c
 * @brief SPL开漏GPIO实现保守速率I2C；逐字节采ACK，SCL/SDA异常有界退出。
 * 使用CMSIS DWT计时，不占用TIM3/TIM4编码器。高电平只释放线路，绝不推挽顶高。
 * 主板3.3V供电，模块需有合适外部上拉；内部弱上拉仅辅助空闲态。
 * 此驱动会阻塞一页的传输时间，不能直接放进运动控制/串口ISR。
 */
#include "oled_i2c.h"
#include "stm32f4xx.h"
#define SCL GPIO_Pin_8
#define SDA GPIO_Pin_9
#define BUS_PINS (SCL | SDA)
#define HALF_CYCLES 128u /* 16MHz下8us，实际频率还受SPL开销影响，低于62.5kHz。 */
#define WAIT_CYCLES 3200u /* SCL拉伸/线路释放最多200us，并有4096次后备上限。 */
volatile oled_bus_status_t g_oled_bus;

/** @brief 半周期延时；DWT停止时同样有限退出并锁存时钟错误，不无限忙等。 */
static void half_delay(void) {
    uint32_t start=DWT->CYCCNT, polls=0u;
    while ((uint32_t)(DWT->CYCCNT-start)<HALF_CYCLES) {
        if (++polls>=4096u) { g_oled_bus.error=OLED_BUS_CLOCK; break; }
        __NOP();
    }
}
/** @brief 释放指定开漏线并等实际输入变高；pin只允许SCL/SDA，返回1或限时失败0。 */
static int release_high(uint16_t pin) {
    uint32_t start=DWT->CYCCNT, polls=0u;
    GPIO_SetBits(GPIOB,pin);
    while (GPIO_ReadInputDataBit(GPIOB,pin)==Bit_RESET) {
        if ((uint32_t)(DWT->CYCCNT-start)>=WAIT_CYCLES || ++polls>=4096u) {
            g_oled_bus.error=pin==SCL ? OLED_BUS_SCL : OLED_BUS_SDA;
            return 0;
        }
    }
    half_delay();
    return g_oled_bus.error==OLED_BUS_OK;
}
/** @brief STOP：SCL高时释放SDA；失败仍释放两线，保留最初故障原因。 */
static int stop_bus(void) {
    uint32_t original=g_oled_bus.error;
    int ok;
    GPIO_ResetBits(GPIOB,SCL | SDA); half_delay();
    ok=release_high(SCL);
    if (ok) ok=release_high(SDA);
    GPIO_SetBits(GPIOB,BUS_PINS);
    if (original!=OLED_BUS_OK) g_oled_bus.error=original;
    return ok && g_oled_bus.error==OLED_BUS_OK;
}
/** @brief START要求两线实际空闲；SCL高时拉低SDA，再拉低SCL。 */
static int start_bus(void) {
    if (!release_high(SDA) || !release_high(SCL)) return 0;
    GPIO_ResetBits(GPIOB,SDA); half_delay();
    GPIO_ResetBits(GPIOB,SCL);
    return g_oled_bus.error==OLED_BUS_OK;
}
/** @brief MSB先发八位，释放SDA采第九拍ACK；NACK或SCL异常立即返回0。 */
static int write_byte(uint8_t value) {
    uint32_t bit;
    for (bit=0u;bit<8u;++bit) {
        if ((value & 0x80u)!=0u) GPIO_SetBits(GPIOB,SDA);
        else GPIO_ResetBits(GPIOB,SDA);
        half_delay();
        if (!release_high(SCL)) return 0;
        GPIO_ResetBits(GPIOB,SCL);
        value=(uint8_t)(value<<1);
    }
    GPIO_SetBits(GPIOB,SDA); half_delay();
    if (!release_high(SCL)) return 0;
    if (GPIO_ReadInputDataBit(GPIOB,SDA)!=Bit_RESET) {
        ++g_oled_bus.nack_bytes; g_oled_bus.error=OLED_BUS_NACK;
        GPIO_ResetBits(GPIOB,SCL); return 0;
    }
    ++g_oled_bus.ack_bytes;
    GPIO_ResetBits(GPIOB,SCL); half_delay();
    return g_oled_bus.error==OLED_BUS_OK;
}
/** @brief 完整事务统一收尾；control=0命令，0x40数据，长度最多128字节。
 * address为7位地址，写线上左移1位，避免把0x78误当7位地址。
 * 即使中途失败也尝试STOP，不发送后续字节；空指针/越界长度不操作总线。
 */
static int transfer(uint8_t address,uint8_t control,const uint8_t *data,uint32_t count) {
    uint32_t i; int ok;
    g_oled_bus.error=OLED_BUS_OK;
    if ((address!=0x3cu && address!=0x3du) || count>128u || (count!=0u && data==0)) {
        g_oled_bus.error=OLED_BUS_ARGUMENT; return 0;
    }
    ok=start_bus();
    if (ok) ok=write_byte((uint8_t)(address<<1));
    if (ok && count!=0u) ok=write_byte(control);
    for (i=0u;ok && i<count;++i) ok=write_byte(data[i]);
    if (!stop_bus()) ok=0;
    return ok;
}

int oled_i2c_init(void) {
    GPIO_InitTypeDef config;
    uint32_t i,first,polls=0u;
    g_oled_bus.error=OLED_BUS_OK;
    if (SystemCoreClock!=16000000u) { g_oled_bus.error=OLED_BUS_CLOCK; return 0; }
    /* DWT属于CMSIS内核支持，SPL负责下方RCC/GPIO，不手写外设寄存器。 */
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    first=DWT->CYCCNT;
    while (DWT->CYCCNT==first) {
        if (++polls>=4096u) { g_oled_bus.error=OLED_BUS_CLOCK; return 0; }
        __NOP();
    }
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB,ENABLE);
    GPIO_SetBits(GPIOB,BUS_PINS); /* 先释放锁存，再切输出，避免初始化产生低脉冲。 */
    GPIO_StructInit(&config);
    config.GPIO_Pin=BUS_PINS; config.GPIO_Mode=GPIO_Mode_OUT;
    config.GPIO_OType=GPIO_OType_OD; config.GPIO_PuPd=GPIO_PuPd_UP;
    config.GPIO_Speed=GPIO_Speed_2MHz; GPIO_Init(GPIOB,&config);
    if (!release_high(SCL)) return 0;
    if (GPIO_ReadInputDataBit(GPIOB,SDA)==Bit_RESET) {
        ++g_oled_bus.recoveries;
        for (i=0u;i<9u;++i) {
            GPIO_ResetBits(GPIOB,SCL); half_delay();
            if (!release_high(SCL)) return 0;
        }
        if (!stop_bus()) return 0;
    }
    if (!release_high(SDA)) return 0;
    g_oled_bus.idle_pins=GPIO_ReadInputData(GPIOB) & BUS_PINS;
    return 1;
}
int oled_i2c_probe(uint8_t address) { return transfer(address,0u,0,0u); }

int oled_ssd1306_init(uint8_t address) {
    /* 128x64、页寻址、内部电荷泵、中等对比度；暂不鉴定实际控制芯片。
     * 先保持AE关屏，清完第一帧后由应用写页函数开启显示，避免随机RAM闪屏。
     */
    static const uint8_t commands[]={0xae,0xd5,0x80,0xa8,0x3f,0xd3,0x00,0x40,
        0x8d,0x14,0x20,0x02,0xa1,0xc8,0xda,0x12,0x81,0x5f,0xd9,0xf1,
        0xdb,0x40,0x2e,0xa4,0xa6};
    return transfer(address,0u,commands,sizeof(commands));
}
int oled_i2c_page(uint8_t address,uint8_t page,const uint8_t *data) {
    uint8_t commands[3];
    static const uint8_t on=0xafu;
    if (page>7u || data==0) { g_oled_bus.error=OLED_BUS_ARGUMENT; return 0; }
    commands[0]=(uint8_t)(0xb0u+page); commands[1]=0x00u; commands[2]=0x10u;
    if (!transfer(address,0u,commands,3u) || !transfer(address,0x40u,data,128u)) return 0;
    /* 首帧最后一页写完才开屏；后续重复AF不改变RAM内容。 */
    return page!=7u || transfer(address,0u,&on,1u);
}
