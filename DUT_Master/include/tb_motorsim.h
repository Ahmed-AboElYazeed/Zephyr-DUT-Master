/*
 * tb_motorsim.h
 *
 * Testbench DC motor plant simulation - shell command interface.
 * Wraps the Simulink-generated dc_motor_math model and exposes it
 * over the Zephyr shell so Robot Framework / Python tooling can
 * drive it from the host.
 */

#ifndef TB_MOTORSIM_H_
#define TB_MOTORSIM_H_

#include <zephyr/kernel.h>

/* How the testbench reads the DUT's voltage command */
typedef enum {
    TB_MOTORSIM_SRC_ADC = 0,   /* read an analog voltage on an ADC pin */
    TB_MOTORSIM_SRC_PWM = 1,   /* read a PWM duty cycle and treat duty% as the command */
} tb_motorsim_src_t;

/* Called once at boot to register the k_timer / thread plumbing. */
void tb_motorsim_init(void);

#endif /* TB_MOTORSIM_H_ */