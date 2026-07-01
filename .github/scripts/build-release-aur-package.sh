#!/usr/bin/env bash
set -euo pipefail

cd /workspace/packaging/arch

updpkgsums
makepkg --printsrcinfo >.SRCINFO
makepkg --clean --cleanbuild --force --noconfirm
namcap PKGBUILD
namcap ./*.pkg.tar.*
