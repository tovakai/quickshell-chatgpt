#!/usr/bin/env bash
set -euo pipefail

# Build a private, separate patched Quickshell. The Arch-managed binary is NOT
# replaced. The running end-4 process is NOT restarted by this script.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd -- "$script_dir/.." && pwd)"
work="${MABEL_BUILD_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/mabel-quickshell-build}"
prefix="${MABEL_QS_PREFIX:-${XDG_DATA_HOME:-$HOME/.local/share}/mabel-quickshell}"
src="$work/source"
build_dir="$work/build"
version=v0.3.2

for executable in git cmake ninja; do
  if ! command -v "$executable" >/dev/null 2>&1; then
    echo "Missing build tool: $executable" >&2
    echo 'Install required packages: sudo pacman -S --needed base-devel cmake ninja cli11 qt6-shadertools spirv-tools vulkan-headers wayland-protocols' >&2
    exit 1
  fi
done

mkdir -p "$work"
if [[ ! -d "$src/.git" ]]; then
  git clone --depth 1 --branch "$version" https://github.com/quickshell-mirror/quickshell.git "$src"
fi
if [[ "$(git -C "$src" describe --tags --exact-match HEAD)" != "$version" ]]; then
  echo "Refusing to patch unexpected Quickshell source checkout in $src" >&2
  exit 1
fi
if grep -q $'\tauto qArgC = 0;' "$src/src/launch/launch.cpp"; then
  git -C "$src" apply --check "$repo/patches/quickshell-webengine-argc.patch"
  git -C "$src" apply "$repo/patches/quickshell-webengine-argc.patch"
elif grep -q $'\tauto qArgC = 1;' "$src/src/launch/launch.cpp"; then
  echo 'QtWebEngine argc patch already applied.'
else
  echo 'Unexpected upstream argc code; refusing to continue.' >&2
  exit 1
fi

echo 'Building a private patched Quickshell; existing Arch package is untouched.'
cmake -S "$src" -B "$build_dir" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$prefix" \
  -DDISTRIBUTOR="Mabel local patched Quickshell"
cmake --build "$build_dir" --parallel "${MABEL_BUILD_JOBS:-4}"
cmake --install "$build_dir"

patched="$prefix/bin/quickshell"
if [[ ! -x "$patched" ]]; then
  echo "Patched binary not found at $patched; check CMake installation output." >&2
  exit 1
fi
echo "Built: $patched"
echo 'Testing QtWebEngine in an isolated process...'
MABEL_QS_BINARY="$patched" bash "$repo/scripts/check-webengine.sh"
echo
echo 'Patched Quickshell passed the isolated WebEngine startup test.'
echo 'Your active end-4 shell and system quickshell have NOT been changed.'
echo 'Next: MABEL_QS_BINARY="'"$patched"'" MABEL_URL="https://YOUR-MABEL-WEBUI-URL/" bash ./install.sh'
