"""
fixture_loader.py

Loads a per-DUT wiring descriptor (YAML) and checks for pin conflicts
before any test runs. See Stage 15 of the implementation plan.
"""

from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise ImportError(
        "fixture_loader requires PyYAML. Install with: pip install pyyaml"
    ) from e


class FixtureLoader:
    def __init__(self, fixture_path: str):
        self.path = Path(fixture_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Fixture file not found: {self.path}")
        with open(self.path) as f:
            self._data = yaml.safe_load(f)
        self._check_conflicts()

    def _check_conflicts(self):
        """Detect duplicate TB pin assignments -- fail fast before any test."""
        seen = {}
        for conn in self._data.get("connections", []):
            pin = conn["tb_pin"]
            if pin in seen:
                raise ValueError(
                    f"Pin conflict in {self.path.name}: "
                    f"'{pin}' assigned to both '{seen[pin]}' and '{conn['signal']}'"
                )
            seen[pin] = conn["signal"]

    def get_pin(self, signal: str) -> str:
        """Look up the testbench pin for a named signal."""
        for conn in self._data.get("connections", []):
            if conn["signal"] == signal:
                return conn["tb_pin"]
        raise KeyError(f"Signal '{signal}' not found in fixture {self.path.name}")

    def get_port(self) -> str:
        return self._data.get("testbench_port")

    def get_capability(self, name: str, default=False):
        return self._data.get("capabilities", {}).get(name, default)

    def summary(self) -> str:
        lines = [
            f"Fixture: {self._data.get('dut_name', '?')} "
            f"rev {self._data.get('dut_revision', '?')}"
        ]
        for c in self._data.get("connections", []):
            lines.append(f"  {c['tb_pin']:6s} <-> {c['dut_pin']:14s} ({c['signal']})")
        return "\n".join(lines)
