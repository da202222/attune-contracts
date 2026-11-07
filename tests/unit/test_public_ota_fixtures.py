"""The published OTA protocol fixtures stay synthetic."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol" / "thingsboard"
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


class PublicOtaFixtureTest(unittest.TestCase):
    def test_schema_is_the_frozen_protocol(self) -> None:
        schema = json.loads((PROTOCOL / "ota_protocol.schema.json").read_text(encoding="utf-8"))
        self.assertEqual("attune.thingsboard.ota-protocol/v1", schema["$id"])
        rendered = json.dumps(schema)
        self.assertNotIn("://", rendered.replace("https://json-schema.org/draft/2020-12/schema", ""))

    def test_fixtures_use_only_synthetic_identifiers(self) -> None:
        for path in sorted((PROTOCOL / "testdata").glob("*.json")):
            body = json.loads(path.read_text(encoding="utf-8"))
            rendered = json.dumps(body)
            self.assertNotIn("://", rendered, path.name)
            self.assertNotIn("sha256:", rendered, path.name)
            for value in _walk(body):
                if isinstance(value, str) and UUID.fullmatch(value):
                    self.assertTrue(set(value.replace("-", "")) <= set("12345678"), value)


if __name__ == "__main__":
    unittest.main()
