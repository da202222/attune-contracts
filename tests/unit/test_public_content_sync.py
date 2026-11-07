"""Run the copied content-sync fixture guards under unittest."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_PATH = Path(__file__).with_name("test_content_sync_contract.py")


def _load():
    spec = importlib.util.spec_from_file_location("content_sync_contract", _PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicContentSyncTest(unittest.TestCase):
    def test_fixture_guards(self) -> None:
        module = _load()
        names = sorted(name for name in dir(module) if name.startswith("test_"))
        self.assertGreaterEqual(len(names), 7)
        for name in names:
            getattr(module, name)()


if __name__ == "__main__":
    unittest.main()
