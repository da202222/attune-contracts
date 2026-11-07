# Attune public contracts

This repository publishes the reviewed Attune contract kernel, the frozen ThingsBoard OTA protocol schema, and synthetic fixtures. It is Apache 2.0.

The commercial server, customer data, production configuration, device identities, and signing keys stay in the private integration repository. Publishing this slice does not grant runtime authority, assign a package, or sign a release. A public copy can be copied, modified, and distributed under the license.

## What is included

- `packages/contracts/` is the language-neutral capability and target contract, plus its generated Python, Kotlin, and TypeScript constants.
- `scripts/contracts.py` checks that kernel with the Python standard library.
- `protocol/thingsboard/ota_protocol.schema.json` is the frozen OTA assignment, cancel, and report schema. The bytes match the private tree at `067084cb753558d11e43773554f18df83fa07d21`; only the directory name changed.
- `protocol/thingsboard/testdata/` uses synthetic UUIDs and versions. Those cases describe the protocol. They do not call a reporter or install anything.
- `docs/content-sync-protocol.md`, `docs/remote-cloud-protocol.md`, and `docs/remote-protocol.md` are the reviewed wire contracts. `docs/fixtures/content-sync/v1/` holds their synthetic examples. Phone numbers there are the reserved `+15550100xxx` range.
- `android/car/tb_ota_report.py`, `android/car/tb_ota_status.py`, and the Docker, OpenWrt, and Windows reporter/status modules are local adapters. They classify a result the updater already finished. They do not fetch, assign, or publish a package.

Product topology notes linked from those protocol documents stay in the private repository. The Windows health-entry module is not part of the public allowlist and is not here.

## Check

```bash
python3 scripts/contracts.py check-generated
python3 -m unittest discover -s tests/unit -p 'test_*.py'
```

`scripts/contracts.py validate` also audits a private Android wire binding that is not in this repository. Use `check-generated` here.

## What stays private

Server implementations, unreleased product modules, customer and device records, production configuration, credentials, and signing or rollout operations are not in this repository.
