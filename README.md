# Mabel in end-4's real AI sidebar

This is **not** a second sidebar, not a fake browser window, and not a reduced API-token client.

It replaces **only** end-4's existing \`AiChat.qml\` content with a \`WebEngineView\` running the **original Mabel/Odysseus mobile WebUI**. end-4's \`SidebarLeft.qml\`, \`SidebarLeftContent.qml\`, global keybindings and IPC are unchanged.

Expected behavior is therefore inherited directly from end-4:
- **Win+A** toggles the existing **LEFT** sidebar (same \`quickshell:sidebarLeftToggle\`).
- Escape / click-outside dismiss, same focus management, pin, detach, and width animation.
- The original chat tab, panel design, app integration and mobile width stay owned by end-4.
- Mabel's original WebUI owns chat, uploads, login/cookies, interactive tool approvals, memory, agent execution, session state and model routing.
- All LLM traffic goes through **Mabel/Odysseus**. Never directly to Strata.

## One actual dependency: QtWebEngine-enabled Quickshell

Stock Quickshell 0.3.2 currently has an upstream bug where constructing \`WebEngineView\` crashes the process because its Qt application receives argc=0. See https://github.com/quickshell-mirror/quickshell/issues/1393.

The real fix is an upstream **one-line launcher patch** (\`auto qArgC = 0;\` → \`auto qArgC = 1;\`, see \`patches/quickshell-webengine-argc.patch\`) and rebuilding Quickshell, or using a fixed upstream build when available.

**Do not inject a WebEngineView into the existing running end-4 shell until it can be started safely.** \`install.sh\` runs an isolated Quickshell process with a harmless about:blank WebEngineView first. If that probe crashes or fails, installation stops without modifying the end-4 config. The probe does not affect the existing running Quickshell process.

## Install on Arch + end-4

Requires \`qt6-webengine\`, Python 3, end-4's actual \`~/.config/quickshell/ii\` config, and a WebEngine-compatible Quickshell build.

    sudo pacman -S qt6-webengine
    git clone -b feat/mabel-quickshell-interface-20261101 https://github.com/tovakai/quickshell-chatgpt.git
    cd quickshell-chatgpt
    MABEL_URL=https://YOUR-MABEL-TAILSCALE-URL/ bash install.sh

The installer detects \`~/.config/quickshell/ii/modules/ii/sidebarLeft/AiChat.qml\`. If yours is elsewhere, set \`QS_CONFIG_DIR=/actual/path/to/ii\`. It saves the original file as \`AiChat.qml.before-mabel\` and replaces only that file. Reload your existing end-4 Quickshell process, then hit **Win+A**.

**No separate launcher, hotkey or Chromium profile is needed.** Log in to Mabel once inside the sidebar; the QtWebEngine profile persists cookies.

**Uninstall and restore the original end-4 AI:**

    bash install.sh restore

Then reload the existing end-4 Quickshell instance.

## Safety and current status

- A confirmed-safe WebEngine build is a **prerequisite**, not something this repo can claim is fixed on your machine.
- \`tests/webengine-probe.qml\` runs in a separate Quickshell process so the original desktop remains safe during dependency checks.
- \`MABEL_SKIP_WEBENGINE_CHECK=1\` is provided for CI and developers who accept the risk; do not use it on an unpatched stock build.
- GitHub CI verifies install/restore and QML integration structure. Live rendering and login on your particular Hyprland desktop remain untested.
- The installed QML embeds Mabel's responsive browser UI rather than recreating functionality with an API bridge.

This repository modifies neither the Mabel backend nor Strata.
