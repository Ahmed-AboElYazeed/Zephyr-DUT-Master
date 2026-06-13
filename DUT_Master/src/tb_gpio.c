#include <zephyr/shell/shell.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>
#include <stdlib.h>
#include "tb_pinmap.h"

int cmd_gpio_set(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 3) {
        shell_error(sh, "ERROR: usage: tb gpio set <pin> <0|1>");
        return -EINVAL;
    }
    const tb_pin_t *p = tb_pin_lookup(argv[1]);
    if (!p) {
        shell_error(sh, "ERROR: unknown pin %s", argv[1]);
        return -ENODEV;
    }
    int val = atoi(argv[2]);
    gpio_pin_configure(p->port, p->pin, GPIO_OUTPUT);
    gpio_pin_set(p->port, p->pin, val);
    shell_print(sh, "OK");
    return 0;
}

int cmd_gpio_get(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 2) {
        shell_error(sh, "ERROR: usage: tb gpio get <pin>");
        return -EINVAL;
    }
    const tb_pin_t *p = tb_pin_lookup(argv[1]);
    if (!p) {
        shell_error(sh, "ERROR: unknown pin %s", argv[1]);
        return -ENODEV;
    }
    gpio_pin_configure(p->port, p->pin, GPIO_INPUT);
    int val = gpio_pin_get(p->port, p->pin);
    shell_print(sh, "%d", val);
    return 0;
}