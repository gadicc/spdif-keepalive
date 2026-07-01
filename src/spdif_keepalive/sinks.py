from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Iterable


class SinkDetectionError(RuntimeError):
    """Raised when no suitable sink can be found."""


@dataclass(frozen=True)
class Sink:
    index: str
    name: str
    driver: str = ""
    sample_spec: str = ""
    state: str = ""
    raw: str = ""


def list_sinks(pactl: str = "pactl") -> list[Sink]:
    try:
        output = subprocess.check_output(
            [pactl, "list", "short", "sinks"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        raise SinkDetectionError(f"could not find pactl command: {pactl}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.output.strip()
        message = f"could not list sinks with {pactl}"
        if detail:
            message = f"{message}: {detail}"
        raise SinkDetectionError(message) from exc

    return parse_short_sinks(output)


def parse_short_sinks(output: str) -> list[Sink]:
    sinks: list[Sink] = []

    for line in output.splitlines():
        if not line.strip():
            continue

        fields = line.split("\t")
        if len(fields) < 2:
            fields = line.split()

        if len(fields) < 2:
            continue

        padded = fields + [""] * 5
        sinks.append(
            Sink(
                index=padded[0],
                name=padded[1],
                driver=padded[2],
                sample_spec=padded[3],
                state=padded[4],
                raw=line,
            )
        )

    return sinks


def choose_sink(sinks: Iterable[Sink], *, target: str | None, target_regex: str) -> str:
    if target:
        return target

    pattern = re.compile(target_regex, re.IGNORECASE)
    matches = [sink.name for sink in sinks if pattern.search(sink.name)]

    if matches:
        return matches[0]

    raise SinkDetectionError(
        "could not autodetect an S/PDIF-like sink; run "
        "`spdif-keepalive --list-sinks` and set target or target_regex"
    )


def format_sinks(sinks: Iterable[Sink]) -> str:
    lines = []

    for sink in sinks:
        suffix = f" [{sink.state}]" if sink.state else ""
        lines.append(f"{sink.index}\t{sink.name}{suffix}")

    return "\n".join(lines)
