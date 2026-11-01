# Architecture

## The one and only chat interface

    Quickshell edge button or Hyprland keybind
               ↓
    Local window launcher (no Mabel API access)
               ↓
    Chromium app-mode narrow floating window
               ↓
    Real Mabel/Odysseus browser UI, including its normal login and interactive approvals
               ↓
    Odysseus backend: sessions, persistent memory, tools, authorization, SSE, models
               ↓
    Selected inference backend, possibly Strata

The launcher never contacts chat or inference HTTP endpoints and never receives authorization cookies. Chromium owns all WebUI networking. No custom memory, tool approval, chat SSE, or provider routing code exists in this repo.

At width 480px, the WebUI's built-in mobile rules (<=768px) activate.

## Windowing decision

Current Quickshell 0.3.2 on Arch is reported to crash on QtWebEngineView because Quickshell constructs its QGuiApplication with argc=0. Avoid risking the running desktop shell: the Quickshell panel only triggers a dedicated Chromium app-mode window, with Hyprland managing its size and location.

The browser is a separate process, not composited inside the QML layer-shell surface. If native Quickshell WebEngine becomes safe, direct embedding can be evaluated separately without rewriting Mabel.

## Authentication

The Chromium profile uses Mabel's native cookie-based interactive authentication, and the backend applies its normal CSRF, ownership, and tool-approval checks. Signing in once in that dedicated profile is expected. No delegated API bearer token is used.

## Follow-up

Verify browser app_id with hyprctl clients -j on the actual machine; then consider a non-destructive hide/show toggle and integration into the existing end-4 Quickshell config.
