from __future__ import annotations

import logging
import signal
import subprocess
from types import FrameType

from .config import Config
from .pcm import generate_chunk
from .sinks import choose_sink, list_sinks
from .volume import calculate_amp, get_sink_volume_factor

logger = logging.getLogger(__name__)


def run_keepalive(config: Config) -> int:
    sinks = [] if config.target else list_sinks(config.pactl)
    target = choose_sink(sinks, target=config.target, target_regex=config.target_regex)
    frames_per_chunk = max(1, int(config.rate * config.chunk_seconds))
    chunks_per_volume_check = max(
        1,
        round(config.volume_check_seconds / config.chunk_seconds),
    )

    command = [
        config.pw_cat,
        "--playback",
        "--raw",
        "--target",
        target,
        "--rate",
        str(config.rate),
        "--channels",
        str(config.channels),
        "--format",
        config.format,
        "-",
    ]

    logger.info("using sink: %s", target)
    logger.debug("starting: %s", " ".join(command))

    stop_requested = False

    def request_stop(signum: int, _frame: FrameType | None) -> None:
        nonlocal stop_requested
        logger.info("received signal %s, stopping", signum)
        stop_requested = True

    previous_sigterm = signal.signal(signal.SIGTERM, request_stop)
    previous_sigint = signal.signal(signal.SIGINT, request_stop)

    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        if process.stdin is None:
            raise RuntimeError("pw-cat stdin pipe was not created")

        amp = _current_amp(config, target)
        chunk_count = 0

        while not stop_requested:
            if process.poll() is not None:
                return process.returncode or 1

            if chunk_count % chunks_per_volume_check == 0:
                amp = _current_amp(config, target)

            process.stdin.write(
                generate_chunk(
                    frames=frames_per_chunk,
                    channels=config.channels,
                    amp=amp,
                )
            )
            process.stdin.flush()
            chunk_count += 1

        process.stdin.close()
        return _wait_or_terminate(process)
    except BrokenPipeError:
        if process is not None:
            return process.poll() or 1
        return 1
    except FileNotFoundError as exc:
        missing = exc.filename or command[0]
        raise RuntimeError(f"could not find command: {missing}") from exc
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        signal.signal(signal.SIGINT, previous_sigint)

        if process is not None and process.poll() is None:
            process.terminate()
            _wait_or_terminate(process)


def _current_amp(config: Config, target: str) -> int:
    volume_factor = get_sink_volume_factor(target, config.pactl)
    amp = calculate_amp(
        target_effective_amp=config.effective_amp,
        volume_factor=volume_factor,
        min_amp=config.min_amp,
        max_amp=config.max_amp,
    )
    logger.debug("volume_factor=%.4f amp=%d", volume_factor, amp)
    return amp


def _wait_or_terminate(process: subprocess.Popen[bytes]) -> int:
    try:
        return process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            return process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait()
