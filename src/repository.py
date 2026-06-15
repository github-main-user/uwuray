import json
import os
from pathlib import Path
from typing import Any


class AppRepository:
    _CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    _BASE_DIR = Path(__file__).parent.parent

    def __init__(self) -> None:
        self.config_dir: Path = self._CONFIG_DIR / "uwuray"
        self.config_dir.mkdir(exist_ok=True)

        self._subscriptions_path: Path = self.config_dir / "subscriptions.json"
        self._presets_path: Path = self.config_dir / "presets.json"
        self._previous_preset_path: Path = self.config_dir / "previous_preset.txt"
        self._config_template_path: Path = self.config_dir / "config_template.json"

    def get_subscription_urls(self) -> list[str]:
        if not self._subscriptions_path.exists():
            return []
        content = self._subscriptions_path.read_text().strip()
        return json.loads(content) if content else []

    def add_subscription(self, url: str) -> None:
        urls = self.get_subscription_urls()
        urls.append(url)
        self._subscriptions_path.write_text(json.dumps(urls, indent=2))

    def get_presets(self) -> dict[str, list[dict[str, Any]]]:
        if not self._presets_path.exists():
            return {}
        content = self._presets_path.read_text().strip()
        return json.loads(content) if content else {}

    def set_presets_for_url(self, url: str, presets: list[dict[str, Any]]) -> None:
        all_presets = self.get_presets()
        all_presets[url] = presets
        self._presets_path.write_text(
            json.dumps(all_presets, ensure_ascii=False, indent=2)
        )

    def get_config_template(self) -> dict[str, Any]:
        if not self._config_template_path.exists():
            self._config_template_path.write_text(
                (self._BASE_DIR / "resources/config_template.json").read_text()
            )
        return json.loads(self._config_template_path.read_text())

    def get_previous_preset(self) -> str:
        if not self._previous_preset_path.exists():
            self._previous_preset_path.touch()
        return self._previous_preset_path.read_text().strip()

    def set_previous_preset(self, preset_name: str) -> None:
        self._previous_preset_path.write_text(preset_name.strip())


repo = AppRepository()
