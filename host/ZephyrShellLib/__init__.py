"""
ZephyrShellLib

Robot Framework library for the Zephyr shell testbench (STM32F401CC
Black Pill running Zephyr OS). Talks to the board's shell over a
USB-TTL UART connection and exposes every `tb ...` shell command as a
Robot Framework keyword.

Combines:
    PeripheralKeywords  -- GPIO, ADC, SPI, UART, PWM (Stage 8)
    MotorSimKeywords    -- DC motor plant simulation (Stage 19)

Connection-level features (Stage 11/12/13):
    - heartbeat ping at connect time
    - cached pin descriptor (`tb desc`)
    - retry-on-timeout
    - thread lock for parallel test runners (pabot)
    - optional fixture file (per-DUT wiring descriptor, Stage 15)
    - optional raw UART logging for post-mortem debugging (Stage 16)

Usage in a .robot file:

    *** Settings ***
    Library    ZephyrShellLib    port=/dev/ttyUSB0    baud=115200

    or, with a fixture file:

    Library    ZephyrShellLib    fixture=fixture/sensor_board_fixture.yaml
"""

import functools
import json
import threading
import time

from .transport import ShellTransport
from .peripheral_keywords import PeripheralKeywords
from .motorsim_keywords import MotorSimKeywords


def requires_connection(fn):
    """Decorator: raise a clear error if the keyword is called on a
    closed connection, instead of a confusing pyserial exception."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not self._t.is_open:
            raise ConnectionError(
                "Serial port is closed. Was the library imported/opened correctly?"
            )
        return fn(self, *args, **kwargs)
    return wrapper


class ZephyrShellLib(PeripheralKeywords, MotorSimKeywords):
    """Robot Framework library for the Zephyr shell testbench."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self, port: str = None, baud: int = 115200, timeout: float = 5.0,
                 retries: int = 1, fixture: str = None, logdir: str = None):
        """
        port:    serial device, e.g. /dev/ttyUSB0 or COM5.
                 Optional if `fixture` provides testbench_port.
        baud:    serial baud rate. Default 115200.
        timeout: default per-command timeout in seconds.
        retries: number of automatic retries on a command timeout.
        fixture: optional path to a YAML wiring descriptor (Stage 15).
                 If given and `port` is not, the port is read from
                 the fixture file's `testbench_port` field.
        logdir:  optional directory to write a timestamped raw
                 TX/RX UART log file to (Stage 16).
        """
        self._lock = threading.Lock()
        self._retries = int(retries)
        self._fixture = None

        if fixture:
            from .fixture_loader import FixtureLoader
            self._fixture = FixtureLoader(fixture)
            if not port:
                port = self._fixture.get_port()
            print(self._fixture.summary())

        if not port:
            raise ValueError("Either 'port' or a 'fixture' with testbench_port must be given.")

        self._t = ShellTransport(port, int(baud), float(timeout), logdir=logdir)
        self.ping_testbench()
        self._descriptor = self._fetch_descriptor()

    # ── lifecycle ──────────────────────────────────────────────────

    def close(self):
        """Close the serial port. Called automatically at suite teardown
        if this keyword is wired into a Suite Teardown."""
        self._t.close()

    # ── fixture passthrough (Stage 15/17) ─────────────────────────

    def get_fixture_pin(self, signal: str) -> str:
        """Look up the testbench pin for a named signal in the loaded fixture."""
        if not self._fixture:
            raise RuntimeError("No fixture file was loaded for this library instance.")
        return self._fixture.get_pin(signal)

    def get_fixture_capability(self, name: str, default=False):
        """Look up a capability flag from the loaded fixture (Stage 17)."""
        if not self._fixture:
            return default
        return self._fixture.get_capability(name, default)

    # ── internals used by both keyword mixins ─────────────────────

    @requires_connection
    def _run(self, cmd: str, timeout: float = None) -> str:
        with self._lock:
            return self._run_with_retry(cmd, timeout=timeout)

    def _run_with_retry(self, cmd: str, timeout: float = None) -> str:
        last_exc = None
        for attempt in range(self._retries + 1):
            try:
                result = self._t.run(cmd, timeout=timeout)
                if result.startswith("ERROR:"):
                    raise RuntimeError(f"Testbench error: {result}")
                return result
            except TimeoutError as e:
                last_exc = e
                if attempt < self._retries:
                    # Flush a newline to clear any partial state, then retry
                    try:
                        self._t.raw_serial.write(b"\r\n")
                        time.sleep(0.3)
                        self._t.raw_serial.reset_input_buffer()
                    except Exception:
                        pass
        raise last_exc

    def _fetch_descriptor(self) -> dict:
        """Fetch the JSON pin descriptor from the firmware.

        If the firmware does not implement `tb desc` (e.g. it returns
        plain-text help instead), fall back to an empty descriptor so
        the library can still be used. A warning is printed so the
        user knows descriptor-dependent features won't work.
        """
        try:
            raw = self._t.run("tb desc", timeout=3.0)
        except TimeoutError:
            print("WARNING: `tb desc` timed out — using empty descriptor")
            return {}

        # If the response looks like a help menu instead of JSON,
        # the firmware doesn't support the descriptor command.
        stripped = raw.strip()
        if not stripped or stripped.startswith("tb") or stripped.startswith("Subcommands:"):
            print("WARNING: Firmware does not support `tb desc` — using empty descriptor")
            return {}

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            # Log the raw response for debugging but don't crash
            print(f"WARNING: Could not parse pin descriptor: {raw!r}")
            return {}
