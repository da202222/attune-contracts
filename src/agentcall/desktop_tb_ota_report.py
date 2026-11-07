"""Turn one Windows updater result into one ThingsBoard OTA progress report.

TBW-07B follow-up. The Windows updater and its signer stay the only install,
failure, and rollback authority. This module only describes a result that
already happened on the device, in the report shape the TBW-06 OTA gate
(``accounts/tb_ota_projection.admit``) accepts for the ``windows`` profile.
It performs no I/O, never assigns or fetches a package, never names a URL,
and never publishes or uploads a build.

Rules:

* An install counts only when the local updater verified the package with
  the Windows signer or the Microsoft Store. Anything else is reported as a
  signature failure and the accepted version does not move.
* Versions only go up. A lower install is rejected without a report; the same
  version again is not reported twice.
* A rollback is accepted only back to the version accepted just before the
  current one.
* One updater result id is reported once. Each report carries the exact
  ``sequence``/``previous_sequence`` pair, so a repeat or a gap is visible to
  the gate instead of producing a second effect.

TBW-18B.1 adds two closed-loop rules on top, still without I/O:

* ``cancel`` takes a frozen-protocol cancel request. A cancel is never a write
  on the device. If the updater has not produced a result for that intent yet,
  the intent is remembered as cancelled and its later result is not reported
  (the local updater state still moves, the sequence does not). If a result for
  that intent was already reported, the result stands.
* ``resend`` rebuilds the last report exactly as it was sent, with the same
  ``sequence``/``previous_sequence``, so a report lost in transit is delivered
  again without taking a new sequence number.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

PROFILE = "windows"
SEQUENCE_LIMIT = 100_000
REPORT_KEYS = frozenset({
    "kind", "intent_id", "profile", "device_id", "sequence", "previous_sequence",
})
_STATE_KEYS = frozenset({"sequence", "accepted_version", "previous_version", "last_result_id"})
_STATE_OPTIONAL = frozenset({"last_report", "cancelled_intent_id"})
_REPORT_KINDS = frozenset({"updated", "signature", "space", "interrupted", "rollback"})
_CANCEL_KEYS = frozenset({
    "intent", "profile", "device_id", "intent_id", "desired_version", "writer", "package_id", "report",
})
_WRITER = "windows_signer"
_PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_LOCAL_KEYS = frozenset({
    "result_id", "status", "version", "sha256", "signer", "signature_verified", "failure",
})
_SIGNERS = frozenset({"windows_signer", "microsoft_store"})
_FAILURES = frozenset({"signature", "space", "interrupted"})
_STATUSES = frozenset({"installed", "install_failed", "rolled_back"})
_VERSION = re.compile(r"^[0-9]{1,5}(?:\.[0-9]{1,5}){1,3}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NOTE = (
    "Windows 的安装、失败和回退只认本机更新器和签名。这里只把已发生的结果报给 ThingsBoard，"
    "不下发、不下载、不发布安装包；版本只升不降，同一结果只报一次。"
)


def empty_state() -> dict[str, Any]:
    return {"sequence": 0, "accepted_version": None, "previous_version": None, "last_result_id": None}


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
    parts = [int(part) for part in value.split(".")]
    return tuple(parts + [0] * (4 - len(parts)))  # type: ignore[return-value]


def _state(value: Any) -> dict[str, Any] | None:
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
    for key in ("accepted_version", "previous_version"):
        if value[key] is not None and _version(value[key]) is None:
            return None
    if value["previous_version"] is not None and value["accepted_version"] is None:
        return None
    if value["previous_version"] is not None and (
        _version(value["previous_version"]) >= _version(value["accepted_version"])
    ):
        return None
    if value["last_result_id"] is not None and _uuid(value["last_result_id"]) is None:
        return None
    if "cancelled_intent_id" in value and _uuid(value["cancelled_intent_id"]) is None:
        return None
    if "last_report" in value and not _stored_report(value["last_report"], sequence):
        return None
    copy = dict(value)
    if "last_report" in copy:
        copy["last_report"] = dict(copy["last_report"])
    return copy


def _stored_report(value: Any, sequence: int) -> bool:
    if type(value) is not dict or set(value) != REPORT_KEYS:
        return False
    if value["kind"] not in _REPORT_KINDS or value["profile"] != PROFILE:
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


def _closed(state: dict[str, Any] | None, **fields: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "ok": False,
        "error": None,
        "effect": "not_reported",
        "report": None,
        "next_state": state,
        "install_accepted": False,
        "accepted_version": state["accepted_version"] if state else None,
        "rollback_accepted": False,
        "assignment_started": False,
        "package_fetched": False,
        "package_uploaded": False,
        "publish_allowed": False,
        "legacy_replay": False,
        "note": _NOTE,
    }
    body.update(fields)
    return body


def _local(value: Any) -> dict[str, Any] | None:
    if type(value) is not dict or not {"result_id", "status", "version", "sha256"} <= set(value):
        return None
    if set(value) - _LOCAL_KEYS:
        return None
    if _uuid(value["result_id"]) is None or value["status"] not in _STATUSES:
        return None
    if _version(value["version"]) is None:
        return None
    if type(value["sha256"]) is not str or _SHA256.fullmatch(value["sha256"]) is None:
        return None
    signer = value.get("signer")
    if signer is not None and signer not in _SIGNERS:
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


def report(state: Any, local: Any, *, intent_id: Any, device_id: Any) -> dict[str, Any]:
    """Return one closed decision and at most one report for the TBW-06 gate.

    ``next_state`` is what the caller stores for the next call; it is the input
    state unchanged whenever nothing is reported.
    """
    current = _state(state)
    if current is None:
        return _closed(None, error="state_rejected")
    intent = _uuid(intent_id)
    device = _uuid(device_id)
    if intent is None or device is None:
        return _closed(current, error="target_rejected")
    result = _local(local)
    if result is None:
        return _closed(current, error="local_result_rejected")
    if result["result_id"] == current["last_result_id"]:
        return _closed(current, ok=True, effect="duplicate_not_reported")
    if current["sequence"] >= SEQUENCE_LIMIT:
        return _closed(current, error="sequence_exhausted")

    status = result["status"]
    version = result["version"]
    accepted = current["accepted_version"]
    rank = _version(version)
    nxt = dict(current)
    fields: dict[str, Any] = {}

    if status == "installed":
        signed = result.get("signature_verified") is True and result.get("signer") in _SIGNERS
        if not signed:
            kind = "signature"
        elif accepted is not None and rank < _version(accepted):
            return _closed(current, error="downgrade_rejected")
        elif accepted is not None and rank == _version(accepted):
            nxt["last_result_id"] = result["result_id"]
            return _closed(nxt, ok=True, effect="version_already_reported")
        else:
            kind = "updated"
            nxt["previous_version"] = accepted
            nxt["accepted_version"] = version
            fields = {"install_accepted": True, "accepted_version": version}
    elif status == "install_failed":
        if accepted is not None and rank <= _version(accepted):
            return _closed(current, error="downgrade_rejected")
        kind = result["failure"]
    else:
        if current["previous_version"] is None or version != current["previous_version"]:
            return _closed(current, error="rollback_target_rejected")
        kind = "rollback"
        nxt["accepted_version"] = version
        nxt["previous_version"] = None
        fields = {"rollback_accepted": True, "accepted_version": version}

    nxt["last_result_id"] = result["result_id"]
    if current.get("cancelled_intent_id") == intent:
        return _closed(nxt, ok=True, effect="cancelled_not_reported", **fields)
    nxt["sequence"] = current["sequence"] + 1
    payload = {
        "kind": kind,
        "intent_id": intent,
        "profile": PROFILE,
        "device_id": device,
        "sequence": nxt["sequence"],
        "previous_sequence": current["sequence"],
    }
    nxt["last_report"] = dict(payload)
    return _closed(nxt, ok=True, effect="reported", report=payload, **fields)


def _cancel_request(value: Any) -> dict[str, Any] | None:
    if type(value) is not dict or set(value) != _CANCEL_KEYS:
        return None
    if value["intent"] != "cancel" or value["profile"] != PROFILE or value["writer"] != _WRITER:
        return None
    if value["report"] is not None:
        return None
    if _uuid(value["device_id"]) is None or _uuid(value["intent_id"]) is None:
        return None
    if _version(value["desired_version"]) is None:
        return None
    package = value["package_id"]
    if type(package) is not str or _PACKAGE_ID.fullmatch(package) is None:
        return None
    return value


def cancel(state: Any, request: Any) -> dict[str, Any]:
    """Reconcile one frozen-protocol cancel request with the stored report state.

    A cancel never installs, rolls back, or assigns anything. Before a result for
    the intent was reported it only stops that intent's result from being
    reported; after a report was sent the reported result stands.
    """
    current = _state(state)
    if current is None:
        return _closed(None, error="state_rejected")
    asked = _cancel_request(request)
    if asked is None:
        return _closed(current, error="cancel_rejected")
    intent = asked["intent_id"]
    last = current.get("last_report")
    if last is not None and last["intent_id"] == intent:
        return _closed(current, ok=True, effect="cancel_result_stands")
    if current.get("cancelled_intent_id") == intent:
        return _closed(current, ok=True, effect="cancel_already_recorded")
    nxt = dict(current)
    nxt["cancelled_intent_id"] = intent
    return _closed(nxt, ok=True, effect="cancelled_before_result")


def resend(state: Any, *, intent_id: Any, device_id: Any) -> dict[str, Any]:
    """Return the last report again, unchanged, for the same intent and device.

    The sequence does not move: the receiver sees the same ``sequence`` and
    ``previous_sequence`` as the lost send, so one delivery has one effect.
    """
    current = _state(state)
    if current is None:
        return _closed(None, error="state_rejected")
    intent = _uuid(intent_id)
    device = _uuid(device_id)
    if intent is None or device is None:
        return _closed(current, error="target_rejected")
    last = current.get("last_report")
    if last is None:
        return _closed(current, error="no_report_to_resend")
    if last["intent_id"] != intent or last["device_id"] != device:
        return _closed(current, error="resend_target_rejected")
    return _closed(current, ok=True, effect="resent", report=dict(last))
