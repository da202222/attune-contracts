from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "contracts.py"

spec = importlib.util.spec_from_file_location("attune_contracts_tool", SCRIPT)
assert spec is not None and spec.loader is not None
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)


class ContractKernelTest(unittest.TestCase):
    def test_registry_invariants_hold(self) -> None:
        registry = contracts.validate_registry()
        self.assertEqual(20, len(registry["capabilities"]))
        self.assertFalse(registry["authority_model"]["registry_grants_runtime_authority"])
        writes = [row for row in registry["capabilities"] if row["side_effect"] == "BOUNDED_WRITE"]
        self.assertTrue(writes)
        self.assertTrue(all(row["idempotency_required"] for row in writes))

    def test_target_ref_makes_router_line_parent_explicit(self) -> None:
        contracts.validate_target_ref(
            {
                "schema_version": 1,
                "kind": "router_line",
                "id": "33333333-3333-4333-8333-333333333333",
                "parent_id": "55555555-5555-4555-8555-555555555555",
            }
        )
        with self.assertRaises(contracts.ContractError):
            contracts.validate_target_ref(
                {
                    "schema_version": 1,
                    "kind": "router_line",
                    "id": "33333333-3333-4333-8333-333333333333",
                    "parent_id": None,
                }
            )

    def test_target_ref_rejects_legacy_alias_shape(self) -> None:
        with self.assertRaises(contracts.ContractError):
            contracts.validate_target_ref(
                {
                    "schema_version": 1,
                    "kind": "router_line",
                    "id": "33333333-3333-4333-8333-333333333333",
                    "parent_id": "55555555-5555-4555-8555-555555555555",
                    "line_id": "33333333-3333-4333-8333-333333333333",
                }
            )

    def test_duplicate_capability_fails_closed(self) -> None:
        registry = contracts.validate_registry()
        invalid = copy.deepcopy(registry)
        invalid["capabilities"].append(copy.deepcopy(invalid["capabilities"][0]))
        with self.assertRaisesRegex(contracts.ContractError, "duplicate capability"):
            contracts.validate_registry(invalid)

    def test_read_and_write_truth_rules_are_distinct(self) -> None:
        registry = contracts.validate_registry()
        for row in registry["capabilities"]:
            if row["side_effect"] == "READ_ONLY":
                self.assertEqual("READ_RESPONSE", row["completion_evidence"])
                self.assertFalse(row["idempotency_required"])
            else:
                self.assertNotEqual("READ_RESPONSE", row["completion_evidence"])
                self.assertTrue(row["idempotency_required"])

    def test_schema_roots_are_fail_closed(self) -> None:
        contracts.validate_schema_documents()
        for filename in contracts.WIRE_SCHEMAS:
            schema = json.loads((contracts.CONTRACTS / filename).read_text(encoding="utf-8"))
            self.assertFalse(schema["additionalProperties"], filename)
            self.assertEqual(set(schema["properties"]), set(schema["required"]), filename)

    def test_generated_bindings_are_deterministic(self) -> None:
        registry = contracts.validate_registry()
        for path, expected in contracts.rendered_files(registry).items():
            self.assertEqual(expected, path.read_text(encoding="utf-8"), str(path))

    def test_cli_check_generated_is_stdlib_only(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "check-generated"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertIn("PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
