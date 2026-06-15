#!/usr/bin/env python
import json
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import asdict

from src.models import VlessPreset
from src.network import fetch_subscription_data, is_subscription_url_valid
from src.parser import parse_presets
from src.repository import repo
from src.singbox import generate_vless_outbound, is_singbox_installed, run_singbox
from src.urltest import run_url_test
from src.utils import select_preset


def update_subscriptions() -> None:
    urls = repo.get_subscription_urls()
    if not urls:
        print("no subscriptions found. use -s/--add-subscription <url> to add one.")
        sys.exit(1)
    for url in urls:
        print(f"fetching {url}...")
        try:
            preset_urls = fetch_subscription_data(url)
            parsed = parse_presets(preset_urls)
            repo.set_presets_for_url(url, [asdict(p) for p in parsed])
            print(f"saved {len(parsed)} presets.")
        except Exception as e:
            print(f"failed: {e}")


def get_presets() -> dict[str, list[VlessPreset]]:
    raw = repo.get_presets()
    urls = repo.get_subscription_urls()
    result: dict[str, list[VlessPreset]] = {}
    for url in urls:
        result[url] = [VlessPreset(**d) for d in raw.get(url, [])]
    return result


def prepare_and_run(
    preset: VlessPreset, log_level: str, proxy_all: bool, print_only: bool
) -> None:
    """Generates the final config and either prints it or runs sing-box."""
    config_template = repo.get_config_template()
    outbound = generate_vless_outbound(preset)

    config_template["log"]["level"] = log_level
    config_template["outbounds"].append(outbound)
    if proxy_all:
        config_template["dns"]["rules"] = []
        config_template["route"]["rules"] = [
            {"protocol": "dns", "action": "hijack-dns"}
        ]
        config_template["route"]["final"] = "vless-out"

    if print_only:
        final_config_str = json.dumps(config_template, indent=2)
        print(final_config_str)
    else:
        if not is_singbox_installed():
            print("`sing-box` needs to be installed. Please install it and try again.")
            sys.exit(1)
        repo.set_previous_preset(preset.name)
        run_singbox(config_template)


def main(args: Namespace) -> None:
    if args.add_subscription:
        url = args.add_subscription.strip()
        if not is_subscription_url_valid(url):
            print("invalid url.")
            sys.exit(1)
        if url in repo.get_subscription_urls():
            print("subscription already exists.")
            sys.exit(0)
        repo.add_subscription(url)
        print("subscription saved.")
        sys.exit(0)

    if args.update_subscription:
        update_subscriptions()
        sys.exit(0)

    urls = repo.get_subscription_urls()
    if not urls:
        print("no subscriptions found. use -s/--add-subscription <url> to add one.")
        sys.exit(1)

    presets_by_url = get_presets()
    if not any(presets_by_url.values()):
        print("no cached presets. run with -u to fetch.")
        sys.exit(1)

    if args.url_test:
        if not is_singbox_installed():
            print("`sing-box` needs to be installed. Please install it and try again.")
            sys.exit(1)
        flat_presets = [p for presets in presets_by_url.values() for p in presets]
        print(f"testing {len(flat_presets)} presets...")
        results = run_url_test(flat_presets)
        results.sort(key=lambda r: (r[1] is None, r[1]))
        width = max(len(p.name) for p, _ in results)
        for preset, delay in results:
            delay_str = f"{delay} ms" if delay is not None else "timeout"
            print(f"{preset.name:<{width}}  {delay_str}")
        sys.exit(0)

    previous_preset_name = repo.get_previous_preset()
    selected_preset: VlessPreset | None = None

    if args.run_previous and previous_preset_name:
        for presets in presets_by_url.values():
            for preset in presets:
                if preset.name == previous_preset_name:
                    selected_preset = preset
                    print(f'running previous preset: "{previous_preset_name}"')
                    break
            if selected_preset:
                break
        if not selected_preset:
            print(f'warning: previous preset "{previous_preset_name}" not found.')

    if not selected_preset:
        flat_presets = [p for presets in presets_by_url.values() for p in presets]
        selected_preset = select_preset(flat_presets)
        if not selected_preset:
            return
        print(f"selected preset: {selected_preset.name}")

    prepare_and_run(selected_preset, args.log_level, args.proxy_all, args.print_config)


def create_parser() -> ArgumentParser:
    """Creates and configures the argument parser."""
    parser = ArgumentParser(description="A Python CLI for sing-box.")
    parser.add_argument(
        "-u",
        "--update-subscription",
        action="store_true",
        help="Fetch and update presets for each subscription, then exit.",
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
    parser.add_argument(
        "-a",
        "--proxy-all",
        action="store_true",
        help="Proxy all trafic through vless.",
    )
    parser.add_argument(
        "-s",
        "--add-subscription",
        metavar="URL",
        help="Add a subscription URL.",
    )
    parser.add_argument(
        "-t",
        "--url-test",
        action="store_true",
        help="Test real delay of all presets and exit.",
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
