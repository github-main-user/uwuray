import shutil
import subprocess
import sys

from src.models import VlessPreset


def is_fzf_installed() -> bool:
    return shutil.which("fzf") is not None


def _select_via_fzf(presets: list[VlessPreset]) -> VlessPreset | None:
    names = "\n".join(p.name for p in presets)
    try:
        result = subprocess.run(
            ["fzf"],
            input=names,
            capture_output=True,
            text=True,
            check=True,
        )
        selected_name = result.stdout.strip()
        for p in presets:
            if p.name == selected_name:
                return p
    except subprocess.CalledProcessError:
        pass
    except KeyboardInterrupt:
        print("\nselection cancelled.")
        sys.exit(0)
    return None


def _select_via_input(presets: list[VlessPreset]) -> VlessPreset:
    while True:
        for i, preset in enumerate(presets, 1):
            print(f"[{i:02}] {preset.name}")

        try:
            raw = input("select preset by number: ")
            idx = int(raw)
            if 1 <= idx <= len(presets):
                return presets[idx - 1]
            print(f"invalid number. enter 1-{len(presets)}.")
        except ValueError:
            print(f'invalid input: "{raw}"')  # type: ignore
        except (EOFError, KeyboardInterrupt):
            print("\nselection cancelled.")
            sys.exit(0)


def select_preset(presets: list[VlessPreset]) -> VlessPreset | None:
    if not presets:
        print("no presets to select.")
        return None

    if is_fzf_installed():
        return _select_via_fzf(presets)

    return _select_via_input(presets)
