// Mace: Smash-Angriffe aus dem Fall.
//  - Gelegenheit: faellt der Bot > 1,5 Bloecke und das Ziel ist in Reichweite -> Wechsel auf Mace + Schlag im selben Tick
//  - Windladung: vor den Fuessen zuenden, hochfliegen, auf das Ziel fallen
//  - Elytra: mit Raketen ueber das Ziel steigen, Elytra gegen Brustpanzer tauschen, draufstuerzen
//    (Smash geht laut MaceItem.canSmashAttack nur, wenn man NICHT gleitet)
//  - Sicherheit: ohne Treffer kurz vor dem Boden eine Windladung nach unten -> kein Fallschaden
const { Vec3 } = require('vec3')

function erstellen (ctx) {
  const { bot, einst, log, wahr, inv, verhalten } = ctx
  let phase = null // null | 'wind' | 'flug' | 'steigen' | 'sturz'
  let phaseSeit = 0
  let ziel = null
  let windSperre = 0 // Ticks bis zur naechsten Windladung (Item-Cooldown 10 Ticks)
  let letzterVersuch = 0
  const an = () => verhalten.mace && einst.mace !== false

  const hotbar = item => item && item.slot >= 36 && item.slot <= 44
  const bodenAbstand = () => {
    const p = bot.entity.position
    for (let dy = 0; dy < 40; dy++) {
      const b = bot.blockAt(new Vec3(p.x, p.y - dy - 0.01, p.z))
      if (b && (b.name === 'water' || b.name === 'slime_block')) return 40 // weiche Landung, keine Windladung noetig
      if (b && b.boundingBox === 'block') return Math.max(0, p.y - b.position.y - 1) // bis zur Oberkante des Blocks
    }
    return 40
  }
  const himmelFrei = (hoehe) => {
    const p = bot.entity.position.floored()
    for (let dy = 2; dy <= hoehe; dy++) if (bot.blockAt(p.offset(0, dy, 0))?.boundingBox === 'block') return false
    return true
  }

  function smashMoeglich () {
    return an() && !bot.entity.elytraFlying && wahr.fallHoehe() > 1.8 && hotbar(inv.mace())
  }

  function smash (e) {
    const mace = inv.mace()
    const fall = wahr.fallHoehe()
    ctx.kampf.schlag(e, mace)
    wahr.fallZuruecksetzen() // der Server setzt die Fallhoehe nach einem Smash zurueck
    log(`Mace-Smash auf ${wahr.name(e)} aus ${fall.toFixed(1)} Bloecken`)
    phase = null
  }

  // Windladung vor die Fuesse: Blick nach unten, werfen, zurueckwechseln (alles in einem Tick)
  function windladungZuenden () {
    const w = inv.windladung()
    if (!hotbar(w) || windSperre > 0) return false
    const vorher = bot.quickBarSlot
    bot.entity.pitch = -Math.PI / 2
    bot.look(bot.entity.yaw, -Math.PI / 2, true)
    bot.setQuickBarSlot(w.slot - 36)
    bot.activateItem()
    bot.deactivateItem()
    bot.setQuickBarSlot(vorher)
    windSperre = 12
    return true
  }

  function setze (p, e = ziel) { phase = p; phaseSeit = 0; ziel = e }

  // Windladungs-Sprung starten, wenn es sich lohnt
  function windSprungPruefen (e) {
    if (!an() || !e || phase) return false
    if (Date.now() - letzterVersuch < 1500) return false
    if (!hotbar(inv.windladung()) || !hotbar(inv.mace()) || !bot.entity.onGround) return false
    const dh = Math.hypot(e.position.x - bot.entity.position.x, e.position.z - bot.entity.position.z)
    if (dh > 4 || !himmelFrei(8)) return false
    letzterVersuch = Date.now()
    if (!windladungZuenden()) return false
    setze('wind', e)
    log(`Mace: Windladungs-Sprung auf ${wahr.name(e)}`)
    return true
  }

  // Elytra-Mace: nur gegen Spieler/grosse Ziele, draussen, mit Raketen und genug Leben
  function elytraMacePruefen (e) {
    if (!an() || einst.elytraMace === false || !e || phase || !verhalten.elytra || einst.elytra === false || bot.entity.isInWater) return false
    // Spieler, dicke Brocken - oder was du ihm als Ziel gibst (G-Taste, /bot greif, was du angreifst)
    const vomBesitzer = ['befehl', 'besitzer'].includes(ctx.kampf.zielGrund?.())
    if (!vomBesitzer && !wahr.istSpieler(e) && !['ravager', 'warden', 'iron_golem', 'wither'].includes(e.name)) return false
    if (Date.now() - letzterVersuch < 8000 || bot.health < 12 || bot.food < 10) return false
    // Raketen sparen: nur mit ordentlich Vorrat (ein Anflug kostet 3-6)
    if (!inv.elytra() || inv.anzahl('firework_rocket') < 12 || !inv.mace() || !himmelFrei(20)) return false
    const d = e.position.distanceTo(bot.entity.position)
    if (d < 4 || d > 24) return false
    letzterVersuch = Date.now()
    setze('steigen', e)
    ctx.elytra.tauschVorbereiten()
    ctx.elytra.abheben({ fuer: 'mace' }).catch(err => { log('Elytra-Mace Start:', err.message); phase = null })
    log(`Elytra-Mace auf ${wahr.name(e)}`)
    return true
  }

  // Gibt true zurueck, wenn der Mace-Ablauf gerade die Steuerung hat
  function physikTick () {
    if (windSperre > 0) windSperre--
    if (!phase) {
      // Notbremse auch ohne Ablauf: tiefer Fall ohne Ziel -> Windladung knapp ueber dem Boden
      landungAbfangen()
      return false
    }
    phaseSeit++
    // Flugmodul nicht (mehr) aktiv (Fehlstart, Wasser, gelandet): sonst blockiert 'steigen' bis zu 25 s
    const flugWeg = phase === 'steigen' && !ctx.elytra.aktiv()
    if (!ziel || ziel.isValid === false || flugWeg || phaseSeit > (phase === 'steigen' ? 500 : 200)) {
      if (phase === 'steigen') {
        log('Elytra-Mace abgebrochen')
        ctx.elytra.zielSetzen(null) // sonst kreist er mit Raketen weiter ueber dem alten Zielpunkt
        ctx.elytra.landen().catch(() => {})
      }
      phase = null
      bot.clearControlStates()
      return false
    }

    const zp = ziel.position
    const p = bot.entity.position
    const dh = Math.hypot(zp.x - p.x, zp.z - p.z)

    if (phase === 'wind' || phase === 'sturz') {
      // In der Luft zum Ziel lenken
      ctx.kampf.schauen(zp.offset(0, (ziel.height ?? 1.8) * 0.5, 0))
      bot.setControlState('forward', dh > 0.8)
      bot.setControlState('sprint', false)
      if (phaseSeit > 3 && bot.entity.onGround) { phase = null; bot.clearControlStates(); return false }
      if (smashMoeglich() && ctx.kampf.abstand(ziel) <= ctx.kampf.reichweite()) { smash(ziel); return true }
      landungAbfangen()
      return true
    }

    if (phase === 'steigen') {
      // Das Flugmodul fliegt; abgeworfen wird, wenn der vorausberechnete Aufprall auf dem Ziel liegt
      const hoehe = abwurfHoehe()
      const h = p.y - zp.y
      const v = bot.entity.velocity
      const t = fallTicks(h, v.y)
      // Nach dem Ablegen bremst die Luft waagrecht mit 0,91 pro Tick: Weg = v * (0,91 + 0,91^2 + ... + 0,91^t);
      // dazu 2 Ticks, die er noch gleitet, bis der Server den Tausch verarbeitet hat
      const drift = 2 + 0.91 * (1 - Math.pow(0.91, t)) / 0.09
      const fehler = Math.hypot(p.x + v.x * drift - zp.x, p.z + v.z * drift - zp.z)
      if (bot.entity.elytraFlying && h >= hoehe - 2 && fehler < 2.2) {
        // Elytra gegen Brustpanzer -> freier Fall (Smash geht nur ohne Gleiten)
        ctx.elytra.landen({ sofort: true }).catch(() => {})
        setze('sturz')
        log(`Elytra-Mace: Abwurf aus ${h.toFixed(0)} Bloecken, ${dh.toFixed(1)} waagrecht, Vorhalt-Fehler ${fehler.toFixed(1)}`)
      } else {
        ctx.elytra.zielSetzen(zp.offset(0, hoehe + 3, 0))
      }
      return false // Flugmodul steuert
    }
    return false
  }

  // Aus welcher Hoehe abwerfen? Mace-Bonus: +4/Block (bis 3), +2 (bis 8), +1 darueber.
  // Hoch nur, wenn ein Fehlwurf abgefangen werden kann (Wasser/Schleim/Windladung), sonst was das Leben hergibt.
  function abwurfHoehe () {
    if (ctx.wasser.kannAbfangen() || hotbar(inv.windladung())) return 16
    return Math.max(6, Math.min(16, bot.health - 4 + 3))
  }

  // Ticks, bis der Bot `hoehe` Bloecke gefallen ist (Schwerkraft 0,08, Luftwiderstand 0,98)
  function fallTicks (hoehe, vy = 0) {
    let y = 0
    for (let t = 1; t < 200; t++) {
      y += vy
      vy = (vy - 0.08) * 0.98
      if (-y >= hoehe) return t
    }
    return 200
  }

  // Tiefer Fall ohne Treffer: kurz vor dem Boden Windladung nach unten (hebt Fallschaden auf)
  function landungAbfangen () {
    if (ctx.wasser.kannAbfangen()) return // Wassereimer/Schleim ist zuverlaessiger (Wasser-Modul)
    if (bot.entity.onGround || bot.entity.elytraFlying || bot.entity.velocity.y > -0.5) return
    const fall = wahr.fallHoehe() + bodenAbstand()
    const schaden = fall - 3 - (inv.verzauberung(inv.getragen('feet'), 'feather_falling') * 0.12 * fall)
    if (schaden < bot.health - 2 && schaden < 6) return
    // Die Ladung braucht 1-2 Ticks bis zum Boden: bei hohem Tempo frueher zuenden
    const vorlauf = Math.max(2.5, -bot.entity.velocity.y * 3 + 1)
    if (bodenAbstand() < vorlauf && windladungZuenden()) {
      log(`Landung mit Windladung abgefangen (Fall ${fall.toFixed(0)})`)
      wahr.fallZuruecksetzen()
    }
  }

  return {
    smashMoeglich, smash, windSprungPruefen, elytraMacePruefen, physikTick, windladungZuenden,
    aktiv: () => !!phase,
    abbrechen: () => { phase = null }
  }
}

module.exports = { erstellen }
