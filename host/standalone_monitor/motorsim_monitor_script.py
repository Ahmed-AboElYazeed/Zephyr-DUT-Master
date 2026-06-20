#!/usr/bin/env python3
"""
motorsim_monitor_script.py  -- FIXED VERSION

Standalone real-time monitor/plotter for the testbench DC motor simulation.
"""

import argparse
import sys
import time
import threading
import collections
import signal
import os

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation


PROMPT = b"blackpill:~$ "


# ---------------------------------------------------------------------------
# Shell transport
# ---------------------------------------------------------------------------

class ShellSession:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 5.0):
        self.ser = serial.Serial(port, baud, timeout=0.05)
        time.sleep(0.5)
        self.ser.reset_input_buffer()
        self._default_timeout = timeout

    def run(self, cmd: str, timeout: float = None) -> str:
        t = timeout or self._default_timeout
        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\r\n").encode())
        buf = b""
        deadline = time.monotonic() + t
        while time.monotonic() < deadline:
            chunk = self.ser.read(256)
            if chunk:
                buf += chunk
            if PROMPT in buf:
                text = buf.decode(errors="replace")
                # Remove echoed command
                if cmd in text:
                    text = text[text.index(cmd) + len(cmd):]
                # Remove prompt
                text = text.replace("blackpill:~$ ", "").strip()
                text = text.replace("uart:~$ ", "").strip()
                if text.startswith("ERROR:"):
                    raise RuntimeError(f"Testbench error: {text}")
                return text
        raise TimeoutError(f"No prompt after {t}s for command: {cmd!r}")

    def close(self):
        if self.ser.is_open:
            self.ser.close()


# ---------------------------------------------------------------------------
# Line parser
# ---------------------------------------------------------------------------

def parse_msim_line(line: str):
    """Parse 'MSIM,t_ms,voltage_v,speed_radps,current_a' -> dict or None."""
    line = line.strip()
    if not line.startswith("MSIM,"):
        return None
    parts = line.split(",")
    if len(parts) != 5:
        return None
    try:
        return {
            "t_ms": int(parts[1]),
            "voltage_v": float(parts[2]),
            "speed_radps": float(parts[3]),
            "current_a": float(parts[4]),
        }
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Background reader thread
# ---------------------------------------------------------------------------

class StreamReader(threading.Thread):
    def __init__(self, ser: serial.Serial, maxlen: int = 5000):
        super().__init__(daemon=True)
        self.ser = ser
        self.samples = collections.deque(maxlen=maxlen)
        self._stop_event = threading.Event()
        self._buf = b""
        self.lines_received = 0
        self.parse_errors = 0

    def run(self):
        while not self._stop_event.is_set():
            try:
                chunk = self.ser.read(256)
            except serial.SerialException:
                break
            if not chunk:
                continue
            self._buf += chunk
            while b"\n" in self._buf:
                raw_line, self._buf = self._buf.split(b"\n", 1)
                # Strip \r if present
                text = raw_line.decode(errors="ignore").strip()
                sample = parse_msim_line(text)
                if sample:
                    self.samples.append(sample)
                    self.lines_received += 1
                elif text and not text.startswith("blackpill:~$") and not text.startswith("uart:~$"):
                    self.parse_errors += 1

    def stop(self):
        self._stop_event.set()


# ---------------------------------------------------------------------------
# Live plot
# ---------------------------------------------------------------------------

