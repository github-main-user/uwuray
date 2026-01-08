import os
import shutil
import subprocess
import tempfile
from typing import Any

from src.models import VlessPreset


def is_singbox_installed() -> bool:
    return shutil.which("sing-box") is not None


def generate_vless_outbound(preset: VlessPreset) -> dict[str, Any]:
    result = {
        "type": "vless",
        "tag": "vless-out",
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
            temp_config.write(str(config))

        print("Running sing-box...")
        run_cmd = ["sing-box", "run", "-c", temp_config_path]
        subprocess.run(run_cmd, check=False)
    finally:
        if temp_config_path and os.path.exists(temp_config_path):
            os.remove(temp_config_path)
