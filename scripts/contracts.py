#!/usr/bin/env python3
"""Validate and generate Attune cross-platform contract constants.

The kernel is deliberately stdlib-only. Product-specific build systems can run
the same gate before installing Android, Server, Web, or Windows dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "packages" / "contracts"
REGISTRY_PATH = CONTRACTS / "capability-registry.v1.json"
TARGET_SCHEMA_PATH = CONTRACTS / "target-ref.v1.schema.json"
GENERATED = CONTRACTS / "generated"

WIRE_SCHEMAS = (
    "capability-command.v1.schema.json",
    "capability-result.v1.schema.json",
    "capability-advertisement.v1.schema.json",
    "capability-descriptor.v1.schema.json",
    "device-capability-discovery.v1.schema.json",
    "device-truth-event.v1.schema.json",
    "cross-endpoint-context.v1.schema.json",
    "target-ref.v1.schema.json",
    "capability-registry.v1.schema.json",
)

KOTLIN_UDC_PATH = (
    ROOT
    / "android"
    / "car-core"
    / "src"
    / "main"
    / "kotlin"
    / "ai"
    / "bondings"
    / "callpilot"
    / "car"
    / "UdcContracts.kt"
)
KOTLIN_SCHEMA_BINDINGS = {
    "capability-command.v1.schema.json": "CapabilityCommandV1",
    "capability-result.v1.schema.json": "CapabilityResultV1",
    "capability-advertisement.v1.schema.json": "CapabilityAdvertisementV1",
    "capability-descriptor.v1.schema.json": "CapabilityDescriptorV1",
    "device-capability-discovery.v1.schema.json": "DeviceCapabilityDiscoveryV1",
    "device-truth-event.v1.schema.json": "DeviceTruthEventV1",
    "cross-endpoint-context.v1.schema.json": "CrossEndpointContextV1",
}

CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9_-]+)+$")
ACTION_RE = re.compile(r"^device\.[a-z][a-z0-9_.-]*$")
CLASSES = {"READ", "INTERACTION", "OPERATE", "CONFIG", "UPDATE", "PRIVILEGED"}
DATA_CLASSES = {
    "NON_SENSITIVE",
    "DEVICE_METADATA",
    "PERSONAL_DATA",
    "LOCATION",
    "COMMUNICATION_CONTENT",
}
SIDE_EFFECTS = {"READ_ONLY", "BOUNDED_WRITE"}
COMPLETION_EVIDENCE = {"READ_RESPONSE", "DEVICE_TRUTH", "TERMINAL_ACK"}


class ContractError(ValueError):
    """Raised when a canonical contract violates a kernel invariant."""


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ContractError(f"{path}: expected object")
    return value


def validate_schema_documents() -> None:
    seen_ids: set[str] = set()
    for filename in WIRE_SCHEMAS:
        path = CONTRACTS / filename
        schema = _load(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ContractError(f"{filename}: must use JSON Schema draft 2020-12")
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ContractError(f"{filename}: missing $id")
        if schema_id in seen_ids:
            raise ContractError(f"{filename}: duplicate $id {schema_id}")
        seen_ids.add(schema_id)
        if schema.get("type") != "object":
            raise ContractError(f"{filename}: root type must be object")
        if schema.get("additionalProperties") is not False:
            raise ContractError(f"{filename}: root must fail closed on unknown fields")
        required = schema.get("required")
        properties = schema.get("properties")
        if not isinstance(required, list) or not isinstance(properties, dict):
            raise ContractError(f"{filename}: required/properties must be declared")
        if set(required) != set(properties):
            raise ContractError(f"{filename}: every root property must be required in v1")


def target_kinds() -> tuple[str, ...]:
    schema = _load(TARGET_SCHEMA_PATH)
    try:
        kinds = schema["properties"]["kind"]["enum"]
    except (KeyError, TypeError) as exc:
        raise ContractError("target-ref schema must define properties.kind.enum") from exc
    if not isinstance(kinds, list) or not kinds or len(kinds) != len(set(kinds)):
        raise ContractError("target-ref kinds must be a non-empty unique list")
    return tuple(str(kind) for kind in kinds)


def validate_target_ref(value: dict[str, Any]) -> None:
    expected = {"schema_version", "kind", "id", "parent_id"}
    if set(value) != expected:
        raise ContractError(f"TargetRef keys must be exactly {sorted(expected)}")
    if value["schema_version"] != 1:
        raise ContractError("TargetRef schema_version must be 1")
    kinds = set(target_kinds())
    kind = value["kind"]
    if kind not in kinds:
        raise ContractError(f"unknown TargetRef kind: {kind!r}")
    try:
        uuid.UUID(str(value["id"]))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ContractError("TargetRef id must be a UUID") from exc

    parent_id = value["parent_id"]
    if kind == "router_line":
        if parent_id is None:
            raise ContractError("router_line TargetRef requires parent_id")
        try:
            uuid.UUID(str(parent_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ContractError("router_line parent_id must be a UUID") from exc
        if str(parent_id) == str(value["id"]):
            raise ContractError("router_line parent_id must differ from id")
    elif parent_id is not None:
        raise ContractError(f"{kind} TargetRef must use parent_id=null")


def validate_registry(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or _load(REGISTRY_PATH)
    if registry.get("schema") != "attune.contracts.capability-registry/v1":
        raise ContractError("unexpected capability registry schema")
    if registry.get("registry_version") != 1:
        raise ContractError("capability registry version must be 1")

    authority = registry.get("authority_model")
    if authority != {
        "policy_source": "server_definition",
        "availability_source": "edge_advertisement",
        "registry_grants_runtime_authority": False,
    }:
        raise ContractError("authority_model must preserve Server policy + Edge availability split")

    actions = registry.get("workspace_actions")
    if not isinstance(actions, list) or not actions or len(actions) != len(set(actions)):
        raise ContractError("workspace_actions must be a non-empty unique list")
    if any(not isinstance(action, str) or not ACTION_RE.fullmatch(action) for action in actions):
        raise ContractError("workspace_actions contains an invalid action")

    kinds = set(target_kinds())
    capabilities = registry.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ContractError("capabilities must be a non-empty list")

    names: set[str] = set()
    required = {
        "name",
        "version",
        "target_kind",
        "class",
        "required_action",
        "data_class",
        "side_effect",
        "idempotency_required",
        "completion_evidence",
    }
    for row in capabilities:
        if not isinstance(row, dict):
            raise ContractError("each capability must be an object")
        if set(row) != required:
            raise ContractError(
                f"{row.get('name', '<unknown>')}: keys must be exactly {sorted(required)}"
            )
        name = row["name"]
        if not isinstance(name, str) or len(name) > 160 or not CAPABILITY_RE.fullmatch(name):
            raise ContractError(f"invalid capability name: {name!r}")
        if name in names:
            raise ContractError(f"duplicate capability name: {name}")
        names.add(name)
        if row["version"] != 1:
            raise ContractError(f"{name}: v1 registry requires version=1")
        if row["target_kind"] not in kinds:
            raise ContractError(f"{name}: unknown target_kind {row['target_kind']!r}")
        if row["class"] not in CLASSES:
            raise ContractError(f"{name}: invalid class")
        if row["required_action"] not in actions:
            raise ContractError(f"{name}: required_action must be declared in workspace_actions")
        if row["data_class"] not in DATA_CLASSES:
            raise ContractError(f"{name}: invalid data_class")
        if row["side_effect"] not in SIDE_EFFECTS:
            raise ContractError(f"{name}: invalid side_effect")
        if not isinstance(row["idempotency_required"], bool):
            raise ContractError(f"{name}: idempotency_required must be boolean")
        if row["completion_evidence"] not in COMPLETION_EVIDENCE:
            raise ContractError(f"{name}: invalid completion_evidence")

        if row["side_effect"] == "READ_ONLY":
            if row["idempotency_required"]:
                raise ContractError(f"{name}: READ_ONLY capability must not require idempotency")
            if row["completion_evidence"] != "READ_RESPONSE":
                raise ContractError(f"{name}: READ_ONLY capability must use READ_RESPONSE")
            if row["class"] != "READ":
                raise ContractError(f"{name}: READ_ONLY capability must use class READ")
        else:
            if not row["idempotency_required"]:
                raise ContractError(f"{name}: BOUNDED_WRITE must require idempotency")
            if row["completion_evidence"] == "READ_RESPONSE":
                raise ContractError(f"{name}: BOUNDED_WRITE cannot complete from READ_RESPONSE")
            if row["class"] == "READ":
                raise ContractError(f"{name}: BOUNDED_WRITE cannot use class READ")

        if name.startswith("router.telephony.") and row["target_kind"] != "router_line":
            raise ContractError(f"{name}: router telephony capabilities must target router_line")
        if row["target_kind"] == "router_line" and not name.startswith("router.telephony."):
            raise ContractError(f"{name}: v1 router_line surface is telephony-only")

    return registry


def _kotlin_parameter_block(source: str, class_name: str) -> str:
    marker = f"data class {class_name}("
    start = source.find(marker)
    if start < 0:
        raise ContractError(f"Kotlin UDC binding missing {class_name}")
    open_index = start + len(marker) - 1
    depth = 0
    for index in range(open_index, len(source)):
        char = source[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[open_index + 1 : index]
    raise ContractError(f"Kotlin UDC binding has unterminated {class_name} parameters")


def _kotlin_wire_fields(source: str, class_name: str) -> set[str]:
    block = _kotlin_parameter_block(source, class_name)
    pattern = re.compile(
        r'(?:@SerialName\("(?P<serial>[^"]+)"\)\s*)?'
        r"val\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:"
    )
    fields = {
        match.group("serial") or match.group("name")
        for match in pattern.finditer(block)
    }
    if not fields:
        raise ContractError(f"Kotlin UDC binding exposes no fields for {class_name}")
    return fields


def validate_kotlin_udc_binding() -> None:
    if not KOTLIN_UDC_PATH.exists():
        raise ContractError(f"missing Kotlin UDC binding: {KOTLIN_UDC_PATH.relative_to(ROOT)}")
    source = KOTLIN_UDC_PATH.read_text(encoding="utf-8")
    for schema_name, class_name in KOTLIN_SCHEMA_BINDINGS.items():
        schema = _load(CONTRACTS / schema_name)
        expected = set(schema["properties"])
        actual = _kotlin_wire_fields(source, class_name)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ContractError(
                f"{class_name} drift vs {schema_name}: missing={missing}, extra={extra}"
            )


def _const_name(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def _sorted_capabilities(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(registry["capabilities"], key=lambda row: row["name"])


def render_python(registry: dict[str, Any]) -> str:
    capabilities = _sorted_capabilities(registry)
    kinds = target_kinds()
    lines = [
        '"""Generated from packages/contracts/*. Do not edit by hand."""',
        "",
        "",
        "SCHEMA_VERSION = 1",
        "",
    ]
    lines.extend(
        f'TARGET_KIND_{_const_name(kind)} = "{kind}"'
        for kind in kinds
    )
    lines.extend([""])
    lines.extend(
        f'CAPABILITY_{_const_name(row["name"])} = "{row["name"]}"'
        for row in capabilities
    )
    lines.extend(["", "", "CAPABILITY_META = {"])
    for row in capabilities:
        capability = f'CAPABILITY_{_const_name(row["name"])}'
        target_kind = f'TARGET_KIND_{_const_name(row["target_kind"])}'
        lines.extend(
            [
                f"    {capability}: {{",
                f'        "version": {row["version"]},',
                f'        "target_kind": {target_kind},',
                f'        "class": "{row["class"]}",',
                f'        "required_action": "{row["required_action"]}",',
                f'        "data_class": "{row["data_class"]}",',
                f'        "side_effect": "{row["side_effect"]}",',
                f'        "idempotency_required": {row["idempotency_required"]},',
                f'        "completion_evidence": "{row["completion_evidence"]}",',
                "    },",
            ]
        )
    lines.extend(["}", ""])
    return "\n".join(lines)


def render_kotlin(registry: dict[str, Any]) -> str:
    capabilities = _sorted_capabilities(registry)
    kinds = target_kinds()
    lines = [
        "// Generated from packages/contracts/*. Do not edit by hand.",
        "package ai.attune.contracts.generated",
        "",
        "object AttuneContractV1 {",
        "    const val SCHEMA_VERSION: Int = 1",
        "",
        "    object TargetKind {",
    ]
    lines.extend(f'        const val {_const_name(kind)}: String = "{kind}"' for kind in kinds)
    lines.extend(["    }", "", "    object Capability {"])
    lines.extend(f'        const val {_const_name(row["name"])}: String = "{row["name"]}"' for row in capabilities)
    lines.extend(["    }", "", "    data class CapabilityMeta(",
                  "        val version: Int,",
                  "        val targetKind: String,",
                  "        val capabilityClass: String,",
                  "        val requiredAction: String,",
                  "        val dataClass: String,",
                  "        val sideEffect: String,",
                  "        val idempotencyRequired: Boolean,",
                  "        val completionEvidence: String,",
                  "    )", "", "    val CAPABILITY_META: Map<String, CapabilityMeta> = mapOf("])
    for row in capabilities:
        name = _const_name(row["name"])
        bool_value = "true" if row["idempotency_required"] else "false"
        lines.extend([
            f"        Capability.{name} to CapabilityMeta(",
            f"            version = {row['version']},",
            f"            targetKind = TargetKind.{_const_name(row['target_kind'])},",
            f'            capabilityClass = "{row["class"]}",',
            f'            requiredAction = "{row["required_action"]}",',
            f'            dataClass = "{row["data_class"]}",',
            f'            sideEffect = "{row["side_effect"]}",',
            f"            idempotencyRequired = {bool_value},",
            f'            completionEvidence = "{row["completion_evidence"]}",',
            "        ),"
        ])
    lines.extend(["    )", "}", ""])
    return "\n".join(lines)


def render_typescript(registry: dict[str, Any]) -> str:
    capabilities = _sorted_capabilities(registry)
    kinds = target_kinds()
    actions = registry["workspace_actions"]
    lines = [
        "// Generated from packages/contracts/*. Do not edit by hand.",
        "export const ATTUNE_CONTRACT_SCHEMA_VERSION = 1 as const;",
        "",
        "export const TARGET_KINDS = [",
    ]
    lines.extend(f'  "{kind}",' for kind in kinds)
    lines.extend(
        [
            "] as const;",
            "export type TargetKind = (typeof TARGET_KINDS)[number];",
            "",
            "export const WORKSPACE_ACTIONS = [",
        ]
    )
    lines.extend(f'  "{action}",' for action in actions)
    lines.extend(
        [
            "] as const;",
            "export type WorkspaceAction = (typeof WORKSPACE_ACTIONS)[number];",
            "",
            "export const CAPABILITY_META = {",
        ]
    )
    for row in capabilities:
        idem = "true" if row["idempotency_required"] else "false"
        lines.extend([
            f'  "{row["name"]}": {{',
            f'    version: {row["version"]},',
            f'    targetKind: "{row["target_kind"]}",',
            f'    capabilityClass: "{row["class"]}",',
            f'    requiredAction: "{row["required_action"]}",',
            f'    dataClass: "{row["data_class"]}",',
            f'    sideEffect: "{row["side_effect"]}",',
            f"    idempotencyRequired: {idem},",
            f'    completionEvidence: "{row["completion_evidence"]}",',
            "  },"
        ])
    lines.extend([
        "} as const;",
        "export type CapabilityName = keyof typeof CAPABILITY_META;",
        ""
    ])
    return "\n".join(lines)


def rendered_files(registry: dict[str, Any]) -> dict[Path, str]:
    return {
        GENERATED / "python" / "attune_contracts.py": render_python(registry),
        GENERATED / "kotlin" / "AttuneContracts.kt": render_kotlin(registry),
        GENERATED / "typescript" / "attune-contracts.ts": render_typescript(registry),
    }


def generate(*, check: bool) -> None:
    registry = validate_registry()
    failures: list[str] = []
    for path, expected in rendered_files(registry).items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                failures.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if failures:
        joined = "\n- ".join(failures)
        raise ContractError(f"generated contracts are stale:\n- {joined}")


def command_validate() -> None:
    validate_schema_documents()
    registry = validate_registry()
    validate_kotlin_udc_binding()
    generate(check=True)
    print(
        "contract kernel PASS: "
        f"{len(registry['capabilities'])} capabilities, "
        f"{len(target_kinds())} target kinds, "
        f"{len(KOTLIN_SCHEMA_BINDINGS)} Kotlin wire bindings, generated outputs in sync"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("generate")
    sub.add_parser("check-generated")
    sub.add_parser("audit-kotlin")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.command == "validate":
            command_validate()
        elif args.command == "generate":
            validate_schema_documents()
            validate_registry()
            generate(check=False)
            print("generated contract constants updated")
        elif args.command == "audit-kotlin":
            validate_schema_documents()
            validate_kotlin_udc_binding()
            print("Kotlin UDC wire-shape audit PASS")
        else:
            validate_schema_documents()
            validate_registry()
            generate(check=True)
            print("generated contract constants PASS")
    except (ContractError, json.JSONDecodeError, OSError) as exc:
        print(f"contract kernel FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
