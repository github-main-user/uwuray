#!/usr/bin/env python
import base64
import json
import sys

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


def main() -> None:
    # TODO: see also for `fzf`
    if not is_singbox_installed():
        print("`sing-box` needs to be installed")
        sys.exit()

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

    # TODO: do only if args.parse == True, or if there are no presets:
    sub_url = settings.SUBSCRIPTION.read_text()
    response = requests.get(sub_url)
    preset_urls = base64.b64decode(response.text).decode().splitlines()
    parsed_presets = parse_presets(preset_urls)
    settings.PRESETS.write_text(
        json.dumps(parsed_presets, ensure_ascii=False, indent=2)
    )

    # Another part
    config_template = json.loads(settings.CONFIG_TEMPLATE.read_text())
    selected_preset = select_preset(parsed_presets)
    outbound = generate_vless_outbound(parsed_presets[selected_preset])
    config_template["outbounds"].append(outbound)
    final_config = json.dumps(config_template)

    run_singbox(final_config)


if __name__ == "__main__":
    # TODO: arguments
    # --log-lefel
    # --parse

    try:
        main()
    except KeyboardInterrupt:
        pass
