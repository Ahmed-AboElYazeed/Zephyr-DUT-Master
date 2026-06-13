#include <zephyr/shell/shell.h>
#include <zephyr/drivers/pwm.h>
#include <stdlib.h>

#define PWM_OUT_DEV  DEVICE_DT_GET(DT_NODELABEL(pwm1))
#define PWM_OUT_CH   1
#define PWM_IN_DEV   DEVICE_DT_GET(DT_NODELABEL(pwm2))
#define PWM_IN_CH    2

int cmd_pwm_set(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 4) {
        shell_error(sh, "ERROR: usage: tb pwm set <pin> <freq_hz> <duty_pct>");
        return -EINVAL;
    }
    uint32_t freq_hz  = atoi(argv[2]);
    uint32_t duty_pct = atoi(argv[3]);

    if (freq_hz == 0 || duty_pct > 100) {
        shell_error(sh, "ERROR: invalid freq or duty");
        return -EINVAL;
    }

    uint32_t period_ns = 1000000000U / freq_hz;
    uint32_t pulse_ns  = period_ns * duty_pct / 100;

    int ret = pwm_set(PWM_OUT_DEV, PWM_OUT_CH,
                      PWM_NSEC(period_ns), PWM_NSEC(pulse_ns), 0);
    if (ret < 0) {
        shell_error(sh, "ERROR: pwm_set failed %d", ret);
        return ret;
    }
    shell_print(sh, "OK");
    return 0;
}

int cmd_pwm_capture(const struct shell *sh, size_t argc, char **argv)
{
    uint64_t period_ns, pulse_ns;
    int ret = pwm_capture_nsec(PWM_IN_DEV, PWM_IN_CH,
                               PWM_CAPTURE_TYPE_BOTH,
                               &period_ns, &pulse_ns,
                               K_MSEC(500));
    if (ret < 0) {
        shell_error(sh, "ERROR: pwm_capture failed %d", ret);
        return ret;
    }
    uint32_t freq_hz  = 1000000000U / period_ns;
    uint32_t duty_pct = pulse_ns * 100 / period_ns;
    shell_print(sh, "%u Hz %u pct", freq_hz, duty_pct);
    return 0;
}

