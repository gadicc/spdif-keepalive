from __future__ import annotations

import random
import struct

from spdif_keepalive.pcm import generate_chunk


def test_generate_chunk_length() -> None:
    chunk = generate_chunk(frames=4800, channels=2, amp=4, rng=random.Random(1))

    assert len(chunk) == 4800 * 2 * 2


def test_generate_chunk_duplicates_sample_to_each_channel() -> None:
    chunk = generate_chunk(frames=8, channels=2, amp=4, rng=random.Random(1))
    samples = struct.unpack("<" + ("h" * 16), chunk)

    for left, right in zip(samples[0::2], samples[1::2]):
        assert left == right
        assert abs(left) == 4
