/* tb_pinmap.c */
#include "tb_pinmap.h"
#include <zephyr/device.h>

static const tb_pin_t pin_table[] = {
    { "PA5", DEVICE_DT_GET(DT_NODELABEL(gpioa)), 5 },
    { "PA6", DEVICE_DT_GET(DT_NODELABEL(gpioa)), 6 },
    { "PB3", DEVICE_DT_GET(DT_NODELABEL(gpiob)), 3 },
    { "PB4", DEVICE_DT_GET(DT_NODELABEL(gpiob)), 4 },
    /* extend as needed */
    { NULL, NULL, 0 }
};

const tb_pin_t *tb_pin_lookup(const char *name)
{
    for (int i = 0; pin_table[i].name != NULL; i++) {
        if (strcmp(pin_table[i].name, name) == 0) {
            return &pin_table[i];
        }
    }
    return NULL;
}
