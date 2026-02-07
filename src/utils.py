import sys
from typing import Any


def select_preset(presets: dict[str, Any]) -> str:
    presets_list = list(presets.keys())
    while True:
        for i, preset_name in enumerate(presets_list):
            print(f"[{i:02}]: {preset_name}")

        try:
            raw_selection = input("Select preset by number: ")
            selected_index = int(raw_selection)
            if 0 <= selected_index < len(presets_list):
                return presets_list[selected_index]
            print(
                f"Invalid number. Please enter a number between 0 and"
                f" {len(presets_list) - 1}."
            )
        except ValueError:
            print(
                f'Invalid input. Please enter a number. You entered: "{raw_selection}"'
            )
        except (EOFError, KeyboardInterrupt):
            print("\nSelection cancelled.")
            sys.exit(0)
