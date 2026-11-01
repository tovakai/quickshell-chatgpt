# End-4 integration

The prior standalone \`shell.qml\` panel was the wrong approach and is no longer part of this branch. The integration is \`../end4/AiChat.qml\`, copied into the existing \`~/.config/quickshell/ii/modules/ii/sidebarLeft/AiChat.qml\` only after saving a backup and passing an isolated QtWebEngine startup check.

All end-4 sidebar behavior stays in its original code: Win+A, focus, dismissal, pinning, detachment and animations.
