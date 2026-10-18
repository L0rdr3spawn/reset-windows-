// Kampf: Ziel waehlen (Besitzer-Ziel, Notfall, Verteidigung, Monster) und Nahkampf mit Krits,
// Axt gegen Schilde und dem Mace-Trick (Wechsel + Schlag im selben Tick nutzt die volle Ladung).
const { goals } = require('mineflayer-pathfinder')

function erstellen (ctx) {
  const { bot, einst, log, wahr, inv, verhalten } = ctx
  let ziel = null // { e, grund, bis }
  let manuell = null // { name|id, bis }
  let ticksSeitSchlag = 100
  let letztesItem = null
  let strafe = 1
  let strafeWechsel = 0
  let pfadZiel = null
  let haltenSperre = 0

  const reichweite = () => verhalten.reichweite ?? 3.0

  // Schild blocken: hoch in der ersten Haelfte der eigenen Schlagpause, runter vor dem Schlag.
  // Sperrt eine Axt den Schild (set_cooldown), bleibt er unten.
  let schildOben = false
  let schildGemeldet = false
  let schildGesperrtBis = 0
  bot._client.on('set_cooldown', p => {
    const name = String(p.cooldownGroup ?? ctx.mcData.items[p.itemID]?.name ?? '')
    if (!name.includes('shield')) return
    schildGesperrtBis = Date.now() + (p.cooldownTicks ?? 100) * 50
    schildOben = false
    log('Schild von Axt gesperrt')
  })
  function schildHoch () {
    if (schildOben || inv.offhand()?.name !== 'shield' || Date.now() < schildGesperrtBis || ctx.handBelegt('kampf')) return
    bot.activateItem(true)
    schildOben = true
  }
  function schildRunter () {
    if (!schildOben) return
    bot.deactivateItem()
    schildOben = false
  }
  const augen = () => bot.entity.position.offset(0, bot.entity.height * 0.9, 0)

  // Abstand Augen -> naechster Punkt der Hitbox des Ziels (so rechnet auch der Server)
  function abstand (e) {
    const a = augen()
    const b = e.position
    const w = (e.width ?? 0.6) / 2
    const h = e.height ?? 1.8
    const dx = Math.max(b.x - w - a.x, 0, a.x - (b.x + w))
    const dy = Math.max(b.y - a.y, 0, a.y - (b.y + h))
    const dz = Math.max(b.z - w - a.z, 0, a.z - (b.z + w))
    return Math.sqrt(dx * dx + dy * dy + dz * dz)
  }

  // Freie Sicht Augen -> Ziel (Koerpermitte oder Kopf)? Sonst wuerde er durch Waende schlagen.
  function sichtFrei (e) {
    const a = augen()
    for (const h of [(e.height ?? 1.8) * 0.5, (e.height ?? 1.8) * 0.9]) {
      const z = e.position.offset(0, h, 0)
      const d = z.minus(a)
      const len = d.norm()
      if (len < 0.3) return true
      const block = bot.world.raycast(a, d.scaled(1 / len), len, b => b.boundingBox === 'block')
      if (!block) return true
    }
    return false
  }

  // ---------------------------------------------------------------- Zielwahl
  function darfAngreifen (e, grund) {
    if (!e || e === bot.entity || !wahr.lebendig(e) || wahr.istBesitzer(e)) return false
    if (wahr.NIE_ANGREIFEN.has(e.name)) return false
    if (wahr.istSpieler(e)) {
      if (e.username === bot.username) return false
      if (grund === 'notfall' || grund === 'befehl') return true
      if (wahr.istFreund(e)) return false
      return einst.pvp || grund === 'verteidigung'
    }
    return true
  }

  // ---------------------------------------------------------------- Gefahrenlage
  // Greift mich dieses Wesen an oder kommt es gerade auf mich zu?
  function greiftMichAn (e) {
    if (wahr.hatAngegriffen(e.id, bot.entity.id, 6000)) return true
    if (!wahr.istMonster(e)) return false
    const d = e.position.distanceTo(bot.entity.position)
    if (d > 10) return false
    const v = e.velocity ?? { x: 0, z: 0 }
    const zuMir = (bot.entity.position.x - e.position.x) * v.x + (bot.entity.position.z - e.position.z) * v.z
    return d < 5 || zuMir > 0.01
  }
  // Creeper, der gerade zuendet (swell_dir = 1) oder angezuendet wurde
  const creeperZuendet = e => e?.name === 'creeper' && (e.metadata?.[16] === 1 || e.metadata?.[18] === true)

  // Fuehrt der direkte Weg zu e an einem Creeper vorbei (< 3 Bloecke neben der Linie)?
  function wegUeberCreeper (e) {
    const a = bot.entity.position
    const abx = e.position.x - a.x
    const abz = e.position.z - a.z
    const len2 = abx * abx + abz * abz || 1
    for (const c of Object.values(bot.entities)) {
      if (c === e || c.name !== 'creeper' || !c.position) continue
      const t = Math.max(0, Math.min(1, ((c.position.x - a.x) * abx + (c.position.z - a.z) * abz) / len2))
      if (Math.hypot(c.position.x - (a.x + abx * t), c.position.z - (a.z + abz * t)) < 3) return true
    }
    return false
  }

  // Im Wache-Modus nur Ziele in der Naehe des Postens (weiter weg: nur mit Bogen)
  function amPosten (e) {
    if (einst.modus !== 'wache') return true
    const w = ctx.bew.wachePos?.()
    // Ausserhalb nur, wenn er es von hier beschiessen kann - sonst wuerde er es waehlen und sofort wieder fallen lassen
    return !w || e.position.distanceTo(w) <= 8 || (ctx.fern.bereit() && sichtFrei(e))
  }
  const manuellAktiv = () => !!manuell && Date.now() < manuell.bis

  // Ziel erreichbar, ohne in eine Gefahr zu laufen? (Fernkampf braucht keinen Weg)
  function sicherErreichbar (e) {
    if (ctx.fern.bereit() && e.position.distanceTo(bot.entity.position) > 6) return true
    return !wegUeberCreeper(e)
  }

  function zielWaehlen () {
    const besitzer = ctx.besitzer()
    const ursprung = besitzer?.position ?? bot.entity.position
    const imUmkreis = (e, r) => e.position.distanceTo(ursprung) <= r || e.position.distanceTo(bot.entity.position) <= r
    const naechster = liste => liste.sort((a, b) => a.position.distanceTo(bot.entity.position) - b.position.distanceTo(bot.entity.position))[0]

    // 1. Befehl "!greif <name>" / Taste G
    if (manuellAktiv()) {
      const e = Object.values(bot.entities).find(x => x !== bot.entity &&
        (manuell.id != null ? x.id === manuell.id : x.username?.toLowerCase() === manuell.name))
      if (e && darfAngreifen(e, 'befehl')) return { e, grund: 'befehl' }
    }
    // Kampf aus: nur ausdrueckliche Ziele (oben), sonst nichts
    if (!einst.kampf) return null

    // 2. Selbstverteidigung zuerst: wer mich gerade angreift oder auf mich zukommt - der naechste. Fernkaempfer
    //    (Skelette) auch von weit weg, wenn ich einen Bogen habe.
    const angreifer = Object.values(bot.entities).filter(e => e !== bot.entity && e.position && wahr.lebendig(e) &&
      e.position.distanceTo(bot.entity.position) <= (ctx.fern.bereit() ? 32 : 16) &&
      darfAngreifen(e, 'verteidigung') && greiftMichAn(e) && sicherErreichbar(e) && amPosten(e))
    const nahAngreifer = naechster(angreifer.filter(e => e.position.distanceTo(bot.entity.position) < 6))
    if (nahAngreifer) return { e: nahAngreifer, grund: 'verteidigung' }

    if (besitzer) {
      // 3. Notfall: Besitzer hat wenig Leben und wird angegriffen -> auch Freunde, Freund wird gesperrt
      const leben = wahr.besitzerLeben()
      if (leben != null && leben <= einst.notfallLebenBesitzer) {
        const feinde = wahr.angreiferVon(besitzer.id, 4000).filter(e => darfAngreifen(e, 'notfall') && sicherErreichbar(e))
        if (feinde.length) {
          const e = feinde.sort((a, b) => a.position.distanceTo(besitzer.position) - b.position.distanceTo(besitzer.position))[0]
          if (wahr.istSpieler(e) && einst.freunde.some(f => f.toLowerCase() === e.username.toLowerCase()) && !wahr.gesperrt(e.username)) {
            wahr.freundSperren(e.username, einst.freundSperreMinuten)
          }
          return { e, grund: 'notfall' }
        }
      }
    }
    // 4. Weiter entfernte Angreifer (z.B. Skelett, das auf mich schiesst)
    const fernAngreifer = naechster(angreifer)
    if (fernAngreifer) return { e: fernAngreifer, grund: 'verteidigung' }

    if (besitzer) {
      // 5. Was der Besitzer angreift
      const bz = wahr.besitzerZiel()
      if (bz && darfAngreifen(bz, 'besitzer') && imUmkreis(bz, einst.kampfRadius + 8) && sicherErreichbar(bz) && amPosten(bz)) return { e: bz, grund: 'besitzer' }
      // 6. Wer den Besitzer angreift
      const feinde = wahr.angreiferVon(besitzer.id, 6000).filter(e => darfAngreifen(e, 'verteidigung') && imUmkreis(e, einst.kampfRadius + 4) && sicherErreichbar(e) && amPosten(e))
      if (feinde.length) return { e: naechster(feinde), grund: 'verteidigung' }
    }

    // 7. Monster in der Naehe (nicht hinter Waenden, nicht an Creepern vorbei; Creeper nur mit Bogen)
    let best = null
    let bestD = einst.kampfRadius
    for (const e of Object.values(bot.entities)) {
      if (!e.position || !wahr.istMonster(e) || !darfAngreifen(e, 'monster')) continue
      if (!sichtFrei(e) || !sicherErreichbar(e) || !amPosten(e)) continue
      if (e.name === 'creeper' && !ctx.fern.bereit()) continue // Creeper nicht anlaufen - nur beschiessen oder ausweichen
      const d = Math.min(e.position.distanceTo(ursprung), e.position.distanceTo(bot.entity.position))
      // Waehrend einer Aufgabe nur, was wirklich nah ist
      if (ctx.aufgaben.aktuell() && d > 8) continue
      if (d < bestD && Math.abs(e.position.y - bot.entity.position.y) < 8) { best = e; bestD = d }
    }
    return best ? { e: best, grund: 'monster' } : null
  }

  // Rueckwaerts (weg vom Creeper) nur, wenn dort Boden ist - kein Abgrund, keine Lava
  function hintenSicher (c) {
    const p = bot.entity.position
    const dx = p.x - c.position.x
    const dz = p.z - c.position.z
    const len = Math.hypot(dx, dz) || 1
    const hinten = p.offset(dx / len * 1.2, 0, dz / len * 1.2)
    const fuss = bot.blockAt(hinten)
    if (fuss && /lava|fire/.test(fuss.name)) return false
    for (let dy = 1; dy <= 3; dy++) {
      const b = bot.blockAt(hinten.offset(0, -dy, 0))
      if (!b || b.name === 'lava') return false
      if (b.boundingBox === 'block' || b.name === 'water') return true
    }
    return false
  }

  // Zuendender Creeper in der Naehe: Schild hoch Richtung Creeper und rueckwaerts weg. true = weicht aus
  let creeperGemeldet = false
  function creeperAusweichen () {
    const c = Object.values(bot.entities).find(e => creeperZuendet(e) && e.position.distanceTo(bot.entity.position) < 5)
    if (!c) return false
    if (bot.pathfinder.goal) bot.pathfinder.setGoal(null)
    schauen(c.position.offset(0, 1, 0))
    bot.setControlState('back', hintenSicher(c))
    bot.setControlState('forward', false)
    bot.setControlState('sprint', false)
    schildHoch()
    if (!creeperGemeldet) { creeperGemeldet = true; log('Creeper zuendet - weiche aus') }
    return true
  }

  function gehirnTick () {
    // Abgelaufenes manuelles Ziel vergessen - sonst kaempft er mit "Kampf aus" fuer immer weiter
    if (manuell && !manuellAktiv()) manuell = null
    if (!einst.kampf && !manuell) { if (ziel) stoppen(); return false }
    const neu = zielWaehlen()
    if (!neu) {
      if (ziel) stoppen()
      // Sicherheit vor Aufgaben: gerade getroffen, aber kein erreichbares Ziel (z.B. Pfeil von weit weg) ->
      // Aufgabe (auch Baritone "mine") pausieren, bis die Lage ruhig ist
      if (Date.now() - wahr.zuletztGetroffen(bot.entity.id) < 3000 && ctx.aufgaben.laeuft()) {
        log('Werde angegriffen - unterbreche die Aufgabe')
        ctx.aufgaben.pausieren()
      }
      return false
    }
    if (ziel?.e.id !== neu.e.id) {
      log(`Kampf: ${wahr.name(neu.e)} (${neu.grund})`)
      if (neu.grund === 'notfall' || (wahr.istSpieler(neu.e) && ziel?.grund !== neu.grund)) ctx.sagen(`Greife ${wahr.name(neu.e)} an (${neu.grund}).`)
      if (ctx.aufgaben.laeuft()) ctx.aufgaben.pausieren()
      pfadZiel = null
      vorbereiten(neu.e)
    }
    ziel = neu
    return true
  }

  // Waffen in die Hotbar legen, damit der Wechsel im Kampf sofort geht
  let vorbereitenLaeuft = false
  async function vorbereiten (e) {
    if (vorbereitenLaeuft) return // Inventar-Klicks nicht parallel (Zielwechsel alle 250 ms moeglich)
    vorbereitenLaeuft = true
    try {
      const w = inv.besteWaffe(e)
      if (w) await inv.inHotbar(w, 0)
      const axt = inv.besteWaffe(e, { schildBrechen: true })
      if (axt && axt !== w && wahr.istSpieler(e)) await inv.inHotbar(axt, 1)
      const mace = inv.mace()
      if (mace && verhalten.mace) await inv.inHotbar(mace, 2)
    } catch (err) { log('Waffen vorbereiten:', err.message) } finally { vorbereitenLaeuft = false }
  }

  function stoppen () {
    if (ziel) log('Kampf beendet.')
    schildRunter()
    ziel = null
    pfadZiel = null
    bot.clearControlStates()
    if (bot.pathfinder.goal instanceof goals.GoalFollow && bot.pathfinder.goal.entity !== ctx.besitzer()) bot.pathfinder.setGoal(null)
  }

  // ---------------------------------------------------------------- Nahkampf, 20x pro Sekunde
  function schauen (pos) {
    const max = (verhalten.maxDrehungProTick ?? 180) * Math.PI / 180
    const a = augen()
    const d = pos.minus(a)
    const yawZiel = Math.atan2(-d.x, -d.z)
    const pitchZiel = Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z))
    let dy = yawZiel - bot.entity.yaw
    while (dy > Math.PI) dy -= 2 * Math.PI
    while (dy < -Math.PI) dy += 2 * Math.PI
    const yaw = bot.entity.yaw + Math.max(-max, Math.min(max, dy))
    const pitch = bot.entity.pitch + Math.max(-max, Math.min(max, pitchZiel - bot.entity.pitch))
    bot.look(yaw, pitch, true)
    return Math.abs(dy) < 0.35
  }

  // Schlag mit `item`; liegt es in der Hotbar, Wechsel + Schlag + Rueckwechsel im selben Tick
  function schlag (e, item) {
    const vorher = bot.quickBarSlot
    const wechsel = item && item.slot >= 36 && item.slot <= 44 && item.slot - 36 !== vorher
    if (wechsel) bot.setQuickBarSlot(item.slot - 36)
    bot.attack(e)
    if (wechsel) bot.setQuickBarSlot(vorher)
    ticksSeitSchlag = 0
  }

  function physikTick () {
    ticksSeitSchlag++
    const gehalten = bot.heldItem?.name ?? null
    if (gehalten !== letztesItem) { letztesItem = gehalten; ticksSeitSchlag = Math.min(ticksSeitSchlag, 0) }
    // Ueberleben geht vor: zuendender Creeper -> ausweichen, egal was sonst ansteht
    // (auch mit "Kampf aus" - das ist Selbstschutz, kein Angriff)
    if (creeperAusweichen()) { ctx.fern.abbrechen(); return }
    if (creeperGemeldet) { creeperGemeldet = false; bot.setControlState('back', false); schildRunter() }
    if (!ziel) { ctx.fern.abbrechen(); return }
    const e = ziel.e
    if (!e.isValid && e.isValid !== undefined) { stoppen(); return }
    const d = abstand(e)

    // Fernkampf: weit weg (ab 8 Bloecken), Creeper ab 4, oder im Wache-Modus ausserhalb des Postens -> Bogen
    const w = einst.modus === 'wache' ? ctx.bew.wachePos?.() : null
    // Befehl/Notfall zaehlen auch ausserhalb des Postens (sonst waehlt das Gehirn sie alle 250 ms neu und hier faellt es wieder weg)
    const ausserhalbPosten = w && e.position.distanceTo(w) > 8 && ziel.grund !== 'befehl' && ziel.grund !== 'notfall'
    // Hand belegt (Essen, Trank): kein Bogen - der Wechsel wuerde das Essen abbrechen
    const belegt = ctx.handBelegt('kampf')
    const fern = !belegt && ctx.fern.bereit() && sichtFrei(e) && (d > 8 || (e.name === 'creeper' && d > 3.5) || ausserhalbPosten) &&
      (e.name === 'creeper' || ctx.fern.darfSchiessen(e, d, { wache: !!ausserhalbPosten })) // Creeper nie anlaufen
    if (fern) {
      if (bot.pathfinder.goal) { bot.pathfinder.setGoal(null); pfadZiel = null }
      if (ctx.fern.tick(e) || e.name === 'creeper') return
    }
    ctx.fern.abbrechen()
    if (ausserhalbPosten) {
      // Mit Bogen und Sicht: am Posten auf den naechsten Schuss warten, statt das Ziel fallen zu lassen (Log-Spam)
      if (ctx.fern.bereit() && sichtFrei(e)) {
        if (pfadZiel != null) { bot.pathfinder.setGoal(null); pfadZiel = null }
        return
      }
      stoppen(); return // ohne Bogen verlaesst er den Posten nicht
    }

    // Hand belegt (Essen, Trank): nur Abstand halten
    if (belegt) {
      schildOben = false // Essen/Trank ersetzt das Blocken
      if (d < 3) { schauen(e.position.offset(0, 1, 0)); bot.setControlState('back', true); bot.setControlState('forward', false) }
      return
    }

    // Anlaufen mit dem Pathfinder, im Nahbereich selbst steuern. Ohne freie Sicht (Wand dazwischen)
    // ebenfalls den Pathfinder nehmen, der geht aussen herum - nie durch die Wand schlagen.
    const sicht = sichtFrei(e)
    if (d > 3.6 || Math.abs(e.position.y - bot.entity.position.y) > 2.5 || !sicht) {
      schildRunter()
      // Ziel neu setzen, wenn der Pathfinder gerade etwas anderes (oder nichts) verfolgt - z.B. nach
      // abgebrochenem Elytra-Start, Essen oder Nachfuellen
      const g = bot.pathfinder.goal
      if (pfadZiel !== e.id || !(g instanceof goals.GoalFollow) || g.entity?.id !== e.id) {
        pfadZiel = e.id
        bot.clearControlStates()
        bot.pathfinder.setGoal(new goals.GoalFollow(e, sicht ? 1.5 : 1), true)
      }
      if (!sicht) { pfadZiel = pfadZiel === e.id ? e.id : null; return }
      if (ctx.mace.elytraMacePruefen(e)) return
      if (ticksSeitSchlag >= 20 && ctx.speer.stich(e, d)) { ticksSeitSchlag = 0; return }
      if (ctx.speer.imKampfSpringen(e, d)) return
      return
    }
    if (pfadZiel != null) { bot.pathfinder.setGoal(null); pfadZiel = null }

    const blickOk = schauen(e.position.offset(0, (e.height ?? 1.8) * 0.6, 0))
    bot.setControlState('forward', d > 2.2)
    bot.setControlState('back', d < 1.2)
    if (--strafeWechsel <= 0) { strafe = Math.random() < 0.5 ? -1 : 1; strafeWechsel = 10 + Math.floor(Math.random() * 20) }
    bot.setControlState('left', strafe < 0 && d < 3)
    bot.setControlState('right', strafe > 0 && d < 3)

    // Waffe: gegen erhobenen Schild die Axt, sonst die beste
    const schild = wahr.blocktMitSchild(e)
    if (schild && !schildGemeldet) { schildGemeldet = true; log(`${wahr.name(e)} blockt mit Schild -> Axt`) }
    if (!schild) schildGemeldet = false
    const waffe = inv.besteWaffe(e, { schildBrechen: schild }) ?? bot.heldItem
    const haupt = inv.besteWaffe(e)
    // Liegt sie nicht in der Hotbar, macht halten() ein bot.equip - nicht 20x pro Sekunde parallel
    if (haupt && bot.heldItem?.name !== haupt.name && !ctx.handBelegt() && Date.now() > haltenSperre && !inv.halten(haupt)) haltenSperre = Date.now() + 1500

    const tempo = inv.angriffsTempo(bot.heldItem)
    const ladungTicks = Math.ceil(20 / Math.min(tempo, 4)) // volle Ladung
    const bereit = ticksSeitSchlag >= ladungTicks
    const inReichweite = d <= reichweite()
    // Knapp ausser Schwertreichweite: Speer-Stich (reicht weiter)
    if (!inReichweite && bereit && blickOk && ctx.speer.stich(e, d)) { ticksSeitSchlag = 0; return }

    // Schild: frueh in der Pause hoch (Gegner nah), rechtzeitig vor Krit-Sprung und Schlag runter
    const restTicks = ladungTicks - ticksSeitSchlag
    if (restTicks > 7 && d < 4 && (wahr.istSpieler(e) || wahr.istMonster(e))) schildHoch()
    else if (restTicks <= 7) schildRunter()

    // Gegen Spieler und dicke Mobs: Windladungs-Sprung mit Mace
    if ((wahr.istSpieler(e) || ['ravager', 'warden', 'iron_golem', 'piglin_brute', 'vindicator'].includes(e.name)) &&
      bereit && ctx.mace.windSprungPruefen(e)) return

    // Mace-Gelegenheit (wir fallen gerade tief genug)
    if (inReichweite && blickOk && ctx.mace.smashMoeglich()) {
      if (ticksSeitSchlag >= ladungTicks - 1) { ctx.mace.smash(e); ticksSeitSchlag = 0 }
      return
    }

    // Krit: kurz vor voller Ladung springen, im Fallen schlagen (nicht sprinten!)
    const kannKrit = !bot.entity.isInWater && !bot.entity.isInLava && !kopfBlockiert()
    if (bot.entity.onGround && kannKrit && inReichweite && ladungTicks - ticksSeitSchlag <= 7 && ladungTicks - ticksSeitSchlag >= 3) {
      bot.setControlState('jump', true)
    } else {
      bot.setControlState('jump', false)
    }
    const faelltGerade = !bot.entity.onGround && bot.entity.velocity.y < -0.08
    const kritJetzt = faelltGerade && kannKrit
    if (inReichweite && blickOk && bereit && (kritJetzt || !kannKrit || ticksSeitSchlag > ladungTicks + 8)) {
      if (kritJetzt) bot.setControlState('sprint', false)
      schildRunter()
      schlag(e, schild ? waffe : null)
    } else {
      bot.setControlState('sprint', d > 2.5)
    }
  }

  // Block ueber dem Kopf? Dann bringt Springen nichts
  function kopfBlockiert () {
    const p = bot.entity.position.floored()
    const b = bot.blockAt(p.offset(0, 2, 0))
    return b && b.boundingBox === 'block'
  }

  return {
    gehirnTick, physikTick, stoppen, abstand, schauen, schlag, reichweite, schildRunter, sichtFrei,
    ziel: () => ziel?.e ?? null,
    zielName: () => ziel ? `${wahr.name(ziel.e)} (${ziel.grund})` : null,
    zielGrund: () => ziel?.grund ?? null,
    manuellSetzen (name, sekunden = 120) {
      manuell = name ? { name: name.toLowerCase(), bis: Date.now() + sekunden * 1000 } : null
      if (!name) stoppen()
    },
    manuellEntity (e, sekunden = 60) { manuell = { id: e.id, bis: Date.now() + sekunden * 1000 } }
  }
}

module.exports = { erstellen }
