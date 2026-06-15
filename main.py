#!/usr/bin/env python
import json
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import asdict

from src.models import VlessPreset
from src.network import fetch_subscription_data, is_subscription_url_valid
from src.parser import parse_presets
from src.repository import repo
from src.selection import select_preset
from src.singbox import build_config_from_template, ensure_singbox, run_singbox
from src.urltest import run_url_test


def _get_all_presets() -> list[VlessPreset]:
    raw = repo.get_presets()
    return [VlessPreset(**d) for presets in raw.values() for d in presets]


def _require_presets() -> list[VlessPreset]:
    if not repo.get_subscription_urls():
        print("no subscriptions found. use `uwuray subscription add <url>` to add one.")
        sys.exit(1)
    presets = _get_all_presets()
    if not presets:
        print("no cached presets. run `uwuray subscription update` to fetch.")
        sys.exit(1)
    return presets


def _prepare_and_run(
    preset: VlessPreset, log_level: str, proxy_all: bool, print_only: bool
) -> None:
    template = repo.get_config_template()
    config = build_config_from_template(template, preset, log_level, proxy_all)

    if print_only:
        print(json.dumps(config, indent=2))
    else:
        ensure_singbox()
        repo.set_previous_preset(preset.name)
        run_singbox(config)


def cmd_run(args: Namespace) -> None:
    presets = _require_presets()
    previous_preset_name = repo.get_previous_preset()
    selected_preset: VlessPreset | None = None

    if args.previous and previous_preset_name:
        selected_preset = next(
            (p for p in presets if p.name == previous_preset_name), None
        )
        if selected_preset:
            print(f'running previous preset: "{previous_preset_name}"')
        else:
            print(f'warning: previous preset "{previous_preset_name}" not found.')

    if not selected_preset:
        selected_preset = select_preset(presets)
        if not selected_preset:
            return
        print(f"selected preset: {selected_preset.name}")

    _prepare_and_run(selected_preset, args.log_level, args.proxy_all, args.print_config)


def cmd_test(_args: Namespace) -> None:
    presets = _require_presets()
    ensure_singbox()
    print(f"testing {len(presets)} presets...")
    results = run_url_test(presets)
    results.sort(key=lambda r: (r[1] is None, r[1] or 0))
    width = max(len(p.name) for p, _ in results)
    for preset, delay in results:
        delay_str = f"{delay} ms" if delay is not None else "timeout"
        print(f"{preset.name:<{width}}  {delay_str}")


def cmd_subscription_add(args: Namespace) -> None:
    url = args.url.strip()
    if not is_subscription_url_valid(url):
        print("invalid url.")
        sys.exit(1)
    if url in repo.get_subscription_urls():
        print("subscription already exists.")
        return
    repo.add_subscription(url)
    print("subscription saved.")


def cmd_subscription_update(_args: Namespace) -> None:
    urls = repo.get_subscription_urls()
    if not urls:
        print("no subscriptions found. use `uwuray subscription add <url>` to add one.")
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


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="uwuray", description="A Python CLI for sing-box.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Select and run a preset.")
    run.add_argument(
        "-p",
        "--previous",
        action="store_true",
        help="Run the previously used preset.",
    )
    run.add_argument(
        "-c",
        "--print-config",
        action="store_true",
        help="Print generated config and exit.",
    )
    run.add_argument(
        "-l",
        "--log-level",
        choices=["trace", "debug", "info", "warn", "error", "fatal", "panic"],
        default="warn",
        help="Set the log level for sing-box (default: warn).",
    )
    run.add_argument(
        "-a",
        "--proxy-all",
        action="store_true",
        help="Proxy all trafic through vless.",
    )
    run.set_defaults(func=cmd_run)

    test = sub.add_parser("test", help="Test real delay of all presets.")
    test.set_defaults(func=cmd_test)

    subscription = sub.add_parser(
        "subscription", aliases=["sub"], help="Manage subscriptions."
    )
    sub_cmd = subscription.add_subparsers(dest="sub_command", required=True)
    add = sub_cmd.add_parser("add", help="Add a subscription URL.")
    add.add_argument("url")
    add.set_defaults(func=cmd_subscription_add)
    update = sub_cmd.add_parser(
        "update", help="Fetch and update presets for each subscription."
    )
    update.set_defaults(func=cmd_subscription_update)

    return parser


def main() -> None:
    cli_parser = create_parser()
    try:
        args = cli_parser.parse_args()
        args.func(args)
    except KeyboardInterrupt:
        print("\nexiting.")
    except Exception as e:
        print(f"an unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
