from __future__ import annotations

import pytest

from spdif_keepalive.sinks import SinkDetectionError, choose_sink, parse_short_sinks


PACTL_SHORT_OUTPUT = """\
42\talsa_output.pci-0000_00_1f.3.analog-stereo\tPipeWire\ts16le 2ch 48000Hz\tRUNNING
43\talsa_output.usb-Generic_USB_SPDIF_Adapter_202110200032-00.iec958-stereo\tPipeWire\ts16le 2ch 48000Hz\tIDLE
"""


def test_parse_short_sinks() -> None:
    sinks = parse_short_sinks(PACTL_SHORT_OUTPUT)

    assert sinks[0].index == "42"
    assert sinks[1].name.endswith("iec958-stereo")


def test_choose_sink_returns_explicit_target_without_matching() -> None:
    assert choose_sink([], target="my-sink", target_regex="iec958") == "my-sink"


def test_choose_sink_detects_digital_sink() -> None:
    sinks = parse_short_sinks(PACTL_SHORT_OUTPUT)

    assert choose_sink(sinks, target=None, target_regex="iec958").endswith("iec958-stereo")


def test_choose_sink_errors_when_no_match() -> None:
    sinks = parse_short_sinks(PACTL_SHORT_OUTPUT)

    with pytest.raises(SinkDetectionError):
        choose_sink(sinks, target=None, target_regex="does-not-exist")
