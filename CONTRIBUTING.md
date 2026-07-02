# Contributing

## Local Tooling

On Arch Linux, install the tools used by the local checks and package build:

```bash
sudo pacman -S base-devel namcap python-build python-pytest
```

`makepkg` is Arch-specific. On other distributions, rely on the GitHub Actions validation job or run the Arch package test in an Arch container.

## Local Checks

Run the main local check suite:

```bash
scripts/check
```

This runs the Python tests, byte-compiles the package, builds a wheel, checks the system sleep hook with `bash -n`, runs `namcap` on the Arch `PKGBUILD`, and verifies `.SRCINFO` generation.

The script runs in a temporary copy of the working tree, so build outputs and Python cache files do not pollute the repository. The copy includes tracked files plus unignored untracked files, so you can test local edits before committing.

## Running From Checkout

Inspect the merged configuration without installing:

```bash
PYTHONPATH=src python -m spdif_keepalive.cli --print-config
```

List detected PipeWire/PulseAudio sinks:

```bash
PYTHONPATH=src python -m spdif_keepalive.cli --list-sinks
```

Run the keepalive stream directly:

```bash
PYTHONPATH=src python -m spdif_keepalive.cli -v
```

## Local Arch Package Test

Build the Arch package without requiring a GitHub release tag:

```bash
scripts/test-aur-package
```

The script creates a temporary source archive from the current working tree, rewrites `source` and `sha256sums` in a temporary `PKGBUILD`, runs `makepkg`, and runs `namcap` against the temporary `PKGBUILD` and built package.

It leaves the temporary build directory in `/tmp` by default and prints the built package path. To install the package after it builds:

```bash
scripts/test-aur-package --install
```

To remove the temporary build directory after the run:

```bash
scripts/test-aur-package --cleanup
```

`namcap` warnings are review prompts, not always hard failures. It can miss Python console-entry-point imports and can mark command/runtime dependencies as unnecessary when they are used by systemd units or subprocess calls rather than imported directly.

After installing a local package, useful smoke checks are:

```bash
spdif-keepalive --print-config
spdif-keepalive --list-sinks
systemctl --user daemon-reload
systemctl --user start spdif-keepalive.service
systemctl --user status spdif-keepalive.service
```

Stop the service when finished:

```bash
systemctl --user stop spdif-keepalive.service
```

## Versioning

`pyproject.toml`, `src/spdif_keepalive/__init__.py`, and `packaging/arch/PKGBUILD` must use the same version.

Use the helper script to bump all three files:

```bash
scripts/bump-version 0.1.1
```

Commit the version bump with the change it releases. The GitHub Actions workflow creates the `vX.Y.Z` tag during publishing. Do not create the tag manually when using the automated release workflow.

The workflow does not auto-bump versions. Keeping the version bump in a normal commit makes releases reviewable and avoids CI committing back to `main`, retriggering itself, or tagging a commit you did not explicitly push.

For Arch packaging-only changes where the upstream source version is unchanged, keep `pkgver` as-is and bump `pkgrel` in `packaging/arch/PKGBUILD` instead. Reset `pkgrel` to `1` whenever `pkgver` changes.

## GitHub Actions

The repository includes a workflow at `.github/workflows/publish-aur.yml`.

The `validate` job runs on every push, pull request, and manual dispatch. It does not need a GitHub release tag. It:

1. reads `project.version`
2. verifies `packaging/arch/PKGBUILD` has the same `pkgver`
3. verifies `src/spdif_keepalive/__init__.py` has the same `__version__`
4. runs the Python tests
5. byte-compiles the Python package
6. checks the system sleep hook with `bash -n`
7. builds a wheel
8. builds the Arch package in an Arch Linux container from a local `git archive`
9. runs `namcap` on the temporary `PKGBUILD` and built package

The `publish-aur` job runs only after validation passes and only on `main`. It:

1. creates tag `v${version}` if it does not already exist
2. generates release `sha256sums` and `.SRCINFO`
3. builds the Arch package from the GitHub release archive
4. runs `namcap`
5. pushes `PKGBUILD`, `.SRCINFO`, `LICENSE`, and `spdif-keepalive.install` to AUR, creating the AUR package repository on first publish if needed

That means a push to `main` is a release. To test without creating a tag, push a branch, open a pull request, or run the workflow manually with `publish` left unchecked.

## AUR SSH Setup

One AUR SSH key can be reused across projects, but a dedicated key per GitHub repository is cleaner because it can be revoked independently if a repo secret is exposed. AUR keys are account-scoped, not package-scoped, so per-repo keys are about operational hygiene rather than narrower permissions.

Create a dedicated passphrase-less key for this workflow:

```bash
ssh-keygen -t ed25519 \
  -C "aur-spdif-keepalive-github-actions" \
  -f ~/.ssh/aur_spdif_keepalive \
  -N ""
```

Add the public key to your AUR account:

```bash
cat ~/.ssh/aur_spdif_keepalive.pub
```

Then add the private key as a GitHub Actions secret:

```bash
gh secret set AUR_SSH_PRIVATE_KEY < ~/.ssh/aur_spdif_keepalive
```

The repository must also allow GitHub Actions to write tags. In GitHub settings, set Actions workflow permissions to `Read and write permissions`.

Useful links:

- AUR account: <https://aur.archlinux.org/account/>
- AUR submission guidelines: <https://wiki.archlinux.org/title/AUR_submission_guidelines>
- GitHub Actions secrets: <https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets>

## Manual AUR Publishing

The workflow should normally handle this. If manual publishing is needed:

1. create and push a GitHub tag, for example `v0.1.0`
2. run `updpkgsums` in `packaging/arch`
3. verify `sha256sums` is no longer `SKIP`
4. run `makepkg --printsrcinfo > .SRCINFO`
5. test with `makepkg -si`
6. commit `PKGBUILD`, `.SRCINFO`, `LICENSE`, and `spdif-keepalive.install` to the AUR Git repository
