import json
import os
import shutil
import subprocess
import tempfile
from typing import Any

from src.models import VlessPreset

SUPPORTED_TRANSPORTS = {"tcp", "ws", "grpc", "http", "httpupgrade", "quic"}


def is_singbox_installed() -> bool:
    return shutil.which("sing-box") is not None


def generate_vless_outbound(
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


def generate_urltest_config(
    presets: list[VlessPreset], api_port: int
) -> dict[str, Any]:
    outbounds = [
        generate_vless_outbound(p, tag=str(i)) for i, p in enumerate(presets)
    ]
    return {
        "log": {"level": "warn"},
        "outbounds": outbounds,
        "experimental": {
            "clash_api": {
                "external_controller": f"127.0.0.1:{api_port}",
            }
        },
    }


def run_singbox(config: dict[str, Any]):
    temp_config_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".json",
            dir=tempfile.gettempdir(),
        ) as temp_config:
            temp_config_path = temp_config.name
            temp_config.write(json.dumps(config, indent=2))

        print("Running sing-box...")
        run_cmd = ["sing-box", "run", "-c", temp_config_path]
        subprocess.run(run_cmd, check=False)
    finally:
        if temp_config_path and os.path.exists(temp_config_path):
            os.remove(temp_config_path)
