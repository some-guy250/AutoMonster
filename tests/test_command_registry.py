"""Behavioral tests for the GUI command registry (no display required)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.command_registry import COMMANDS, PROGRESS_COMMANDS, CommandSpec, get_spec  # noqa: E402


class _FakeController:
    """Every attribute is a callable that records the call and returns a sentinel."""

    SENTINEL = object()

    def __init__(self) -> None:
        self.calls = []

    def __getattr__(self, name: str):
        def _method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return _FakeController.SENTINEL

        return _method


class _FakeProgress:
    def __call__(self, value) -> None:
        return None


def _sample_params(spec: CommandSpec) -> dict:
    """Build a call from each spec's declared parameter defaults."""
    return {name: defn.get("default") for name, defn in spec.params.items()}


class TestCommandRegistry(unittest.TestCase):
    def test_every_spec_is_well_formed(self) -> None:
        self.assertGreater(len(COMMANDS), 0)
        for name, spec in COMMANDS.items():
            self.assertIsInstance(spec, CommandSpec)
            self.assertEqual(spec.name, name)
            self.assertIsInstance(spec.params, dict)
            self.assertTrue(callable(spec.run), f"{name}: run is not callable")

    def test_progress_commands_are_subset(self) -> None:
        for name in PROGRESS_COMMANDS:
            self.assertIn(name, COMMANDS)

    def test_get_spec_known_and_unknown(self) -> None:
        self.assertIs(get_spec("PVP"), COMMANDS["PVP"])
        with self.assertRaises(ValueError):
            get_spec("Does Not Exist")

    def test_every_run_executes_with_default_params(self) -> None:
        for name, spec in COMMANDS.items():
            with self.subTest(command=name):
                ctrl = _FakeController()
                spec.run(ctrl, _FakeProgress(), **_sample_params(spec))
                self.assertEqual(
                    len(ctrl.calls), 1, f"{name}: expected exactly one controller call"
                )


if __name__ == "__main__":
    unittest.main()
