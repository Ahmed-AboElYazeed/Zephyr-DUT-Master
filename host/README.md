# Testbench Host — Robot Framework package

Complete host-side package: the `ZephyrShellLib` Robot Framework
library, all test suites (Stages 1-19), reusable keyword patterns,
fixture support, and unit tests. Pair with the firmware side
(`app/`) covered in the implementation plan.

## Layout

```
host/
├── ZephyrShellLib/
│   ├── __init__.py            <- the Robot Framework library class
│   ├── transport.py           <- serial send/receive/prompt parsing/logging
│   ├── peripheral_keywords.py <- GPIO/ADC/SPI/UART/PWM keywords (Stage 8)
│   ├── motorsim_keywords.py   <- DC motor plant simulation keywords (Stage 19)
│   └── fixture_loader.py      <- YAML wiring descriptor + conflict check (Stage 15)
│
├── fixture/
│   └── sensor_board_fixture.yaml
│
├── tests/
│   ├── resources/
│   │   ├── testbench.resource     <- connection setup, shared by all suites
│   │   ├── patterns_gpio.resource
│   │   ├── patterns_uart.resource
│   │   └── patterns_power.resource
│   ├── gpio_tests.robot
│   ├── adc_tests.robot
│   ├── spi_tests.robot
│   ├── uart_tests.robot
│   ├── pwm_tests.robot
│   ├── motorsim_tests.robot
│   └── soak_tests.robot
│
├── tests_unit/
│   └── test_lib_unit.py       <- pure-Python, no hardware required
│
├── standalone_monitor/
│   └── motorsim_monitor_wayland.py   <- live plotting, independent of Robot Framework
│
├── requirements.txt
├── Makefile
└── README.md   (this file)
```

## Setup

```bash
cd host
pip install -r requirements.txt
```

## Running unit tests (no hardware)

```bash
make unit-test
```

## Running hardware tests

```bash
# All suites except soak
make test PORT=/dev/ttyUSB0

# A single suite
make test-gpio PORT=/dev/ttyUSB0
make test-motorsim PORT=/dev/ttyUSB0 SOURCE=adc PIN=PA0
make test-motorsim PORT=/dev/ttyUSB0 SOURCE=pwm PIN=PA1

# Soak tests (slow, run separately / overnight)
make test-soak PORT=/dev/ttyUSB0
```

Or call `robot` directly for full control:

```bash
robot --outputdir results \
      --variable PORT:/dev/ttyUSB0 \
      --variable INPUT_SOURCE:adc \
      --variable INPUT_PIN:PA0 \
      tests/motorsim_tests.robot
```

## Using a fixture file instead of raw port/pins

```robot
*** Settings ***
Library    ZephyrShellLib    fixture=fixture/sensor_board_fixture.yaml
```

The fixture supplies `testbench_port` and lets keywords look up pins
by logical signal name via `Get Fixture Pin    reset` instead of
hardcoding `PB3` throughout your test suite.

## Standalone live plotting (no Robot Framework)

```bash
python3 standalone_monitor/motorsim_monitor_wayland.py \
    --port /dev/ttyUSB0 --source adc --pin PA0
```

See `standalone_monitor/FIRMWARE_FIX_README.txt` if you haven't
already applied the direct-UART-write fix to `tb_motorsim.c` (needed
for streaming to work reliably).

## Key design notes

- **Retries & locking**: every keyword goes through `ZephyrShellLib._run()`,
  which retries once on timeout and holds a thread lock, so this library
  is safe to use with `pabot` parallel execution.
- **`ERROR:` responses** from any `tb ...` shell command are automatically
  converted into a Robot Framework `RuntimeError`, which Robot reports as
  a clean test FAIL with the firmware's error message.
- **UART logging**: pass `logdir=results/uart_logs` to the library import
  to get a timestamped raw TX/RX log per run, useful for post-mortem
  debugging of flaky hardware tests.
