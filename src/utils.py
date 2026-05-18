import sys

from src.models import VlessPreset


def select_preset(presets: list[VlessPreset]) -> VlessPreset | None:
    if not presets:
        print("no presets to select.")
        return None

    while True:
        for i, preset in enumerate(presets):
            print(f"[{i:02}] {preset.name}")

        try:
            raw = input("select preset by number: ")
            idx = int(raw)
            if 0 <= idx < len(presets):
                return presets[idx]
            print(f"invalid number. enter 0-{len(presets) - 1}.")
        except ValueError:
            print(f'invalid input: "{raw}"')
        except (EOFError, KeyboardInterrupt):
            print("\nselection cancelled.")
            sys.exit(0)
