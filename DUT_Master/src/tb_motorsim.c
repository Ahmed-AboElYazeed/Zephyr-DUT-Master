#include <zephyr/kernel.h>
#include <zephyr/shell/shell.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/pwm.h>
#include "dc_motor_math.h"

/* Scaling constants */
#define ADC_VREF_MV   3300
#define ADC_MAX       4095    /* 12-bit */
#define MAX_LOAD_N    10.0
#define MAX_SPEED_RPM 500.0

static struct k_timer sim_timer;
static bool sim_running;

/* ADC channel for DUT voltage command (PA0) and load command (PA1) */
#define ADC_DEV   DEVICE_DT_GET(DT_NODELABEL(adc1))
/* PWM channel used as feedback "DAC" output to DUT (PA8) */
#define PWM_FB_DEV DEVICE_DT_GET(DT_NODELABEL(pwm1))
#define PWM_FB_CH  0

static int16_t read_adc_mv(int channel)
{
    int16_t buf;
    struct adc_sequence seq = {
        .channels = BIT(channel),
        .buffer = &buf,
        .buffer_size = sizeof(buf),
        .resolution = 12,
    };
    adc_read(ADC_DEV, &seq);
    return (int32_t)buf * ADC_VREF_MV / ADC_MAX;
}

static void write_feedback_mv(int32_t mv)
{
    /* Output speed feedback as a PWM duty proportional to mv/3300 */
    uint32_t period_ns = 1000000;  /* 1 kHz */
    uint32_t pulse_ns = (uint32_t)((int64_t)period_ns * mv / ADC_VREF_MV);
    pwm_set(PWM_FB_DEV, PWM_FB_CH, PWM_NSEC(period_ns), PWM_NSEC(pulse_ns), 0);
}

static void sim_step(struct k_timer *timer)
{
    /* 1. Read DUT voltage command (PA0, channel 0) */
    int16_t volt_mv = read_adc_mv(0);
    dc_motor_math_U.voltage_in = (real_T)volt_mv / 1000.0;  /* mV -> V, 0-3.3V */

    /* 2. Read DUT load command (PA1, channel 1), scale 0-3.3V -> 0-10N */
    int16_t load_mv = read_adc_mv(1);
    dc_motor_math_U.load_in = (real_T)load_mv / ADC_VREF_MV * MAX_LOAD_N;

    /* 3. Step the model */
    dc_motor_math_step();

    /* 4. Scale speed_sig (0-500 RPM) -> 0-3.3V feedback */
    real_T speed = dc_motor_math_Y.speed_sig;
    if (speed < 0) speed = 0;
    if (speed > MAX_SPEED_RPM) speed = MAX_SPEED_RPM;
    int32_t fb_mv = (int32_t)(speed / MAX_SPEED_RPM * ADC_VREF_MV);
    write_feedback_mv(fb_mv);
}

K_TIMER_DEFINE(motorsim_timer, sim_step, NULL);

int cmd_motorsim_start(const struct shell *sh, size_t argc, char **argv)
{
    if (sim_running) {
        shell_error(sh, "ERROR: simulation already running");
        return -EALREADY;
    }
    dc_motor_math_initialize();
    /* model step size is 0.2s -> 200ms period */
    k_timer_start(&motorsim_timer, K_MSEC(200), K_MSEC(200));
    sim_running = true;
    shell_print(sh, "OK");
    return 0;
}

int cmd_motorsim_stop(const struct shell *sh, size_t argc, char **argv)
{
    if (!sim_running) {
        shell_error(sh, "ERROR: simulation not running");
        return -EALREADY;
    }
    k_timer_stop(&motorsim_timer);
    dc_motor_math_terminate();
    sim_running = false;
    shell_print(sh, "OK");
    return 0;
}

int cmd_motorsim_get(const struct shell *sh, size_t argc, char **argv)
{
    if (!sim_running) {
        shell_error(sh, "ERROR: simulation not running");
        return -EAGAIN;
    }
    shell_print(sh, "speed=%d.%02d rpm current=%d.%03d A",
        (int)dc_motor_math_Y.speed_sig,
        (int)(dc_motor_math_Y.speed_sig * 100) % 100,
        (int)dc_motor_math_Y.current_sig,
        (int)(dc_motor_math_Y.current_sig * 1000) % 1000);
    return 0;
}

