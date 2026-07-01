from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from .config import ConfigError, build_config
from .runner import run_keepalive
from .sinks import SinkDetectionError, format_sinks, list_sinks


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    overrides = {
        "target": args.target,
        "target_regex": args.target_regex,
        "effective_amp": args.effective_amp,
        "min_amp": args.min_amp,
        "max_amp": args.max_amp,
        "rate": args.rate,
        "channels": args.channels,
        "chunk_seconds": args.chunk_seconds,
        "volume_check_seconds": args.volume_check_seconds,
        "format": args.format,
        "pw_cat": args.pw_cat,
        "pactl": args.pactl,
    }

    try:
        config = build_config(
            config_path=args.config,
            overrides=overrides,
            require_config=args.config is not None,
        )

        if args.print_config:
            print(json.dumps(config.to_dict(), indent=2, sort_keys=True))
            return 0

        if args.list_sinks:
            print(format_sinks(list_sinks(config.pactl)))
            return 0

        return run_keepalive(config)
    except (ConfigError, SinkDetectionError, RuntimeError) as exc:
        logging.error("%s", exc)
        return 2


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="spdif-keepalive",
        description=(
            "Keep S/PDIF/TOSLINK outputs awake by playing very low-level raw "
            "PCM noise through PipeWire."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="TOML config path; defaults to ~/.config/spdif-keepalive/config.toml",
    )
    parser.add_argument(
        "--target",
        help="Exact PipeWire/Pulse sink name. If omitted, an S/PDIF-like sink is autodetected.",
    )
    parser.add_argument(
        "--target-regex",
        help="Case-insensitive regex used for autodetecting a sink name.",
    )
    parser.add_argument(
        "--effective-amp",
        type=int,
        help="Desired effective post-volume s16 amplitude. Default: 4.",
    )
    parser.add_argument("--min-amp", type=int, help="Minimum generated s16 amplitude.")
    parser.add_argument("--max-amp", type=int, help="Maximum generated s16 amplitude.")
    parser.add_argument("--rate", type=int, help="PCM sample rate. Default: 48000.")
    parser.add_argument("--channels", type=int, help="PCM channel count. Default: 2.")
    parser.add_argument(
        "--chunk-seconds",
        type=float,
        help="PCM chunk duration. Smaller values react to volume changes faster.",
    )
    parser.add_argument(
        "--volume-check-seconds",
        type=float,
        help="How often to sample sink volume and adjust generated amplitude.",
    )
    parser.add_argument("--format", help="pw-cat sample format. Only s16 is supported.")
    parser.add_argument("--pw-cat", help="pw-cat command path.")
    parser.add_argument("--pactl", help="pactl command path.")
    parser.add_argument(
        "--list-sinks",
        action="store_true",
        help="Print available sinks and exit.",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print merged config and exit.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity.",
    )

    return parser.parse_args(argv)


def configure_logging(verbose: int) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
