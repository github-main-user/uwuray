import os
import shutil
import subprocess
import tempfile
from urllib.parse import parse_qs, unquote, urlparse

import requests

from src.config import settings


def is_singbox_installed() -> bool:
    return shutil.which("sing-box") is not None


def is_subscription_url_valid(url: str) -> bool:
    # if given string is a valid url
    try:
        urlparse(url)
        return True
    except ValueError:
        return False


def is_subscription_url_reachable(url: str) -> bool:
    # if given url is reachable
    try:
        response = requests.get(url, allow_redirects=True, timeout=5)
        return response.status_code < 400
    except requests.RequestException:
        return False


def _parse_vless_string(url: str) -> tuple[str, dict] | None:
    result = urlparse(url)

    if result.scheme != "vless":
        return None

    query_params = {k: v[0] for k, v in parse_qs(result.query).items()}

    return (
        unquote(result.fragment) if result.fragment else "No name",
        {
            "scheme": result.scheme,
            "uuid": result.username,
            "host": result.hostname,
            "port": result.port,
            "extra": query_params,
        },
    )


def parse_presets(urls: list[str]) -> dict:
    result = {}
    for url in urls:
        parsed_url = _parse_vless_string(url)
        if parsed_url:
            result[parsed_url[0]] = parsed_url[1]
    return result


def generate_vless_outbound(parsed_preset: dict) -> dict:
    return {
        "type": "vless",
        "tag": "vless-out",
        "server": parsed_preset["host"],
        "server_port": parsed_preset["port"],
        "flow": parsed_preset["extra"].get("flow", ""),
        "tls": {
            "enabled": True,
            "reality": {
                "enabled": True,
                "public_key": parsed_preset["extra"]["pbk"],
                "short_id": parsed_preset["extra"]["sid"],
            },
            "server_name": parsed_preset["extra"]["sni"],
            "utls": {
                "enabled": True,
                "fingerprint": parsed_preset["extra"]["fp"],
            },
        },
        "uuid": parsed_preset["uuid"],
        "transport": {
            "type": parsed_preset["extra"]["type"],
        },
    }


def fzf_select(options):
    proc = subprocess.Popen(
        "fzf", stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )

    input_data = "\n".join(options)
    stdout, _ = proc.communicate(input=input_data)

    result = stdout.strip()
    return result


def run_singbox(config: str):
    """
    Checks and runs sing-box with the given configuration.
    """
    temp_config_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".json",
            dir=settings.APP_CONFIG_PATH,
        ) as temp_config:
            temp_config_path = temp_config.name
            temp_config.write(config)

        check_cmd = ["sing-box", "check", "-c", temp_config_path]
        print("Checking configuration...")
        result = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print("Configuration check failed:")
            print(result.stderr)
            return

        print("Configuration check successful. Running sing-box...")
        run_cmd = ["sing-box", "run", "-c", temp_config_path]
        subprocess.run(run_cmd, check=False)

    finally:
        if temp_config_path and os.path.exists(temp_config_path):
            os.remove(temp_config_path)
