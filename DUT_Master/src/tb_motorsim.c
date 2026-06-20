/*
 * tb_motorsim.c
 *
 * Testbench DC motor plant simulation.
 *
 * Wraps the Simulink-generated dc_motor_math model (voltage -> speed,
 * 2 continuous states: armature current, rotor speed) and drives it
 * from a real DUT input signal that can be EITHER:
 *
 *   - an analog voltage read via ADC                  (tb motorsim start adc <pin>)
 *   - a PWM duty cycle, interpreted as 0-100% -> 0-Vmax (tb motorsim start pwm <pin>)
 *
 * The simulated speed is:
 *   - readable on demand          (tb motorsim get)
 *   - streamed continuously       (tb motorsim stream on/off)
 *     Uses uart_poll_out() directly to bypass printk/log subsystem,
 *     guaranteeing raw MSIM lines reach the host without prefixing
 *     or buffering issues.
 *
 * Shell command tree (registered in tb_cmds.c):
 *   tb motorsim start <adc|pwm> <pin> [vmax_mv]
 *   tb motorsim stop
 *   tb motorsim get
 *   tb motorsim stream <on|off>
 *   tb motorsim source <adc|pwm> <pin>      (change source while NOT running)
 *   tb motorsim params <R> <L> <J> <K> <b>  (override plant parameters at runtime)
 */

#include <zephyr/kernel.h>
#include <zephyr/shell/shell.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/device.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>     /* fabs() */

#include "dc_motor_math.h"
#include "tb_motorsim.h"

/* ------------------------------------------------------------------ */
/* Configuration                                                       */
/* ------------------------------------------------------------------ */

#define MOTORSIM_STEP_MS   200     /* must match dc_motor_math_M->Timing.stepSize0 (0.2s) */
#define ADC_RESOLUTION     12
#define ADC_VREF_MV        3300
#define DEFAULT_VMAX_MV    3300    /* voltage that maps to 100% PWM duty or full-scale ADC */

#define ADC_DEV_NODE       DT_NODELABEL(adc1)
#define PWM_IN_DEV_NODE    DT_NODELABEL(pwm2)   /* capture-capable PWM timer, see Stage 7 overlay */

/* Shell UART device for raw stream output (bypass printk/logging) */
#define SHELL_UART_NODE    DT_NODELABEL(usart1)

/* ------------------------------------------------------------------ */
/* State                                                               */
/* ------------------------------------------------------------------ */

static struct k_timer       motorsim_timer;
static struct k_work        motorsim_work;
static bool                 sim_running;
static bool                 stream_enabled;
static tb_motorsim_src_t    input_source = TB_MOTORSIM_SRC_ADC;
static int                  input_channel = 0;   /* ADC channel index OR PWM capture channel index */
static uint32_t             vmax_mv = DEFAULT_VMAX_MV;
static uint32_t             step_count;

static const struct device *adc_dev;
static const struct device *pwm_in_dev;
static const struct device *shell_uart_dev;

/* ------------------------------------------------------------------ */
/* Pin name -> ADC channel lookup (extend as needed, mirrors Stage 4) */
/* ------------------------------------------------------------------ */

static int pin_to_adc_channel(const char *pin)
{
    if (strcmp(pin, "PA0") == 0) return 0;
    if (strcmp(pin, "PA1") == 0) return 1;
    if (strcmp(pin, "PA2") == 0) return 2;
    if (strcmp(pin, "PA3") == 0) return 3;
    return -1;
}

/* PWM capture channel lookup -- mirrors Stage 7 overlay (pwm2 = TIM2 CH2 on PA1) */
static int pin_to_pwm_channel(const char *pin)
{
    if (strcmp(pin, "PA1") == 0) return 1;   /* TIM2 CH2 */
    return -1;
}

/* ------------------------------------------------------------------ */
/* Raw UART output helper (bypasses printk/log subsystem)            */
/* ------------------------------------------------------------------ */

