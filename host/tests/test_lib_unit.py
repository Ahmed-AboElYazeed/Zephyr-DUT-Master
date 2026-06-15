# tests/test_lib_unit.py
from unittest.mock import MagicMock, patch
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


with patch("serial.Serial"):
    from ZephyrShellLib import ZephyrShellLib

def make_lib(responses):
    """Build a lib instance whose serial port returns canned responses."""
    with patch("serial.Serial") as mock_serial:
        lib = ZephyrShellLib(port="/dev/null")
        # Queue responses: each call to _drain returns the next entry
        lib._t._ser.read = MagicMock(side_effect=responses)
    return lib

def test_adc_read_mv_parses_correctly():
    lib = ZephyrShellLib.__new__(ZephyrShellLib)
    # directly test _extract
    from ZephyrShellLib.transport import ShellTransport
    t = ShellTransport.__new__(ShellTransport)
    raw = b"tb adc read PA0\r\n1842 mV\r\nuart:~$ "
    assert t._extract(raw, "tb adc read PA0") == "1842 mV"

def test_error_raises():
    lib = ZephyrShellLib.__new__(ZephyrShellLib)
    lib._t = MagicMock()
    lib._t.run.return_value = "ERROR: unknown pin XY"
    with pytest.raises(RuntimeError, match="ERROR"):
        lib._run("tb gpio get XY")
