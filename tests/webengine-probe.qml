//@ pragma UseQApplication
import QtQuick
import QtWebEngine
import Quickshell

// Run in an ISOLATED Quickshell process, never in the running end-4 shell.
// The stock Quickshell 0.3.2 argc=0 bug aborts only this probe.
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 180
        implicitHeight: 80
        WebEngineView {
            anchors.fill: parent
            url: "about:blank"
        }
    }
}
