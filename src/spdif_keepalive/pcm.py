from __future__ import annotations

import random
import struct
from random import Random


def generate_chunk(
    *,
    frames: int,
    channels: int,
    amp: int,
    rng: Random | None = None,
) -> bytes:
    if frames < 1:
        raise ValueError("frames must be positive")

    if channels < 1:
        raise ValueError("channels must be positive")

    source = rng or random
    sample_format = struct.Struct("<" + ("h" * channels))
    chunk = bytearray()

    for _ in range(frames):
        sample = amp if source.getrandbits(1) else -amp
        chunk.extend(sample_format.pack(*([sample] * channels)))

    return bytes(chunk)
