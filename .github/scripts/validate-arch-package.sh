#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_VERSION:?PROJECT_VERSION must be set}"

workdir="/tmp/spdif-keepalive-aur-validate"
archive="spdif-keepalive-${PROJECT_VERSION}.tar.gz"

rm -rf "$workdir"
mkdir -p "$workdir"

cd /workspace
git -c safe.directory=/workspace archive \
  --format=tar \
  --prefix="spdif-keepalive-${PROJECT_VERSION}/" \
  HEAD | gzip -n >"$workdir/$archive"

cp packaging/arch/PKGBUILD "$workdir/PKGBUILD"
cp packaging/arch/LICENSE "$workdir/LICENSE"
cp packaging/arch/spdif-keepalive.install "$workdir/spdif-keepalive.install"

cd "$workdir"
sed -i 's#^source=.*#source=("${pkgname}-${pkgver}.tar.gz")#' PKGBUILD

checksum="$(sha256sum "$archive" | cut -d " " -f 1)"
sed -i "s#^sha256sums=.*#sha256sums=('${checksum}')#" PKGBUILD

makepkg --printsrcinfo >.SRCINFO
makepkg --clean --cleanbuild --force --noconfirm
namcap PKGBUILD
namcap ./*.pkg.tar.*
