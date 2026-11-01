#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "$0")" && pwd)"
bin="$HOME/.local/bin"
config="$HOME/.config/quickshell/mabel"
mkdir -p "$bin" "$config"
install -m 755 "$repo/scripts/mabel-webui" "$bin/mabel-webui"
install -m 644 "$repo/quickshell/shell.qml" "$config/shell.qml"
printf 'Installed Mabel WebUI launcher: %s\n' "$bin/mabel-webui"
printf 'Toggle: %s toggle\n' "$bin/mabel-webui"
printf 'Optional Quickshell edge tab: quickshell -p %s/shell.qml\n' "$config"
printf 'This invokes the real WebUI. No separate chat bridge or token.\n'
