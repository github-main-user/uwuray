import json
import os
from pathlib import Path
from typing import Any


class AppRepository:
    _CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    _BASE_DIR = Path(__file__).parent.parent

    def __init__(self) -> None:
        self.APP_CONFIG_PATH: Path = self._CONFIG_DIR / "uwuray"
        self.APP_CONFIG_PATH.mkdir(exist_ok=True)

        self._SUBSCRIPTIONS: Path = self.APP_CONFIG_PATH / "subscriptions.json"
        self._PRESETS: Path = self.APP_CONFIG_PATH / "presets.json"
        self._PREVIOUS_PRESET: Path = self.APP_CONFIG_PATH / "previous_preset.txt"
        self._CONFIG_TEMPLATE: Path = self.APP_CONFIG_PATH / "config_template.json"

    def get_subscription_urls(self) -> list[str]:
        if not self._SUBSCRIPTIONS.exists():
            return []
        content = self._SUBSCRIPTIONS.read_text().strip()
        return json.loads(content) if content else []

    def add_subscription(self, url: str) -> None:
        urls = self.get_subscription_urls()
        urls.append(url)
        self._SUBSCRIPTIONS.write_text(json.dumps(urls, indent=2))

    def get_presets(self) -> dict[str, list[dict[str, Any]]]:
        if not self._PRESETS.exists():
            return {}
        content = self._PRESETS.read_text().strip()
        return json.loads(content) if content else {}

    def set_presets_for_url(self, url: str, presets: list[dict[str, Any]]) -> None:
        all_presets = self.get_presets()
        all_presets[url] = presets
        self._PRESETS.write_text(json.dumps(all_presets, ensure_ascii=False, indent=2))

    def get_config_template(self) -> dict[str, Any]:
        if not self._CONFIG_TEMPLATE.exists():
            self._CONFIG_TEMPLATE.write_text(
                (self._BASE_DIR / "resources/config_template.json").read_text()
            )
        return json.loads(self._CONFIG_TEMPLATE.read_text())

    def get_previous_preset(self) -> str:
        if not self._PREVIOUS_PRESET.exists():
            self._PREVIOUS_PRESET.touch()
        return self._PREVIOUS_PRESET.read_text().strip()

    def set_previous_preset(self, preset_name: str) -> None:
        self._PREVIOUS_PRESET.write_text(preset_name.strip())


repo = AppRepository()
