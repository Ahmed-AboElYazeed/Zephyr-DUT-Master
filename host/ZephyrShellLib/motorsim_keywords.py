"""
motorsim_keywords.py

DC motor plant simulation keywords (Stage 19). Mixed into ZephyrShellLib.
All keywords route through self._run(), which raises RuntimeError on
"ERROR:" responses -- Robot Framework turns that into a clean test FAIL.
"""

import time


class MotorSimKeywords:

    # ── lifecycle ──────────────────────────────────────────────────

    def motorsim_start(self, source: str, pin: str, vmax_mv: int = 3300):
        """Start the DC motor plant simulation.

        *source* must be ``adc`` or ``pwm`` -- selects whether the
        testbench reads the DUT's voltage command from an analog ADC
        pin or from a PWM duty cycle (0-100% mapped to 0-vmax_mv).

        *pin* is the physical testbench pin used to read the command
        (e.g. ``PA0`` for adc, ``PA1`` for pwm capture).

        Example:
        | Motorsim Start | adc | PA0 |
        | Motorsim Start | pwm | PA1 | vmax_mv=3300 |
        """
        source = source.lower()
        if source not in ("adc", "pwm"):
            raise ValueError(f"source must be 'adc' or 'pwm', got {source!r}")
        self._run(f"tb motorsim start {source} {pin} {int(vmax_mv)}")

    def motorsim_stop(self):
        """Stop the DC motor plant simulation."""
        self._run("tb motorsim stop")

    def motorsim_ensure_stopped(self):
        """Stop the simulation if running; do nothing (no error) if not.
        Safe to call unconditionally in Suite/Test Setup."""
        try:
            self._run("tb motorsim stop")
        except RuntimeError:
            pass

    def motorsim_set_source(self, source: str, pin: str):
        """Change the input source while the simulation is stopped."""
        source = source.lower()
        if source not in ("adc", "pwm"):
            raise ValueError(f"source must be 'adc' or 'pwm', got {source!r}")
        self._run(f"tb motorsim source {source} {pin}")

    def motorsim_set_params(self, R: float, L: float, J: float,
                            K: float, b: float):
        """Override the plant model parameters before starting a run.

        R: armature resistance (Ohm)
        L: armature inductance (H)
        J: rotor inertia (kg*m^2)
        K: torque/back-EMF constant (N*m/A)
        b: viscous friction coefficient (N*m*s)
        """
        self._run(f"tb motorsim params {R} {L} {J} {K} {b}")

    # ── readback ───────────────────────────────────────────────────

    def motorsim_get(self) -> dict:
        """Read the current simulated state as a one-shot snapshot.

        Returns a dict with keys: t_ms, voltage_v, speed_radps, current_a
        """
        raw = self._run("tb motorsim get")
        result = {}
        for token in raw.split():
            key, _, value = token.partition("=")
            if key == "t_ms":
                result[key] = int(value)
            elif key in ("voltage_v", "speed_radps", "current_a"):
                result[key] = float(value)
        return result

    def motorsim_get_speed_radps(self) -> float:
        """Convenience: return only the simulated speed in rad/s."""
        return self.motorsim_get()["speed_radps"]

    def motorsim_get_speed_rpm(self) -> float:
        """Convenience: return the simulated speed converted to RPM."""
        return self.motorsim_get()["speed_radps"] * 60.0 / (2 * 3.141592653589793)

    # ── streaming control ──────────────────────────────────────────

    def motorsim_stream_on(self):
        """Enable continuous streaming of MSIM,... lines from firmware.

        Note: while streaming is on, avoid calling other keywords that
        read from the serial port on the SAME connection -- stream
        lines will interleave with command responses. Use
        `Collect Motorsim Samples` instead, which handles this safely.
        """
        self._run("tb motorsim stream on")

    def motorsim_stream_off(self):
        """Disable continuous streaming."""
        self._run("tb motorsim stream off")

    def collect_motorsim_samples(self, duration_s: float, max_samples: int = 10000) -> list:
        """Enable streaming, collect samples for *duration_s* seconds,
        disable streaming, and return a list of dicts:
        [{"t_ms": int, "voltage_v": float, "speed_radps": float, "current_a": float}, ...]

        Use this when asserting on a transient response curve (rise
        time, overshoot, settling time) rather than a steady-state
        snapshot.
        """
        ser = self._t.raw_serial
        ser.reset_input_buffer()
        self.motorsim_stream_on()

        samples = []
        deadline = time.monotonic() + duration_s
        buf = b""
        while time.monotonic() < deadline and len(samples) < max_samples:
            chunk = ser.read(256)
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                parsed = self._parse_msim_line(line)
                if parsed:
                    samples.append(parsed)

        self.motorsim_stream_off()
        return samples

    @staticmethod
    def _parse_msim_line(line: bytes):
        """Parse one 'MSIM,t_ms,voltage_v,speed_radps,current_a' line."""
        try:
            text = line.decode(errors="ignore").strip()
            if not text.startswith("MSIM,"):
                return None
            parts = [p.strip() for p in text.split(",")]
            if len(parts) != 5:
                return None
            return {
                "t_ms": int(parts[1]),
                "voltage_v": float(parts[2]),
                "speed_radps": float(parts[3]),
                "current_a": float(parts[4]),
            }
        except (ValueError, IndexError):
            return None
