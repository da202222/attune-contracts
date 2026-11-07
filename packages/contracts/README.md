# Attune cross-platform contract kernel

Status: **v1 contract authority; runtime adoption is staged**

This directory is the language-neutral source of truth for Attune cross-platform
device addressing, capability names, wire envelopes, and policy/truth metadata.

It does **not** grant production authority. Runtime authorization remains
Server-owned and runtime availability remains Edge/Device-Truth-owned.

## Authority split

The invariant is:

```text
Server policy definition + Workspace RBAC
                    |
                    v
canonical capability/TargetRef contract
                    |
                    v
bounded platform adapter
                    |
                    v
Edge advertisement + Device Truth
```

The registry therefore fixes semantic metadata but explicitly carries
`registry_grants_runtime_authority=false`.

## Canonical v1 documents

- `target-ref.v1.schema.json` — typed endpoint identity. `router_line` requires
  an explicit Router Node parent; the wire contract has no ambiguous
  `device_id || line_id` alias.
- `capability-registry.v1.json` — canonical capability name/version, target
  kind, Workspace action, data class, side-effect class, idempotency rule and
  completion evidence.
- `capability-command.v1.schema.json` — Edge execution envelope.
- `capability-result.v1.schema.json` — terminal result + truth relationship.
- `capability-advertisement.v1.schema.json` — Edge-owned availability.
- `capability-descriptor.v1.schema.json` — Server policy joined to Edge
  availability.
- `device-capability-discovery.v1.schema.json` — visible devices and their
  current descriptors.
- `device-truth-event.v1.schema.json` — observed truth/evidence event.
- `cross-endpoint-context.v1.schema.json` — Server-owned audit/authorization
  context; never an Edge authority grant.

All schemas use JSON Schema draft 2020-12, reject unknown root fields and keep
all v1 root fields explicit.

## Generated language bindings

`python3 scripts/contracts.py generate` produces deterministic constants for:

- Python: `generated/python/attune_contracts.py`
- Kotlin: `generated/kotlin/AttuneContracts.kt`
- TypeScript: `generated/typescript/attune-contracts.ts`

Generated files are mirrors, not authority. CI runs `check-generated` and fails
if somebody edits a generated file or changes the registry without regenerating.

## Transitional adapter audit

Android already has the strongest current UDC wire model in
`android/car-core/.../UdcContracts.kt`. During migration, CI compares the exact
serialized field set of its seven shared wire data classes with these schemas.
That turns the new language-neutral schemas into a fail-closed contract without
changing Android runtime behavior in this slice.

Windows `cloud_control.py` camelCase envelopes and Server
`device_id`/`line_id` compatibility aliases are intentionally **not** promoted
into this kernel. They remain compatibility adapters to be migrated in later
slices.

## TargetRef v1

Example Router Line target:

```json
{
  "schema_version": 1,
  "kind": "router_line",
  "id": "33333333-3333-4333-8333-333333333333",
  "parent_id": "55555555-5555-4555-8555-555555555555"
}
```

Rules:

- `id` is always the stable endpoint UUID.
- `router_line` requires the stable parent Router Node UUID.
- all other v1 target kinds require `parent_id=null`.
- new internal APIs must use typed TargetRef semantics rather than guessing
  whether an identifier is a PC, Router Node, or Line from a field alias.
- legacy `device_id` / `line_id` inputs may only be normalized at an explicit
  compatibility boundary during migration.

## Validation

```bash
python3 scripts/contracts.py validate
python3 -m unittest discover -s tests/unit -p 'test_contract_kernel.py'
```

The validator is stdlib-only so Android, Server, Windows, Router and Web CI can
run it before installing product-specific dependencies.

## Mainline rule

After this PR merges, contract evolution is made on `main` through these
canonical files. Long-lived product branches may consume a released contract
revision, but they do not become independent contract authorities.

A product can remain gated or validation-only while still compiling against the
same semantic contract. Source authority and production activation are separate.
