---
name: jevbaritone-bot
description: "Echter Baritone-Begleitbot (2. MC-Client, Account NotL0rdr3spawn) mit eigener Fabric-Mod jevbaritone; Jev entscheidet, lokales LLM plant Mehrschritt-Aufgaben"
metadata: 
  node_type: memory
  type: project
  originSessionId: 741a9993-f7c8-47e3-bed7-1b83afe0566c
  modified: 2026-09-19T19:36:11.903Z
---

Seit 2026-09-19 ersetzt dieser Bot den Mineflayer-Bot ([[mc-begleitbot-mineflayer]]) — der User wollte echtes Baritone und echte Physik (Knockback). Mod-Projekt: `C:\Users\reiss\Documents\claude\jevbaritone\` (Vorlage attrswap, siehe [[eigene-fabric-mods]]), Baritone als `compileOnly`/`clientCompileOnly` aus `libs/baritone-meteor-26.2.jar` (stammt aus dem Meteor-Setup der Instanz 26.2 — funktioniert auf 26.2, offizielles Baritone nur bis 1.21.3).

Prism-Instanz **Jev-Bot** (fabric-api, sodium, baritone-meteor, jevbaritone; Config `config/jevbaritone.properties`: besitzer, heim). Start: `prismlauncher.exe --launch Jev-Bot --profile NotL0rdr3spawn --server 127.0.0.1:25566` ([[mc-testserver-lokal]]). Neue Instanzordner erkennt Prism erst nach Rescan (Unterordner anlegen+löschen). Mod-Jar ist gesperrt, solange der Client läuft → javaw mit `instances\Jev-Bot` in der CommandLine beenden, Jar kopieren, neu starten.

Pipeline: Chat vom Besitzer → Jev (noul an_bot/mehrschritt/ohne_ende, choice aktion/block/item) → Baritone-Befehl (`mine`, `goto`, `follow player`, `farm`, `explore`, `tunnel`, `surface`) oder `Werkbank.java` (Crafting per `handlePlaceRecipe` + QUICK_MOVE). Bei mehrschritt ≥ 0.5 plant `Planer.java` über LM Studio (`google/gemma-4-e4b`, json_schema), Schritte laufen nacheinander. `#…` geht direkt an Baritone. API-Key: Env, sonst `reg query HKCU\Environment`.

Stand 2026-09-19 abends (User macht am 20.09. weiter): Module Werkbank (Crafting, Bretter/Stöcke vorab, Werkbank bauen/hinstellen), Ofen (Schmelzen), Kampf (Monster <8 Blöcke, Creeper meiden), Auto-Respawn, Rückfragen-Kontext, `sagen`. NEU und noch ungetestet im Spiel: `Wissen.java` + `assets/jevbaritone/wissen.json` (aus minecraft-data 26.1 via `wissen-erzeugen.js`, mit `NODE_PATH=mc-bot/node_modules` laufen lassen) — der Rezeptbaum der erkannten Ziele plus Wiki-Fakten gehen an den Planer; außerdem breitere Platzsuche beim Hinstellen und robusteres Öffnen von Werkbank/Ofen. Letzter Live-Befund: Werkbank öffnete erst beim 2. Versuch, Ofen fand keinen Platz. Test-Server und Bot-Client sind gestoppt; Server-Start: `mc-testserver\start.cmd`.

**Why:** Mixin `BlockOptionalMetaMixin` ist nötig: Baritone berechnet Drops über Fake-Server-Loot-Tabellen, Fabric-Loot-API v3 wirft dabei NPE (reloadableRegistries) → Mengenzählung bei `#mine N` kaputt.
**How to apply:** 26.2-API-Namen: `ContainerInput` (statt ClickType), `handleContainerInput`, `Item.getName(ItemStack)` → `new ItemStack(it).getHoverName()`, `Identifier`. Gemma-Planung dauert 5–40 s, weil zwei MC-Clients die GPU belegen.
