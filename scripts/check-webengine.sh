#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${MABEL_SKIP_WEBENGINE_CHECK:-0}" == 1 ]]; then
  echo 'WARNING: Skipping WebEngine crash probe by explicit request'
  exit 0
fi
if ! command -v timeout >/dev/null; then
  echo 'Need the coreutils timeout command' >&2
  exit 1
fi
qs="${MABEL_QS_BINARY:-$(command -v quickshell || command -v qs || true)}"
if [[ -n "${MABEL_QS_BINARY:-}" && ! -x "$qs" ]]; then
  echo "MABEL_QS_BINARY is not executable: $qs" >&2
  exit 1
fi
if [[ -z "$qs" ]]; then
  echo 'Quickshell executable not found (quickshell/qs)' >&2
  exit 1
fi
if command -v pacman >/dev/null && ! pacman -Q qt6-webengine >/dev/null 2>&1; then
  echo 'Qt WebEngine missing. Install: sudo pacman -S qt6-webengine' >&2
  exit 1
fi
log="$(mktemp)"
trap 'rm -f "$log"' EXIT
set +e
timeout --signal=TERM 7s "$qs" -p "$repo/tests/webengine-probe.qml" >"$log" 2>&1
status="$?"
set -e
if [[ "$status" -eq 124 ]] && ! grep -Eqi 'FATAL|QML.*(Error|not installed)|Argument list is empty|failed to load' "$log"; then
  echo 'Isolated QtWebEngine probe succeeded. Existing desktop shell untouched.'
  exit 0
fi
echo 'QtWebEngine cannot safely start in this Quickshell build.' >&2
echo 'Nothing has been installed or replaced.' >&2
echo 'Stock Quickshell 0.3.2 currently crashes with argc=0 when creating WebEngineView.' >&2
echo 'See upstream issue: https://github.com/quickshell-mirror/quickshell/issues/1393' >&2
tail -n 25 "$log" >&2
exit 1
