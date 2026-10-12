#ifndef YEYE_STM32F4XX_CONF_H
#define YEYE_STM32F4XX_CONF_H
/* USE_STDPERIPH_DRIVER makes stm32f4xx.h include this configuration file. */
#include "stm32f4xx_rcc.h"
#include "stm32f4xx_gpio.h"
#include "stm32f4xx_usart.h"
#include "misc.h"

/* Keep vendor argument assertions off until an assert_failed handler is added. */
#ifdef USE_FULL_ASSERT
#include <stdint.h>
void assert_failed(uint8_t *file, uint32_t line);
#define assert_param(expr) ((expr) ? (void)0 : assert_failed((uint8_t *)__FILE__, __LINE__))
#else
#define assert_param(expr) ((void)0)
#endif
#endif
