from __future__ import annotations

import os
import re
import tomllib
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping

DEFAULT_TARGET_REGEX = r"(iec958|spdif|s/pdif|toslink|digital|usb.*(spdif|iec958))"


class ConfigError(ValueError):
    """Raised when configuration is invalid."""


@dataclass(frozen=True)
class Config:
    target: str | None = None
    target_regex: str = DEFAULT_TARGET_REGEX
    effective_amp: int = 4
    min_amp: int = 1
    max_amp: int = 512
    rate: int = 48_000
    channels: int = 2
    chunk_seconds: float = 0.10
    volume_check_seconds: float = 1.0
    format: str = "s16"
    pw_cat: str = "pw-cat"
    pactl: str = "pactl"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CONFIG_KEYS = frozenset(Config.__dataclass_fields__)

ENVIRONMENT_OVERRIDES: Mapping[str, tuple[str, Callable[[str], Any]]] = {
    "SPDIF_KEEPALIVE_TARGET": ("target", str),
    "SPDIF_KEEPALIVE_TARGET_REGEX": ("target_regex", str),
    "SPDIF_KEEPALIVE_EFFECTIVE_AMP": ("effective_amp", int),
    "SPDIF_KEEPALIVE_MIN_AMP": ("min_amp", int),
    "SPDIF_KEEPALIVE_MAX_AMP": ("max_amp", int),
    "SPDIF_KEEPALIVE_RATE": ("rate", int),
    "SPDIF_KEEPALIVE_CHANNELS": ("channels", int),
    "SPDIF_KEEPALIVE_CHUNK_SECONDS": ("chunk_seconds", float),
    "SPDIF_KEEPALIVE_VOLUME_CHECK_SECONDS": ("volume_check_seconds", float),
    "SPDIF_KEEPALIVE_FORMAT": ("format", str),
    "SPDIF_KEEPALIVE_PW_CAT": ("pw_cat", str),
    "SPDIF_KEEPALIVE_PACTL": ("pactl", str),
}


def default_config_path(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    if xdg_config_home := env.get("XDG_CONFIG_HOME"):
        return Path(xdg_config_home) / "spdif-keepalive" / "config.toml"

    home = Path(env.get("HOME") or Path.home())
    return home / ".config" / "spdif-keepalive" / "config.toml"


def build_config(
    *,
    config_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
    overrides: Mapping[str, Any] | None = None,
    require_config: bool = False,
) -> Config:
    env = os.environ if environ is None else environ
    path = config_path or default_config_path(env)
    config = Config()

    if path.exists():
        config = apply_mapping(config, load_toml(path), source=str(path))
    elif require_config:
        raise ConfigError(f"config file does not exist: {path}")

    config = apply_environment(config, env)
    if overrides:
        config = apply_mapping(config, present_values(overrides), source="command line")

    return validate_config(config)


def load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"config file must contain a TOML table: {path}")

    return data


def apply_environment(config: Config, environ: Mapping[str, str]) -> Config:
    values: dict[str, Any] = {}

    for env_name, (field_name, coercer) in ENVIRONMENT_OVERRIDES.items():
        if env_name not in environ:
            continue

        raw_value = environ[env_name]
        if raw_value == "" and field_name == "target":
            values[field_name] = None
            continue

        try:
            values[field_name] = coercer(raw_value)
        except ValueError as exc:
            raise ConfigError(f"{env_name} has invalid value {raw_value!r}") from exc

    return apply_mapping(config, values, source="environment")


def apply_mapping(config: Config, values: Mapping[str, Any], *, source: str) -> Config:
    unknown = sorted(set(values) - CONFIG_KEYS)
    if unknown:
        keys = ", ".join(unknown)
        raise ConfigError(f"unknown config key in {source}: {keys}")

    if not values:
        return config

    return replace(config, **dict(values))


def present_values(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def validate_config(config: Config) -> Config:
    if config.target is not None and not str(config.target).strip():
        raise ConfigError("target must not be blank")

    if not str(config.target_regex).strip() and config.target is None:
        raise ConfigError("target_regex must not be blank when target is not set")

    try:
        re.compile(config.target_regex)
    except re.error as exc:
        raise ConfigError(f"target_regex is invalid: {exc}") from exc

    if config.effective_amp < 1:
        raise ConfigError("effective_amp must be at least 1")

    if config.min_amp < 1:
        raise ConfigError("min_amp must be at least 1")

    if config.max_amp < config.min_amp:
        raise ConfigError("max_amp must be greater than or equal to min_amp")

    if config.rate < 1:
        raise ConfigError("rate must be positive")

    if config.channels < 1:
        raise ConfigError("channels must be positive")

    if config.chunk_seconds <= 0:
        raise ConfigError("chunk_seconds must be positive")

    if config.volume_check_seconds <= 0:
        raise ConfigError("volume_check_seconds must be positive")

    if config.format != "s16":
        raise ConfigError("only format='s16' is currently supported")

    if not config.pw_cat:
        raise ConfigError("pw_cat must not be blank")

    if not config.pactl:
        raise ConfigError("pactl must not be blank")

    return config
