from __future__ import annotations

import math

from spdif_keepalive.volume import calculate_amp, parse_volume_factor


def test_parse_volume_factor_averages_channel_db_values() -> None:
    output = (
        "Volume: front-left: 32768 /  50% / -6.00 dB, "
        "front-right: 32768 /  50% / -6.00 dB"
    )

    assert math.isclose(parse_volume_factor(output), 0.501187, rel_tol=0.00001)


def test_parse_volume_factor_defaults_to_one_without_db_values() -> None:
    assert parse_volume_factor("Volume: 65536 / 100%") == 1.0


def test_calculate_amp_compensates_for_sink_volume() -> None:
    assert calculate_amp(
        target_effective_amp=4,
        volume_factor=0.5,
        min_amp=1,
        max_amp=512,
    ) == 8


def test_calculate_amp_clamps_to_safety_rails() -> None:
    assert calculate_amp(
        target_effective_amp=4,
        volume_factor=0.001,
        min_amp=1,
        max_amp=512,
    ) == 512
