#!/usr/bin/env python
import base64
import json
import sys
from argparse import ArgumentParser, Namespace

import requests

from src.config import settings
from src.utils import (
    generate_vless_outbound,
    is_singbox_installed,
    is_subscription_url_reachable,
    is_subscription_url_valid,
    parse_presets,
    run_singbox,
    select_preset,
)


def main(args: Namespace) -> None:
    if not is_singbox_installed():
        print("`sing-box` needs to be installed")
        sys.exit()

    previous_preset = settings.PREVIOUS_PRESET.read_text()
    parsed_presets = json.loads(settings.PRESETS.read_text())
    config_template = json.loads(settings.CONFIG_TEMPLATE.read_text())

    if args.run_previous and previous_preset:
        selected_preset = previous_preset
        print(f'Running previous template: "{previous_preset.strip()}"')
    else:
        subscription = settings.SUBSCRIPTION.read_text()

        if not subscription:
            print("You need to add subscription first")
            sub_url = None
            while not sub_url:
                sub_url = input("Paste your subscription link here: ").strip()

                if not is_subscription_url_valid(sub_url):
                    print("Given text is not a valid url")
                    sub_url = None
                    continue

                print("Tring to reach given host")
                if not is_subscription_url_reachable(sub_url):
                    print("Given text is not reachable")
                    sub_url = None
                    continue

            settings.SUBSCRIPTION.write_text(sub_url)
            print("Subscription link is saved")

        if not parsed_presets or args.update_subscription:
            sub_url = settings.SUBSCRIPTION.read_text()
            response = requests.get(sub_url)
            preset_urls = base64.b64decode(response.text).decode().splitlines()
            parsed_presets = parse_presets(preset_urls)
            settings.PRESETS.write_text(
                json.dumps(parsed_presets, ensure_ascii=False, indent=2)
            )

        selected_preset = select_preset(parsed_presets)

    outbound = generate_vless_outbound(parsed_presets[selected_preset])
    config_template["outbounds"].append(outbound)
    final_config = json.dumps(config_template, indent=2)

    if args.print_config:
        print(final_config)
    else:
        run_singbox(final_config)
        settings.PREVIOUS_PRESET.write_text(selected_preset)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-u", "--update-subscription", help="Update subscription")
    parser.add_argument(
        "-s",
        "--print-config",
        action="store_true",
        help="Print generated config and exit",
    )
    parser.add_argument(
        "-p", "--run-previous", action="store_true", help="Run previous preset"
    )

    try:
        main(parser.parse_args())
    except KeyboardInterrupt:
        pass
