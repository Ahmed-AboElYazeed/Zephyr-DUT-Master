import serial
import time

PROMPT = "blackpill:~$ "

class ShellTransport:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 5.0):
        self._ser = serial.Serial(port, baud, timeout=0.05)
        self._default_timeout = timeout
        time.sleep(0.5)
        self._ser.reset_input_buffer()
        # Flush any stale prompt
        self._ser.write(b"\r\n")
        self._drain(timeout=1.0)

    def run(self, cmd: str, timeout: float = None) -> str:
        t = timeout or self._default_timeout
        self._ser.reset_input_buffer()
        self._ser.write((cmd + "\r\n").encode())
        raw = self._drain(timeout=t)
        return self._extract(raw, cmd)

    def _drain(self, timeout: float) -> bytes:
        buf = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = self._ser.read(256)
            if chunk:
                buf += chunk
            if PROMPT.encode() in buf:
                return buf
        raise TimeoutError(
            f"No shell prompt after {timeout}s. Buffer: {buf!r}"
        )

    def _extract(self, raw: bytes, cmd: str) -> str:
        text = raw.decode(errors="replace")
        # Remove echoed command
        if cmd in text:
            text = text[text.index(cmd) + len(cmd):]
        # Remove prompt
        text = text.replace(PROMPT, "")
        # Clean up
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines)

    def close(self):
        if self._ser.is_open:
            self._ser.close()