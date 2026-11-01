# Mabel in end-4's actual Win+A left sidebar

**Behavioral contract:** Win+A opens/closes end-4's EXISTING left sidebar. Same animation, focus, Escape, outside-click dismissal, pinning and detachment. Only the AI tab changes: it embeds Mabel's original responsive WebUI through QtWebEngine. Mabel itself handles sessions, memory, agent tools, browser login and interactive tool approvals. No API-token bridge; no separate Chromium window; no direct Strata calls.

This is a drop-in replacement for end-4 `AiChat.qml`, **not** a second Quickshell configuration. The existing `SidebarLeft.qml` and Hyprland keybind are left alone.

## Reproduced Quickshell crash, and the fix

On stock Quickshell 0.3.2, QtWebEngine aborts because `src/launch/launch.cpp` passes `argc=0` to `QGuiApplication`. Qt requires `argc>=1`; see https://github.com/quickshell-mirror/quickshell/issues/1393 . The one-line source patch included here changes `auto qArgC = 0;` to `auto qArgC = 1;`.

The installer runs an isolated startup test first and refuses to modify the actual end-4 config unless that probe passes. **Do not skip the test on the stock binary.**

### Step 1: build a separate, patched Quickshell without touching the active desktop

On Arch, from this repo:

    sudo pacman -S --needed base-devel cmake ninja cli11 qt6-shadertools spirv-tools vulkan-headers wayland-protocols qt6-webengine
    bash scripts/build-patched-quickshell.sh

The helper checks out tagged upstream `v0.3.2`, applies the one-line patch, builds to `~/.local/share/mabel-quickshell/bin/quickshell`, and runs the QtWebEngine test using that binary in an **isolated process**. It never overwrites `/usr/bin/quickshell` or restarts end-4. It may need extra CMake dependencies enabled by your distro; build errors are reported.

**Stop here if the build or isolated probe fails.** Keep your existing end-4 shell unchanged.

### Step 2: deliberate switchover (ONLY after private build passes)

The installer now refuses to replace the live AI tab while **any Quickshell instance is running**. This prevents end-4 hot-reload from crashing an unpatched process.

Before changing anything, make sure you know how your end-4 shell starts on login. You must change its autostart command to the private patched binary or the next desktop login will load the unpatched executable. The location of your current end-4 config may differ; the default is `~/.config/quickshell/ii`.

Once the private binary is known good and you are ready to switch, end-4's named instance can be stopped with:

    quickshell kill -c ii

Then install the replacement AI view while Quickshell is stopped:

    MABEL_QS_BINARY="$HOME/.local/share/mabel-quickshell/bin/quickshell" \
      MABEL_URL="https://YOUR-MABEL-WEBUI-URL/" bash install.sh

Start the patched shell with:

    "$HOME/.local/share/mabel-quickshell/bin/quickshell" -c ii

Now Win+A should toggle the original end-4 left sidebar containing Mabel's mobile WebUI. Sign in inside the embedded view once for its persistent browser cookies. **Live UI parity still needs testing**; CI only checks the installer and QML structure.

### Roll back

If the integrated webview misbehaves, **stop the patched shell** and restore the saved end-4 AI component:

    bash install.sh restore

Then start your original Quickshell binary/config and restore any changed startup command. The installer preserves `AiChat.qml.before-mabel`.

## Installation safety

- No changes to Odysseus, Strata or Hyprland keybindings.
- No standalone floating app window.
- No new QtWebEngine-containing code is placed in the active shell while the old shell is running.
- The optional `MABEL_QS_BINARY` env var selects a patched test binary. It does not install or replace a binary.
- `MABEL_SKIP_WEBENGINE_CHECK=1` exists only for CI/development; do not use it on stock Quickshell.
- Existing end-4 instance MUST use the patched binary when `AiChat.qml` contains QtWebEngine. The repo cannot automatically change your unknown systemd/Hyprland startup setup.

The implementation is tracked in [PR #1](https://github.com/tovakai/quickshell-chatgpt/pull/1); remains draft pending a real end-4 smoke test.
