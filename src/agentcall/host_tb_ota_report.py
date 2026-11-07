"""Turn one Docker or OpenWrt updater result into one ThingsBoard OTA report.

TBW-07C. The host updater stays the only install, failure, and rollback
authority. Docker installs stay on the OCI digest pinned by
``packaging/docker/managed-updater.sh``. OpenWrt installs stay on the signed
feed and ``attune-feed-updater``. This module only describes a result that
already happened, in the report shape the TBW-06 gate accepts for the
``linux-docker`` and ``openwrt`` profiles.

It performs no I/O. It does not fetch a package, assign a desired version,
open the host Docker socket, write the feed, drain a call, or invoke either
updater. A ThingsBoard checksum or UPDATED state is not acceptance. Versions
only go up, and one updater result is reported once.

``cancel`` and ``resend`` reconcile one frozen-protocol command with that
stored report. A cancel never installs, fetches, or assigns a version.
Before a result for the intent is reported, the intent is remembered and the
later result is not sent (the updater's local version and digest still move,
the sequence does not). After a report was sent, that report stands.
``resend`` returns the last report unchanged, with the same sequence pair.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

SEQUENCE_LIMIT = 100_000
REPORT_KEYS = frozenset({
    "kind", "intent_id", "profile", "device_id", "sequence", "previous_sequence",
})
_STATE_KEYS = frozenset({
    "sequence", "accepted_version", "previous_version",
    "accepted_digest", "previous_digest", "last_result_id",
})
_STATE_OPTIONAL = frozenset({"last_report", "cancelled_intent_id"})
_REPORT_KINDS = frozenset({"updated", "signature", "space", "interrupted", "rollback"})
_CANCEL_KEYS = frozenset({
    "intent", "profile", "device_id", "intent_id", "desired_version", "writer", "package_id", "report",
})
_PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_REQUEST_VERSION = re.compile(r"^[0-9]{1,5}(?:\.[0-9]{1,5}){1,3}$")
_OPTIONAL_LOCAL = frozenset({"signer", "signature_verified", "failure"})
_FAILURES = frozenset({"signature", "space", "interrupted"})
_STATUSES = frozenset({"installed", "install_failed", "rolled_back"})
_VERSION = re.compile(
    r"^[0-9]{1,5}(?:\.[0-9]{1,5}){1,3}(?:\+local\.[0-9a-f]{7,40})?$"
)
_PROFILES = {
    "linux-docker": {
        "writer": "oci_digest",
        "signers": frozenset({"oci_digest"}),
        "digest_key": "digest",
        "digest_re": re.compile(r"^sha256:[0-9a-f]{64}$"),
        "note": (
            "Docker 的安装、失败和回退只认宿主更新器和 OCI digest。这里只把已发生的结果报给"
            " ThingsBoard，不下发、不下载、不发布镜像，也不打开宿主 Docker socket；"
            "版本只升不降，同一结果只报一次。"
        ),
    },
    "openwrt": {
        "writer": "openwrt_signed_feed",
        "signers": frozenset({"openwrt_signed_feed"}),
        "digest_key": "sha256",
        "digest_re": re.compile(r"^[0-9a-f]{64}$"),
        "note": (
            "OpenWrt 的安装、失败和回退只认签名 feed 和本机更新器。这里只把已发生的结果报给"
            " ThingsBoard，不下发、不下载、不改 feed；版本只升不降，同一结果只报一次。"
        ),
    },
}


def empty_state() -> dict[str, Any]:
    return {
        "sequence": 0,
        "accepted_version": None,
        "previous_version": None,
        "accepted_digest": None,
        "previous_digest": None,
        "last_result_id": None,
    }


def _uuid(value: Any) -> str | None:
    if type(value) is not str:
        return None
    try:
        canonical = str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        return None
    return canonical if canonical == value else None


def _version(value: Any) -> tuple[int, int, int, int] | None:
    if type(value) is not str or _VERSION.fullmatch(value) is None:
        return None
    parts = [int(part) for part in value.split("+", 1)[0].split(".")]
    return tuple(parts + [0] * (4 - len(parts)))  # type: ignore[return-value]


def _digest(spec: dict[str, Any], value: Any) -> str | None:
    if type(value) is not str or spec["digest_re"].fullmatch(value) is None:
        return None
    return value


def _stored_report(value: Any, sequence: int, profile: str) -> bool:
    if type(value) is not dict or set(value) != REPORT_KEYS:
        return False
    if value["kind"] not in _REPORT_KINDS or value["profile"] != profile:
        return False
    if _uuid(value["intent_id"]) is None or _uuid(value["device_id"]) is None:
        return False
    return (
        type(value["sequence"]) is int
        and type(value["previous_sequence"]) is int
        and value["sequence"] == sequence
        and sequence >= 1
        and value["previous_sequence"] == sequence - 1
    )


def _state(value: Any, spec: dict[str, Any], profile: str) -> dict[str, Any] | None:
    if value is None:
        return empty_state()
    if type(value) is not dict:
        return None
    keys = set(value)
    if not _STATE_KEYS <= keys or keys - _STATE_KEYS - _STATE_OPTIONAL:
        return None
    sequence = value["sequence"]
    if type(sequence) is not int or not 0 <= sequence <= SEQUENCE_LIMIT:
        return None
    accepted = value["accepted_version"]
    previous = value["previous_version"]
    accepted_digest = value["accepted_digest"]
    previous_digest = value["previous_digest"]
    if accepted is None:
        if accepted_digest is not None or previous is not None or previous_digest is not None:
            return None
    elif _version(accepted) is None or _digest(spec, accepted_digest) is None:
        return None
    if previous is None:
        if previous_digest is not None:
            return None
    elif (
        accepted is None or _version(previous) is None or _digest(spec, previous_digest) is None
        or _version(previous) >= _version(accepted) or previous_digest == accepted_digest
    ):
        return None
    if value["last_result_id"] is not None and _uuid(value["last_result_id"]) is None:
        return None
    if "cancelled_intent_id" in value and _uuid(value["cancelled_intent_id"]) is None:
        return None
    if "last_report" in value and not _stored_report(value["last_report"], sequence, profile):
        return None
    copy = dict(value)
    if "last_report" in copy:
        copy["last_report"] = dict(copy["last_report"])
    return copy


def _closed(state: dict[str, Any] | None, note: str, **fields: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "ok": False,
        "error": None,
        "effect": "not_reported",
        "report": None,
        "next_state": state,
        "install_accepted": False,
        "accepted_version": state["accepted_version"] if state else None,
        "accepted_digest": state["accepted_digest"] if state else None,
        "rollback_accepted": False,
        "assignment_started": False,
        "package_fetched": False,
        "package_uploaded": False,
        "publish_allowed": False,
        "legacy_replay": False,
        "updater_invoked": False,
        "host_socket_used": False,
        "feed_written": False,
        "note": note,
    }
    body.update(fields)
    return body


def _local(value: Any, spec: dict[str, Any]) -> dict[str, Any] | None:
    digest_key = spec["digest_key"]
    if type(value) is not dict or not {"result_id", "status", "version", digest_key} <= set(value):
        return None
    if set(value) - ({"result_id", "status", "version", digest_key} | _OPTIONAL_LOCAL):
        return None
    if _uuid(value["result_id"]) is None or value["status"] not in _STATUSES:
        return None
    if _version(value["version"]) is None or _digest(spec, value[digest_key]) is None:
        return None
    signer = value.get("signer")
    if signer is not None and signer not in spec["signers"]:
        return None
    if "signature_verified" in value and type(value["signature_verified"]) is not bool:
        return None
    failure = value.get("failure")
    if value["status"] == "install_failed":
        if failure not in _FAILURES:
            return None
    elif failure is not None:
        return None
    return value


def report(
    state: Any, local: Any, *, profile: Any, intent_id: Any, device_id: Any,
) -> dict[str, Any]:
    """Return one closed decision and at most one report for the TBW-06 gate.

    ``next_state`` is what the caller stores for the next call. It is the input
    state unchanged whenever nothing is reported.
    """
    spec = _PROFILES.get(profile) if type(profile) is str else None
    if spec is None:
        return _closed(None, _PROFILES["linux-docker"]["note"], error="profile_rejected")
    note = spec["note"]
    current = _state(state, spec, profile)
    if current is None:
        return _closed(None, note, error="state_rejected")
    intent = _uuid(intent_id)
    device = _uuid(device_id)
    if intent is None or device is None:
        return _closed(current, note, error="target_rejected")
    result = _local(local, spec)
    if result is None:
        return _closed(current, note, error="local_result_rejected")
    if result["result_id"] == current["last_result_id"]:
        return _closed(current, note, ok=True, effect="duplicate_not_reported")
    if current["sequence"] >= SEQUENCE_LIMIT:
        return _closed(current, note, error="sequence_exhausted")

    status = result["status"]
    version = result["version"]
    digest = result[spec["digest_key"]]
    accepted = current["accepted_version"]
    rank = _version(version)
    nxt = dict(current)
    fields: dict[str, Any] = {}

    if status == "installed":
        signed = result.get("signature_verified") is True and result.get("signer") in spec["signers"]
        if not signed:
            kind = "signature"
        elif accepted is not None and rank < _version(accepted):
            return _closed(current, note, error="downgrade_rejected")
        elif accepted is not None and rank == _version(accepted):
            nxt["last_result_id"] = result["result_id"]
            return _closed(nxt, note, ok=True, effect="version_already_reported")
        elif current["accepted_digest"] is not None and digest == current["accepted_digest"]:
            return _closed(current, note, error="digest_not_advanced")
        else:
            kind = "updated"
            nxt["previous_version"] = accepted
            nxt["previous_digest"] = current["accepted_digest"]
            nxt["accepted_version"] = version
            nxt["accepted_digest"] = digest
            fields = {
                "install_accepted": True,
                "accepted_version": version,
                "accepted_digest": digest,
            }
    elif status == "install_failed":
        if accepted is not None and rank <= _version(accepted):
            return _closed(current, note, error="downgrade_rejected")
        kind = result["failure"]
    else:
        if (
            current["previous_version"] is None or version != current["previous_version"]
            or digest != current["previous_digest"]
        ):
            return _closed(current, note, error="rollback_target_rejected")
        kind = "rollback"
        nxt["accepted_version"] = version
        nxt["accepted_digest"] = digest
        nxt["previous_version"] = None
        nxt["previous_digest"] = None
        fields = {
            "rollback_accepted": True,
            "accepted_version": version,
            "accepted_digest": digest,
        }

    nxt["last_result_id"] = result["result_id"]
    if current.get("cancelled_intent_id") == intent:
        return _closed(nxt, note, ok=True, effect="cancelled_not_reported", **fields)
    nxt["sequence"] = current["sequence"] + 1
    payload = {
        "kind": kind,
        "intent_id": intent,
        "profile": profile,
        "device_id": device,
        "sequence": nxt["sequence"],
        "previous_sequence": current["sequence"],
    }
    nxt["last_report"] = dict(payload)
    return _closed(nxt, note, ok=True, effect="reported", report=payload, **fields)


def _cancel_request(value: Any, spec: dict[str, Any], profile: str) -> dict[str, Any] | None:
    if type(value) is not dict or set(value) != _CANCEL_KEYS:
        return None
    if value["intent"] != "cancel" or value["profile"] != profile or value["writer"] != spec["writer"]:
        return None
    if value["report"] is not None:
        return None
    if _uuid(value["device_id"]) is None or _uuid(value["intent_id"]) is None:
        return None
    if type(value["desired_version"]) is not str or _REQUEST_VERSION.fullmatch(value["desired_version"]) is None:
        return None
    package = value["package_id"]
    if type(package) is not str or _PACKAGE_ID.fullmatch(package) is None:
        return None
    return value


def cancel(state: Any, request: Any) -> dict[str, Any]:
    """Reconcile one frozen-protocol cancel with the stored host report.

    A cancel never installs, fetches, or assigns anything. Before a result for
    the intent was reported it only stops that intent's result from being
    reported; after a report was sent the reported result stands.
    """
    asked_profile = request.get("profile") if type(request) is dict else None
    spec = _PROFILES.get(asked_profile) if type(asked_profile) is str else None
    note = spec["note"] if spec is not None else _PROFILES["linux-docker"]["note"]
    if spec is None:
        return _closed(None, note, error="cancel_rejected")
    current = _state(state, spec, asked_profile)
    if current is None:
        # A state that belongs to the other host profile is a protocol mismatch,
        # not a corrupt record. Return it unchanged.
        for other, other_spec in _PROFILES.items():
            if other == asked_profile:
                continue
            other_state = _state(state, other_spec, other)
            if other_state is not None:
                return _closed(other_state, note, error="cancel_rejected")
        return _closed(None, note, error="state_rejected")
    asked = _cancel_request(request, spec, asked_profile)
    if asked is None:
        return _closed(current, note, error="cancel_rejected")
    intent = asked["intent_id"]
    last = current.get("last_report")
    if last is not None and last["intent_id"] == intent:
        return _closed(current, note, ok=True, effect="cancel_result_stands")
    if current.get("cancelled_intent_id") == intent:
        return _closed(current, note, ok=True, effect="cancel_already_recorded")
    nxt = dict(current)
    nxt["cancelled_intent_id"] = intent
    return _closed(nxt, note, ok=True, effect="cancelled_before_result")


def resend(state: Any, *, profile: Any, intent_id: Any, device_id: Any) -> dict[str, Any]:
    """Return the last report again, unchanged, for the same intent and device."""
    spec = _PROFILES.get(profile) if type(profile) is str else None
    note = spec["note"] if spec is not None else _PROFILES["linux-docker"]["note"]
    if spec is None:
        return _closed(None, note, error="profile_rejected")
    current = _state(state, spec, profile)
    if current is None:
        return _closed(None, note, error="state_rejected")
    intent = _uuid(intent_id)
    device = _uuid(device_id)
    if intent is None or device is None:
        return _closed(current, note, error="target_rejected")
    last = current.get("last_report")
    if last is None:
        return _closed(current, note, error="no_report_to_resend")
    if last["intent_id"] != intent or last["device_id"] != device:
        return _closed(current, note, error="resend_target_rejected")
    return _closed(current, note, ok=True, effect="resent", report=dict(last))
