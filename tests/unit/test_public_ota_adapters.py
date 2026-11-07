"""Published OTA adapters stay local and use synthetic identifiers."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEVICE = "11111111-1111-4111-8111-111111111111"
INTENT = "22222222-2222-4222-8222-222222222222"
RESULT = "33333333-3333-4333-8333-333333333333"
SHA = "ab" * 32
BANNED = ("urllib", "requests", "httpx", "aiohttp", "subprocess", "import socket")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicOtaAdapterTest(unittest.TestCase):
    def test_adapters_do_not_open_a_transport(self) -> None:
        paths = [
            ROOT / "android/car/tb_ota_report.py",
            ROOT / "android/car/tb_ota_status.py",
            ROOT / "src/agentcall/host_tb_ota_report.py",
            ROOT / "src/agentcall/host_tb_ota_status.py",
            ROOT / "src/agentcall/desktop_tb_ota_report.py",
            ROOT / "src/agentcall/desktop_tb_ota_status.py",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for banned in BANNED:
                self.assertNotIn(banned, text, path.name)

    def test_synthetic_results_report_without_publishing(self) -> None:
        car = _load("car_report", ROOT / "android/car/tb_ota_report.py")
        windows = _load("windows_report", ROOT / "src/agentcall/desktop_tb_ota_report.py")
        host = _load("host_report", ROOT / "src/agentcall/host_tb_ota_report.py")
        cases = [
            (car, None, {
                "result_id": RESULT,
                "status": "installed",
                "version": "0.8.0",
                "sha256": SHA,
                "signer": "forgejo_fdf_site",
                "signature_verified": True,
            }),
            (windows, None, {
                "result_id": RESULT,
                "status": "installed",
                "version": "0.8.0",
                "sha256": SHA,
                "signer": "windows_signer",
                "signature_verified": True,
            }),
            (host, "linux-docker", {
                "result_id": RESULT,
                "status": "installed",
                "version": "0.8.0",
                "digest": "sha256:" + SHA,
                "signer": "oci_digest",
                "signature_verified": True,
            }),
            (host, "openwrt", {
                "result_id": RESULT,
                "status": "installed",
                "version": "0.8.0",
                "sha256": SHA,
                "signer": "openwrt_signed_feed",
                "signature_verified": True,
            }),
        ]
        for module, profile, local in cases:
            kwargs = {"intent_id": INTENT, "device_id": DEVICE}
            if profile is not None:
                kwargs["profile"] = profile
            body = module.report(module.empty_state(), local, **kwargs)
            rendered = json.dumps(body)
            self.assertTrue(body["ok"], rendered)
            self.assertEqual("reported", body["effect"])
            self.assertNotIn("://", rendered.replace("sha256:", ""))
            self.assertFalse(body["publish_allowed"])
            self.assertFalse(body["package_uploaded"])


if __name__ == "__main__":
    unittest.main()
