"""
peripheral_keywords.py

Core testbench peripheral keywords (GPIO, ADC, SPI, UART, PWM) --
Stage 8 of the implementation plan. Mixed into ZephyrShellLib.
"""


class PeripheralKeywords:

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
        return self._run(f"tb spi xfer {bus} {payload}")

    # ── UART (to DUT, separate from the shell UART) ───────────────

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

    # ── descriptor / housekeeping (Stage 11/12) ───────────────────

    def ping_testbench(self):
        """Send a heartbeat check. Raises if the testbench doesn't reply 'pong'."""
        result = self._run("tb ping", timeout=2.0)
        if "pong" not in result:
            raise RuntimeError(f"Testbench did not respond to ping. Got: {result!r}")

    def reset_testbench(self):
        """Trigger a software reset and wait for the shell to come back up."""
        try:
            self._t.raw_serial.write(b"tb reset\r\n")
        except Exception:
            pass
        import time
        time.sleep(2.0)
        self._t.raw_serial.reset_input_buffer()
        self.ping_testbench()

    def get_descriptor(self) -> dict:
        """Return the cached pin descriptor dict (fetched once at connect time)."""
        return self._descriptor

    def get_adc_pins(self) -> list:
        return self._descriptor.get("adc", [])

    def get_pwm_out_pins(self) -> list:
        return self._descriptor.get("pwm_out", [])

    def get_uart_history(self, last_n: int = 10) -> str:
        """Return the last N raw TX/RX lines for failure diagnosis,
        read back from the UART log file if logging was enabled."""
        if not getattr(self._t, "_log", None):
            return "(no UART log enabled -- pass logdir= to ZephyrShellLib to enable)"
        try:
            with open(self._t._log.name) as f:
                lines = f.readlines()
            return "".join(lines[-last_n:])
        except Exception as e:
            return f"(could not read UART log: {e})"
