import qs
import qs.modules.common
import QtQuick
import QtWebEngine

// Drop-in replacement for end-4's AiChat.qml.
// SidebarLeft.qml still owns SUPER+A, focus, Escape, pin, detach, and styling.
// This embeds Mabel's ORIGINAL responsive WebUI, with real interactive cookies.
// No API tokens, no alternate chat path, no direct Strata access.
Item {
    id: root
    property string mabelUrl: __MABEL_URL_JSON__
    anchors.fill: parent
    clip: true

    WebEngineProfile {
        id: mabelProfile
        storageName: "mabel-sidebar"
        offTheRecord: false
        persistentCookiesPolicy: WebEngineProfile.ForcePersistentCookies
    }

    WebEngineView {
        id: mabelWeb
        anchors.fill: parent
        profile: mabelProfile
        url: root.mabelUrl
        focus: true
        settings.javascriptEnabled: true
        settings.localStorageEnabled: true
    }

    // End-4's SidebarLeftContent focuses the active SwipeView page.
    // Transfer that focus to the actual browser view for immediate typing.
    onFocusChanged: {
        if (focus) mabelWeb.forceActiveFocus()
    }
}
