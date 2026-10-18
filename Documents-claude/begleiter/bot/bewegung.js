// Folgen (zu Fuss, per Speer-Sprung oder Elytra), Loot aufsammeln, Wache, Entsperren des Pathfinders.
const { goals } = require('mineflayer-pathfinder')
const { Vec3 } = require('vec3')

function erstellen (ctx) {
  const { bot, einst, log } = ctx
  let wachePos = null

  // Standplatz neben dem Besitzer: meist 2-3 Bloecke, manchmal 5-7; seitlich/hinter ihm statt vor seinem Gesicht.
  // Bewegt sich der Besitzer, folgt der Bot direkt; steht er, sucht sich der Bot ab und zu einen neuen Platz.
  let platz = null // { pos, anker, bis }
  let blickBis = 0
  let ausstieg = null // { ziel, ticks }: selbst ans Ufer steuern

  function stehbar (x, y, z) {
    const fuss = bot.blockAt(new Vec3(x, y, z))
    const kopf = bot.blockAt(new Vec3(x, y + 1, z))
    const unten = bot.blockAt(new Vec3(x, y - 1, z))
    if (!fuss || !kopf || !unten) return false
    const frei = b => b.boundingBox === 'empty' && !['water', 'lava', 'fire', 'sweet_berry_bush', 'powder_snow', 'cobweb'].includes(b.name)
    return frei(fuss) && frei(kopf) && unten.boundingBox === 'block' && !['magma_block', 'cactus'].includes(unten.name)
  }

  function standplatzWaehlen (b) {
    const nah = Math.random() < 0.65
    const [min, max] = nah ? [2.3, 3.2] : [5, 7]
    const blick = b.yaw // Mineflayer: 0 = Norden (-z); Versatz (-sin, -cos) * d zeigt in Blickrichtung
    for (let versuch = 0; versuch < 24; versuch++) {
      // Winkel relativ zur Blickrichtung des Besitzers: 0 = vor ihm, PI = hinter ihm. Vorne (+-55 Grad) meiden.
      const seite = Math.random() < 0.5 ? -1 : 1
      const w = seite * (0.96 + Math.random() * (Math.PI - 0.96))
      const richtung = blick + w
      const dist = min + Math.random() * (max - min)
      const x = Math.floor(b.position.x - Math.sin(richtung) * dist)
      const z = Math.floor(b.position.z - Math.cos(richtung) * dist)
      for (const dy of [0, 1, -1, 2, -2]) {
        const y = Math.floor(b.position.y) + dy
        if (stehbar(x, y, z)) return new Vec3(x + 0.5, y, z + 0.5)
      }
    }
    return null
  }

  function vorSeinemGesicht (b, pos) {
    const dx = pos.x - b.position.x
    const dz = pos.z - b.position.z
    const d = Math.hypot(dx, dz)
    if (d > 4.5 || d < 0.01) return false
    return (-Math.sin(b.yaw) * dx - Math.cos(b.yaw) * dz) / d > Math.cos(50 * Math.PI / 180)
  }

  function folgenTick () {
    const b = ctx.besitzer()
    if (einst.modus === 'wache' && wachePos) {
      if (bot.entity.position.distanceTo(wachePos) > 2 && !(bot.pathfinder.goal instanceof goals.GoalNear)) {
        bot.pathfinder.setGoal(new goals.GoalNear(wachePos.x, wachePos.y, wachePos.z, 1))
      }
      return
    }
    if (ausstieg) return // steuert gerade selbst aus dem Wasser
    if (!b) {
      // Besitzer in einer anderen Dimension: durch sein Portal hinterher
      if (ctx.portal.tick()) return
      // Besitzer ausser Sichtweite (gleiche Dimension): weit weg -> Elytra, sonst Position von der Mod
      if (ctx.elytra.folgenPruefen()) return
      const m = ctx.wahr.besitzerModPos()
      const dim = ctx.wahr.besitzerDim()
      if (m && (!dim || dim === ctx.dimension())) {
        const g = bot.pathfinder.goal
        if (!(g instanceof goals.GoalNear) || Math.hypot(g.x - m.x, g.z - m.z) > 6 || Math.abs(g.y - m.y) > 4) {
          bot.pathfinder.setMovements(ctx.bewegungNormal)
          bot.pathfinder.setGoal(new goals.GoalNear(m.x, m.y, m.z, einst.folgeAbstand))
        }
      }
      return
    }
    if (ctx.elytra.folgenPruefen()) return

    if (einst.loot && ctx.inv.freieSlots() > 0) {
      const drop = naechsterDrop(b)
      if (drop) {
        platz = null
        bot.pathfinder.setGoal(new goals.GoalNear(drop.position.x, drop.position.y, drop.position.z, 0))
        return
      }
    }

    const d = b.position.distanceTo(bot.entity.position)
    const tempo = ctx.wahr.besitzerTempoHorizontal() // Bloecke/s

    // Besitzer laeuft/sprintet weg oder ist weit weg: direkt hinterher (ggf. per Speer-Sprung)
    if (tempo > 2.5 || d > 12) {
      platz = null
      if (ctx.speer.zuBesitzerSpringen(b)) return
      const ziel = bot.pathfinder.goal
      if (ziel instanceof goals.GoalFollow && ziel.entity?.id === b.id) return
      bot.pathfinder.setMovements(ctx.bewegungNormal)
      bot.pathfinder.setGoal(new goals.GoalFollow(b, 3), true)
      return
    }

    // Besitzer steht: Standplatz suchen/halten
    const jetzt = Date.now()
    // Besitzer hat sich umgedreht und der Platz liegt jetzt vor seinem Gesicht: nach 1,5 s einen neuen suchen
    if (platz && vorSeinemGesicht(b, platz.pos)) platz.vorneSeit ??= jetzt
    else if (platz) platz.vorneSeit = null
    if (!platz || platz.anker.distanceTo(b.position) > 3 || jetzt > platz.bis || platz.pos.distanceTo(b.position) < 1.5 ||
      (platz.vorneSeit && jetzt - platz.vorneSeit > 1500)) {
      const pos = standplatzWaehlen(b)
      platz = pos ? { pos, anker: b.position.clone(), bis: jetzt + 10000 + Math.random() * 20000 } : null
      if (!platz) { // kein freier Platz: einfach in der Naehe bleiben
        if (!(bot.pathfinder.goal instanceof goals.GoalFollow)) bot.pathfinder.setGoal(new goals.GoalFollow(b, 3), true)
        return
      }
      bot.pathfinder.setMovements(ctx.bewegungNormal)
      bot.pathfinder.setGoal(new goals.GoalNear(platz.pos.x, platz.pos.y, platz.pos.z, 0.6))
      return
    }
    // Am Platz: ab und zu den Besitzer anschauen
    if (bot.entity.position.distanceTo(platz.pos) < 1.2 && jetzt > blickBis && !ctx.kampf.ziel()) {
      blickBis = jetzt + 1500 + Math.random() * 4000
      bot.lookAt(b.position.offset(0, 1.6, 0)).catch(() => {})
    }
  }

  // Pathfinder findet keinen Weg zum Platz -> neuen suchen
  bot.on('path_update', r => { if (r.status === 'noPath' && platz) platz = null })

  function naechsterDrop (b) {
    if (Date.now() < (ctx.lootPauseBis ?? 0)) return null // gerade etwas abgegeben
    let best = null
    let bestD = einst.lootRadius
    for (const e of Object.values(bot.entities)) {
      if (e.name !== 'item' || !e.position) continue
      const d = e.position.distanceTo(b.position)
      if (d < 2.5) continue // liegt direkt bei dir - das hebst du selbst auf
      if (d < bestD && Math.abs(e.position.y - bot.entity.position.y) < 4) { best = e; bestD = d }
    }
    return best
  }

  function wacheSetzen () {
    wachePos = bot.entity.position.floored()
    einst.modus = 'wache'
  }

  entsperrenEinrichten()

  // Offene Zauntore haben in prismarine boundingBox 'block' (nur shapes ist leer) - der Pathfinder hielt sie fuer
  // massiv und fand z.B. nicht in eine Koppel. Offen = begehbar.
  for (const m of [ctx.bewegungNormal, ctx.bewegungArbeit]) {
    const getBlock = m.getBlock.bind(m)
    m.getBlock = (pos, dx, dy, dz) => {
      const b = getBlock(pos, dx, dy, dz)
      if (b.openable && b.shapes?.length === 0) {
        b.safe = !m.blocksToAvoid.has(b.type)
        b.physical = false
      }
      return b
    }
  }

  // Paper (26.2 ueber ViaBackwards) setzt den Bot jeden Tick zurueck, wenn die gesendete Position exakt an einer
  // Wand anliegt (Mineflayers Kollision rechnet dort minimal anders als der Server). Folge: er "klebt" an Waenden,
  // kommt keine Uferkante hoch und haengt an Ecken fest. Abhilfe: nach der Physik 2 mm Abstand zur Wand.
  const WAND_SPALT = 0.002
  function beruehrtSeite (achse, richtung) {
    const p = bot.entity.position
    const hw = 0.3
    const rand = p[achse] + richtung * hw // Aussenkante der Hitbox auf dieser Seite
    const probe = rand + richtung * 0.0005
    const quer = achse === 'x' ? 'z' : 'x'
    for (let by = Math.floor(p.y + 0.01); by <= Math.floor(p.y + 1.79); by++) {
      for (let bq = Math.floor(p[quer] - hw + 0.001); bq <= Math.floor(p[quer] + hw - 0.001); bq++) {
        const pos = achse === 'x' ? new Vec3(Math.floor(probe), by, bq) : new Vec3(bq, by, Math.floor(probe))
        const b = bot.blockAt(pos)
        if (!b || !b.shapes?.length) continue
        for (const [x0, y0, z0, x1, y1, z1] of b.shapes) {
          const lo = { x: pos.x + x0, y: pos.y + y0, z: pos.z + z0 }
          const hi = { x: pos.x + x1, y: pos.y + y1, z: pos.z + z1 }
          if (hi.y <= p.y + 0.001 || lo.y >= p.y + 1.8) continue
          if (hi[quer] <= p[quer] - hw || lo[quer] >= p[quer] + hw) continue
          if (probe > lo[achse] - 1e-9 && probe < hi[achse] + 1e-9) return true
        }
      }
    }
    return false
  }
  // Vanilla springt an der Wasseroberflaeche richtig ab (LivingEntity.aiStep: im Wasser, Fluessigkeit an den Fuessen
  // <= 0,4 hoch -> jumpFromGround, danach 10 Ticks Pause). prismarine-physics kennt nur +0,04 pro Tick - damit kommt
  // ein Mineflayer-Bot keine 1-Block-Uferkante hoch. Hier nachgebaut (0,38 + die 0,04 der Physik = 0,42).
  let wasserSprungPause = 0
  function wasserTiefe () {
    const p = bot.entity.position
    let y = Math.floor(p.y)
    let b = bot.blockAt(new Vec3(p.x, y, p.z))
    if (b?.name !== 'water') return null
    while (bot.blockAt(new Vec3(p.x, y + 1, p.z))?.name === 'water') y++
    const oben = bot.blockAt(new Vec3(p.x, y, p.z))
    const stufe = Number(oben?.getProperties?.().level ?? 0)
    const hoehe = stufe >= 8 ? 1 : (8 - stufe) / 9
    return y + hoehe - p.y
  }
  bot.on('physicsTick', () => {
    const e = bot.entity
    if (!e) return
    if (wasserSprungPause > 0) wasserSprungPause--
    if (e.isInWater && bot.controlState.jump && wasserSprungPause === 0) {
      const t = wasserTiefe()
      if (t != null && t > 0 && t <= 0.4) {
        e.velocity.y = 0.38
        wasserSprungPause = 10
      }
    }
  })

  bot.on('physicsTick', () => {
    const e = bot.entity
    if (!e || !e.isCollidedHorizontally || e.elytraFlying) return
    for (const achse of ['x', 'z']) {
      for (const r of [1, -1]) if (beruehrtSeite(achse, r)) e.position[achse] -= r * WAND_SPALT
    }
  })

  // Der Pathfinder plant manchmal Spruenge, die er dann nicht schafft ("stuck"), und wiederholt sie endlos.
  // Abhilfe: 1.-2. Fehlschlag selbst hinspringen, 3. Fehlschlag den Punkt teuer machen.
  function entsperrenEinrichten () {
    let pfad = []
    let sprungZiel = null
    let sprungTicks = 0
    const fehlschlaege = new Map()
    const schluessel = p => `${Math.floor(p.x)},${Math.floor(p.y)},${Math.floor(p.z)}`
    bot.on('path_update', r => { pfad = r.path })
    bot.on('path_reset', grund => {
      if (grund !== 'stuck' || !pfad.length) return
      const key = schluessel(pfad[0])
      const n = (fehlschlaege.get(key) ?? 0) + 1
      fehlschlaege.set(key, n)
      if (n <= 2) {
        sprungZiel = pfad[0]
        sprungTicks = 14
      } else if (n === 3) {
        log(`Komme nicht auf ${key}, plane drumherum.`)
        const [x, y, z] = key.split(',').map(Number)
        const meiden = bl => bl && (bl.position.x === x && bl.position.z === z && (bl.position.y === y || bl.position.y === y + 1)) ? 100 : 0
        for (const m of [ctx.bewegungNormal, ctx.bewegungArbeit]) {
          m.exclusionAreasStep.push(meiden)
          if (m.exclusionAreasStep.length > 40) m.exclusionAreasStep.shift()
        }
      }
      if (fehlschlaege.size > 200) fehlschlaege.clear()
    })
    bot.on('physicsTick', () => {
      if (!bot.entity || ctx.elytra.aktiv() || ctx.wasser.aktiv() || ctx.portal?.laeuft()) { spur.length = 0; return }
      // Im Wasser Kopf oben halten (sonst haengt der Pathfinder am Grund bzw. im See fest)
      if (bot.entity.isInWater && (bot.pathfinder.goal || ctx.kampf.ziel())) bot.setControlState('jump', true)
      if (wasserTick()) return
      if (befreienTick(sprungTicks)) return
      if (sprungTicks <= 0 || !sprungZiel) return
      sprungTicks--
      const p = bot.entity.position
      bot.entity.yaw = Math.atan2(-(sprungZiel.x - p.x), -(sprungZiel.z - p.z))
      bot.setControlState('forward', true)
      bot.setControlState('sprint', false)
      bot.setControlState('jump', sprungZiel.y > p.y + 0.4)
      const d = Math.hypot(sprungZiel.x - p.x, sprungZiel.z - p.z)
      if (sprungTicks === 0 || (d < 0.3 && Math.abs(sprungZiel.y - p.y) < 0.5)) {
        sprungTicks = 0
        bot.setControlState('jump', false)
      }
    })
  }

  // ---------------------------------------------------------------- Wasser verlassen / nicht haengen bleiben
  // Fortschritt der letzten 2 s (40 Ticks): wie weit ist der Bot gekommen?
  const spur = []
  let wasserTicks = 0
  let befreien = 0 // Ticks, in denen er sich selbst freistrampelt
  let befreienZaehler = 0
  let laufTicks = 0 // wie lange der Pathfinder schon ununterbrochen vorwaerts drueckt
  let fehlUfer = [] // { pos, bis }: nicht erreichte Ausstiege eine Weile meiden (sonst immer wieder dasselbe Ufer)
  function fortschritt () {
    if (spur.length < 40) return Infinity
    const a = spur[0]
    const p = bot.entity.position
    return Math.hypot(p.x - a.x, p.z - a.z)
  }
  function wohinWill () {
    const g = bot.pathfinder.goal
    if (g?.entity?.position) return g.entity.position
    if (g && g.x != null && g.z != null) return new Vec3(g.x, g.y ?? bot.entity.position.y, g.z)
    const b = ctx.besitzer()
    return b?.position ?? null
  }

  // Ufer suchen: begehbarer Platz auf Hoehe der Wasseroberflaeche (+-1), nah am Bot, bevorzugt Richtung Ziel
  function uferSuchen () {
    const p = bot.entity.position.floored()
    let oben = p.y
    while (oben < p.y + 6 && ['water', 'bubble_column', 'seagrass', 'tall_seagrass', 'kelp', 'kelp_plant'].includes(bot.blockAt(new Vec3(p.x, oben, p.z))?.name)) oben++
    const ziel = wohinWill()
    let best = null
    let bestWert = Infinity
    for (let dx = -8; dx <= 8; dx++) {
      for (let dz = -8; dz <= 8; dz++) {
        for (const y of [oben, oben + 1, oben - 1]) {
          if (!stehbar(p.x + dx, y, p.z + dz)) continue
          // muss direkt an die Wasseroberflaeche grenzen, sonst ist er von hier aus nicht erreichbar
          const amWasser = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([ax, az]) =>
            bot.blockAt(new Vec3(p.x + dx + ax, oben - 1, p.z + dz + az))?.name === 'water')
          if (!amWasser) continue
          const kandidat = new Vec3(p.x + dx + 0.5, y, p.z + dz + 0.5)
          if (fehlUfer.some(f => f.bis > Date.now() && f.pos.distanceTo(kandidat) < 2)) continue
          // Ausstiege auf Hoehe der Wasseroberflaeche bevorzugen: eine volle Blockkante darueber ist aus tiefem
          // Wasser nicht zu erklimmen (dann muss er sich einen Tritt setzen)
          const wert = Math.hypot(dx, dz) + (ziel ? kandidat.distanceTo(ziel) * 0.4 : 0) + (y > oben ? 6 : Math.abs(y - oben) * 0.5)
          if (wert < bestWert) { best = kandidat; bestWert = wert }
        }
      }
    }
    return best
  }

  // Block unter die Fuesse setzen (in das Wasser/die Luft darunter), an einen festen Nachbarblock geklickt
  const BAUBLOCK = /^(dirt|coarse_dirt|cobblestone|cobbled_deepslate|stone|netherrack|\w+_planks|sandstone|andesite|diorite|granite|tuff|deepslate|blackstone|basalt|end_stone)$/
  function trittSetzen () {
    const block = ctx.inv.finde(i => BAUBLOCK.test(i.name))
    if (!block) return false
    const p = bot.entity.position
    const zelle = new Vec3(Math.floor(p.x), Math.floor(p.y) - 1, Math.floor(p.z))
    // Fuesse muessen ueber der Zelle sein - auch bei der Position, die der Server gerade kennt (letzter Tick)
    if (p.y - (zelle.y + 1) < 0.02 || !gesendet || gesendet.y - (zelle.y + 1) < 0.02) return false
    if (Math.floor(gesendet.x) !== zelle.x || Math.floor(gesendet.z) !== zelle.z) return false
    const hier = bot.blockAt(zelle)
    if (!hier || hier.boundingBox !== 'empty') return false
    for (const [dx, dy, dz, richtung] of [[0, -1, 0, 1], [1, 0, 0, 4], [-1, 0, 0, 5], [0, 0, 1, 2], [0, 0, -1, 3]]) {
      const nachbar = bot.blockAt(zelle.offset(dx, dy, dz))
      if (!nachbar || nachbar.boundingBox !== 'block') continue
      // richtung = Flaeche des Nachbarn, die zur Zelle zeigt (0 unten, 1 oben, 2 Norden, 3 Sueden, 4 Westen, 5 Osten)
      const vorher = bot.quickBarSlot
      const slot = block.slot >= 36 && block.slot <= 44 ? block.slot - 36 : null
      if (slot == null) { ctx.inv.inHotbar(block, 6).catch(() => {}); return false }
      if (slot !== vorher) bot.setQuickBarSlot(slot)
      const c = { 1: [0.5, 1, 0.5], 2: [0.5, 0.5, 0], 3: [0.5, 0.5, 1], 4: [0, 0.5, 0.5], 5: [1, 0.5, 0.5] }[richtung]
      bot._client.write('block_place', {
        hand: 0, location: nachbar.position, direction: richtung, cursorX: c[0], cursorY: c[1], cursorZ: c[2],
        insideBlock: false, worldBorderHit: false, sequence: 0
      })
      bot.swingArm()
      if (slot !== vorher) bot.setQuickBarSlot(vorher)
      log(`Kante zu hoch - setze ${block.name} als Tritt bei ${zelle}`)
      return true
    }
    return false
  }

  // Zuletzt an den Server gesendete Position (dieser Listener laeuft vor dem Senden)
  let gesendet = null
  bot.on('physicsTick', () => { if (bot.entity) setImmediate(() => { gesendet = bot.entity?.position.clone() }) })

  // Im Wasser oder beim Auf-und-ab direkt darueber (dann ist isInWater kurz false)
  const nass = () => bot.entity.isInWater || ['water', 'bubble_column'].includes(bot.blockAt(bot.entity.position.offset(0, -0.7, 0))?.name)

  // true = steuert gerade selbst ans Ufer
  function wasserTick () {
    const e = bot.entity
    spur.push(e.position.clone())
    if (spur.length > 40) spur.shift()
    wasserTicks = nass() ? wasserTicks + 1 : 0
    if (ausstieg) {
      ausstieg.ticks++
      const p = e.position
      const z = ausstieg.ziel
      const dh = Math.hypot(z.x - p.x, z.z - p.z)
      if ((!nass() && e.onGround && dh < 1.5) || ausstieg.ticks > 160 || ctx.kampf.ziel()) {
        log(ausstieg.ticks > 160 ? 'Ufer nicht erreicht' : 'Aus dem Wasser raus')
        if (ausstieg.ticks > 160) {
          const jetzt = Date.now()
          fehlUfer = fehlUfer.filter(f => f.bis > jetzt).concat({ pos: z, bis: jetzt + 60000 })
        }
        ausstieg = null
        spur.length = 0 // erst wieder 2 s Fortschritt messen, damit der Pathfinder eine Chance bekommt
        bot.clearControlStates()
        return false
      }
      e.yaw = Math.atan2(-(z.x - p.x), -(z.z - p.z))
      bot.setControlState('forward', true)
      bot.setControlState('sprint', dh > 3)
      // Springen = im Wasser nach oben schwimmen; an der Uferkante hebt es ihn heraus
      bot.setControlState('jump', e.isInWater || (dh < 2 && z.y > p.y + 0.3))
      // Kante zu hoch (> 0,6 ueber den Fuessen im Sprung): Tritt-Block unter sich setzen
      // (Kante mindestens 1 Block ueber der Zelle unter den Fuessen = ueber der Wasseroberflaeche)
      if (dh < 1.6 && z.y - Math.floor(p.y) >= 1 && e.velocity.y > 0 && !e.isInWater && ausstieg.ticks - (ausstieg.tritt ?? -99) > 15) {
        if (trittSetzen()) ausstieg.tritt = ausstieg.ticks
      }
      return true
    }
    // Im Wasser ohne Fortschritt (1,5 s), obwohl er irgendwohin will -> selbst ans Ufer
    const ziel = wohinWill()
    if (wasserTicks > 30 && ziel && fortschritt() < 1.5 && !ctx.kampf.ziel()) {
      const zielImWasser = bot.blockAt(ziel.floored())?.name === 'water'
      if (zielImWasser && ziel.distanceTo(e.position) < 3) return false
      const ufer = uferSuchen()
      if (ufer) {
        log(`Im Wasser festgesteckt - schwimme ans Ufer ${ufer.floored()}`)
        bot.pathfinder.setGoal(null)
        ausstieg = { ziel: ufer, ticks: 0 }
        return true
      }
    }
    return false
  }

  // An Land: Pfad aktiv, aber 2 s kaum vom Fleck -> kurz seitlich springen und neu planen
  function befreienTick (sprungTicks) {
    if (befreien > 0) {
      befreien--
      if (befreien === 0) {
        bot.clearControlStates()
        // Neu planen, ohne das Ziel anzufassen (setGoal wuerde goto()-Aufrufe und den dynamic-Status stoeren)
        if (bot.pathfinder.goal) bot.pathfinder.setMovements(bot.pathfinder.movements)
        spur.length = 0
      }
      return true
    }
    const g = bot.pathfinder.goal
    // Nur wenn er wirklich laufen will (Pathfinder drueckt vorwaerts); sonst Zaehler zuruecksetzen, damit ein
    // frischer Weg nicht sofort als "haengt fest" zaehlt
    if (!g || nass() || !bot.pathfinder.isMoving() || sprungTicks > 0 || !bot.controlState.forward) { laufTicks = 0; return false }
    if (++laufTicks < 40) return false
    const ziel = wohinWill()
    if (!ziel || ziel.distanceTo(bot.entity.position) < 2.5) return false
    if (fortschritt() > 0.6) { befreienZaehler = 0; return false }
    befreienZaehler++
    log(`Haenge fest bei ${bot.entity.position.floored()} - befreie mich (${befreienZaehler}. Mal)`)
    const seite = Math.random() < 0.5 ? 'left' : 'right'
    bot.clearControlStates()
    bot.setControlState(seite, true)
    bot.setControlState('back', befreienZaehler % 2 === 0)
    bot.setControlState('jump', true)
    befreien = 8
    spur.length = 0
    laufTicks = 0
    return true
  }

  return {
    folgenTick,
    ausstiegLaeuft: () => !!ausstieg,
    wachePos: () => einst.modus === 'wache' ? wachePos : null,
    wacheSetzen,
    stehen () {
      bot.pathfinder.setGoal(null)
      bot.clearControlStates()
    }
  }
}

module.exports = { erstellen }
