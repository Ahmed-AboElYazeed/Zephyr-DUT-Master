from .transport import ShellTransport

from .motor_sim import MotorSim, rpm_to_pwm_duty, adc_voltage_to_motor_voltage
import time

class ZephyrShellLib:
    """Robot Framework library for the Zephyr shell testbench."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self, port: str, baud: int = 115200, timeout: float = 5.0):
        self._t = ShellTransport(port, int(baud), float(timeout))

    # ── connection ─────────────────────────────────────────────────

    def close(self):
        """Close the serial port. Called automatically at suite teardown."""
        self._t.close()

    # ── helpers ────────────────────────────────────────────────────

    def _run(self, cmd: str, timeout: float = None) -> str:
        result = self._t.run(cmd, timeout)
        if result.startswith("ERROR:"):
            raise RuntimeError(f"Testbench error: {result}")
        return result

    # ── GPIO ───────────────────────────────────────────────────────

    def gpio_set(self, pin: str, value):
        """Drive GPIO *pin* to *value* (0 or 1)."""
        self._run(f"tb gpio set {pin} {int(value)}")

    def gpio_get(self, pin: str) -> int:
        """Read GPIO *pin*. Returns 0 or 1."""
        return int(self._run(f"tb gpio get {pin}"))

    # ── ADC ────────────────────────────────────────────────────────

    def adc_read_mv(self, pin: str) -> int:
        """Read ADC on *pin*. Returns integer millivolts."""
        raw = self._run(f"tb adc read {pin}")   # "1842 mV"
        return int(raw.split()[0])

    # ── SPI ────────────────────────────────────────────────────────

    def spi_transfer(self, bus, *hex_bytes: str) -> str:
        """Transfer hex bytes over SPI *bus*. Returns received bytes as 'DE AD ...'"""
        payload = " ".join(hex_bytes)
        return self._run(f"tb spi trans {bus} {payload}")

    # ── UART ───────────────────────────────────────────────────────

    def uart_send(self, dev: str, text: str):
        """Send *text* over testbench UART *dev* to the DUT."""
        self._run(f"tb uart send {dev} {text}")

    def uart_recv(self, dev: str, timeout_ms: int = 500) -> str:
        """Receive a line from DUT over UART *dev*, waiting up to *timeout_ms*."""
        return self._run(f"tb uart recv {dev} {timeout_ms}",
                         timeout=float(timeout_ms) / 1000 + 2.0)

    # ── PWM ────────────────────────────────────────────────────────

    def pwm_set(self, pin: str, freq_hz: int, duty_pct: int):
        """Start PWM on *pin* at *freq_hz* Hz and *duty_pct* % duty cycle."""
        self._run(f"tb pwm set {pin} {freq_hz} {duty_pct}")

    def pwm_capture(self, pin: str) -> dict:
        """Capture PWM on *pin*. Returns dict with keys freq_hz and duty_pct."""
        raw = self._run(f"tb pwm capture {pin}", timeout=3.0)
        parts = raw.split()    # "999 Hz 49 pct"
        return {"freq_hz": int(parts[0]), "duty_pct": int(parts[2])}

    def pwm_get_freq(self, pin: str) -> int:
        """Convenience: return only the captured frequency in Hz."""
        return self.pwm_capture(pin)["freq_hz"]

    def pwm_get_duty(self, pin: str) -> int:
        """Convenience: return only the captured duty cycle in percent."""
        return self.pwm_capture(pin)["duty_pct"]
    

    def motorsim_start(self):
        """Start the DC motor plant simulation."""
        self._run("tb motorsim start")

    def motorsim_stop(self):
        """Stop the DC motor plant simulation."""
        self._run("tb motorsim stop")

    def motorsim_get(self) -> dict:
        """Get current simulated speed (rpm) and current (A)."""
        raw = self._run("tb motorsim get")
        # "speed=123.45 rpm current=1.234 A"
        parts = raw.replace("=", " ").split()
        return {"speed_rpm": float(parts[1]), "current_a": float(parts[4])}
    
    def run_motor_test_sequence(self,
                            ref_speeds=None,
                            setpoint_duration_s=None,
                            check_interval_s=None,
                            error_limit_rpm=None,
                            load_nm=None,
                            adc_pin="PA0",
                            pwm_pin="PA8") -> str:
        """
        Run the complete closed-loop motor test sequence.
        
        For each reference speed in ref_speeds:
        - Set PWM duty to represent ref speed
        - Every check_interval_s seconds:
            a. Read DUT voltage output (ADC)
            b. Run motor simulation with that voltage + load
            c. Compare actual speed to reference
            d. Log PASS/FAIL
        
        All parameters are optional — defaults come from class variables.
        
        Returns:
            String like "PASS PASS FAIL PASS ..." (one per check)
        """
        # Use defaults if not provided
        ref_speeds = ref_speeds or self.REF_SPEEDS_RPM
        duration = setpoint_duration_s or self.SETPOINT_DURATION_S
        interval = check_interval_s or self.CHECK_INTERVAL_S
        limit = error_limit_rpm or self.SPEED_ERROR_LIMIT_RPM
        load = load_nm if load_nm is not None else self.LOAD_TORQUE_NM
        
        # Reset simulation
        self.motorsim_start()
        self.motorsim_set_load(load)
        
        results = []
        
        for ref_rpm in ref_speeds:
            self.motorsim_set_reference_speed(ref_rpm)
            
            # Run for setpoint_duration, checking every interval
            elapsed = 0.0
            while elapsed < duration:
                time.sleep(interval)
                elapsed += interval
                
                # 1. Read DUT voltage output (ADC)
                adc_v = self.adc_read_voltage(adc_pin)
                motor_v = adc_voltage_to_motor_voltage(adc_v)
                
                # 2. Run motor simulation
                sim_result = self.motorsim_run_step(motor_v, interval)
                actual_rpm = sim_result["speed_rpm"]
                
                # 3. Calculate error
                error = abs(ref_rpm - actual_rpm)
                passed = error < limit
                
                # 4. Log result
                self._results_log.append((
                    time.time(), ref_rpm, actual_rpm, error, passed
                ))
                results.append("PASS" if passed else "FAIL")
                
                # 5. Send actual speed back to DUT as feedback
                feedback_duty = rpm_to_pwm_duty(actual_rpm)
                self.pwm_set(pwm_pin, self.PWM_MAX_FREQ, feedback_duty)
        
        return " ".join(results)