from dataclasses import dataclass


@dataclass
class VlessPreset:
    name: str
    uuid: str
    host: str
    port: int
    transport_type: str
    server_name: str  # sni
    fingerprint: str | None  # fp
    public_key: str  # pbk
    short_id: str  # sid
    flow: str | None = None
