# Quickshell adapter (planned)

Target: end-4 illogical-impulse `~/.config/quickshell/ii`.

Existing installation uses `services/Ai.qml`, `services/ai/*ApiStrategy.qml`, and `modules/ii/sidebarLeft/AiChat.qml`. A future adapter should preserve Gemini and Mistral, avoid storing credentials in QML, and talk to the local bridge over a restricted channel.

No production QML plugin or installer exists in v0.0.1. **Do not replace or modify your live dots using this directory yet.**