def run_live_plot(reader: StreamReader, window_s: float):
    fig, (ax_v, ax_w, ax_i) = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle("DC Motor Simulation — Live Monitor")

    line_v, = ax_v.plot([], [], color="#3b82f6", label="Voltage command (V)")
    line_w, = ax_w.plot([], [], color="#10b981", label="Speed (rad/s)")
    line_i, = ax_i.plot([], [], color="#f97316", label="Current (A)")

    for ax, lbl in ((ax_v, "Voltage (V)"), (ax_w, "Speed (rad/s)"), (ax_i, "Current (A)")):
        ax.set_ylabel(lbl)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left", fontsize=8)
    ax_i.set_xlabel("time (s)")

    status_text = fig.text(0.5, 0.965, "", ha="center", fontsize=9, color="gray")

    def update(_frame):
        samples = list(reader.samples)
        if not samples:
            return line_v, line_w, line_i

        t0 = samples[0]["t_ms"]
        t_now = samples[-1]["t_ms"]

        # Trim to the requested rolling window
        cutoff = t_now - window_s * 1000
        visible = [s for s in samples if s["t_ms"] >= cutoff]

        t = [(s["t_ms"] - t0) / 1000.0 for s in visible]
        v = [s["voltage_v"] for s in visible]
        w = [s["speed_radps"] for s in visible]
        i = [s["current_a"] for s in visible]

        line_v.set_data(t, v)
        line_w.set_data(t, w)
        line_i.set_data(t, i)

        for ax, data in ((ax_v, v), (ax_w, w), (ax_i, i)):
            ax.relim()
            ax.autoscale_view()
        if t:
            for ax in (ax_v, ax_w, ax_i):
                ax.set_xlim(max(0, t[-1] - window_s), max(window_s, t[-1]))

        status_text.set_text(
            f"samples={reader.lines_received}  "
            f"latest: V={v[-1]:.3f}V  speed={w[-1]:.3f}rad/s  I={i[-1]:.3f}A"
            if v else ""
        )
        return line_v, line_w, line_i

    ani = animation.FuncAnimation(fig, update, interval=200, cache_frame_data=False)
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    plt.show()
    return ani


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Live monitor/plotter for the Zephyr testbench DC motor simulation."
    )
    parser.add_argument("--port", required=True, help="Serial port, e.g. /dev/ttyUSB0 or COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--source", choices=["adc", "pwm"], required=True,
        help="Where the testbench reads the DUT's voltage command from"
    )
    parser.add_argument(
        "--pin", required=True,
        help="Physical pin to read (e.g. PA0 for adc, PA1 for pwm capture)"
    )
    parser.add_argument("--vmax-mv", type=int, default=3300,
                        help="mV that maps to 100%% PWM duty / full-scale ADC")
    parser.add_argument("--window", type=float, default=20.0,
                        help="Rolling plot window in seconds (default: 20)")
    parser.add_argument("--csv", default=None,
                        help="Optional: also write all samples to this CSV file")
    args = parser.parse_args()

    print(f"Connecting to {args.port} @ {args.baud}...")
    session = ShellSession(args.port, args.baud)

    print("Checking testbench...")
    try:
        session.run("tb motorsim get", timeout=2.0)
    except RuntimeError as e:
        print(f"ERROR: testbench did not respond. Got: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting motor simulation: source={args.source} pin={args.pin} vmax_mv={args.vmax_mv}")
    try:
        session.run(f"tb motorsim start {args.source} {args.pin} {args.vmax_mv}")
    except RuntimeError as e:
        print(f"ERROR starting simulation: {e}", file=sys.stderr)
        sys.exit(1)

    print("Enabling stream...")
    session.run("tb motorsim stream on")

    reader = StreamReader(session.ser)
    reader.start()

    csv_file = None
    if args.csv:
        # Line buffering + explicit flush for immediate disk writes
        csv_file = open(args.csv, "w", buffering=1)
        csv_file.write("t_ms,voltage_v,speed_radps,current_a\n")
        print(f"Logging samples to {args.csv}")

        def csv_writer_loop():
            written = 0
            while not reader._stop_event.is_set():
                samples = list(reader.samples)
                for s in samples[written:]:
                    line = f"{s['t_ms']},{s['voltage_v']},{s['speed_radps']},{s['current_a']}\n"
                    csv_file.write(line)
                    csv_file.flush()
                    os.fsync(csv_file.fileno())
                written = len(samples)
                time.sleep(0.2)

        threading.Thread(target=csv_writer_loop, daemon=True).start()

    def cleanup(*_):
        print("\nStopping simulation and closing port...")
        reader.stop()
        try:
            session.run("tb motorsim stream off", timeout=2.0)
            session.run("tb motorsim stop", timeout=2.0)
        except Exception as e:
            print(f"(cleanup warning: {e})")
        if csv_file:
            csv_file.close()
        session.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    print(f"Plotting live (rolling {args.window}s window). Close the plot window or Ctrl+C to stop.")
    try:
        run_live_plot(reader, args.window)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
