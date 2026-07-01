from __future__ import annotations

import pytest

from spdif_keepalive.config import ConfigError, build_config


def test_default_effective_amp_is_four() -> None:
    config = build_config(environ={"HOME": "/tmp/no-such-home"})

    assert config.effective_amp == 4


def test_precedence_is_file_then_environment_then_cli(tmp_path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("effective_amp = 19\nmax_amp = 128\n", encoding="utf-8")

    config = build_config(
        config_path=config_file,
        environ={"SPDIF_KEEPALIVE_EFFECTIVE_AMP": "8"},
        overrides={"effective_amp": 4},
    )

    assert config.effective_amp == 4
    assert config.max_amp == 128


def test_unknown_config_key_is_rejected(tmp_path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("typo_amp = 4\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="unknown config key"):
        build_config(config_path=config_file)


def test_invalid_regex_is_rejected(tmp_path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text('target_regex = "("\n', encoding="utf-8")

    with pytest.raises(ConfigError, match="target_regex is invalid"):
        build_config(config_path=config_file)
