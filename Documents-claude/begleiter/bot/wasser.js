// Wasser: Auto-MLG gegen Fallschaden (Wassereimer, im Nether Schleim/Pulverschnee/Heu/Netz) und danach wieder
// aufnehmen, Eimer an unendlichen Quellen nachfuellen, Luft. Alles rein client-seitig wie ein normaler Spieler.
const { Vec3 } = require('vec3')

// Landen auf diesen Bloecken macht weniger (Faktor) Fallschaden
const WEICH = { slime_block: 0, cobweb: 0, powder_snow: 0, hay_block: 0.2, honey_block: 0.2 }
// Ersatz, wo Wasser nicht geht (Nether) oder kein Wassereimer da ist - Reihenfolge = Vorrang.
// Windladungen macht das Mace-Modul (landungAbfangen); Heu/Spinnennetz nur, wenn keine Windladung da ist.
const ERSATZ = ['slime_block', 'hay_block', 'cobweb']
const AUGE = 1.62
const REICHWEITE = 4.48 // Blockreichweite 4,5 (Strahl ab Augenhoehe) minus Rundung

function erstellen (ctx) {
  const { bot, log, wahr, inv } = ctx
  let mlg = null // { phase: 'fall'|'aufnehmen', art, name, ziel (Landeblock), platz (wo Wasser/Block hinkommt), versuche, versuchTick, ticks }
  let nachfuellenBis = 0
  let tick = 0
  let vorherPos = null // zuletzt an den Server geschickte Position (der Server rechnet Item-Benutzung damit)
  let umlegen = false
  let luftSprung = false
  let ackSeit = 0 // Tick der letzten Server-Bestaetigung fuer Benutzen/Setzen
  bot._client.on('acknowledge_player_digging', () => { ackSeit = tick })

  const hotbar = item => item && item.slot >= 36 && item.slot <= 44
  const wassereimer = () => inv.finde(i => i.name === 'water_bucket')
  const leererEimer = () => inv.finde(i => i.name === 'bucket')
  const nether = () => ctx.dimension() === 'minecraft:the_nether'
  const fest = b => b && b.boundingBox === 'block'

  // Aufprall vorausberechnen: Flugbahn Tick fuer Tick (Schwerkraft 0,08, Luftwiderstand 0,98 senkrecht, 0,91 waagrecht),
  // Hitbox-Mitte und -Ecken. Liefert den Landeblock (oder Wasser/weiche Bloecke), Ticks bis dahin und die Hoehe.
  function aufprall () {
    const start = bot.entity.position
    let { x, y, z } = start
    let { x: vx, y: vy, z: vz } = bot.entity.velocity
    const ecken = [[0, 0], [0.3, 0.3], [-0.3, 0.3], [0.3, -0.3], [-0.3, -0.3]]
    for (let t = 1; t <= 120; t++) {
      const nx = x + vx
      const ny = y + vy
      const nz = z + vz
      for (let by = Math.floor(y - 0.001); by >= Math.floor(ny); by--) {
        for (const [dx, dz] of ecken) {
          const b = bot.blockAt(new Vec3(nx + dx, by, nz + dz))
          if (!b) continue
          if (b.name === 'water' || b.name === 'bubble_column') return { block: b, wasser: true, ticks: t, hoehe: start.y - by }
          if (fest(b) || WEICH[b.name] != null) return { block: b, wasser: false, ticks: t, hoehe: start.y - (by + 1) }
        }
      }
      x = nx; y = ny; z = nz
      vy = (vy - 0.08) * 0.98
      vx *= 0.91
      vz *= 0.91
    }
    return null
  }

  // Trifft eine der kommenden Positionen, die der Server kennt, das Reichweitenfenster ueber dem Landeblock?
  // Bei Endgeschwindigkeit (~3,9 Bloecke/Tick) kann der Bot pro Tick ueber das ganze Fenster springen.
  function fensterVerpasst (a, art) {
    if (!a) return false
    const oben = a.block.position.y + 1
    const max = art === 'block' ? REICHWEITE + 1 - AUGE : REICHWEITE - AUGE // Bloecke setzen: Reichweite + 1
    let y = vorherPos?.y ?? bot.entity.position.y
    let vy = bot.entity.velocity.y
    const hoehen = [y - oben, bot.entity.position.y - oben]
    y = bot.entity.position.y
    for (let t = 0; t < 120 && y > oben; t++) { y += vy; vy = (vy - 0.08) * 0.98; hoehen.push(y - oben) }
    if (art !== 'block') return !hoehen.some(h => h > 0.02 && h <= max)
    // Block: der Server rechnet die Reichweite ab der vorigen Position, die neue darf aber noch nicht in der
    // Zelle stecken -> zwei aufeinanderfolgende Positionen: vorher in Reichweite, jetzt ueber der Blockoberkante
    for (let i = 1; i < hoehen.length; i++) if (hoehen[i - 1] <= max && hoehen[i] > 1.05) return false
    return true
  }

  function schadenBei (a) {
    if (!a || a.wasser) return 0
    const oben = a.block.position.y + 1
    let s = Math.max(wahr.fallHoehe() + a.hoehe, (hoechst ?? oben) - oben) - 3
    s *= WEICH[a.block.name] ?? (a.block.name.endsWith('_bed') ? 0.5 : 1)
    s *= 1 - Math.min(inv.verzauberung(inv.getragen('feet'), 'feather_falling') * 0.12, 0.48)
    s *= 1 - Math.min(inv.schutz().epf * 4, 80) / 100
    return Math.max(0, s)
  }

  // Erwarteter Fallschaden bei der Landung (fuer andere Module)
  function fallschaden () {
    const a = aufprall()
    return { schaden: schadenBei(a), boden: a }
  }

  // Laub, Stufen, Zaeune, Treppen ... nehmen Wasser in sich auf (waterlogged): der Eimer flutet dann den Block
  // selbst, statt Wasser obendrauf zu setzen - und der Bot schlaegt trotzdem auf dem festen Block auf.
  const nimmtWasserAuf = b => b?.getProperties?.().waterlogged !== undefined
  const BAUBLOCK = /^(dirt|coarse_dirt|cobblestone|cobbled_deepslate|stone|netherrack|\w+_planks|sandstone|andesite|diorite|granite|tuff|deepslate|blackstone|end_stone)$/

  // Womit abfangen? Wasser zuerst (ausser im Nether), dann Schleim, Heu/Netz nur ohne Windladung.
  // Landet er auf einem wasseraufnehmenden Block: weiche Bloecke, sonst erst einen Baublock obendrauf
  // (danach sieht die Vorausberechnung den neuen Block und setzt Wasser darauf).
  function mittelWaehlen (a = aufprall()) {
    const wasserGeht = !nether() && !nimmtWasserAuf(a?.block)
    if (wasserGeht) {
      const w = wassereimer()
      if (w) return { art: 'wasser', item: w }
    }
    for (const name of ERSATZ) {
      if ((name === 'hay_block' || name === 'cobweb') && inv.windladung()) return null // Windladung ist besser
      const it = inv.finde(i => i.name === name)
      if (it) return { art: 'block', item: it, platz: name }
    }
    if (!nether() && nimmtWasserAuf(a?.block) && wassereimer()) {
      const bau = inv.finde(i => BAUBLOCK.test(i.name))
      if (bau) return { art: 'block', item: bau, platz: bau.name }
    }
    return null
  }

  function blickVon (auge, punkt) {
    const d = punkt.minus(auge)
    return { yaw: Math.atan2(-d.x, -d.z), pitch: Math.atan2(d.y, Math.hypot(d.x, d.z)) }
  }

  // Eimer aus der Hotbar benutzen: der Server zielt mit der mitgeschickten Blickrichtung ab seiner Augenposition
  function eimerBenutzen (item, blick) {
    const vorher = bot.quickBarSlot
    bot.entity.yaw = blick.yaw
    bot.entity.pitch = blick.pitch
    bot.look(blick.yaw, blick.pitch, true)
    if (item.slot - 36 !== vorher) bot.setQuickBarSlot(item.slot - 36)
    bot.activateItem()
    bot.deactivateItem()
    if (item.slot - 36 !== vorher) bot.setQuickBarSlot(vorher)
  }

  // Block oben auf den Landeblock setzen (der Server prueft dabei nur die Reichweite, nicht die Blickrichtung)
  function blockSetzen (item, landeblock) {
    const vorher = bot.quickBarSlot
    if (item.slot - 36 !== vorher) bot.setQuickBarSlot(item.slot - 36)
    bot._client.write('block_place', {
      hand: 0,
      location: landeblock.position,
      direction: 1,
      cursorX: 0.5,
      cursorY: 1,
      cursorZ: 0.5,
      insideBlock: false,
      worldBorderHit: false,
      sequence: 0
    })
    bot.swingArm()
    if (item.slot - 36 !== vorher) bot.setQuickBarSlot(vorher)
  }

  function versuchen (mittel, a) {
    const auge = (vorherPos ?? bot.entity.position).offset(0, AUGE, 0)
    if (mittel.art === 'block') blockSetzen(mittel.item, a.block)
    else eimerBenutzen(mittel.item, blickVon(auge, a.block.position.offset(0.5, 1, 0.5)))
    const n = (mlg?.phase === 'fall' ? mlg.versuche : 0) + 1
    mlg = { phase: 'fall', art: mittel.art, name: mittel.item.name, block: mittel.platz ?? mittel.item.name, ziel: a.block.position, platz: a.block.position.offset(0, 1, 0), versuche: n, versuchTick: tick }
    vorhersagen(mlg)
    const h = ((vorherPos ?? bot.entity.position).y - (a.block.position.y + 1)).toFixed(1)
    if (n === 1) log(`MLG: ${mittel.item.name} auf ${a.block.name} (Server-Hoehe ${h}, Landung in ${a.ticks} Ticks${a.landetJetzt ? ' = gleich' : ''}, erwarteter Schaden ${schadenBei(a).toFixed(0)})`)
  }

  // Client-Vorhersage wie in Vanilla: den gesetzten Block bzw. das Wasser sofort lokal eintragen, damit die
  // eigene Physik (und die naechste Aufprall-Berechnung) nicht erst auf die Antwort des Servers wartet.
  // Lehnt der Server ab, korrigiert sein Block-Update das wieder.
  function vorhersagen (m) {
    const name = m.art === 'wasser' ? 'water' : m.block
    const b = ctx.mcData.blocksByName[name]
    const hier = bot.blockAt(m.platz)
    if (!b || !hier || hier.boundingBox !== 'empty' || hier.name === name) return
    // Nicht in die eigene Hitbox (sonst schiebt die Physik den Bot aus dem Block heraus)
    if (m.art === 'block' && bot.entity.position.y < m.platz.y + 1) return
    try { bot.world.setBlockStateId(m.platz, b.defaultState) } catch {}
  }

  // Liegt das Wasser / der Block schon?
  function liegt (m) {
    const b = m && bot.blockAt(m.platz)
    if (!b) return false
    if (m.art === 'wasser') return b.name === 'water'
    return b.name === m.block
  }

  // true = Wasser-Modul hat gerade die Steuerung
  let vorher = null // { onGround, vy } des zuletzt gesendeten Ticks
  let hoechst = null // hoechster Punkt seit dem letzten Bodenkontakt (eigene Fallhoehe, auch im Landetick gueltig)
  function physikTick () {
    tick++
    const e = bot.entity
    try { return mlgTick(e) } finally {
      vorherPos = e.position.clone()
      vorher = { onGround: e.onGround, vy: e.velocity.y }
      if (e.onGround || e.isInWater || e.elytraFlying) hoechst = e.position.y
      else hoechst = Math.max(hoechst ?? e.position.y, e.position.y)
    }
  }

  function mlgTick (e) {
    // Luft knapp: Kopf oben halten
    const luft = e.metadata?.[1]
    if (e.isInWater && typeof luft === 'number' && luft < 150) { bot.setControlState('jump', true); luftSprung = true } else if (luftSprung && (!e.isInWater || luft >= 290)) {
      // Springen wieder loslassen, sonst huepft er nach dem Auftauchen endlos weiter
      luftSprung = false
      bot.setControlState('jump', false)
    }

    if (mlg?.phase === 'aufnehmen') return aufnehmenTick()

    // Lokal schon gelandet, die Landung ist aber noch nicht beim Server (Position geht erst nach diesem Tick raus):
    // letzte Gelegenheit, mit der Position, die der Server noch kennt
    const abgefangen = mlg?.phase === 'fall' && liegt(mlg) && (mlg.art === 'wasser' || WEICH[mlg.block] != null)
    const landetJetzt = e.onGround && vorher && !vorher.onGround && vorher.vy < -0.5 && !abgefangen
    if (!landetJetzt && (e.onGround || e.elytraFlying || e.isInWater || e.velocity.y > -0.3)) {
      if (mlg?.phase === 'fall' && (e.onGround || e.isInWater || e.velocity.y > -0.1)) {
        log(`MLG: gelandet (${liegt(mlg) ? mlg.name + ' lag' : 'ohne ' + mlg.name}, ${mlg.versuche} Versuch(e), Leben ${Math.round(bot.health)})`)
        mlg = { ...mlg, phase: 'aufnehmen', ticks: 0 }
      }
      return false
    }
    // Wasser oder weicher Block liegt schon: einfach reinfallen. Ein harter Baublock (auf Laub gesetzt) ist nur
    // die Unterlage fuer das Wasser - dann geht es mit dem Eimer weiter.
    if (mlg?.phase === 'fall' && liegt(mlg) && (mlg.art === 'wasser' || WEICH[mlg.block] != null)) return false

    let a
    if (landetJetzt) {
      const b = bot.blockAt(e.position.offset(0, -0.2, 0))
      if (!fest(b) && WEICH[b?.name] == null) return false
      a = { block: b, wasser: false, ticks: 0, hoehe: 0, landetJetzt: true }
    } else {
      a = aufprall()
    }
    if (!a || a.wasser) return false
    const schaden = schadenBei(a)
    if (schaden < 2 || (schaden < 5 && schaden < bot.health - 6)) return false
    const mittel = mittelWaehlen(a)
    if (!mittel) return false
    if (!hotbar(mittel.item)) {
      if (!umlegen) { umlegen = true; inv.inHotbar(mittel.item, 7).catch(() => {}).finally(() => { umlegen = false }) }
      return false
    }

    // Reichweite ab der Augenposition, die der Server gerade kennt
    const auge = (vorherPos ?? e.position).offset(0, AUGE, 0)
    const d = auge.distanceTo(a.block.position.offset(0.5, 1, 0.5))
    if (d > (mittel.art === 'block' ? REICHWEITE + 1 : REICHWEITE)) return !!mlg
    // Ein Block kann nur in eine Zelle, in der der Bot noch nicht steckt: Fuesse (auch die gleich gesendete
    // Position) muessen ueber der Oberkante des neuen Blocks sein, sonst lehnt der Server ab
    if (mittel.art === 'block' && e.position.y < a.block.position.y + 2 + 0.05) return !!mlg
    // Noch keine Antwort auf den letzten Versuch? Nicht doppelt benutzen (sonst holt der leere Eimer das Wasser zurueck)
    // Nur beim Wasser auf die Server-Antwort warten (ein zweiter Eimer-Klick wuerde das Wasser wieder aufnehmen);
    // nach einem gesetzten Unterlage-Block darf das Wasser sofort hinterher
    if (mlg?.phase === 'fall' && mlg.art === 'wasser' && ackSeit < mlg.versuchTick && tick - mlg.versuchTick < 6) return true
    if (mlg?.phase === 'fall' && mlg.art === 'block' && mittel.art === 'block' && tick - mlg.versuchTick < 3) return true
    versuchen(mittel, a)
    return true
  }

  // Nach der Landung: Wasser/Pulverschnee mit dem leeren Eimer wieder einsammeln, Schleim/Heu/Netz abbauen
  function aufnehmenTick () {
    mlg.ticks++
    if (mlg.ticks > 40 || !liegt(mlg)) {
      if (mlg.aufgenommen) log(`MLG: ${mlg.name} wieder ${mlg.art === 'block' ? 'abgebaut' : 'aufgenommen'}`)
      mlg = null
      return false
    }
    if (mlg.art === 'block') {
      if (mlg.ticks === 3 && !mlg.aufgenommen && ctx.handNehmen('mlg', 60, 3000)) {
        mlg.aufgenommen = true
        bot.dig(bot.blockAt(mlg.platz), true).catch(() => {}).finally(() => ctx.handFrei('mlg'))
      }
      return false
    }
    // Eimer: alle 4 Ticks versuchen, solange dort noch etwas liegt
    const eimer = leererEimer()
    if (!eimer || !hotbar(eimer) || mlg.ticks % 4 !== 2) return false
    const auge = bot.entity.position.offset(0, AUGE, 0)
    const punkt = mlg.platz.offset(0.5, 0.5, 0.5)
    if (auge.distanceTo(punkt) > REICHWEITE) return false
    eimerBenutzen(eimer, blickVon(auge, punkt))
    mlg.aufgenommen = true
    return false
  }

  // Eimer nachfuellen: nur an einer unendlichen Quelle (Quellblock mit >= 2 Quell-Nachbarn)
  function unendlicheQuelle () {
    const quellen = bot.findBlocks({
      matching: b => b.name === 'water' && (b.metadata === 0 || b.getProperties?.().level === 0 || b.getProperties?.().level === '0'),
      maxDistance: 24,
      count: 200
    })
    const istQuelle = p => {
      const b = bot.blockAt(p)
      if (!b || b.name !== 'water') return false
      const l = b.getProperties?.().level
      return l === 0 || l === '0' || l === undefined
    }
    for (const p of quellen.sort((a, b) => a.distanceTo(bot.entity.position) - b.distanceTo(bot.entity.position))) {
      const nachbarn = [[1, 0], [-1, 0], [0, 1], [0, -1]].filter(([dx, dz]) => istQuelle(p.offset(dx, 0, dz))).length
      if (nachbarn >= 2) return p
    }
    return null
  }

  let fuellt = false
  // Synchron pruefen; wenn es losgeht, laeuft das Nachfuellen im Hintergrund (true = gestartet)
  function nachfuellenStarten () {
    if (fuellt || Date.now() < nachfuellenBis || wassereimer() || !leererEimer() || mlg) return false
    if (ctx.kampf.ziel() || ctx.aufgaben.laeuft() || ctx.elytra.aktiv() || wahr.imKampf() || nether()) return false
    nachfuellenBis = Date.now() + 30000
    const q = unendlicheQuelle()
    if (!q) return false
    const b = ctx.besitzer()
    if (b && b.position.distanceTo(q) > 20) return false // nicht weit vom Besitzer weg
    fuellt = true
    nachfuellen(q).finally(() => { fuellt = false })
    return true
  }

  async function nachfuellen (q) {
    log(`Fuelle Wassereimer an unendlicher Quelle ${q.x} ${q.y} ${q.z}`)
    // Haengt der Weg (Pathfinder plant nach "stuck" endlos neu), blockiert fuellt sonst das Folgen fuer immer
    const abbruch = setTimeout(() => bot.pathfinder.setGoal(null), 20000)
    try {
      const { goals } = require('mineflayer-pathfinder')
      await bot.pathfinder.goto(new goals.GoalNear(q.x, q.y + 1, q.z, 2))
      const eimer = leererEimer()
      if (!eimer) return false
      await bot.equip(eimer, 'hand')
      // Auf die Blockmitte zielen (0,9 lag knapp ueber der Wasseroberflaeche) und die Blickrichtung erst beim Server
      // ankommen lassen; bis zu 3 Versuche
      for (let i = 0; i < 3 && !wassereimer(); i++) {
        await bot.lookAt(q.offset(0.5, 0.5, 0.5), true)
        await ctx.warte(120)
        const e = leererEimer()
        if (!e) break
        if (bot.heldItem?.name !== 'bucket') await bot.equip(e, 'hand')
        bot.activateItem()
        bot.deactivateItem()
        await ctx.warte(300)
      }
      log(wassereimer() ? 'Wassereimer gefuellt' : 'Wassereimer fuellen hat nicht geklappt')
      return !!wassereimer()
    } catch (e) {
      log('Nachfuellen:', e.message)
      return false
    } finally {
      clearTimeout(abbruch)
    }
  }

  return {
    physikTick, fallschaden, aufprall, mittelWaehlen, nachfuellenStarten, unendlicheQuelle,
    nachfuellenLaeuft: () => fuellt,
    aktiv: () => mlg?.phase === 'fall',
    // Kann gleich ein Mittel (Wasser/Block) den Sturz abfangen? Dann braucht das Mace-Modul keine Windladung
    kannAbfangen: () => {
      const m = mittelWaehlen()
      if (!m || !hotbar(m.item)) return false
      // Wird das Fenster uebersprungen, darf das Mace-Modul mit der Windladung einspringen
      return !(e => !e.onGround && e.velocity.y < -0.3 && fensterVerpasst(aufprall(), m.art))(bot.entity)
    },
    // Sturz, den kein Mittel sicher abfaengt -> Totem bereithalten (Ueberleben-Modul)
    toedlicherSturz: () => {
      const e = bot.entity
      if (e.onGround || e.isInWater || e.elytraFlying || e.velocity.y > -0.5) return false
      const a = aufprall()
      const s = schadenBei(a)
      if (s < bot.health) return false
      const m = mittelWaehlen(a)
      return !m || fensterVerpasst(a, m.art)
    }
  }
}

module.exports = { erstellen, WEICH }
