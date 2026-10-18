---
name: nur-brave-als-browser
description: "User will nur Brave; Opera/Opera GX/Yandex am 2026-10-01 entfernt, Edge bleibt nur als Mikrofon für den Voice Browser und ist per Richtlinie ruhiggestellt"
metadata:
  node_type: memory
  type: user
  originSessionId: 897e51a7-2859-4c70-8137-7463f9a0442d
  modified: 2026-10-01T14:48:18.898Z
---

Der User nutzt ausschließlich Brave (Standardbrowser). Am 2026-10-01 wurden Opera, Opera GX und
die Yandex-Reste (Browser + „Taskbar icons of Yandex services“) samt Tasks, Autostarts, ProgIDs
und Profildaten entfernt, ebenso leere Chrome-/Firefox-Profilstubs. Edge wurde bewusst NICHT
deinstalliert, weil [[voice-browser]] Edge für die Spracherkennung braucht; stattdessen Richtlinien
`HKLM\SOFTWARE\Policies\Microsoft\Edge` → `StartupBoostEnabled=0`, `BackgroundModeEnabled=0`,
Autostart-Eintrag und Desktop-Verknüpfungen entfernt. WebView2 muss bleiben (Seelen UI u. a.).

**Why:** Wunsch „alles außer Brave weg“; Edge-Ausnahme hat der User selbst so gewählt.

**How to apply:** Keine anderen Browser installieren oder vorschlagen; Links/Tests in Brave.
`HKCU\Software\Google\Chrome` (Extensions, NativeMessagingHosts) NICHT löschen – Brave liest das
mit. Opera still deinstallieren geht nur mit
`<ver>\installer.exe --uninstall --runimmediately --deleteuserprofile=0 --installfolder="<dir>"`
(`opera.exe /uninstall /silent` tut nichts). Registry-Aufräumen muss außerhalb des App-Containers
laufen, siehe [[claude-app-container-virtualisiert-hkcu]]. Opera GX, Yandex und die Profilstubs
kamen zusammen am 2026-07-22 gegen 04:21 (Partner-Bundle-Kennung in Operas `installer_prefs.json`);
taucht davon etwas wieder auf, nach dem Bundle-Installer suchen.
