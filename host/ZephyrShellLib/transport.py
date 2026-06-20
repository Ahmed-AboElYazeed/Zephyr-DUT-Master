"""
transport.py

Low-level serial transport for talking to the Zephyr shell on the
STM32 testbench. This is the only module that touches pyserial
directly -- everything else (ZephyrShellLib and its keyword mixins)
goes through ShellTransport.run().

Responsibilities:
    - open/close the serial port
    - send a command string, read until the shell prompt reappears
    - strip the echoed command (if any) and the trailing prompt
    - raise TimeoutError / RuntimeError on failure
    - optional raw TX/RX logging to a file for post-mortem debugging
"""

import datetime
import pathlib
import time

import serial


# Update this if you changed CONFIG_SHELL_PROMPT_UART away from the default.
DEFAULT_PROMPT = b"blackpill:~$ "


class ShellTransport:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 5.0,
                 prompt: bytes = DEFAULT_PROMPT, logdir: str = None):
        self.prompt = prompt
        self._ser = serial.Serial(port, baud, timeout=0.05)
        self._default_timeout = timeout

        self._log = None
        if logdir:
            pathlib.Path(logdir).mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._log = open(f"{logdir}/uart_{ts}.log", "wb")

        time.sleep(0.5)
        self._ser.reset_input_buffer()
        # Flush any stale prompt left over from a previous session
        self._ser.write(b"\r\n")
        try:
            self._drain(timeout=1.0)
        except TimeoutError:
            pass  # fine if nothing was pending

    # ── public API ─────────────────────────────────────────────────

    def run(self, cmd: str, timeout: float = None) -> str:
        """Send a command string and return the output (stripped of prompt)."""
        t = timeout or self._default_timeout
        self._ser.reset_input_buffer()
        self._write_log("TX", cmd.encode())
        self._ser.write((cmd + "\r\n").encode())
        raw = self._drain(timeout=t)
        self._write_log("RX", raw)
        return self._extract(raw, cmd)

    def close(self):
        if self._ser.is_open:
            self._ser.close()
        if self._log:
            self._log.close()

    @property
    def is_open(self) -> bool:
        return self._ser.is_open

    @property
    def raw_serial(self) -> serial.Serial:
        """Expose the underlying pyserial object for streaming-style
        keywords (e.g. Collect Motorsim Samples) that need to read
        continuously rather than command/response style."""
        return self._ser

    def reopen(self):
        """Re-open a closed port (used by the auto-reconnect logic)."""
        if not self._ser.is_open:
            self._ser.open()

    # ── internals ──────────────────────────────────────────────────

    def _drain(self, timeout: float) -> bytes:
        buf = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = self._ser.read(256)
            if chunk:
                buf += chunk
            if self.prompt in buf:
                return buf
        raise TimeoutError(f"No shell prompt after {timeout}s. Buffer: {buf!r}")

    def _extract(self, raw: bytes, cmd: str) -> str:
        """Strip the command echo (if any) and the trailing prompt."""
        text = raw.decode(errors="replace")
        # Only strip the command echo when it appears right at the start
        # of the response (after optional leading whitespace/newlines).
        # Using text.index(cmd) anywhere in the string could accidentally
        # strip a matching substring from the actual response body.
        stripped = text.lstrip("\r\n")
        if stripped.startswith(cmd):
            text = stripped[len(cmd):]
        # Remove prompt occurrences
        text = text.replace(self.prompt.decode(), "")
        return text.strip()

    def _write_log(self, direction: str, data: bytes):
        if self._log:
            ts = datetime.datetime.now().strftime("%H:%M:%S.%f")
            prefix = f"[{ts}] {direction}: ".encode()
            self._log.write(prefix + data + b"\n")
            self._log.flush()
