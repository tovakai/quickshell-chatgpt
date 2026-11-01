import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

// Standalone Mabel sidebar. QML never speaks directly to a model provider.
PanelWindow {
    id: root
    anchors { top: true; bottom: true; right: true }
    implicitWidth: 455
    exclusiveZone: 0
    aboveWindows: true
    focusable: true
    color: "transparent"

    property var sessions: []
    property var models: []
    property string currentSession: ""
    property string connection: "Connecting to Mabel…"
    property string activity: ""
    property bool busy: false
    property bool approvalPending: false
    property int activeReply: -1
    property string mode: "agent"

    function call(command) {
        if (bridge.running) bridge.write(JSON.stringify(command) + "\n")
    }
    function openMabel() {
        Quickshell.execDetached(["xdg-open", Quickshell.env("MABEL_URL") || "http://127.0.0.1:7000"])
    }
    function chooseSession(sid) {
        if (!sid) return
        currentSession = sid
        activeReply = -1
        conversation.clear()
        activity = ""
        approvalPending = false
        call({op: "history", session: sid})
    }
    function refresh() {
        call({op: "sessions"})
        call({op: "models"})
    }
    function sendMessage() {
        var value = composer.text.trim()
        if (!value || !currentSession || busy) return
        conversation.append({messageRole: "user", messageText: value})
        conversation.append({messageRole: "assistant", messageText: ""})
        activeReply = conversation.count - 1
        busy = true
        approvalPending = false
        activity = "Mabel is working…"
        call({op: "send", session: currentSession, message: value, mode: mode})
        composer.text = ""
        transcript.positionViewAtEnd()
    }
    function receive(line) {
        var event
        try { event = JSON.parse(line) }
        catch (e) { connection = "Bridge sent invalid JSON"; return }

        if (event.type === "hello") {
            connection = "Connected · " + (event.backend || "Odysseus") + " " + (event.version || "")
        } else if (event.type === "models") {
            models = event.models || []
            modelPicker.model = models.map(function(m) { return m.label })
        } else if (event.type === "sessions") {
            sessions = event.sessions || []
            sessionPicker.model = sessions.map(function(s) { return s.name + (s.model ? " · " + s.model : "") })
            var index = sessions.findIndex(function(s) { return s.id === currentSession })
            if (index < 0 && sessions.length > 0) {
                index = 0
                chooseSession(sessions[0].id)
            }
            sessionPicker.currentIndex = index
        } else if (event.type === "created") {
            chooseSession(event.session)
        } else if (event.type === "history") {
            if (event.session !== currentSession) return
            conversation.clear()
            var rows = event.messages || []
            for (var i = 0; i < rows.length; ++i)
                conversation.append({messageRole: rows[i].role, messageText: rows[i].content || ""})
            activeReply = -1
            transcript.positionViewAtEnd()
        } else if (event.type === "reply") {
            if (event.session !== currentSession) return
            if (activeReply < 0) {
                conversation.append({messageRole: "assistant", messageText: ""})
                activeReply = conversation.count - 1
            }
            if (event.replace !== undefined)
                conversation.setProperty(activeReply, "messageText", event.replace)
            else if (event.delta !== undefined)
                conversation.setProperty(activeReply, "messageText", conversation.get(activeReply).messageText + event.delta)
            transcript.positionViewAtEnd()
        } else if (event.type === "activity") {
            if (!event.session || event.session === currentSession)
                activity = event.message || ""
        } else if (event.type === "approval_needed") {
            if (event.session === currentSession) {
                approvalPending = true
                activity = "Approval needed in Mabel: " + (event.message || "Review the proposed action")
            }
        } else if (event.type === "begin") {
            busy = true
        } else if (event.type === "done") {
            busy = false
            activeReply = -1
            if (!approvalPending) activity = "Turn complete"
            call({op: "history", session: event.session})
            call({op: "sessions"})
        } else if (event.type === "error") {
            busy = false
            activeReply = -1
            activity = event.message || "Mabel request failed"
            connection = connection.startsWith("Connected") ? connection : "Mabel unavailable"
        }
    }

    Process {
        id: bridge
        command: ["python3", "-u", "-m", "bridge"]
        workingDirectory: Quickshell.env("MABEL_WIDGET_HOME")
            || ((Quickshell.env("HOME") || "") + "/.local/share/mabel-quickshell")
        stdinEnabled: true
        running: true
        onStarted: {
            root.call({op: "hello"})
            root.refresh()
        }
        onExited: (code, status) => {
            root.busy = false
            root.connection = "Bridge exited (" + code + ")"
        }
        stdout: SplitParser {
            onRead: line => root.receive(line)
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#171920"
        border.color: "#37343f"
        border.width: 1
        radius: 12

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "MABEL"
                    color: "#e6c8b9"
                    font.pixelSize: 22
                    font.bold: true
                    font.letterSpacing: 3
                }
                Item { Layout.fillWidth: true }
                Button { text: "Open full app"; onClicked: root.openMabel() }
            }
            Text {
                Layout.fillWidth: true
                text: root.connection
                color: root.connection.startsWith("Connected") ? "#93bbaa" : "#dfa995"
                font.pixelSize: 12
                elide: Text.ElideRight
            }
            RowLayout {
                Layout.fillWidth: true
                ComboBox {
                    id: sessionPicker
                    Layout.fillWidth: true
                    model: []
                    onActivated: index => {
                        if (index >= 0 && index < root.sessions.length)
                            root.chooseSession(root.sessions[index].id)
                    }
                }
                Button {
                    text: "↻"
                    onClicked: root.refresh()
                    ToolTip.text: "Refresh Mabel sessions"
                    ToolTip.visible: hovered
                }
            }
            RowLayout {
                Layout.fillWidth: true
                ComboBox {
                    id: modelPicker
                    Layout.fillWidth: true
                    model: []
                }
                Button {
                    text: "+ Chat"
                    enabled: !root.busy && root.models.length > 0
                    onClicked: {
                        var item = root.models[modelPicker.currentIndex]
                        if (item) root.call({op: "new", endpoint_id: item.endpoint_id, model: item.model})
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#20222b"
                radius: 9
                border.color: "#343742"
                ListView {
                    id: transcript
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    clip: true
                    model: ListModel { id: conversation }
                    delegate: Rectangle {
                        required property string messageRole
                        required property string messageText
                        width: transcript.width
                        height: bubbleText.implicitHeight + 24
                        radius: 9
                        color: messageRole === "user" ? "#353342" : "#282b35"
                        Text {
                            id: bubbleText
                            anchors.fill: parent
                            anchors.margins: 12
                            text: messageText || (root.busy ? "…" : "")
                            textFormat: Text.PlainText
                            color: messageRole === "user" ? "#f6ded3" : "#e1e5ef"
                            font.pixelSize: 14
                            wrapMode: Text.Wrap
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}
                }
            }
            Text {
                text: root.activity
                Layout.fillWidth: true
                visible: text.length > 0
                color: root.activity.startsWith("Approval") ? "#e6bd83" : "#9eacb8"
                wrapMode: Text.Wrap
                font.pixelSize: 12
                maximumLineCount: 3
                elide: Text.ElideRight
            }
            TextArea {
                id: composer
                Layout.fillWidth: true
                Layout.preferredHeight: 92
                placeholderText: "Ask Mabel… (Ctrl+Enter to send)"
                wrapMode: TextArea.Wrap
                color: "#eef0f5"
                placeholderTextColor: "#858897"
                background: Rectangle {
                    color: "#252834"
                    radius: 8
                    border.color: composer.activeFocus ? "#ab8c9f" : "#40414e"
                }
                Keys.onPressed: event => {
                    if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter)
                            && (event.modifiers & Qt.ControlModifier)) {
                        root.sendMessage()
                        event.accepted = true
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                ComboBox {
                    model: ["Agent", "Chat"]
                    currentIndex: 0
                    onActivated: index => root.mode = index === 0 ? "agent" : "chat"
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: root.busy ? "Stop" : "Resume"
                    enabled: root.currentSession.length > 0
                    onClicked: {
                        if (root.busy) root.call({op: "stop", session: root.currentSession})
                        else root.call({op: "resume", session: root.currentSession})
                    }
                }
                Button {
                    text: "Send"
                    enabled: !root.busy && root.currentSession.length > 0 && composer.text.trim().length > 0
                    onClicked: root.sendMessage()
                }
            }
        }
    }
}