static void shell_uart_write_line(const char *buf, size_t len)
{
    if (!shell_uart_dev) {
        return;
    }
    for (size_t i = 0; i < len; i++) {
        uart_poll_out(shell_uart_dev, buf[i]);
    }
}

/* ------------------------------------------------------------------ */
/* ADC read helper (properly configured)                              */
/* ------------------------------------------------------------------ */

static int16_t adc_read_channel(int channel)
{
    int16_t buf = 0;

    struct adc_sequence seq = {
        .channels    = BIT(channel),
        .buffer      = &buf,
        .buffer_size = sizeof(buf),
        .resolution  = ADC_RESOLUTION,
    };

    int ret = adc_read(adc_dev, &seq);
    if (ret < 0) {
        return -1;
    }

    return buf;
}

/* ------------------------------------------------------------------ */
/* Input acquisition                                                   */
/* ------------------------------------------------------------------ */

/* Returns the DUT's commanded voltage in volts (0.0 - vmax_mv/1000.0) */
static real_T read_input_voltage(void)
{
    if (input_source == TB_MOTORSIM_SRC_ADC) {
        int16_t raw = adc_read_channel(input_channel);
        if (raw < 0) {
            return 0.0;
        }

        /* Convert raw ADC to millivolts */
        int32_t mv = ((int32_t)raw * ADC_VREF_MV) / ((1 << ADC_RESOLUTION) - 1);
        if (mv < 0) mv = 0;

        return (real_T)mv / 1000.0;

    } else {
        /* PWM source: capture duty cycle, map 0-100% -> 0-vmax */
        uint64_t period_ns = 0, pulse_ns = 0;
        int ret = pwm_capture_nsec(pwm_in_dev, input_channel,
                                   PWM_CAPTURE_TYPE_BOTH,
                                   &period_ns, &pulse_ns,
                                   K_MSEC(50));
        if (ret < 0 || period_ns == 0) {
            return 0.0;
        }
        uint32_t duty_pct = (uint32_t)((uint64_t)pulse_ns * 100U / period_ns);
        if (duty_pct > 100) duty_pct = 100;
        return ((real_T)duty_pct / 100.0) * ((real_T)vmax_mv / 1000.0);
    }
}

/* ------------------------------------------------------------------ */
/* Format helpers: convert double to "int.frac" safely                */
/* ------------------------------------------------------------------ */

static void fmt_double(char *buf, size_t buflen, real_T val)
{
    /* Handle NaN/inf */
    if (!isfinite(val)) {
        snprintf(buf, buflen, "0.000");
        return;
    }

    int sign = (val < 0) ? -1 : 1;
    real_T absval = val * sign;
    int intpart = (int)absval;
    int fracpart = (int)((absval - intpart) * 1000.0 + 0.5);
    if (fracpart >= 1000) { fracpart = 0; intpart++; }

    if (sign < 0) {
        snprintf(buf, buflen, "-%d.%03d", intpart, fracpart);
    } else {
        snprintf(buf, buflen, "%d.%03d", intpart, fracpart);
    }
}

/* ------------------------------------------------------------------ */
/* Simulation step (runs in a workqueue, NOT in timer ISR context)    */
/* ------------------------------------------------------------------ */

static void motorsim_work_handler(struct k_work *work)
{
    ARG_UNUSED(work);

    if (!sim_running) {
        return;
    }

    /* 1. Acquire the DUT's voltage command from the selected source */
    dc_motor_math_U.voltage_in = read_input_voltage();
    dc_motor_math_U.load_in = 0.0;  /* no external load by default */

    /* 2. Step the model (internally runs the ODE3 fixed-step solver) */
    dc_motor_math_step();
    step_count++;

    /* 3. Stream a line to the host if streaming is enabled.
     *    Uses uart_poll_out() directly to bypass printk/log subsystem,
     *    preventing timestamp prefixing, buffering, or dropped lines.
     *    Format: MSIM,t_ms,voltage_v,speed_radps,current_a
     */
    if (stream_enabled) {
        real_T current = dc_motor_math_X.Integrator_CSTATE;
        real_T speed   = dc_motor_math_X.Integrator1_CSTATE;
        uint32_t t_ms  = step_count * MOTORSIM_STEP_MS;

        char v_str[16], s_str[16], c_str[16];
        fmt_double(v_str, sizeof(v_str), dc_motor_math_U.voltage_in);
        fmt_double(s_str, sizeof(s_str), speed);
        fmt_double(c_str, sizeof(c_str), current);

        char line[96];
        int n = snprintf(line, sizeof(line),
            "MSIM,%u,%s,%s,%s\n",
            t_ms, v_str, s_str, c_str);

        if (n > 0 && n < (int)sizeof(line)) {
            shell_uart_write_line(line, (size_t)n);
        }
    }
}

