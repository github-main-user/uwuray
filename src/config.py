import json
import os
from pathlib import Path
from typing import Any


class Settings:
    _CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    _BASE_DIR = Path(__file__).parent.parent

    def __init__(self) -> None:
        self.APP_CONFIG_PATH: Path = self._CONFIG_DIR / "uwuray"
        self.APP_CONFIG_PATH.mkdir(exist_ok=True)

        self._SUBSCRIPTION: Path = self.APP_CONFIG_PATH / "subscription.txt"
        self._SUBSCRIPTION.touch()

        self._PRESETS: Path = self.APP_CONFIG_PATH / "presets.json"
        self._PRESETS.touch()

        self._PREVIOUS_PRESET: Path = self.APP_CONFIG_PATH / "previous_preset.txt"
        self._PREVIOUS_PRESET.touch()

    def get_subscription_url(self) -> str:
        return self._SUBSCRIPTION.read_text().strip()

    def save_subscription_url(self, url: str) -> None:
        self._SUBSCRIPTION.write_text(url)

    def get_presets(self) -> dict[str, Any]:
        content = self._PRESETS.read_text()
        return json.loads(content) if content else {}

    def save_presets(self, presets: dict[str, Any]) -> None:
        self._PRESETS.write_text(json.dumps(presets, ensure_ascii=False, indent=2))

    def get_config_template(self) -> dict[str, Any]:
        return json.loads(
            (self._BASE_DIR / "resources/config_template.json").read_text()
        )

    def get_previous_preset(self) -> str:
        return self._PREVIOUS_PRESET.read_text().strip()

    def save_previous_preset(self, preset_name: str) -> None:
        self._PREVIOUS_PRESET.write_text(preset_name.strip())


settings = Settings()
