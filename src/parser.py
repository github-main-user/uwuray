from urllib.parse import parse_qs, unquote, urlparse

from src.models import VlessPreset


def _parse_vless_string(url: str) -> VlessPreset | None:
    try:
        result = urlparse(url)
        if result.scheme != "vless":
            return None

        uuid = result.username
        host = result.hostname
        port = result.port

        if not (uuid and host and port):
            return None

        query_params = {k: v[0] for k, v in parse_qs(result.query).items()}

        return VlessPreset(
            name=unquote(result.fragment) if result.fragment else "No name",
            uuid=uuid,
            host=host,
            port=port,
            transport_type=query_params["type"],
            server_name=query_params["sni"],
            fingerprint=query_params["fp"],
            public_key=query_params["pbk"],
            short_id=query_params["sid"],
            flow=query_params.get("flow"),
        )
    except (KeyError, AttributeError, TypeError):
        return None


def parse_presets(urls: list[str]) -> dict[str, VlessPreset]:
    result = {}
    for url in urls:
        parsed_preset = _parse_vless_string(url)
        if parsed_preset:
            result[parsed_preset.name] = parsed_preset
    return result
