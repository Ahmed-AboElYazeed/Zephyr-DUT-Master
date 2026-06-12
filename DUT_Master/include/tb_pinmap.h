/* tb_pinmap.h */
#include <zephyr/drivers/gpio.h>

typedef struct {
    const char *name;        /* "PA5", "PB3", etc. */
    const struct device *port;
    gpio_pin_t pin;
} tb_pin_t;

const tb_pin_t *tb_pin_lookup(const char *name);
