"""
test_lib_unit.py

Pure-Python unit tests for ZephyrShellLib -- no hardware required.
Run with: pytest host/tests_unit/
"""

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_serial():
    with patch("serial.Serial") as mock_cls:
        instance = MagicMock()
        instance.is_open = True
        mock_cls.return_value = instance
        yield instance


def test_extract_strips_echo_and_prompt():
    from ZephyrShellLib.transport import ShellTransport
    t = ShellTransport.__new__(ShellTransport)
    t.prompt = b"uart:~$ "
    raw = b"tb adc read PA0\r\n1842 mV\r\nuart:~$ "
    assert t._extract(raw, "tb adc read PA0") == "1842 mV"


def test_extract_handles_no_echo():
    from ZephyrShellLib.transport import ShellTransport
    t = ShellTransport.__new__(ShellTransport)
    t.prompt = b"uart:~$ "
    raw = b"OK\r\nuart:~$ "
    assert t._extract(raw, "tb gpio set PA5 1") == "OK"


def test_motorsim_parse_msim_line():
    from ZephyrShellLib.motorsim_keywords import MotorSimKeywords
    line = b"MSIM,1000,2.500,12.345,0.870"
    result = MotorSimKeywords._parse_msim_line(line)
    assert result == {
        "t_ms": 1000,
        "voltage_v": 2.5,
        "speed_radps": 12.345,
        "current_a": 0.870,
    }


def test_motorsim_parse_msim_line_rejects_garbage():
    from ZephyrShellLib.motorsim_keywords import MotorSimKeywords
    assert MotorSimKeywords._parse_msim_line(b"garbage line") is None
    assert MotorSimKeywords._parse_msim_line(b"MSIM,only,three,fields") is None
    assert MotorSimKeywords._parse_msim_line(b"MSIM,notanint,1.0,2.0,3.0") is None


def test_motorsim_get_parses_response():
    from ZephyrShellLib.motorsim_keywords import MotorSimKeywords

    class FakeLib(MotorSimKeywords):
        def _run(self, cmd, timeout=None):
            return "t_ms=2000 voltage_v=2.500 speed_radps=12.345 current_a=0.870"

    lib = FakeLib()
    result = lib.motorsim_get()
    assert result["t_ms"] == 2000
    assert result["voltage_v"] == 2.5
    assert result["speed_radps"] == 12.345
    assert result["current_a"] == 0.870


def test_motorsim_get_speed_rpm_conversion():
    from ZephyrShellLib.motorsim_keywords import MotorSimKeywords

    class FakeLib(MotorSimKeywords):
        def _run(self, cmd, timeout=None):
            return "t_ms=0 voltage_v=0.0 speed_radps=10.471975512 current_a=0.0"

    lib = FakeLib()
    rpm = lib.motorsim_get_speed_rpm()
    assert abs(rpm - 100.0) < 0.01  # 10.47 rad/s ~= 100 RPM


def test_run_raises_on_error_response():
    class FakeTransport:
        is_open = True
        raw_serial = MagicMock()

        def run(self, cmd, timeout=None):
            return "ERROR: unknown pin XY"

    from ZephyrShellLib import ZephyrShellLib
    lib = ZephyrShellLib.__new__(ZephyrShellLib)
    lib._t = FakeTransport()
    lib._lock = __import__("threading").Lock()
    lib._retries = 0

    with pytest.raises(RuntimeError, match="ERROR"):
        lib._run("tb gpio get XY")


def test_fixture_loader_detects_pin_conflict(tmp_path):
    from ZephyrShellLib.fixture_loader import FixtureLoader

    fixture_yaml = tmp_path / "bad_fixture.yaml"
    fixture_yaml.write_text("""
dut_name: test_dut
dut_revision: "1.0"
testbench_port: /dev/ttyUSB0
connections:
  - tb_pin: PA0
    dut_pin: SIG_A
    signal: signal_a
    direction: tb_out
  - tb_pin: PA0
    dut_pin: SIG_B
    signal: signal_b
    direction: tb_out
""")
    with pytest.raises(ValueError, match="Pin conflict"):
        FixtureLoader(str(fixture_yaml))


def test_fixture_loader_get_pin(tmp_path):
    from ZephyrShellLib.fixture_loader import FixtureLoader

    fixture_yaml = tmp_path / "good_fixture.yaml"
    fixture_yaml.write_text("""
dut_name: test_dut
dut_revision: "1.0"
testbench_port: /dev/ttyUSB0
connections:
  - tb_pin: PB3
    dut_pin: RESET_N
    signal: reset
    direction: tb_out
""")
    loader = FixtureLoader(str(fixture_yaml))
    assert loader.get_pin("reset") == "PB3"
    with pytest.raises(KeyError):
        loader.get_pin("nonexistent")
