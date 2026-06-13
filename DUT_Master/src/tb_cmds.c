#include <zephyr/shell/shell.h>

/* Declared extern in each peripheral's .c file */
extern int cmd_gpio_get(const struct shell *sh, size_t argc, char **argv);
extern int cmd_gpio_set(const struct shell *sh, size_t argc, char **argv);
extern int pin_to_channel(const char *pin);
extern int cmd_adc_read(const struct shell *sh, size_t argc, char **argv);


SHELL_STATIC_SUBCMD_SET_CREATE(sub_gpio,
    SHELL_CMD_ARG(set, NULL, "set <pin> <0|1>", cmd_gpio_set, 3, 0),
    SHELL_CMD_ARG(get, NULL, "get <pin>",       cmd_gpio_get, 2, 0),
    SHELL_SUBCMD_SET_END
);
SHELL_STATIC_SUBCMD_SET_CREATE(sub_adc,
    SHELL_CMD_ARG(read, NULL, "read <pin>", cmd_adc_read, 2, 0),
    SHELL_SUBCMD_SET_END
);

SHELL_STATIC_SUBCMD_SET_CREATE(sub_tb,
    SHELL_CMD(gpio,  &sub_gpio,  "GPIO control (set/get)",         NULL),
    SHELL_CMD(adc,   &sub_adc,   "ADC read (read)",                NULL),
    SHELL_SUBCMD_SET_END
);

SHELL_CMD_REGISTER(tb, &sub_tb, "Testbench commands", NULL);
