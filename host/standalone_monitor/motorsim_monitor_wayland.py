#!/usr/bin/env python3
"""
motorsim_monitor_wayland.py — live on-screen plotting, Wayland-compatible.

Two changes from the previous "Agg" version:

1. DIAGNOSTIC LOGGING: every raw line read from the serial port is
   counted and the last few are kept, so when something goes wrong
   you can SEE what the firmware actually sent instead of guessing.
   Pass --debug to print every raw line as it arrives.

2. REAL LIVE PLOTTING: uses matplotlib's "QtAgg" backend (falls back
   to TkAgg if no Qt binding is installed) instead of "Agg". Agg is a
   headless, file-only backend -- it can never open a window, which is
   why the previous script only ever produced PNG files. QtAgg renders
   through Qt's native Wayland support and updates live on screen.

Install on Ubuntu 22.04 (Wayland session):
    pip install pyserial matplotlib PyQt5
    # or, if you prefer system packages:
    sudo apt install python3-pyqt5

Usage:
    python3 motorsim_monitor_wayland.py --port /dev/ttyUSB0 --source adc --pin PA0
    python3 motorsim_monitor_wayland.py --port /dev/ttyUSB0 --source pwm --pin PA1 --debug
"""

import argparse
import sys
import time
import threading
import collections
import signal
import os

import serial

import matplotlib

# --- Backend selection: try Qt first (best Wayland support), fall back
#     gracefully so the script still runs even if Qt bindings are missing.
_BACKEND_USED = None
for _candidate in ("QtAgg", "Qt5Agg", "TkAgg"):
    try:
        matplotlib.use(_candidate, force=True)
        _BACKEND_USED = _candidate
        break
    except Exception:
        continue

import matplotlib.pyplot as plt
import matplotlib.animation as animation


PROMPT = b"blackpill:~$ "


# ---------------------------------------------------------------------------
# Shell transport
# ---------------------------------------------------------------------------

class ShellSession:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 5.0, debug: bool = False):
        self.ser = serial.Serial(port, baud, timeout=0.05)
        self.debug = debug
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
                if self.debug:
                    print(f"[DEBUG run() raw] {chunk!r}", file=sys.stderr)
            if PROMPT in buf:
                text = buf.decode(errors="replace")
                if cmd in text:
                    text = text[text.index(cmd) + len(cmd):]
                text = text.replace("blackpill:~$ ", "").strip()
                text = text.replace("uart:~$ ", "").strip()
                if text.startswith("ERROR:"):
                    raise RuntimeError(f"Testbench error: {text}")
                return text
        raise TimeoutError(
            f"No prompt after {t}s for command: {cmd!r}. "
            f"Raw buffer received: {buf!r}"
        )

    def close(self):
        if self.ser.is_open:
            self.ser.close()


def parse_msim_line(line: str):
    """Parse MSIM line. Defensive against whitespace and missing fields."""
    line = line.strip()
    if not line.startswith("MSIM,"):
        return None
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 5:
        return None
    try:
        return {
            "t_ms": int(parts[1]),
            "voltage_v": float(parts[2]),
            "speed_radps": float(parts[3]),
            "current_a": float(parts[4]),
        }
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Background reader thread
# ---------------------------------------------------------------------------

class StreamReader(threading.Thread):
    def __init__(self, ser: serial.Serial, maxlen: int = 10000, debug: bool = False):
        super().__init__(daemon=True)
        self.ser = ser
        self.debug = debug
        self.samples = collections.deque(maxlen=maxlen)
        self._stop_event = threading.Event()
        self._buf = b""
        self.lines_received = 0
        self.parse_errors = 0
        self.raw_bytes_received = 0
        # Keep the last N raw (non-matching) lines for diagnostics --
        # this is what you print/inspect when samples stay at 0.
        self.last_unmatched_lines = collections.deque(maxlen=20)

    def run(self):
        while not self._stop_event.is_set():
            try:
                chunk = self.ser.read(256)
            except serial.SerialException:
                break
            if not chunk:
                continue
            self.raw_bytes_received += len(chunk)
            self._buf += chunk
            while b"\n" in self._buf:
                raw_line, self._buf = self._buf.split(b"\n", 1)
                text = raw_line.decode(errors="ignore").strip()
                if self.debug and text:
                    print(f"[DEBUG raw line] {text!r}", file=sys.stderr)
                sample = parse_msim_line(text)
                if sample:
                    self.samples.append(sample)
                    self.lines_received += 1
                elif text and not text.startswith("blackpill") and not text.startswith("uart"):
                    self.parse_errors += 1
                    self.last_unmatched_lines.append(text)

    def stop(self):
        self._stop_event.set()


# ---------------------------------------------------------------------------
# Live on-screen plot (QtAgg/TkAgg — actually opens a window, unlike Agg)
# ---------------------------------------------------------------------------

