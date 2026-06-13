#include <zephyr/shell/shell.h>
#include <zephyr/drivers/adc.h>

#define ADC_DEV  DEVICE_DT_GET(DT_NODELABEL(adc1))
#define ADC_VREF 3300   /* mV */
#define ADC_RES  12     /* bits */

/* Map "PA0" → channel 0, "PA1" → channel 1, etc. */
int pin_to_channel(const char *pin)
{
    if (strcmp(pin, "PA0") == 0) return 0;
    if (strcmp(pin, "PA1") == 0) return 1;
    if (strcmp(pin, "PA2") == 0) return 2;
    if (strcmp(pin, "PA3") == 0) return 3;
    return -1;
}

int cmd_adc_read(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 2) {
        shell_error(sh, "ERROR: usage: tb adc read <pin>");
        return -EINVAL;
    }

    int ch = pin_to_channel(argv[1]);
    if (ch < 0) {
        shell_error(sh, "ERROR: unknown ADC pin %s", argv[1]);
        return -ENODEV;
    }

    const struct device *adc = ADC_DEV;
    int16_t buf;
    struct adc_sequence seq = {
        .channels    = BIT(ch),
        .buffer      = &buf,
        .buffer_size = sizeof(buf),
        .resolution  = ADC_RES,
    };

    int ret = adc_read(adc, &seq);
    if (ret < 0) {
        shell_error(sh, "ERROR: adc_read failed %d", ret);
        return ret;
    }

    int32_t mv = (int32_t)buf * ADC_VREF / ((1 << ADC_RES) - 1);
    shell_print(sh, "%d mV", mv);
    return 0;
}
