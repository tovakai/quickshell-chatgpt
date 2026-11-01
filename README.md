# Mabel for Quickshell

A keyboard-friendly Quickshell/Hyprland sidebar for **Mabel**, powered by the **Odysseus backend**. This rebuilds the old, unused ChatGPT SIWC prototype.

## Routing contract

    Quickshell/QML → local Python stdio bridge → Mabel/Odysseus HTTP API
                                                   ↓
                                  sessions, memory, tools, approvals
                                                   ↓
                                  Odysseus-selected model (e.g. Strata)

No OpenAI login, direct Strata inference, duplicate conversation database, model API keys in QML, or separate agent harness. Every message goes through Mabel's own chat pipeline.

## Installation on Arch/Hyprland

Requires Python 3.12+, Quickshell, QtQuick Controls, and a running Odysseus/Mabel backend. The bridge uses the Python standard library only.

    git clone https://github.com/tovakai/quickshell-chatgpt
    cd quickshell-chatgpt
    bash ./install.sh
    quickshell -p ~/.config/quickshell/mabel/shell.qml

The installer creates a separate Quickshell configuration and does not modify existing end-4/illogical-impulse dotfiles. Re-run it after pulling updates.

## Configure the Mabel server

The default is http://127.0.0.1:7000 (Odysseus). For an SSH tunnel forwarding Mabel to localhost port 7001:

    MABEL_URL=http://127.0.0.1:7001 quickshell -p ~/.config/quickshell/mabel/shell.qml

When Odysseus authentication is enabled, create a token in its Settings → API Tokens with **chat** scope. Store it only on the machine running Quickshell:

    mkdir -p ~/.config/mabel-quickshell
    umask 077
    printf '%s' 'YOUR_MABEL_CHAT_TOKEN' > ~/.config/mabel-quickshell/token
    chmod 600 ~/.config/mabel-quickshell/token

The bridge reads the token file. QML never sees the secret. Auth-disabled single-user localhost Mabel can operate without a token. For authenticated remote use, prefer HTTPS/Tailscale or an SSH tunnel. MABEL_TOKEN_FILE can override the token path.

**Never set MABEL_URL to the Strata inference server (port 8080).** Point it at Mabel on 7000, or your configured Mabel proxy/tunnel (for example 7001).

For development from the repository checkout without running the installer:

    MABEL_WIDGET_HOME="$PWD" quickshell -p "$PWD/quickshell/shell.qml"

## Initial features

- Backend-owned session listing, history and new sessions.
- Discover model endpoints through Odysseus; select a model for a new conversation.
- Chat and Agent modes. Agent is the default.
- Mabel SSE replies, final response replacement and coarse agent activity.
- Stop with the exact Odysseus run ID. Resume an existing detached run.
- Mabel owns model selection, memories, tool execution, chat history and session authorization.
- Ctrl+Enter sends; Enter adds a newline.

**Approvals:** Odysseus deliberately rejects tool approval decisions made with bearer tokens. The sidebar surfaces an approval notice and provides Open full app for interactive approval in Mabel. No approval is silently granted or bypassed.

Not yet implemented: rich Markdown, images, file attachments, inline approval buttons, simultaneous streams, full tool cards, hotkey IPC toggle, or embedded integration into end-4 sidebar.

## Protocol

The Quickshell Process launches python3 -u -m bridge and sends newline-delimited JSON commands.

    {"op":"hello"}
    {"op":"sessions"}
    {"op":"models"}
    {"op":"history","session":"SESSION_ID"}
    {"op":"new","endpoint_id":"ID","model":"MODEL"}
    {"op":"send","session":"SESSION_ID","message":"Hello","mode":"agent"}
    {"op":"resume","session":"SESSION_ID"}
    {"op":"stop","session":"SESSION_ID"}

The bridge emits hello, sessions, models, history, created, begin, run, reply, activity, approval_needed, done and error messages. No provider auth or model credentials cross this IPC interface.

## Tests

    python3 -m unittest discover -s tests -v

Offline tests do not contact a model. Live Quickshell and Mabel testing on the current release worktree is still required.

See docs/ARCHITECTURE.md for the security and API boundaries.
