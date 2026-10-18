// Fernkampf mit Bogen: Gegner, die zu weit weg sind (Skelette, Gegner jenseits von Loechern, im Wache-Modus alles
// ausserhalb des Postens), werden beschossen statt angelaufen. Zielen mit Pfeilflugbahn und Vorhalt.
// Vanilla: Pfeil startet 0,1 unter Augenhoehe mit 3 Bloecken/Tick (volle Spannung nach 20 Ticks),
// je Tick Schwerkraft 0,05 und Luftwiderstand 0,99.
const { Vec3 } = require('vec3')

function erstellen (ctx) {
  const { bot, log, inv } = ctx
  let spannt = 0 // Ticks seit Spannbeginn (0 = nicht gespannt)
  const schuesse = new Map() // Ziel-ID -> abgegebene Schuesse
  const erlaubt = new Map() // Ziel-ID -> Schuesse fuer dieses Ziel (1-3, je nach Weg)
  let letzterSchuss = 0
  let ziel = null
  let holt = false // Bogen wird gerade in die Hotbar gelegt

  // Steht ein Spieler (Besitzer, Freund) oder Dorfbewohner nah an der Schusslinie? Dann nicht loslassen
  function schussFrei (von, nach, e) {
    const d = nach.minus(von)
    const len2 = d.dot(d) || 1
    for (const x of Object.values(bot.entities)) {
      if (x === e || x === bot.entity || !x.position || !(x.type === 'player' || x.name === 'villager')) continue
      const m = x.position.offset(0, 0.9, 0)
      const t = Math.max(0, Math.min(1, m.minus(von).dot(d) / len2))
      if (m.distanceTo(von.plus(d.scaled(t))) < 1.5) return false
    }
    return true
  }

  const bogen = () => inv.finde(i => i.name === 'bow')
  const pfeile = () => inv.items().filter(i => /^(arrow|spectral_arrow|tipped_arrow)$/.test(i.name)).reduce((s, i) => s + i.count, 0)
  const bereit = () => !!bogen() && pfeile() > 0

  // Flugbahn: Winkel (Mineflayer-Pitch, + = hoch), bei dem der Pfeil in `weite` Bloecken auf Hoehe `dy` ankommt
  function winkelFuer (weite, dy) {
    let best = null
    for (let grad = -45; grad <= 60; grad += 0.5) {
      const p = grad * Math.PI / 180
      let h = Math.cos(p) * 3
      let vy = Math.sin(p) * 3
      let x = 0
      let y = 0
      let t = 0
      for (; t < 100 && x < weite; t++) {
        x += h
        y += vy
        h *= 0.99
        vy = vy * 0.99 - 0.05
      }
      const fehler = Math.abs(y - dy)
      if (x >= weite && (!best || fehler < best.fehler)) best = { fehler, pitch: p, ticks: t }
    }
    return best
  }

  // Pro Physik-Tick, solange ein Fernziel besteht. true = Bogen hat die Steuerung
  function tick (e) {
    if (!e || !bereit()) { abbrechen(); return false }
    const b = bogen()
    if (bot.heldItem?.name !== 'bow') {
      if (b.slot >= 36 && b.slot <= 44) bot.setQuickBarSlot(b.slot - 36)
      else {
        if (!holt) { holt = true; inv.inHotbar(b, 4).catch(() => {}).finally(() => { holt = false }) }
        return true
      }
    }
    ziel = e
    const auge = bot.entity.position.offset(0, 1.52, 0)
    // Vorhalt: wo ist das Ziel, wenn der Pfeil ankommt?
    const mitte = e.position.offset(0, (e.height ?? 1.8) * 0.6, 0)
    const erste = winkelFuer(Math.hypot(mitte.x - auge.x, mitte.z - auge.z), mitte.y - auge.y)
    const flug = erste?.ticks ?? 10
    const v = e.velocity ?? { x: 0, y: 0, z: 0 }
    const vor = mitte.offset(v.x * flug, 0, v.z * flug)
    const w = winkelFuer(Math.hypot(vor.x - auge.x, vor.z - auge.z), vor.y - auge.y)
    if (!w) { abbrechen(); return false }
    const yaw = Math.atan2(-(vor.x - auge.x), -(vor.z - auge.z))
    bot.look(yaw, w.pitch, true)
    bot.clearControlStates()
    if (spannt === 0) { bot.activateItem(); spannt = 1; return true }
    spannt++
    if (spannt >= 22 && schussFrei(auge, vor, e)) { // voll gespannt (20 Ticks) + etwas Luft, niemand in der Linie
      bot.deactivateItem()
      log(`Bogenschuss auf ${ctx.wahr.name(e)} (${e.position.distanceTo(bot.entity.position).toFixed(0)} Bloecke)`)
      spannt = 0
      schuesse.set(e.id, (schuesse.get(e.id) ?? 0) + 1)
      letzterSchuss = Date.now()
    }
    return true
  }

  function abbrechen () {
    if (spannt > 0) {
      // Loslassen (deactivateItem) wuerde den Pfeil irgendwohin abschiessen. Kurzer Slotwechsel bricht das
      // Spannen ab, ohne zu schiessen (Server: stopUsingItem)
      if (bot.heldItem?.name === 'bow') {
        const s = bot.quickBarSlot
        bot.setQuickBarSlot((s + 1) % 9)
        bot.setQuickBarSlot(s)
      }
      spannt = 0
    }
    ziel = null
  }

  // Darf noch geschossen werden? Beim ersten Mal wird das Budget aus der Entfernung festgelegt: ~1 Schuss je
  // 8 Bloecke Weg, hoechstens 3 - danach laeuft er hin. Wache (ohne Weg zum Ziel): hoechstens alle 3 s.
  function darfSchiessen (e, d, { wache = false } = {}) {
    if (spannt > 0) return true // angefangenen Schuss zu Ende bringen
    if (wache) return Date.now() - letzterSchuss > 3000
    if (schuesse.size > 200) { schuesse.clear(); erlaubt.clear() } // vor dem Setzen, sonst ist erlaubt.get() undefined
    if (!erlaubt.has(e.id)) erlaubt.set(e.id, Math.max(1, Math.min(3, Math.round(d / 8))))
    return (schuesse.get(e.id) ?? 0) < erlaubt.get(e.id)
  }

  return { bereit, tick, abbrechen, darfSchiessen, spannt: () => spannt > 0, pfeile }
}

module.exports = { erstellen }
