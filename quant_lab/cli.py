"""Top-level command entry point for quant-lab package identity checks."""

from __future__ import annotations

import argparse
import json

from quant_lab import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quant_lab")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit package identity as JSON.",
    )
    args = parser.parse_args(argv)

    payload = {
        "product_name": "quant-lab",
        "python_import": "quant_lab",
        "version": __version__,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"{payload['product_name']} {payload['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
