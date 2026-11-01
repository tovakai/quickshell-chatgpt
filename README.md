# Mabel WebUI for Quickshell / Hyprland

**The entire original Mabel/Odysseus WebUI, not a separate chat client.**

We display Mabel's normal WebUI in a narrow Chromium app window, floated on the right by Hyprland. The existing mobile layout activates automatically at viewport widths below 768px. This means full chat history, interactive tool approvals, memory, agent features, attachments, model routing and everything else the WebUI already provides.

    Optional Quickshell edge tab → local mabel-webui launcher → Chromium --app=MABEL_URL
                                                                     ↓
                                                 The real Mabel/Odysseus WebUI
                                                                     ↓
                                           Odysseus memory, tools, approvals
                                                                     ↓
                                                 Selected model via Strata etc.

There are **no API-token restrictions**, because Mabel authenticates normally in the embedded browser-app window using its own login page/cookies. A separate Chromium profile lives under ~/.local/share/mabel-webui/chromium; you may need to log in once even if Firefox is already authenticated.

## Install

Requires Arch/Hyprland, Chromium and Python 3:

    sudo pacman -S chromium
    git clone -b feat/mabel-quickshell-interface-20261101 https://github.com/tovakai/quickshell-chatgpt.git
    cd quickshell-chatgpt
    bash install.sh

Launch/toggle the Mabel window:

    ~/.local/bin/mabel-webui toggle

By default it loads **Mabel** at http://127.0.0.1:7000, never Strata. If your active Mabel is behind a localhost tunnel on 7001:

    MABEL_URL=http://127.0.0.1:7001 ~/.local/bin/mabel-webui toggle

You can also set MABEL_BROWSER to the executable of another Chromium-based browser that supports --app.

## Quickshell edge button (optional)

    quickshell -p ~/.config/quickshell/mabel/shell.qml

The 36px "M" tab toggles the actual WebUI app window. Quickshell **does not** embed Chromium, and won't crash on the currently reported Quickshell QtWebEngine issue. It does not need any model provider configuration.

For a keyboard toggle, add this in your Hyprland config (adjust the home path):

    bind = SUPER, M, exec, /home/YOUR_USER/.local/bin/mabel-webui toggle

If needed, prefix the launch command with the MABEL_URL environment variable. For the Quickshell button, MABEL_URL must be in Quickshell's environment when started.

## Differences from native embedding

This is a floating browser-app window controlled by Hyprland, **not** a QML WebEngineView. It looks and behaves like Mabel's mobile WebUI and retains its full capabilities, but the window remains a separate Chromium process. Closing/toggling the window does not delete Mabel chats or browser cookies. A running detached Mabel agent may continue server-side.

The browser profile is separate from Firefox. The login is the original Mabel interactive login, not an Odysseus API token.

There is currently an upstream Quickshell 0.3.2 bug on Arch where WebEngineView can terminate Quickshell because it passes argc=0 to Qt. Avoiding direct embedding is intentional.

## Files

- scripts/mabel-webui: browser app window launch/close, selection, Hyprland placement.
- quickshell/shell.qml: optional tiny edge launcher only.
- install.sh: installs the helper and Quickshell launcher separately.
- tests/test_launcher.py: offline geometry, routing and window identification tests.

This feature branch is not yet visually tested on your actual Arch desktop. If native Chromium produces an unexpected app_id, inspect with hyprctl clients -j so we can tighten the window selector.

The earlier Python chat API bridge is **removed** from this branch.
