#!/usr/bin/env python
import json
import sys
from argparse import ArgumentParser, Namespace

from src.config import settings
from src.models import VlessPreset
from src.network import (
    fetch_subscription_data,
    is_subscription_url_reachable,
    is_subscription_url_valid,
)
from src.parser import parse_presets
from src.singbox import generate_vless_outbound, is_singbox_installed, run_singbox
from src.utils import select_preset


def handle_subscription() -> None:
    """Ensures a valid subscription URL is present, prompting the user if not."""
    if settings.get_subscription_url():
        return

    print("You need to add a subscription first.")
    while True:
        try:
            sub_url = input("Paste your subscription link here: ").strip()
            if not is_subscription_url_valid(sub_url):
                print("The provided text is not a valid URL.")
                continue

            print("Trying to reach the given host...")
            if not is_subscription_url_reachable(sub_url):
                print("The host is not reachable.")
                continue

            settings.save_subscription_url(sub_url)
            print("Subscription link saved.")
            break
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            sys.exit(0)


def get_presets(force_update: bool) -> dict[str, VlessPreset]:
    """
    Loads presets from cache or fetches them from the subscription URL.
    The presets are stored as a dictionary mapping from the preset name to the
    VlessPreset object.
    """
    cached_presets = settings.get_presets()

    if not cached_presets or force_update:
        print("Fetching presets from subscription...")
        sub_url = settings.get_subscription_url()
        preset_urls = fetch_subscription_data(sub_url)
        parsed_presets = parse_presets(preset_urls)

        presets_to_save = {
            name.strip(): preset.__dict__ for name, preset in parsed_presets.items()
        }
        settings.save_presets(presets_to_save)
        return parsed_presets

    return {name: VlessPreset(**data) for name, data in cached_presets.items()}


def prepare_and_run(preset: VlessPreset, log_level: str, print_only: bool) -> None:
    """Generates the final config and either prints it or runs sing-box."""
    config_template = settings.get_config_template()
    outbound = generate_vless_outbound(preset)

    config_template["log"]["level"] = log_level
    config_template["outbounds"].append(outbound)

    if print_only:
        final_config_str = json.dumps(config_template, indent=2)
        print(final_config_str)
    else:
        settings.save_previous_preset(preset.name)
        run_singbox(config_template)


def main(args: Namespace) -> None:
    if not is_singbox_installed():
        print("`sing-box` needs to be installed. Please install it and try again.")
        sys.exit(1)

    handle_subscription()

    previous_preset_name = settings.get_previous_preset()
    presets = get_presets(force_update=args.update_subscription)

    selected_preset_name: str | None = None

    if args.run_previous and previous_preset_name:
        if previous_preset_name in presets:
            selected_preset_name = previous_preset_name
            print(f'Running previous preset: "{previous_preset_name}"')
        else:
            print(f'Warning: Previous preset "{previous_preset_name}" not found.')

    if not selected_preset_name:
        selected_preset_name = select_preset(presets)
        print(f"Selected preset: {selected_preset_name}")

    selected_preset = presets[selected_preset_name]
    prepare_and_run(selected_preset, args.log_level, args.print_config)


def create_parser() -> ArgumentParser:
    """Creates and configures the argument parser."""
    parser = ArgumentParser(description="A Python CLI for sing-box.")
    parser.add_argument(
        "-u",
        "--update-subscription",
        action="store_true",
        help="Update presets from the subscription link.",
    )
    parser.add_argument(
        "-c",
        "--print-config",
        action="store_true",
        help="Print generated config and exit.",
    )
    parser.add_argument(
        "-p",
        "--run-previous",
        action="store_true",
        help="Run the previously used preset.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["trace", "debug", "info", "warn", "error", "fatal", "panic"],
        default="warn",
        help="Set the log level for sing-box (default: warn).",
    )
    return parser


if __name__ == "__main__":
    cli_parser = create_parser()
    try:
        main(cli_parser.parse_args())
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
