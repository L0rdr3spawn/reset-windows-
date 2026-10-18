---
name: eigene-fabric-mods
description: "Eigene Fabric-Mods attrswap + autocart (26.3, v1.4.0, mit Client-Gametests) — Ort, Bauen ohne JDK, gemessene Spielmechanik"
metadata: 
  node_type: memory
  type: project
  originSessionId: 64d37166-1cdd-47bb-a710-2767657ae1ba
  modified: 2026-09-24T16:51:07.434Z
---

Selbstgebaute Client-Mods, Gruppe `de.reiss`, jeweils eigenes Gradle-Projekt unter `C:\Users\reiss\Documents\claude\`:

- **attrswap** — Angriff, Hotbar-Slotwechsel, zweiter Angriff in einem Client-Tick. Dazu Elytra→Brustpanzer-Tausch. Braucht serverseitig `update-equipment-on-player-actions: false`, siehe [[minecraft-server-crafty]].
- **autocart** (ab 2026-09-16) — Tastendruck legt TNT-Lore auf die nächste Schiene, setzt Feuer auf die Ziellinie und schießt eine geladene Armbrust hindurch. Zustandsautomat mit einem Schritt pro Tick.

**Stand 2026-09-24: beide auf 26.3 (v1.4.0)**, Jars + Fabric API liegen in Prism-Instanz „26.3"; die 1.0.0-Jars bleiben in „26.2". Portierfallen 26.2→26.3: kein GLFW mehr im Classpath (`InputConstants.Type.KEYBOARD` + `InputConstants.KEY_V`), `swing(hand, SwingAnimation, false)` ist nur noch lokale Animation, `piercingAttack(anim, weapon)` swingt selbst, `minecraft.gui.screen()` statt `minecraft.screen`, `SwingSource.PREDICTED`. `ServerboundUseItemPacket` trägt die Rotation mit (26.2 + 26.3), Armbrust braucht keinen Zielticks-Vorlauf. Fabric-Template für 26.3 nutzt weiter Loom 1.17-SNAPSHOT + Gradle 9.5.1.

**Client-Gametests (seit 1.2.0):** beide Projekte haben `src/gametest` + `./gradlew runClientGameTest` (echte Singleplayer-Welt, Ergebnis im Log unter `====`). Fallen: `attribute @a` geht nicht (nur ein Entity → `@p`), Loren stapeln nicht, `tp … facing` zielt von den Füßen, neue Orte erst forceloaden + Plattform vor dem tp bauen, `report()`-Meldungen von autocart stehen auf DEBUG in `build/run/clientGameTest/logs/debug.log`.

**Gemessene Fakten (widerlegen frühere Annahmen):** `Player#attack` setzt die Ladung per `onAttack()` sofort zurück (26.2 wie 26.3), ein zweiter Schlag im selben Tick hat also ~4 % Ladung. Deshalb attrswap-Modus `single` (Default): Schwert halten, im selben Tick mit Mace schlagen und zurückwechseln → 40,8 Schaden gegenüber Mace allein 37,8 und altem Doppelschlag 20,8 (8 Blöcke Fall). `double` bleibt für Axt→Mace gegen Schilde. Brennender Pfeil lässt TNT-Lore **sofort** explodieren (keine 4-s-Lunte) → autocart baut Deckung jetzt vor dem Schuss und lässt Pfeilbahn frei; mit leerer Armbrust wird zuerst geladen, dann gebaut (sonst Feuer aus/Pfeil in eigener Wand).

**Why:** Auf dem Rechner ist **kein JDK installiert**, `java` liegt nicht im PATH. Gradle scheitert sonst sofort mit „JAVA_HOME is not set".

**How to apply:** Bauen mit Prisms mitgeliefertem JDK 25:
`JAVA_HOME="$APPDATA/PrismLauncher/java/java-runtime-epsilon" ./gradlew build` — die Jar landet in `build/libs/`, Zielordner ist `%APPDATA%\PrismLauncher\instances\26.2\minecraft\mods\` (Instanz „26.2" wird gespielt, „26.2 moded" liegt brach). Projekte nutzen **offizielle Mojang-Mappings**, nicht Yarn (also `MultiPlayerGameMode`, nicht `ClientPlayerInteractionManager`). Zwei Fallstricke: In 26.2 liegt die TNT-Lore in `net.minecraft.world.entity.vehicle.minecart.MinecartTNT` (Unterpaket `minecart`!), und nach `setSelectedSlot` muss man `ensureHasSentCarriedItem` per Invoker-Mixin selbst auslösen, sonst benutzt der Server noch das alte Item.

**v1.3.0-Features:** attrswap `auto` (Mace bei Smash-Fall, Axt gegen Schild, beides = Axt→Mace „stun slam") + `onclick` (Mixin auf `Minecraft#startAttack`, übernimmt normalen Linksklick nur wenn auto etwas findet), beide Default an; Schild-Fall ungetestet (kein blockender Gegner im Singleplayer). autocart `burst` (Default aus, Grim-Risiko): Schiene+Lore+Feuer+Schuss in einem Tick, Explosion t3 statt t9.

**v1.4.0 (2026-09-25):** autocart rechnet Explosionen richtig: brennender Pfeil → Stärke 4 + Zufall·1,5·Pfeiltempo (Armbrust 4…8,7), Klasse `Blast` für jedes LivingEntity (Rüstung/Schutz/Totem des Gegners sind clientseitig sichtbar). Neu: Vorteilsprüfung (nur feuern, wenn das Ziel mehr nimmt), eigener Totem erlaubt Pop, Auto-Totem, Nachschuss bei Fehlschuss (Explosion per Mixin auf `ClientPacketListener#handleExplosion` erkannt, nicht am Fehlen der Lore), keine zweite Lore auf belegter Schiene, Lore auf der Blicklinie zählt als Ziel (Entity-Reichweite 3 < Blockreichweite 4,5). attrswap: Lunge-Taste R — Server prüft den Speer-Stoß mit den Attributen des vorher gehaltenen Items `(ticker+5)/delay>=1`, leere Hand reicht nach einem Tick. Gemessen: Lunge III = 3 Blöcke, Vanilla-Stoß mit frischem Speer = 0.
