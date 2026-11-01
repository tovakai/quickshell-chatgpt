# Architecture: reuse end-4's actual sidebar

end-4 Super+A keybinding => quickshell:sidebarLeftToggle
     => end-4 SidebarLeft.qml / GlobalStates.sidebarLeftOpen
     => end-4 SidebarLeftContent.qml / AI tab
     => replace ONLY AiChat.qml with a QtWebEngine WebEngineView
     => original Mabel/Odysseus mobile WebUI at configured URL
     => normal interactive browser login, persistent cookies
     => normal Mabel tools, approvals, chat SSE, memory, sessions, models
     => Odysseus routes to inference provider (Strata or other)

No new PanelWindow, no new browser window, no new hotkey, no API-token bridge. Sidebar interaction remains end-4's existing code.

**Compatibility blocker:** current Quickshell 0.3.2 constructs its Qt app with argc=0 and QtWebEngine aborts. A fixed / one-line patched Quickshell is required. The installer first launches an isolated QML WebEngine probe, refusing to modify the end-4 AI component on crash.

The replacement component inherits focus when the SwipeView focuses its page. The existing parent SidebarLeft handles Escape, dismiss, pin, detach and animation. QtWebEngine persists its own browser storage and cookies.
