import base64
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException


def is_subscription_url_valid(url: str) -> bool:
    try:
        urlparse(url)
        return True
    except Exception:
        return False


def is_subscription_url_reachable(url: str) -> bool:
    try:
        response = requests.get(url, allow_redirects=True, timeout=5)
        return response.status_code < 400
    except RequestException:
        return False


def fetch_subscription_data(url: str) -> list[str]:
    response = requests.get(url)
    response.raise_for_status()
    return base64.b64decode(response.text).decode().splitlines()
