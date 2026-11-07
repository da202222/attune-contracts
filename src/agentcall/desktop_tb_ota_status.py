"""Reconcile a Windows updater result with a ThingsBoard OTA report.

TBW-07B. The native updater is the only install, failure, and rollback
authority. A ThingsBoard package state, including UPDATED, DOWNLOADED, and
VERIFIED, is not a Windows install and cannot assign, download, or publish a
package. This module performs no I/O.

A version has to be the numeric form the Windows reporter stores. A label
that reporter would refuse is not an install. ThingsBoard state is still
not an install.

TBW-18B.1: a cancel request for the intent is a record, not a write. When it is
passed in, a local result that already happened stands; otherwise the intent
is shown as cancelled before any install. A cancel never starts, stops, or
undoes an install.
"""

from __future__ import annotations

import re
from typing import Any

_TB_STATES = frozenset({
    "QUEUED",
    "INITIATED",
    "DOWNLOADING",
    "DOWNLOADED",
    "VERIFIED",
    "UPDATING",
    "UPDATED",
    "FAILED",
})
_LOCAL_STATUSES = frozenset({
    "installed",
    "install_failed",
    "rolled_back",
    "idle",
    "store_managed",
})
_FORBIDDEN_KEYS = frozenset({
    "url",
    "package_url",
    "assign",
    "token",
    "password",
    "secret",
    "number",
    "text",
    "command",
    "digits",
})
_VERSION = re.compile(r"^[0-9]{1,5}(?:\.[0-9]{1,5}){1,3}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NOTE = "Windows 安装、失败和回退只认本机更新器。ThingsBoard 的 OTA 状态不能代替安装结果，也不能发布包装。"


def _closed(**fields: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "ok": False,
        "install_accepted": False,
        "install_source": "none",
        "accepted_version": None,
        "rollback_accepted": False,
        "tb_state": None,
        "tb_install_accepted": False,
        "version_mismatch": False,
        "publish_allowed": False,
        "package_uploaded": False,
        "assignment_started": False,
        "cancel_reconciliation": None,
        "note": _NOTE,
    }
    body.update(fields)
    return body


def _version(value: Any) -> str | None:
    if value is None:
        return None
    if type(value) is not str or _VERSION.fullmatch(value) is None:
        return ""
    return value


def _sha256(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        return ""
    return value


def _reject_report_shape(value: Any, *, depth: int = 0) -> bool:
    if depth > 4:
        return True
    if isinstance(value, dict):
        if _FORBIDDEN_KEYS.intersection(value):
            return True
        return any(_reject_report_shape(item, depth=depth + 1) for item in value.values())
    if isinstance(value, list):
        return any(_reject_report_shape(item, depth=depth + 1) for item in value)
    if isinstance(value, str):
        return "://" in value or any(ord(char) < 32 or ord(char) == 127 for char in value)
    return type(value) not in {bool, int, float, type(None)}


def reconcile(local: Any, tb_report: Any = None, *, cancelled: Any = False) -> dict[str, Any]:
    """Return one closed comparison. Publication and assignment stay off."""
    if type(cancelled) is not bool:
        return _closed(error="cancel_flag_rejected")
    if type(local) is not dict or _reject_report_shape(local):
        return _closed(error="local_report_rejected")
    status = local.get("status")
    if status not in _LOCAL_STATUSES:
        return _closed(error="local_status_rejected")
    version = _version(local.get("version"))
    digest = _sha256(local.get("sha256"))
    if version == "" or digest == "":
        return _closed(error="local_report_rejected")
    publication = local.get("publication_status")
    if publication is not None and (
        type(publication) is not str or not 1 <= len(publication) <= 80
        or any(ord(char) < 32 or ord(char) == 127 for char in publication)
    ):
        return _closed(error="local_report_rejected")

    tb_state = None
    tb_version = None
    if tb_report is not None:
        if type(tb_report) is not dict or _reject_report_shape(tb_report):
            return _closed(error="tb_report_rejected")
        tb_state = tb_report.get("state")
        if tb_state not in _TB_STATES:
            return _closed(error="tb_state_rejected")
        tb_version = _version(tb_report.get("version"))
        if tb_version == "":
            return _closed(error="tb_report_rejected")
        allowed = {"state", "version"}
        if set(tb_report) - allowed:
            return _closed(error="tb_report_rejected")

    installed = status == "installed"
    cancel_reconciliation = None
    if cancelled:
        has_result = status in {"installed", "install_failed", "rolled_back"}
        cancel_reconciliation = "local_result_stands" if has_result else "cancelled_before_install"
    return _closed(
        ok=True,
        error=None,
        install_accepted=installed,
        install_source="windows_updater" if installed else "none",
        accepted_version=version if installed else None,
        rollback_accepted=status == "rolled_back",
        tb_state=tb_state,
        tb_install_accepted=False,
        version_mismatch=bool(version and tb_version and version != tb_version),
        cancel_reconciliation=cancel_reconciliation,
    )