def run_live_plot(reader: StreamReader, window_s: float):
    fig, (ax_v, ax_w, ax_i) = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle(f"DC Motor Simulation — Live Monitor  [backend: {_BACKEND_USED}]")

    line_v, = ax_v.plot([], [], color="#3b82f6", label="Voltage command (V)")
    line_w, = ax_w.plot([], [], color="#10b981", label="Speed (rad/s)")
    line_i, = ax_i.plot([], [], color="#f97316", label="Current (A)")

    for ax, lbl in ((ax_v, "Voltage (V)"), (ax_w, "Speed (rad/s)"), (ax_i, "Current (A)")):
        ax.set_ylabel(lbl)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left", fontsize=8)
    ax_i.set_xlabel("time (s)")

    status_text = fig.text(0.5, 0.965, "waiting for data...", ha="center", fontsize=9, color="gray")

    def update(_frame):
        samples = list(reader.samples)
        if not samples:
            status_text.set_text(
                f"waiting for data...  raw_bytes={reader.raw_bytes_received}  "
                f"parse_errors={reader.parse_errors}"
            )
            return line_v, line_w, line_i

        t0 = samples[0]["t_ms"]
        t_now = samples[-1]["t_ms"]
        cutoff = t_now - window_s * 1000
        visible = [s for s in samples if s["t_ms"] >= cutoff]

        t = [(s["t_ms"] - t0) / 1000.0 for s in visible]
        v = [s["voltage_v"] for s in visible]
        w = [s["speed_radps"] for s in visible]
        i = [s["current_a"] for s in visible]

        line_v.set_data(t, v)
        line_w.set_data(t, w)
        line_i.set_data(t, i)

        for ax in (ax_v, ax_w, ax_i):
            ax.relim()
            ax.autoscale_view()
        if t:
            for ax in (ax_v, ax_w, ax_i):
                ax.set_xlim(max(0, t[-1] - window_s), max(window_s, t[-1]))

        status_text.set_text(
            f"samples={reader.lines_received}  parse_errors={reader.parse_errors}  "
            f"latest: V={v[-1]:.3f}V  speed={w[-1]:.3f}rad/s  I={i[-1]:.3f}A"
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
        description="Live on-screen monitor/plotter for the Zephyr testbench DC motor simulation (Wayland-compatible)."
    )
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--source", choices=["adc", "pwm"], required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--vmax-mv", type=int, default=3300)
    parser.add_argument("--window", type=float, default=20.0, help="rolling plot window, seconds")
    parser.add_argument("--csv", default=None, help="optional: also log all samples to this CSV")
    parser.add_argument("--debug", action="store_true",
                        help="print every raw line received over serial (use this to diagnose 'samples=0')")
    args = parser.parse_args()

    print(f"[backend] matplotlib using: {_BACKEND_USED}")
    if _BACKEND_USED == "TkAgg":
        print("[backend] Qt not found, falling back to TkAgg. "
              "For best Wayland support: pip install PyQt5", file=sys.stderr)
    if _BACKEND_USED is None:
        print("ERROR: no interactive matplotlib backend available. "
              "Install one with: pip install PyQt5", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to {args.port} @ {args.baud}...")
    session = ShellSession(args.port, args.baud, debug=args.debug)

    print("Checking testbench...")
    try:
        session.run("tb ping", timeout=2.0)
    except (RuntimeError, TimeoutError) as e:
        print(f"ERROR: testbench not responding to 'tb ping': {e}", file=sys.stderr)
        print("Hint: verify --port and that the firmware is flashed and booted.", file=sys.stderr)
        sys.exit(1)

    # If a sim is already running from a previous crashed run, stop it
    # first so 'start' doesn't fail with ERROR: simulation already running.
    try:
        session.run("tb motorsim stop", timeout=2.0)
        print("(stopped a simulation that was already running)")
    except RuntimeError:
        pass  # wasn't running, that's fine

    print(f"Starting motor simulation: source={args.source} pin={args.pin} vmax_mv={args.vmax_mv}")
    try:
        session.run(f"tb motorsim start {args.source} {args.pin} {args.vmax_mv}")
    except RuntimeError as e:
        print(f"ERROR starting simulation: {e}", file=sys.stderr)
        sys.exit(1)

    print("Enabling stream...")
    session.run("tb motorsim stream on")

    reader = StreamReader(session.ser, debug=args.debug)
    reader.start()

    csv_file = None
    if args.csv:
        csv_file = open(args.csv, "w", buffering=1)
        csv_file.write("t_ms,voltage_v,speed_radps,current_a\n")

        def csv_writer_loop():
            written = 0
            while not reader._stop_event.is_set():
                samples = list(reader.samples)
                for s in samples[written:]:
                    csv_file.write(f"{s['t_ms']},{s['voltage_v']},{s['speed_radps']},{s['current_a']}\n")
                written = len(samples)
                time.sleep(0.5)

        threading.Thread(target=csv_writer_loop, daemon=True).start()
        print(f"Logging samples to {args.csv}")

    # Watchdog: if after 3 seconds we still have zero samples, print
    # diagnostics so the failure mode is immediately visible instead of
    # silently sitting at samples=0 forever.
    def diagnostic_watchdog():
        time.sleep(3.0)
        if reader.lines_received == 0:
            print("\n[DIAGNOSTIC] No MSIM samples received after 3 seconds.", file=sys.stderr)
            print(f"[DIAGNOSTIC] raw_bytes_received={reader.raw_bytes_received}", file=sys.stderr)
            print(f"[DIAGNOSTIC] parse_errors={reader.parse_errors}", file=sys.stderr)
            if reader.last_unmatched_lines:
                print("[DIAGNOSTIC] Last unmatched lines received:", file=sys.stderr)
                for line in reader.last_unmatched_lines:
                    print(f"    {line!r}", file=sys.stderr)
            else:
                print("[DIAGNOSTIC] No lines at all were received -- check wiring/port, "
                      "or the firmware may not be sending on this UART.", file=sys.stderr)
            print("[DIAGNOSTIC] Re-run with --debug to see every raw line live.\n", file=sys.stderr)

    threading.Thread(target=diagnostic_watchdog, daemon=True).start()

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
        print(f"Total samples: {reader.lines_received}  parse_errors: {reader.parse_errors}")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    print(f"Plotting live (rolling {args.window}s window). Close the plot window or Ctrl+C to stop.")
    try:
        run_live_plot(reader, args.window)
    finally:
        cleanup()


if __name__ == "__main__":
    main()