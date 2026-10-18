// Speer: Stoss (Paket PlayerAction STAB, wie MultiPlayerGameMode.piercingAttack) mit Lunge-Verzauberung
// schiebt den Spieler nach vorn. Den Schub rechnet der Server (EnchantmentHelper.doPostPiercingAttackEffects)
// und schickt ihn als Geschwindigkeit zurueck - dafuer braucht Mineflayer nichts Besonderes.

const { Vec3 } = require('vec3')

function erstellen (ctx) {
  const { bot, einst, log, inv, verhalten } = ctx
  let sperre = 0 // ms-Zeitstempel
  let holt = false // Speer wird gerade in die Hotbar gelegt (nicht jeden Tick neu klicken)
  const an = () => verhalten.speer && einst.speer !== false
  const hotbar = item => item && item.slot >= 36 && item.slot <= 44

  function lungeSpeer () {
    const s = inv.speer()
    return s && inv.verzauberung(s, 'lunge') > 0 ? s : null
  }

  // Stoss in Blickrichtung (horizontal auf `ziel`). Das STAB-Paket hat keine Rotation - der Server nimmt die
  // zuletzt gesendete Blickrichtung. Daher erst schauen (geht mit dem Positionspaket dieses Ticks raus) und
  // erst im folgenden Tick stossen; bis dahin die Blickrichtung gegen Pathfinder/Kampf halten.
  // Wechsel + Stoss + Rueckwechsel im selben Tick.
  // zielen = true: genau auf den Punkt (Stich auf einen Gegner), sonst waagerecht (Sprung)
  let geplant = null
  function stossTick () {
    const g = geplant
    if (!g || !bot.entity) { geplant = null; bot.removeListener('physicsTick', stossTick); return }
    bot.look(g.yaw, g.hoch, true)
    bot.entity.yaw = g.yaw
    bot.entity.pitch = g.hoch
    if (++g.ticks < 2) return
    geplant = null
    bot.removeListener('physicsTick', stossTick)
    const s = inv.speer()
    if (!s || !hotbar(s)) return
    const vorher = bot.quickBarSlot
    if (s.slot - 36 !== vorher) bot.setQuickBarSlot(s.slot - 36)
    bot._client.write('block_dig', { status: 7, location: { x: 0, y: 0, z: 0 }, face: 0, sequence: 0 })
    bot.swingArm('right')
    if (s.slot - 36 !== vorher) bot.setQuickBarSlot(vorher)
  }

  function stoss (ziel, { hoch = 0, zielen = false } = {}) {
    const s = inv.speer()
    if (!s || !hotbar(s)) {
      if (s && !holt) { holt = true; inv.inHotbar(s, 4).catch(() => {}).finally(() => { holt = false }) }
      return false
    }
    if (geplant) return false
    const p = bot.entity.position
    const yaw = Math.atan2(-(ziel.x - p.x), -(ziel.z - p.z))
    if (zielen) hoch = Math.atan2(ziel.y - (p.y + 1.62), Math.hypot(ziel.x - p.x, ziel.z - p.z))
    geplant = { yaw, hoch, ticks: 0 }
    // als letzter Listener, damit die Blickrichtung nach Pathfinder und Kampf gesetzt wird
    bot.on('physicsTick', stossTick)
    sperre = Date.now() + 700
    return true
  }

  // Jeder Lunge-Stoss kostet Hunger: nur satt, nur am Boden, hoechstens alle 5 s
  let letzterSprung = 0
  function kannSpringen (minHunger = 14) {
    return an() && !ctx.handBelegt() && Date.now() > sperre && Date.now() - letzterSprung > 5000 && bot.entity.onGround &&
      bot.food >= minHunger && !bot.entity.isInWater && lungeSpeer()
  }

  // Wie weit traegt der Stoss? (gemessen: Lunge III ~3 Bloecke, also ~1 Block je Stufe)
  const weite = () => inv.verzauberung(lungeSpeer(), 'lunge') * 1.0 + 0.5

  // Flugstrecke vorher pruefen: Weg frei, Landestelle mit Boden (kein Loch/Absturz), nichts Gefaehrliches
  // unter den Fuessen, kein Creeper/TNT in der Naehe der Landestelle
  const GEFAHR_BLOCK = new Set(['lava', 'fire', 'soul_fire', 'magma_block', 'cactus', 'sweet_berry_bush', 'powder_snow', 'cobweb', 'water'])
  const GEFAHR_WESEN = new Set(['creeper', 'tnt', 'tnt_minecart', 'end_crystal'])
  function landungSicher (ziel) {
    const p = bot.entity.position
    const dx = ziel.x - p.x
    const dz = ziel.z - p.z
    const len = Math.hypot(dx, dz) || 1
    const w = weite()
    for (let i = 0.5; i <= w + 0.51; i += 0.5) {
      const x = p.x + dx / len * i
      const z = p.z + dz / len * i
      for (const h of [0.1, 1, 1.7]) {
        const b = bot.blockAt(new Vec3(x, p.y + h, z))
        if (!b || b.boundingBox === 'block' || GEFAHR_BLOCK.has(b.name)) return false
      }
    }
    // Landestelle: Boden hoechstens 1 Block tiefer, kein Gefahrenblock darunter
    const lx = p.x + dx / len * w
    const lz = p.z + dz / len * w
    let boden = null
    for (let dy = 0; dy >= -2; dy--) {
      const b = bot.blockAt(new Vec3(lx, p.y - 1 + dy, lz))
      if (b && b.boundingBox === 'block') { boden = b; break }
      if (b && GEFAHR_BLOCK.has(b.name)) return false
    }
    if (!boden || GEFAHR_BLOCK.has(boden.name) || boden.position.y < p.y - 2.5) return false
    const landung = new Vec3(lx, p.y, lz)
    for (const e of Object.values(bot.entities)) {
      if (e.position && GEFAHR_WESEN.has(e.name) && e.position.distanceTo(landung) < 4.5) return false
    }
    return true
  }

  // Freie Strecke? (keine Wand in Hueft- und Kopfhoehe auf den naechsten Bloecken)
  function wegFrei (ziel, bloecke = 6) {
    const p = bot.entity.position
    const dx = ziel.x - p.x
    const dz = ziel.z - p.z
    const len = Math.hypot(dx, dz) || 1
    for (let i = 1; i <= Math.min(bloecke, len); i++) {
      const x = p.x + dx / len * i
      const z = p.z + dz / len * i
      for (const h of [0.5, 1.5]) {
        const b = bot.blockAt(p.offset(x - p.x, h, z - p.z))
        if (b && b.boundingBox === 'block') return false
      }
    }
    return true
  }

  function springen (ziel, grund) {
    if (!wegFrei(ziel) || !landungSicher(ziel)) return false
    log(`Speer-Sprung ${grund} (${ziel.distanceTo(bot.entity.position).toFixed(1)} Bloecke, Hunger ${bot.food})`)
    letzterSprung = Date.now()
    return stoss(ziel)
  }

  // Im Kampf: nur wenn der Gegner richtig weit weg ist (ab 9 Bloecken) und der Sprung nicht ueber ihn hinaus geht
  function imKampfSpringen (e, d) {
    if (!kannSpringen(12) || d < 7 || d > 16 || d - weite() < 3 || Math.abs(e.position.y - bot.entity.position.y) > 1.5) return false
    return springen(e.position, `auf ${ctx.wahr.name(e)}`)
  }

  // Stich mit mehr Reichweite als das Schwert - nur mit einem Speer OHNE Lunge (Lunge wuerde ihn nach vorn
  // schiessen und Hunger kosten)
  function stich (e, d) {
    if (lungeSpeer()) return false
    if (!an() || Date.now() < sperre || d <= ctx.kampf.reichweite() || d > 4.4 || !inv.speer()) return false
    const ok = stoss(e.position.offset(0, (e.height ?? 1.8) * 0.6, 0), { zielen: true })
    if (ok) log(`Speer-Stich auf ${ctx.wahr.name(e)} (${d.toFixed(1)} Bloecke)`)
    return ok
  }

  // Beim Folgen: weit weg vom Besitzer -> zu ihm hinschiessen (kostet Hunger, daher nur satt)
  function zuBesitzerSpringen (b) {
    if (!b || !kannSpringen(16)) return false
    const d = b.position.distanceTo(bot.entity.position)
    if (d < Math.max(einst.speerSprungAb, 16) || Math.abs(b.position.y - bot.entity.position.y) > 1.5) return false
    return springen(b.position, 'zu dir')
  }

  return { stoss, stich, imKampfSpringen, zuBesitzerSpringen, lungeSpeer, kannSpringen, landungSicher, wegFrei }
}

module.exports = { erstellen }
