import os
from pathlib import Path


class Settings:
    _CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    _BASE_DIR = Path(__file__).parent.parent

    def __init__(self) -> None:
        print(self._BASE_DIR)

        self.APP_CONFIG_PATH: Path = self._CONFIG_DIR / "uwuray"
        self.APP_CONFIG_PATH.mkdir(exist_ok=True)

        self.SUBSCRIPTION: Path = self.APP_CONFIG_PATH / "subscription.txt"
        self.SUBSCRIPTION.touch()

        self.PRESETS: Path = self.APP_CONFIG_PATH / "presets.json"
        self.PRESETS.touch()

        self.CONFIG_TEMPLATE: Path = self.APP_CONFIG_PATH / "config_template.json"
        if not self.CONFIG_TEMPLATE.exists():
            self.CONFIG_TEMPLATE.write_text(
                (self._BASE_DIR / "src/config_template.json").read_text()
            )

        self.PREVIOUS_PRESET: Path = self.APP_CONFIG_PATH / "previous_preset.txt"
        self.PREVIOUS_PRESET.touch()


settings = Settings()
