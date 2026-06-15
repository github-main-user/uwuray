import json
import os
import socket
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from src.models import VlessPreset
from src.singbox import generate_urltest_config

TEST_URL = "https://www.gstatic.com/generate_204"
TIMEOUT_MS = 5000


def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_api(base_url: str, process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("sing-box exited before the API came up")
        try:
            requests.get(base_url, timeout=0.5)
            return
        except requests.ConnectionError:
            time.sleep(0.1)
    raise RuntimeError("clash API did not come up in time")


def measure_delay(base_url: str, tag: str) -> int | None:
    try:
        response = requests.get(
            f"{base_url}/proxies/{tag}/delay",
            params={"url": TEST_URL, "timeout": TIMEOUT_MS},
            timeout=TIMEOUT_MS / 1000 + 5,
        )
        if response.status_code == 200:
            return response.json()["delay"]
    except requests.RequestException:
        pass
    return None


def run_url_test(
    presets: list[VlessPreset],
) -> list[tuple[VlessPreset, int | None]]:
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    config = generate_urltest_config(presets, port)

    temp_config_path = None
    process = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".json",
            dir=tempfile.gettempdir(),
        ) as temp_config:
            temp_config_path = temp_config.name
            temp_config.write(json.dumps(config))

        process = subprocess.Popen(
            ["sing-box", "run", "-c", temp_config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_for_api(base_url, process)

        with ThreadPoolExecutor(max_workers=16) as executor:
            delays = executor.map(
                lambda i: measure_delay(base_url, str(i)), range(len(presets))
            )
            return list(zip(presets, delays))
    finally:
        if process:
            process.terminate()
        if temp_config_path and os.path.exists(temp_config_path):
            os.remove(temp_config_path)
