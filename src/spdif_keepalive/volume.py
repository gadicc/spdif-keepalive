from __future__ import annotations

import re
import subprocess

DB_VALUE_RE = re.compile(r"/\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*dB")


def parse_volume_factor(pactl_output: str) -> float:
    db_values = [float(value) for value in DB_VALUE_RE.findall(pactl_output)]

    if not db_values:
        return 1.0

    db = sum(db_values) / len(db_values)
    return max(10 ** (db / 20.0), 0.000001)


def get_sink_volume_factor(sink_name: str, pactl: str = "pactl") -> float:
    try:
        output = subprocess.check_output(
            [pactl, "get-sink-volume", sink_name],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return 1.0

    return parse_volume_factor(output)


def calculate_amp(
    *,
    target_effective_amp: int,
    volume_factor: float,
    min_amp: int,
    max_amp: int,
) -> int:
    amp = round(target_effective_amp / max(volume_factor, 0.000001))
    return max(min_amp, min(max_amp, amp))
