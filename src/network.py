import base64
from urllib.parse import urlparse

import requests


def is_subscription_url_valid(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def fetch_subscription_data(url: str) -> list[str]:
    response = requests.get(
        url,
        headers={
            "User-Agent": "v2RayTun/v5.20.65 Platform/linux",
            "x-hwid": "00000000",
        },
    )
    response.raise_for_status()
    return base64.b64decode(response.text).decode().splitlines()
