// Dem Besitzer durch Portale folgen. Die Mod meldet seine Dimension; wechselt er sie, merkt sich die Wahrnehmung,
// wo er zuletzt stand (im Portal). Der Bot laeuft dorthin, sucht das Portal, geht hinein und folgt danach weiter.
const { goals } = require('mineflayer-pathfinder')
const { Vec3 } = require('vec3')

const PORTALE = ['nether_portal', 'end_portal', 'end_gateway']
const DIM_NAME = { 'minecraft:overworld': 'die Oberwelt', 'minecraft:the_nether': 'den Nether', 'minecraft:the_end': 'das End' }
const DIM_WO = { 'minecraft:overworld': 'in der Oberwelt', 'minecraft:the_nether': 'im Nether', 'minecraft:the_end': 'im End' }

function erstellen (ctx) {
  const { bot, log, wahr } = ctx
  let laeuft = false
  let gemeldet = 0
  const dimName = d => DIM_NAME[d] ?? d

  const imPortal = () => [0, 0.5, 1.2].some(dy => PORTALE.includes(bot.blockAt(bot.entity.position.offset(0, dy, 0))?.name))

  function noetig () {
    const d = wahr.besitzerDim()
    return !!d && !!ctx.dimension() && d !== ctx.dimension()
  }

  // Aus dem Folgen-Takt: true = die Portal-Logik hat die Steuerung
  function tick () {
    if (laeuft) return true
    if (!noetig()) return false
    const spur = wahr.portalSpur(ctx.dimension())
    if (!spur) {
      if (Date.now() - gemeldet > 60000) {
        gemeldet = Date.now()
        ctx.sagen(`Du bist ${DIM_WO[wahr.besitzerDim()] ?? 'in ' + wahr.besitzerDim()} - ich weiss nicht, durch welches Portal du gegangen bist.`)
      }
      return false
    }
    laeuft = true
    durchgehen(spur)
      .catch(e => log('Portal:', e.message))
      .finally(() => { laeuft = false; bot.clearControlStates() })
    return true
  }

  // goto mit Zeitlimit: haengt der Pathfinder (endloses Neuplanen nach "stuck"), bliebe laeuft sonst fuer immer true
  async function gehe (ziel, ms) {
    const zeit = setTimeout(() => bot.pathfinder.setGoal(null), ms)
    try { await bot.pathfinder.goto(ziel) } finally { clearTimeout(zeit) }
  }

  async function durchgehen (spur) {
    const dimVorher = ctx.dimension()
    const ziel = new Vec3(spur.pos.x, spur.pos.y, spur.pos.z)
    ctx.sagen(`Folge dir durchs Portal in ${dimName(spur.nach)}.`)
    log(`Portal: laufe zu ${ziel.floored()} (${spur.von} -> ${spur.nach})`)
    bot.pathfinder.setMovements(ctx.bewegungNormal)
    if (bot.entity.position.distanceTo(ziel) > 3) {
      // Der Weg kann schon durchs Portal fuehren - dann bricht goto mit dem Dimensionswechsel ab
      await gehe(new goals.GoalNear(ziel.x, ziel.y, ziel.z, 2), 90000).catch(e => log('Portal-Weg:', e.message))
    }
    if (ctx.dimension() !== dimVorher) return angekommen(dimVorher)
    if (ctx.besitzer()) return // Besitzer ist wieder da (gleiche Dimension) - nicht mehr durchs Portal

    const ids = PORTALE.map(n => ctx.mcData.blocksByName[n]?.id).filter(id => id != null)
    // Unterster Portalblock nahe der Stelle, an der der Besitzer verschwunden ist
    const bloecke = bot.findBlocks({ point: ziel, matching: ids, maxDistance: 6, count: 64 }).map(p => bot.blockAt(p)).filter(Boolean)
    const portal = bloecke.sort((a, b) => a.position.y - b.position.y || a.position.distanceTo(ziel) - b.position.distanceTo(ziel))[0]
    if (!portal) {
      ctx.sagen('Hier finde ich kein Portal.')
      wahr.portalSpurVergessen(spur)
      return
    }
    // Vor das Portal stellen (Netherportal: quer zur Ebene, sonst gegen den Rahmen), dann hinein
    const vor = vorPlatz(portal)
    if (vor) await gehe(new goals.GoalBlock(vor.x, vor.y, vor.z), 15000).catch(e => log('Portal-Anlauf:', e.message))
    if (ctx.dimension() !== dimVorher) return angekommen(dimVorher)
    // Die letzten Schritte selbst steuern: der Pathfinder plant nicht in Portalbloecke hinein
    bot.pathfinder.setGoal(null)
    const mitte = portal.position.offset(0.5, 0, 0.5)
    const bis = Date.now() + 15000
    while (Date.now() < bis && ctx.dimension() === dimVorher && ctx.bot === bot && !ctx.besitzer()) {
      const p = bot.entity.position
      if (imPortal()) {
        bot.clearControlStates() // im Netherportal stehen bleiben, bis es zieht (~4 s)
      } else {
        bot.entity.yaw = Math.atan2(-(mitte.x - p.x), -(mitte.z - p.z))
        bot.setControlState('forward', Math.hypot(mitte.x - p.x, mitte.z - p.z) > 0.15)
        bot.setControlState('sprint', false)
        bot.setControlState('jump', portal.position.y > p.y + 0.5)
      }
      await ctx.warte(50)
    }
    bot.clearControlStates()
    if (ctx.dimension() !== dimVorher) return angekommen(dimVorher)
    if (ctx.besitzer()) return
    ctx.sagen('Das Portal bringt mich nicht rueber.')
    wahr.portalSpurVergessen(spur)
  }

  function stehbar (p) {
    const frei = b => b && b.boundingBox === 'empty' && !['lava', 'fire', 'soul_fire'].includes(b.name)
    const unten = bot.blockAt(p.offset(0, -1, 0))
    return frei(bot.blockAt(p)) && frei(bot.blockAt(p.offset(0, 1, 0))) && unten && unten.boundingBox === 'block'
  }

  // Standplatz direkt vor dem Portal. Netherportal: Achse x -> von Norden/Sueden (z +-1), Achse z -> von Westen/Osten
  function vorPlatz (portal) {
    const p = portal.position
    const achse = portal.getProperties?.().axis
    const seiten = portal.name !== 'nether_portal' ? [[0, -1], [0, 1], [-1, 0], [1, 0]]
      : achse === 'z' ? [[-1, 0], [1, 0]] : [[0, -1], [0, 1]]
    const kandidaten = []
    for (const [dx, dz] of seiten) {
      for (const dy of [0, -1, 1, -2]) {
        const v = p.offset(dx, dy, dz)
        if (stehbar(v)) { kandidaten.push(v); break }
      }
    }
    return kandidaten.sort((a, b) => a.distanceTo(bot.entity.position) - b.distanceTo(bot.entity.position))[0] ?? null
  }

  async function angekommen (dimVorher) {
    log(`Portal: ${dimVorher} -> ${ctx.dimension()}`)
    bot.pathfinder.setGoal(null)
    // Aus dem Ankunftsportal heraustreten, sonst zieht es ihn nach der Abklingzeit zurueck
    for (let i = 0; i < 20 && !bot.entity?.position; i++) await ctx.warte(100)
    await ctx.warte(600) // Chunks laden
    if (!imPortal()) return
    const hier = bot.blockAt(bot.entity.position.floored())
    const portal = PORTALE.includes(hier?.name) ? hier : bot.blockAt(bot.entity.position.offset(0, 0.5, 0).floored())
    const raus = portal && vorPlatz(portal)
    if (!raus) return log('Portal: kein Platz zum Heraustreten gefunden')
    const zeit = setTimeout(() => bot.pathfinder.setGoal(null), 5000)
    await bot.pathfinder.goto(new goals.GoalBlock(raus.x, raus.y, raus.z)).catch(() => {})
    clearTimeout(zeit)
    log(`Portal: herausgetreten nach ${raus}`)
  }

  // Nach jedem Dimensionswechsel alte Wege verwerfen (Koordinaten gelten nicht mehr)
  bot.on('respawn', () => { try { bot.pathfinder.setGoal(null) } catch {} })

  return { tick, laeuft: () => laeuft, noetig, imPortal, dimName }
}

module.exports = { erstellen, PORTALE }