static void motorsim_timer_handler(struct k_timer *timer)
{
    ARG_UNUSED(timer);
    /* Defer the actual work out of ISR context */
    k_work_submit(&motorsim_work);
}

/* ------------------------------------------------------------------ */
/* Shell commands                                                      */
/* ------------------------------------------------------------------ */

int cmd_motorsim_start(const struct shell *sh, size_t argc, char **argv)
{
    if (sim_running) {
        shell_error(sh, "ERROR: simulation already running");
        return -EALREADY;
    }
    if (argc < 3) {
        shell_error(sh, "ERROR: usage: tb motorsim start <adc|pwm> <pin> [vmax_mv]");
        return -EINVAL;
    }

    if (strcmp(argv[1], "adc") == 0) {
        int ch = pin_to_adc_channel(argv[2]);
        if (ch < 0) {
            shell_error(sh, "ERROR: unknown ADC pin %s", argv[2]);
            return -ENODEV;
        }
        input_source  = TB_MOTORSIM_SRC_ADC;
        input_channel = ch;
    } else if (strcmp(argv[1], "pwm") == 0) {
        int ch = pin_to_pwm_channel(argv[2]);
        if (ch < 0) {
            shell_error(sh, "ERROR: unknown PWM capture pin %s", argv[2]);
            return -ENODEV;
        }
        input_source  = TB_MOTORSIM_SRC_PWM;
        input_channel = ch;
    } else {
        shell_error(sh, "ERROR: source must be 'adc' or 'pwm', got '%s'", argv[1]);
        return -EINVAL;
    }

    if (argc >= 4) {
        vmax_mv = (uint32_t)atoi(argv[3]);
    } else {
        vmax_mv = DEFAULT_VMAX_MV;
    }

    dc_motor_math_initialize();
    step_count = 0;
    sim_running = true;
    stream_enabled = false;

    k_timer_start(&motorsim_timer, K_MSEC(MOTORSIM_STEP_MS), K_MSEC(MOTORSIM_STEP_MS));

    shell_print(sh, "OK source=%s pin=%s vmax_mv=%u step_ms=%u",
                argv[1], argv[2], vmax_mv, MOTORSIM_STEP_MS);
    return 0;
}

int cmd_motorsim_stop(const struct shell *sh, size_t argc, char **argv)
{
    ARG_UNUSED(argc);
    ARG_UNUSED(argv);

    if (!sim_running) {
        shell_error(sh, "ERROR: simulation not running");
        return -EALREADY;
    }
    k_timer_stop(&motorsim_timer);
    dc_motor_math_terminate();
    sim_running = false;
    stream_enabled = false;
    shell_print(sh, "OK");
    return 0;
}

int cmd_motorsim_get(const struct shell *sh, size_t argc, char **argv)
{
    ARG_UNUSED(argc);
    ARG_UNUSED(argv);

    if (!sim_running) {
        shell_error(sh, "ERROR: simulation not running");
        return -EAGAIN;
    }

    real_T current = dc_motor_math_X.Integrator_CSTATE;
    real_T speed   = dc_motor_math_X.Integrator1_CSTATE;

    char v_str[16], s_str[16], c_str[16];
    fmt_double(v_str, sizeof(v_str), dc_motor_math_U.voltage_in);
    fmt_double(s_str, sizeof(s_str), speed);
    fmt_double(c_str, sizeof(c_str), current);

    shell_print(sh, "t_ms=%u voltage_v=%s speed_radps=%s current_a=%s",
                step_count * MOTORSIM_STEP_MS, v_str, s_str, c_str);
    return 0;
}

