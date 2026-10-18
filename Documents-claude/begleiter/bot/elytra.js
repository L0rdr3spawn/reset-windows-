// Elytra: abheben, mit Raketen fliegen, dem Besitzer in der Luft folgen, landen, Brustpanzer zuruecktauschen.
const { Vec3 } = require('vec3')

function erstellen (ctx) {
  const { bot, einst, log, wahr, inv, verhalten } = ctx
  let modus = null // null | 'start' | 'steigen' | 'flug' | 'landung'
  let zweck = null // 'folgen' | 'mace' | 'befehl'
  let zielPunkt = null
  let raketenSperre = 0
  let startTicks = 0
  let tickZaehler = 0
  let sperreBis = 0 // nach Fehlstart eine Weile nicht neu versuchen

  // Kann er hier abheben? Nicht im Wasser/Lava/an Leitern und nicht mit Blaettern/Bloecken direkt ueber dem Kopf
  function startHindernis () {
    if (bot.entity.isInWater || bot.entity.isInLava) return 'im Wasser'
    const p = bot.entity.position.floored()
    for (let dy = 2; dy <= 10; dy++) if (bot.blockAt(p.offset(0, dy, 0))?.boundingBox === 'block') return 'Decke ueber dem Kopf'
    return null
  }

  const an = () => verhalten.elytra && einst.elytra !== false
  const hotbar = item => item && item.slot >= 36 && item.slot <= 44

  async function elytraAnziehen () {
    if (inv.getragen('torso')?.name === 'elytra') return true
    const e = inv.finde(i => i.name === 'elytra')
    if (!e) return false
    await bot.equip(e, 'torso')
    return true
  }

  async function brustpanzerZurueck () {
    if (inv.getragen('torso')?.name !== 'elytra') return
    const brust = inv.items().filter(i => i.name.endsWith('_chestplate')).sort((a, b) => inv.ruestungWert(b) - inv.ruestungWert(a))[0]
    if (brust) await bot.equip(brust, 'torso').catch(e => log('Brustpanzer anlegen:', e.message))
  }

  async function abheben ({ fuer = 'folgen' } = {}) {
    if (!an()) throw new Error('Elytra ist aus')
    if (modus) return
    if (!inv.raketen()) throw new Error('keine Raketen')
    const hindernis = startHindernis()
    if (hindernis) throw new Error(hindernis)
    if (!ctx.handNehmen('elytra', 70, 4000)) throw new Error('Hand belegt')
    modus = 'start'
    zweck = fuer
    zielPunkt = null
    startTicks = 0
    try {
      bot.pathfinder.setGoal(null)
      if (!await elytraAnziehen()) throw new Error('keine Elytra')
      await inv.inHotbar(inv.raketen(), 8)
      log(`Elytra: hebe ab (${fuer})`)
    } catch (e) {
      modus = null
      bot.clearControlStates()
      ctx.handFrei('elytra')
      throw e
    }
  }

  // bot.elytraFly() schickt fuer 26.1 die Aktionsnummer 8 (Server kickt: "Failed to decode packet player_command"),
  // und der Name heisst in minecraft-data inzwischen start_fall_flying (unbekannte Namen werden still zu 0). Deshalb die Zahl.
  function elytraOeffnen () {
    if (inv.getragen('torso')?.name !== 'elytra') return
    bot._client.write('entity_action', { entityId: bot.entity.id, actionId: 6, jumpBoost: 0 }) // 6 = START_FALL_FLYING
  }

  // Raketen sparsam: frueh. alle 2 s (bei < 10 Raketen alle 3 s), nie waehrend eine noch zieht
  let raketenWarnung = false
  function rakete () {
    const r = inv.raketen()
    if (!hotbar(r) || raketenSperre > 0 || bot.fireworkRocketDuration > 0) return false
    const vorrat = inv.anzahl('firework_rocket')
    if (vorrat < 10 && !raketenWarnung) { raketenWarnung = true; log(`Nur noch ${vorrat} Raketen - fliege sparsam`) }
    const vorher = bot.quickBarSlot
    bot.setQuickBarSlot(r.slot - 36)
    bot.activateItem()
    bot.deactivateItem()
    bot.setQuickBarSlot(vorher)
    raketenSperre = inv.anzahl('firework_rocket') < 10 ? 60 : 40
    return true
  }

  function blickAuf (pos) {
    const p = bot.entity.position
    const d = pos.minus(p)
    const yaw = Math.atan2(-d.x, -d.z)
    const pitch = Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z))
    bot.look(yaw, pitch, true)
  }

  // Wohin fliegen? Beim Folgen: etwas hinter und ueber den Besitzer, mit Vorhalt
  // Fliegt der Besitzer: Punkt ~8 Bloecke hinter ihm und 3 seitlich versetzt (Flugrichtung aus seiner Spur),
  // so bleibt der Bot mit 8-9 Bloecken Abstand dran statt in ihn hineinzufliegen.
  let seite = Math.random() < 0.5 ? -1 : 1
  function folgeZiel () {
    const b = ctx.besitzer()
    if (b) {
      const v = wahr.besitzerTempo()
      const h = Math.hypot(v.x, v.z)
      if (h < 0.15) {
        // Besitzer schwebt/kreist langsam: auf aktueller Seite in 8 Bloecken bleiben
        const weg = bot.entity.position.minus(b.position)
        const len = Math.hypot(weg.x, weg.z) || 1
        return b.position.offset(weg.x / len * 8, 1.5, weg.z / len * 8)
      }
      const rx = v.x / h
      const rz = v.z / h
      return b.position.offset(-rx * 7.5 + -rz * 3 * seite, 1.5 + v.y * 4, -rz * 7.5 + rx * 3 * seite)
    }
    const m = wahr.besitzerModPos()
    return m ? new Vec3(m.x, m.y + 2, m.z) : null
  }

  // ---------------------------------------------------------------- Flugsteuerung wie ein Spieler
  // Nie sprunghaft herumreissen: pro Tick hoechstens ~10 Grad seitlich und ~6 Grad hoch/runter drehen
  const MAX_YAW = 10 * Math.PI / 180
  const MAX_PITCH = 6 * Math.PI / 180
  const begrenzt = (x, m) => Math.max(-m, Math.min(m, x))
  function weich (yawZiel, pitchZiel, faktor = 1) {
    let dy = yawZiel - bot.entity.yaw
    while (dy > Math.PI) dy -= 2 * Math.PI
    while (dy < -Math.PI) dy += 2 * Math.PI
    const yaw = bot.entity.yaw + begrenzt(dy, MAX_YAW * faktor)
    const pitch = begrenzt(bot.entity.pitch + begrenzt(pitchZiel - bot.entity.pitch, MAX_PITCH * faktor), 1.2)
    bot.look(yaw, pitch, true)
  }
  const richtungZu = z => {
    const p = bot.entity.position
    return { yaw: Math.atan2(-(z.x - p.x), -(z.z - p.z)), pitch: Math.atan2(z.y - p.y, Math.hypot(z.x - p.x, z.z - p.z)) }
  }

  // Wie weit ist der Weg in Richtung (yaw, pitch) frei? Prueft den Koerper plus ~0,8 Bloecke Abstand ringsum
  // (Gleiten gegen eine Wand kostet Aufprall-Schaden je nach Tempo); mitBoden = auch 1,5 Bloecke Luft darunter
  function freiBis (yaw, pitch, weite, mitBoden = true) {
    const dx = -Math.sin(yaw) * Math.cos(pitch)
    const dy = Math.sin(pitch)
    const dz = -Math.cos(yaw) * Math.cos(pitch)
    const p = bot.entity.position
    const proben = [[0, 0.3, 0], [0, 1.6, 0], [0.8, 0.9, 0], [-0.8, 0.9, 0], [0, 0.9, 0.8], [0, 0.9, -0.8]]
    if (mitBoden) proben.push([0, -1.5, 0])
    for (let i = 1; i <= weite; i++) {
      for (const [ox, oy, oz] of proben) {
        const b = bot.blockAt(new Vec3(p.x + dx * i + ox, p.y + dy * i + oy, p.z + dz * i + oz))
        if (b && (b.boundingBox === 'block' || b.name === 'lava')) return i
      }
    }
    return Infinity
  }

  // Richtung zum Ziel; liegt ~1 s Flug voraus ein Hindernis: erst hochziehen, dann seitlich ausweichen
  function sichereRichtung (yaw, pitch, mitBoden = true) {
    const weite = Math.max(6, Math.min(30, Math.ceil(bot.entity.velocity.norm() * 20)))
    if (freiBis(yaw, pitch, weite, mitBoden) === Infinity) return { yaw, pitch, frei: true }
    for (const [dyaw, dp] of [[0, 0.35], [0, 0.6], [0.5, 0.25], [-0.5, 0.25], [1, 0.3], [-1, 0.3], [0, 0.9], [1.6, 0.3], [-1.6, 0.3]]) {
      if (freiBis(yaw + dyaw, Math.min(pitch + dp, 1.0), weite, mitBoden) === Infinity) return { yaw: yaw + dyaw, pitch: Math.min(pitch + dp, 1.0), frei: false }
    }
    return { yaw, pitch: 0.9, frei: false } // nichts frei: steil hoch
  }

  // Zum Punkt fliegen: sichere Richtung, weich gedreht, nie steiler als ~35 Grad nach unten,
  // mit Mindesthoehe ueber dem Boden
  function fliegeZu (ziel, { minHoehe = 5, mitBoden = true } = {}) {
    const r = richtungZu(ziel)
    let pitch = Math.max(-0.6, Math.min(0.9, r.pitch))
    if (bodenAbstand() < minHoehe) pitch = Math.max(pitch, 0.15)
    const s = sichereRichtung(r.yaw, pitch, mitBoden)
    weich(s.yaw, s.pitch, s.frei ? 1 : 1.6) // beim Ausweichen etwas schneller drehen
    return s.frei
  }

  // true = Flugmodul hat die Steuerung
  function physikTick () {
    if (raketenSperre > 0) raketenSperre--
    if (!modus) return false
    tickZaehler++

    if (modus === 'start') {
      startTicks++
      // Springen, im Fallen die Elytra oeffnen, dann Rakete
      if (startTicks === 1) { bot.clearControlStates(); bot.look(bot.entity.yaw, 0.6, true) }
      if (bot.entity.onGround) bot.setControlState('jump', true)
      else {
        bot.setControlState('jump', false)
        if (!bot.entity.elytraFlying && bot.entity.velocity.y < 0 && startTicks % 5 === 0) elytraOeffnen()
        if (bot.entity.elytraFlying) { rakete(); modus = 'steigen'; startTicks = 0 }
      }
      if (startTicks > 60) { log('Elytra: Start fehlgeschlagen'); sperreBis = Date.now() + 15000; beenden() }
      return true
    }

    if (!bot.entity.elytraFlying) {
      // Gelandet (oder Elytra kaputt/abgelegt)
      if (bot.entity.onGround || bot.entity.isInWater) beenden()
      else if (bot.entity.velocity.y < -0.5 && tickZaehler % 5 === 0) elytraOeffnen() // Elytra in der Luft zugegangen: wieder oeffnen statt abzustuerzen
      return modus != null && zweck !== 'mace'
    }

    const p = bot.entity.position
    const tempo = bot.entity.velocity.norm()

    // Nach dem Start erst steil hoch (sonst fliegt er in Bodennaehe gegen alles)
    if (modus === 'steigen') {
      startTicks++
      weich(bot.entity.yaw, 0.9, 2)
      if (bot.fireworkRocketDuration <= 0 && startTicks > 2) rakete()
      if (startTicks > 25 || bodenAbstand() > 12) modus = 'flug'
      return true
    }

    let ziel = zielPunkt ?? folgeZiel()
    const b = ctx.besitzer()
    const besitzerFliegt = b && (wahr.gleitet(b) || wahr.besitzerGleitetMod())
    const horizontal = z => Math.hypot(z.x - p.x, z.z - p.z)

    if (!zielPunkt && b) {
      if (zweck === 'befehl' && !besitzerFliegt) {
        // Ueber dem Besitzer kreisen, bis !land kommt
        const w = tickZaehler / 40
        ziel = b.position.offset(Math.cos(w) * 10, 12, Math.sin(w) * 10)
      } else if (zweck === 'folgen' && !besitzerFliegt && horizontal(b.position) < 14) {
        modus = 'landung'
        ziel = landeplatz(b.position) // mit etwas Abstand neben ihm, nie in Lava/Wasser/Feuer
      } else if (horizontal(ziel) > 20) {
        // Reiseflug: nicht in Bodenhoehe
        ziel = ziel.offset(0, 10, 0)
      }
    }
    if (!ziel) { modus = 'landung'; ziel = p.offset(bot.entity.velocity.x * 10, -10, bot.entity.velocity.z * 10) }
    const d = ziel.distanceTo(p)

    if (modus === 'landung') {
      // Beim Aufsetzen zaehlt Fallhoehe (steiler als -0,5/Tick) und Aufprall-Schaden bei hohem Tempo. Darum:
      // flach anfliegen, ab ~25 Bloecken ohne Rakete ausrollen, nah am Ziel Nase hoch zum Bremsen und knapp
      // ueber dem Boden die Elytra gegen den Brustpanzer tauschen. Zu schnell und zu tief -> durchstarten.
      const nah = horizontal(ziel)
      const boden = bodenAbstand()
      const vh = Math.hypot(bot.entity.velocity.x, bot.entity.velocity.z)
      const r = richtungZu(ziel)
      if (nah < 12 || vh < 0.2) {
        const s = sichereRichtung(r.yaw, 0.35, false)
        weich(s.yaw, s.pitch)
        if (vh < 0.35 && boden <= 3) {
          log(`Elytra: setze auf (${boden} ueber Boden, Tempo ${vh.toFixed(2)})`)
          landen({ sofort: true }).catch(() => {})
        } else if (boden <= 1 && vh > 0.45) {
          weich(r.yaw, 0.7, 2) // zu schnell so tief: hochziehen, nochmal anfliegen
        }
        return true
      }
      const sollHoehe = ziel.y + 3 + Math.min(nah * 0.1, 6)
      const pitch = Math.max(-0.3, Math.min(0.3, Math.atan2(sollHoehe - p.y, nah)))
      const s = sichereRichtung(r.yaw, pitch, false)
      weich(s.yaw, s.pitch, s.frei ? 1 : 1.6)
      if (nah > 40 && tempo < 0.8 && s.frei) rakete()
      return true
    }

    // Normaler Flug: auf das Ziel zu. Rakete nur, wenn er zurueckfaellt (weit weg UND langsamer als der
    // Besitzer), deutlich zu tief ist oder der Boden gefaehrlich nah kommt
    const wegFrei = fliegeZu(ziel, { minHoehe: zweck === 'mace' ? 3 : 5 })
    const besitzerTempo = b ? Math.hypot(wahr.besitzerTempo().x, wahr.besitzerTempo().z) : 0 // Bloecke/Tick
    const faelltZurueck = d > 14 && tempo < Math.max(0.8, besitzerTempo * 0.95)
    const zuTief = (ziel.y - p.y > 8 && bot.entity.velocity.y < 0.1) || bodenAbstand() < 3
    const sehrWeit = d > 45 && tempo < 1.8
    // Rakete nur mit freier Bahn voraus - nie in ein Hindernis hinein beschleunigen (ausser zum Hochziehen)
    if ((faelltZurueck || sehrWeit) && wegFrei) rakete()
    else if (zuTief && bot.entity.pitch > 0.3) rakete()
    return true
  }

  // Sicherer Landeplatz 2-6 Bloecke neben `pos`: fester Boden (kein Magma/Kaktus), zwei Bloecke Luft, keine
  // Lava/Feuer daneben. Wird gemerkt, solange sich der Besitzer kaum bewegt (sonst springt das Ziel jeden Tick).
  let landung = null // { anker, ziel }
  const GEFAHR = new Set(['lava', 'fire', 'soul_fire', 'magma_block', 'cactus', 'campfire', 'soul_campfire', 'sweet_berry_bush', 'powder_snow'])
  function landeplatz (pos) {
    if (landung && landung.anker.distanceTo(pos) < 3) return landung.ziel
    const frei = b => b && b.boundingBox === 'empty' && !GEFAHR.has(b.name) && b.name !== 'water'
    let best = null
    for (let r = 2; r <= 6 && !best; r++) {
      for (let i = 0; i < 16 && !best; i++) {
        const w = i * Math.PI / 8
        const x = Math.floor(pos.x + Math.cos(w) * r)
        const z = Math.floor(pos.z + Math.sin(w) * r)
        for (const dy of [0, 1, -1, 2, -2]) {
          const y = Math.floor(pos.y) + dy
          const unten = bot.blockAt(new Vec3(x, y - 1, z))
          if (!unten || unten.boundingBox !== 'block' || GEFAHR.has(unten.name)) continue
          if (!frei(bot.blockAt(new Vec3(x, y, z))) || !frei(bot.blockAt(new Vec3(x, y + 1, z)))) continue
          const nachbarn = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([ax, az]) => GEFAHR.has(bot.blockAt(new Vec3(x + ax, y, z + az))?.name) || GEFAHR.has(bot.blockAt(new Vec3(x + ax, y - 1, z + az))?.name))
          if (nachbarn) continue
          best = new Vec3(x + 0.5, y, z + 0.5)
          break
        }
      }
    }
    // Kein Platz daneben (z.B. Insel): direkt auf seinen Block
    landung = { anker: pos.clone(), ziel: best ?? pos.clone() }
    return landung.ziel
  }

  function bodenAbstand () {
    const p = bot.entity.position
    for (let dy = 0; dy < 30; dy++) {
      const bl = bot.blockAt(p.offset(0, -dy - 0.01, 0))
      if (bl && bl.boundingBox === 'block') return dy
    }
    return 30
  }

  function beenden () {
    const war = modus
    if (war && war !== 'start') sperreBis = Math.max(sperreBis, Date.now() + 6000) // nicht sofort wieder abheben
    modus = null
    zielPunkt = null
    bot.clearControlStates()
    ctx.handFrei('elytra')
    if (war) {
      log('Elytra: gelandet')
      if (zweck !== 'mace') brustpanzerZurueck()
    }
    zweck = null
  }

  // Sofort-Landung: Elytra gegen Brustpanzer tauschen (fuer Mace-Sturz) bzw. normal landen
  const besterBrustpanzer = () => inv.items().filter(i => i.name.endsWith('_chestplate')).sort((a, b) => inv.ruestungWert(b) - inv.ruestungWert(a))[0]

  // Wie in Vanilla: Ruestung in der Hand benutzen tauscht sie sofort mit dem getragenen Teil - ein Paket, im
  // selben Tick (statt mehrerer Inventar-Klicks, waehrend derer er noch weitergleitet)
  function schnellTauschen (item) {
    if (!item || !hotbar(item)) return false
    const vorher = bot.quickBarSlot
    bot.setQuickBarSlot(item.slot - 36)
    bot.activateItem()
    bot.deactivateItem()
    bot.setQuickBarSlot(vorher)
    return true
  }

  // Brustpanzer schon in die Hotbar legen, damit der Tausch beim Abwurf/Aufsetzen sofort geht
  function tauschVorbereiten () {
    const b = besterBrustpanzer()
    if (b && !hotbar(b)) inv.inHotbar(b, 5).catch(() => {})
  }

  async function landen ({ sofort = false } = {}) {
    if (!sofort) { if (modus) zweck = 'folgen'; zielPunkt = null; return } // fliegt zum Besitzer und landet neben ihm
    modus = null
    zielPunkt = null
    sperreBis = Math.max(sperreBis, Date.now() + 6000)
    ctx.handFrei('elytra')
    const brust = besterBrustpanzer()
    if (brust && schnellTauschen(brust)) return
    if (brust) await bot.equip(brust, 'torso')
    else await bot.unequip('torso')
  }

  // Soll der Bot fliegen, um dem Besitzer zu folgen?
  function folgenPruefen () {
    // Fliegt der Besitzer, darf er nach 2 s wieder los; sonst gilt die volle Pause nach der Landung
    const besitzerFliegt = wahr.besitzerGleitetMod() || (ctx.besitzer() && wahr.gleitet(ctx.besitzer()))
    if (!an() || modus || Date.now() < sperreBis - (besitzerFliegt ? 4000 : 0) || startHindernis()) return false
    // Besitzer sichtbar oder (weit weg, ausser Sichtweite) Position von der Mod in derselben Dimension
    const b = ctx.besitzer()
    const m = wahr.besitzerModPos()
    const gleicheDim = !wahr.besitzerDim() || wahr.besitzerDim() === ctx.dimension()
    const pos = b?.position ?? (m && gleicheDim ? new Vec3(m.x, m.y, m.z) : null)
    if (!pos || !inv.elytra() || !inv.raketen()) return false
    const d = pos.distanceTo(bot.entity.position)
    const fliegt = (b && wahr.gleitet(b)) || wahr.besitzerGleitetMod()
    // Nur weit weg laufen lohnt den Flug nicht, wenn die Raketen knapp werden (8 bleiben fuer Notfaelle)
    if (fliegt || (d > einst.elytraFolgenAb && inv.anzahl('firework_rocket') > 8)) {
      // Klappt der Start nicht (Hand belegt, keine Elytra ...): 5 s zu Fuss weiter statt stehen zu bleiben
      abheben({ fuer: 'folgen' }).catch(e => { log('Elytra-Start:', e.message); sperreBis = Math.max(sperreBis, Date.now() + 5000) })
      return true
    }
    return false
  }

  return {
    abheben, landen, physikTick, folgenPruefen, rakete, brustpanzerZurueck, tauschVorbereiten, schnellTauschen,
    aktiv: () => modus != null,
    modus: () => modus,
    zielSetzen: (p) => { if (modus) zielPunkt = p }
  }
}

module.exports = { erstellen }
