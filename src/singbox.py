import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from src.models import VlessPreset

SUPPORTED_TRANSPORTS = {"tcp", "ws", "grpc", "http", "httpupgrade", "quic"}


def ensure_singbox() -> None:
    if shutil.which("sing-box") is None:
        print("`sing-box` is not installed. install it and try again.")
        sys.exit(1)


@contextmanager
def temp_config(config: dict[str, Any]) -> Generator[str]:
    path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json", dir=tempfile.gettempdir()
        ) as f:
            path = f.name
            f.write(json.dumps(config))
        yield path
    finally:
        if path and os.path.exists(path):
            os.remove(path)


def _generate_vless_outbound(
    preset: VlessPreset, tag: str = "vless-out"
) -> dict[str, Any]:
    result = {
        "type": "vless",
        "tag": tag,
        "server": preset.host,
        "server_port": preset.port,
        "uuid": preset.uuid,
        "flow": preset.flow or "",
        "tls": {
            "enabled": True,
            "server_name": preset.server_name,
            "reality": {
                "enabled": True,
                "public_key": preset.public_key,
                "short_id": preset.short_id,
            },
            "utls": {"enabled": True, "fingerprint": preset.fingerprint},
        },
    }

    if preset.transport_type != "tcp":
        result["transport"] = {"type": preset.transport_type}

    return result


def build_config_from_template(
    template: dict[str, Any], preset: VlessPreset, log_level: str, proxy_all: bool
) -> dict[str, Any]:
    template["log"]["level"] = log_level
    template["outbounds"].append(_generate_vless_outbound(preset))
    if proxy_all:
        template["dns"]["rules"] = []
        template["route"]["rules"] = [{"protocol": "dns", "action": "hijack-dns"}]
        template["route"]["final"] = "vless-out"
    return template


def build_urltest_config(presets: list[VlessPreset], api_port: int) -> dict[str, Any]:
    outbounds = [_generate_vless_outbound(p, tag=str(i)) for i, p in enumerate(presets)]
    return {
        "log": {"level": "warn"},
        "outbounds": outbounds,
        "experimental": {
            "clash_api": {
                "external_controller": f"127.0.0.1:{api_port}",
            }
        },
    }


def run_singbox(config: dict[str, Any]) -> None:
    with temp_config(config) as path:
        print("running sing-box...")
        result = subprocess.run(
            ["sing-box", "run", "-c", path], capture_output=True, text=True, check=False
        )
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        if result.returncode and any(
            error in result.stderr.lower()
            for error in ("permission denied", "operation not permitted")
        ):
            print(
                "sing-box needs network-admin permissions for the TUN interface.\n"
                'run: sudo setcap cap_net_admin=+ep "$(command -v sing-box)"'
            )
