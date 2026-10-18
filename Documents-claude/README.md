# Minecraft-Projekte (reiss)

Alles rund um Minecraft 26.x an einem Ort. Lokal liegt das Repo unter `C:\Users\reiss\Documents\claude\` – einige Pfade im Code
gehen davon aus (z. B. `botlink` startet `begleiter` über `~/Documents/claude/begleiter`).

| Ordner | Was | Technik |
|---|---|---|
| `begleiter/` | Begleiter-Bot (Mineflayer) für den Zweitaccount: folgen, kämpfen (Mace, Speer, Bogen, Elytra), Auto-MLG, Portale, Baritone-Befehle, Aufgaben | Node.js, `manager.js` (HTTP 127.0.0.1:47811), `bot/` |
| `botlink/` | Client-Mod zum Begleiter: `/bot`-Befehle, Einstellungs-Menü (Taste B), Bot-Inventar als Kiste, Leuchten, Wegweiser, Menü-Knöpfe, Taste G | Fabric 26.3, Mojang-Mappings |
| `attrswap/` | Client-Mod: Angriff + Slotwechsel im selben Tick (Mace/Axt), Lunge-Taste | Fabric 26.3 |
| `autocart/` | Client-Mod: TNT-Lore auf Schiene legen und zünden | Fabric 26.3 |
| `jevbaritone/` | Älterer Bot als echter Client mit Baritone + Jev-Planung | Fabric 26.2, Baritone (libs/) |
| `mc-bot/` | Älterer Mineflayer-Bot (Vorgänger von `begleiter`) | Node.js |
| `mc-settings/` | Einstellungen (Tasten, FOV, …) über alle Prism-Instanzen synchron halten | PowerShell |
| `mc-kampfserver/`, `mc-survival/`, `mc-testserver/` | Lokale Paper-26.2-Testserver: nur Konfiguration (keine Welten/Jars). `server.properties.beispiel` → `server.properties` kopieren und RCON-Passwort setzen | Paper + ViaVersion/ViaBackwards |
| `upgrader-modpack/` | Modpack des Upgrader-Servers (.mrpack) | – |

## Starten (Begleiter-Bot ausprobieren)

Doppelklick auf `begleiter/START.cmd`: startet den Manager frisch (mit dem aktuellen Code) und danach Minecraft 26.3
aus Prism (mit der Botlink-Mod). Im Spiel: Pausenmenue **"Bot holen"** (Singleplayer) oder `/bot join` auf einem Server,
Taste **B** = Einstellungen, Taste **G** = Wesen angreifen / zu Block gehen / in die Luft = wieder folgen, `/bot hilfe`.
Achtung: `START.cmd` loggt einen schon laufenden Bot aus (Manager-Neustart).

## Bauen

- **Fabric-Mods** (`botlink`, `attrswap`, `autocart`, `jevbaritone`): JDK 25 nötig. Lokal ohne installiertes JDK:
  `JAVA_HOME="$APPDATA/PrismLauncher/java/java-runtime-epsilon" ./gradlew build` → Jar in `build/libs/`.
  Client-Gametests: `./gradlew runClientGameTest` (öffnet einen Test-Client).
- **Node** (`begleiter`, `mc-bot`): `npm install`, dann z. B. `node bc.js join <profil>` bzw. `node manager.js`.

## Nicht im Repo (bewusst)

Welten, Server-/Plugin-Jars, `node_modules`, Build-Ordner, Logs, `begleiter/daten/` (Logs, RCON-Passwörter, Bot-Einstellungen),
`begleiter/viaproxy/` (ViaProxy-Jar + Konten), Microsoft-Login-Token (`.auth/`). Der TypeSafe-API-Key kommt aus der Umgebung
(`TYPESAFE_API_KEY`), nie aus Dateien.

## Hinweise für Arbeit ohne den PC (Cloud)

Code lesen, ändern, bauen und Node-Logik testen geht überall. Alles, was einen laufenden Minecraft-Client, Prism-Instanzen,
die lokalen Server oder den Heimserver braucht, geht nur auf dem PC (Windows, Pfade unter `C:\Users\reiss\`).
