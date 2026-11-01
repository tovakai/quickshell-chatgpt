#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config="${QS_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/quickshell/ii}"
target="$config/modules/ii/sidebarLeft/AiChat.qml"
backup="$target.before-mabel"
mode="${1:-install}"

if [[ "$mode" == restore ]]; then
  if [[ ! -f "$backup" ]]; then
    echo "No backup found at $backup" >&2
    exit 1
  fi
  cp -p -- "$backup" "$target"
  echo "Restored original end-4 AI panel: $target"
  exit 0
fi
if [[ "$mode" != install ]]; then
  echo "Usage: bash install.sh [install|restore]" >&2
  exit 2
fi
if [[ ! -f "$target" ]]; then
  echo "end-4's real AiChat.qml not found at $target" >&2
  echo 'Set QS_CONFIG_DIR to the directory containing the active end-4 shell.qml.' >&2
  echo 'Not installing a separate floating Chromium app.' >&2
  exit 1
fi

# This probe runs its own independent Quickshell process BEFORE changing
# end-4's active QML. Stock builds crash if QtWebEngine is instantiated.
bash "$repo/scripts/check-webengine.sh"

url="${MABEL_URL:-http://127.0.0.1:7000/}"
python3 - "$repo/end4/AiChat.qml" "$target" "$backup" "$url" <<'PY'
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlsplit

source, target, backup = (Path(sys.argv[i]) for i in (1, 2, 3))
url = sys.argv[4].strip()
parsed = urlsplit(url)
if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
    raise SystemExit("MABEL_URL must be the HTTP(S) address of the real Mabel WebUI")
if parsed.port == 8080:
    raise SystemExit("Port 8080 is your Strata server, not Mabel. Use the Mabel WebUI URL.")
template = source.read_text()
replacement = template.replace("__MABEL_URL_JSON__", json.dumps(url))
if replacement == template:
    raise SystemExit("URL placeholder not found in bundled QML")
if backup.exists():
    if target.read_text() != replacement and "mabel-sidebar" not in target.read_text():
        raise SystemExit("Refusing to overwrite a changed end-4 AI panel while an existing Mabel backup is present")
else:
    shutil.copy2(target, backup)
temp = target.with_name("AiChat.qml.mabel-new")
temp.write_text(replacement)
os.replace(temp, target)
print("Original end-4 AI panel backed up:", backup)
print("Installed real Mabel WebUI inside existing end-4 left sidebar:", target)
print("Mabel URL:", url)
print("Reload end-4 Quickshell using your existing reload shortcut, then Win+A.")
PY
