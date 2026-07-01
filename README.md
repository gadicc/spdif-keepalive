# spdif-keepalive

`spdif-keepalive` keeps S/PDIF/TOSLINK optical audio outputs awake by playing a very low-level noise stream through a PipeWire sink.

Some optical audio chains treat near-silence as inactivity. In this setup, a Razer Leviathan connected over optical input through a USB-to-TOSLINK adapter goes into standby after enough quiet time. When real audio starts again, the first roughly 1.5 seconds can be lost. Short notification sounds may be missed entirely.

This tool avoids that by continuously sending barely perceptible stereo PCM noise that is loud enough to defeat the silence detector, but quiet enough to stay out of the way.

## How it works

`spdif-keepalive`:

- autodetects a digital-looking PipeWire/PulseAudio sink name, such as one containing `iec958`, `spdif`, `toslink`, or `digital`
- generates random signed 16-bit stereo PCM samples
- pipes those samples into `pw-cat --playback --raw`
- checks the sink volume with `pactl`
- adjusts the generated sample amplitude so the effective post-volume amplitude stays near the configured target

The default effective amplitude is `4`, which is the current known-good value for the original Cubilux USB-C to TOSLINK adapter and Razer Leviathan optical input setup.

## Requirements

- Linux
- systemd user services
- PipeWire with PulseAudio compatibility tools
- `pw-cat`
- `pactl`
- Python 3.11 or newer

On Arch Linux, the relevant runtime packages are usually:

```bash
sudo pacman -S python pipewire libpulse systemd
```

## Install from source

```bash
python -m pip install .
```

For a system-wide install, install the systemd assets too:

```bash
sudo install -Dm644 systemd/spdif-keepalive.service \
  /usr/lib/systemd/user/spdif-keepalive.service

sudo install -Dm755 systemd/spdif-keepalive-sleep \
  /usr/lib/systemd/system-sleep/spdif-keepalive
```

Then enable the user service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now spdif-keepalive.service
```

Check logs with:

```bash
journalctl --user -u spdif-keepalive.service -f
```

## Configuration

The best place for persistent user configuration is:

```text
~/.config/spdif-keepalive/config.toml
```

Create it only if the defaults are not enough:

```bash
mkdir -p ~/.config/spdif-keepalive
cp examples/config.toml ~/.config/spdif-keepalive/config.toml
```

Example:

```toml
# Exact sink override. Usually not needed if autodetection works.
target = "alsa_output.usb-Generic_USB_SPDIF_Adapter_202110200032-00.iec958-stereo"

# Or customize autodetection instead of pinning the full sink name.
# target_regex = "iec958|USB_SPDIF|Leviathan"

effective_amp = 4
min_amp = 1
max_amp = 512

rate = 48000
channels = 2
chunk_seconds = 0.10
volume_check_seconds = 1.0
```

Autodetection intentionally only picks sinks that look digital. If no sink matches, the service exits and systemd retries. This avoids accidentally playing the keepalive stream through normal speakers.

To inspect available sinks:

```bash
spdif-keepalive --list-sinks
```

To inspect the merged configuration:

```bash
spdif-keepalive --print-config
```

Configuration precedence is:

1. built-in defaults
2. `~/.config/spdif-keepalive/config.toml`
3. environment variables
4. command-line flags

## Environment overrides

The systemd unit loads this optional file:

```text
~/.config/spdif-keepalive/env
```

Use it when you prefer systemd-style overrides:

```systemd
SPDIF_KEEPALIVE_TARGET=alsa_output.usb-Generic_USB_SPDIF_Adapter_202110200032-00.iec958-stereo
SPDIF_KEEPALIVE_EFFECTIVE_AMP=4
SPDIF_KEEPALIVE_TARGET_REGEX="iec958|spdif|toslink|digital"
```

Supported environment variables:

- `SPDIF_KEEPALIVE_TARGET`
- `SPDIF_KEEPALIVE_TARGET_REGEX`
- `SPDIF_KEEPALIVE_EFFECTIVE_AMP`
- `SPDIF_KEEPALIVE_MIN_AMP`
- `SPDIF_KEEPALIVE_MAX_AMP`
- `SPDIF_KEEPALIVE_RATE`
- `SPDIF_KEEPALIVE_CHANNELS`
- `SPDIF_KEEPALIVE_CHUNK_SECONDS`
- `SPDIF_KEEPALIVE_VOLUME_CHECK_SECONDS`
- `SPDIF_KEEPALIVE_FORMAT`
- `SPDIF_KEEPALIVE_PW_CAT`
- `SPDIF_KEEPALIVE_PACTL`

## Suspend and resume

The optional system sleep hook stops active `spdif-keepalive.service` instances before suspend and restarts only those same instances after resume. This keeps `pw-cat` from writing into a disappearing USB or dock audio device.

The hook is generic: it does not hardcode a username.

The post-resume delay defaults to 3 seconds. Override it for the system hook with:

```bash
sudo systemctl edit systemd-suspend.service
```

Then add an environment override if needed:

```ini
[Service]
Environment=SPDIF_KEEPALIVE_RESUME_DELAY_SECONDS=5
```

## Arch Linux and AUR

An Arch packaging template lives in:

```text
packaging/arch/PKGBUILD
```

Before publishing to AUR:

1. replace `REPLACE_ME` in the package URL
2. create and push a GitHub tag, for example `v0.1.0`
3. replace `sha256sums=('SKIP')` with the real source archive checksum
4. run `makepkg --printsrcinfo > .SRCINFO`
5. test with `makepkg -si`

The package installs:

- `/usr/bin/spdif-keepalive`
- `/usr/lib/systemd/user/spdif-keepalive.service`
- `/usr/lib/systemd/system-sleep/spdif-keepalive`
- documentation under `/usr/share/doc/spdif-keepalive`

## Development

Run tests:

```bash
pytest
```

Run locally without installing:

```bash
PYTHONPATH=src python -m spdif_keepalive.cli --print-config
PYTHONPATH=src python -m spdif_keepalive.cli --list-sinks
```

Run the keepalive stream directly:

```bash
PYTHONPATH=src python -m spdif_keepalive.cli -v
```
