import sys

from src.models import VlessPreset


def select_preset(presets: list[VlessPreset]) -> VlessPreset | None:
    if not presets:
        print("There is no preset to select")
        return

    while True:
        for i, preset in enumerate(presets):
            print(f"[{i:02}]: {preset.name}")

        try:
            raw_selection = input("Select preset by number: ")
            selected_index = int(raw_selection)
            if 0 <= selected_index < len(presets):
                return presets[selected_index]
            print(
                f"Invalid number. Please enter a number between 0 and"
                f" {len(presets) - 1}."
            )
        except ValueError:
            print(
                f'Invalid input. Please enter a number. You entered: "{raw_selection}"'
            )
        except (EOFError, KeyboardInterrupt):
            print("\nSelection cancelled.")
            sys.exit(0)
