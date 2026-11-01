import QtQuick
import Quickshell

// Mabel's *original* WebUI runs as an ordinary Chromium app window.
// This Quickshell panel is just a toggle, not an embedded browser or LLM client.
PanelWindow {
    id: root
    anchors { top: true; right: true }
    margins { top: 138 }
    implicitWidth: 36
    implicitHeight: 64
    exclusiveZone: 0
    aboveWindows: true
    focusable: false
    color: "transparent"

    Rectangle {
        anchors.fill: parent
        radius: 9
        color: button.containsMouse ? "#433745" : "#28232f"
        border.color: "#78586d"

        Text {
            anchors.centerIn: parent
            text: "M"
            font.bold: true
            font.pixelSize: 20
            color: "#ead0de"
        }

        MouseArea {
            id: button
            anchors.fill: parent
            hoverEnabled: true
            onClicked: Quickshell.execDetached(["mabel-webui", "toggle"])
        }
    }
}
