#include <zephyr/shell/shell.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>
#include <stdlib.h>
#include "tb_pinmap.h"

static int cmd_gpio_set(const struct shell *sh, size_t argc, char **argv)
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

static int cmd_gpio_get(const struct shell *sh, size_t argc, char **argv)
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

SHELL_STATIC_SUBCMD_SET_CREATE(sub_gpio,
    SHELL_CMD_ARG(set, NULL, "set <pin> <0|1>", cmd_gpio_set, 3, 0),
    SHELL_CMD_ARG(get, NULL, "get <pin>",       cmd_gpio_get, 2, 0),
    SHELL_SUBCMD_SET_END
);

SHELL_STATIC_SUBCMD_SET_CREATE(sub_tb,
    SHELL_CMD(gpio, &sub_gpio, "GPIO commands", NULL),
    SHELL_SUBCMD_SET_END
);

SHELL_CMD_REGISTER(tb, &sub_tb, "Testbench root command", NULL);