int cmd_motorsim_stream(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 2) {
        shell_error(sh, "ERROR: usage: tb motorsim stream <on|off>");
        return -EINVAL;
    }
    if (strcmp(argv[1], "on") == 0) {
        stream_enabled = true;
        shell_print(sh, "OK streaming on (format: MSIM,t_ms,voltage_v,speed_radps,current_a)");
    } else if (strcmp(argv[1], "off") == 0) {
        stream_enabled = false;
        shell_print(sh, "OK streaming off");
    } else {
        shell_error(sh, "ERROR: must be 'on' or 'off'");
        return -EINVAL;
    }
    return 0;
}

int cmd_motorsim_source(const struct shell *sh, size_t argc, char **argv)
{
    /* Allows changing source without starting the sim (e.g. for setup verification) */
    if (sim_running) {
        shell_error(sh, "ERROR: stop the simulation before changing source");
        return -EBUSY;
    }
    if (argc != 3) {
        shell_error(sh, "ERROR: usage: tb motorsim source <adc|pwm> <pin>");
        return -EINVAL;
    }
    if (strcmp(argv[1], "adc") == 0) {
        int ch = pin_to_adc_channel(argv[2]);
        if (ch < 0) {
            shell_error(sh, "ERROR: unknown ADC pin %s", argv[2]);
            return -ENODEV;
        }
        input_source = TB_MOTORSIM_SRC_ADC;
        input_channel = ch;
    } else if (strcmp(argv[1], "pwm") == 0) {
        int ch = pin_to_pwm_channel(argv[2]);
        if (ch < 0) {
            shell_error(sh, "ERROR: unknown PWM capture pin %s", argv[2]);
            return -ENODEV;
        }
        input_source = TB_MOTORSIM_SRC_PWM;
        input_channel = ch;
    } else {
        shell_error(sh, "ERROR: source must be 'adc' or 'pwm'");
        return -EINVAL;
    }
    shell_print(sh, "OK");
    return 0;
}

int cmd_motorsim_params(const struct shell *sh, size_t argc, char **argv)
{
    /* tb motorsim params <R> <L> <J> <K> <b> */
    extern real_T dc_motor_math_R, dc_motor_math_L, dc_motor_math_J;
    extern real_T dc_motor_math_K, dc_motor_math_b;

    if (sim_running) {
        shell_error(sh, "ERROR: stop the simulation before changing params");
        return -EBUSY;
    }
    if (argc != 6) {
        shell_error(sh, "ERROR: usage: tb motorsim params <R> <L> <J> <K> <b>");
        return -EINVAL;
    }
    dc_motor_math_R = atof(argv[1]);
    dc_motor_math_L = atof(argv[2]);
    dc_motor_math_J = atof(argv[3]);
    dc_motor_math_K = atof(argv[4]);
    dc_motor_math_b = atof(argv[5]);

    shell_print(sh, "OK R=%s L=%s J=%s K=%s b=%s",
                argv[1], argv[2], argv[3], argv[4], argv[5]);
    return 0;
}

/* ------------------------------------------------------------------ */
/* Init                                                                */
/* ------------------------------------------------------------------ */

void tb_motorsim_init(void)
{
    adc_dev    = DEVICE_DT_GET(ADC_DEV_NODE);
    pwm_in_dev = DEVICE_DT_GET(PWM_IN_DEV_NODE);
    shell_uart_dev = DEVICE_DT_GET(SHELL_UART_NODE);

    k_work_init(&motorsim_work, motorsim_work_handler);
    k_timer_init(&motorsim_timer, motorsim_timer_handler, NULL);
}
