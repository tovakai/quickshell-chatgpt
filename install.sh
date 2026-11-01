#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")" && pwd)"
data="$HOME/.local/share/mabel-quickshell"
config="$HOME/.config/quickshell/mabel"
mkdir -p "$data/bridge" "$config"
install -m 644 "$repo/bridge/__init__.py" "$repo/bridge/client.py" "$repo/bridge/protocol.py" "$repo/bridge/__main__.py" "$data/bridge/"
install -m 644 "$repo/quickshell/shell.qml" "$config/shell.qml"
printf 'Installed standalone Mabel sidebar to %s\n' "$config/shell.qml"
printf 'Run: quickshell -p %s\n' "$config/shell.qml"
printf 'MABEL_URL defaults to http://127.0.0.1:7000 (Odysseus, never Strata).\n'
