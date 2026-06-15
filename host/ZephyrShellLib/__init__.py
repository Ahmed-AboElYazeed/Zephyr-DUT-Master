from .transport import ShellTransport

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
