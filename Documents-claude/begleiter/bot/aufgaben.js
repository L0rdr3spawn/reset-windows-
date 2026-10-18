// Aufgaben des Bots. Jede Art ist eine async-Funktion; Parameter (Block, Item, Mob, Menge ...)
// kommen aus minecraft-data, deshalb geht jede Aufgabe fuer jeden passenden Block/Item/Mob.
const { goals } = require('mineflayer-pathfinder')
const { Vec3 } = require('vec3')

// Rohstoff-Gruppen: mehrere Bloecke, die fuer den Spieler "dasselbe" sind
const ROHSTOFFE = {
  holz: { name: 'Holz (Baumstaemme faellen)', bloecke: n => n.endsWith('_log') && !n.startsWith('stripped_'), standard: 16 },
  stein: { name: 'Stein bzw. Bruchstein', bloecke: ['stone', 'cobblestone'], standard: 32 },
  kohle: { name: 'Kohle', bloecke: ['coal_ore', 'deepslate_coal_ore'], standard: 16 },
  eisen: { name: 'Eisenerz', bloecke: ['iron_ore', 'deepslate_iron_ore'], standard: 8 },
  kupfer: { name: 'Kupfererz', bloecke: ['copper_ore', 'deepslate_copper_ore'], standard: 16 },
  gold: { name: 'Golderz', bloecke: ['gold_ore', 'deepslate_gold_ore', 'nether_gold_ore'], standard: 8 },
  diamant: { name: 'Diamanten', bloecke: ['diamond_ore', 'deepslate_diamond_ore'], standard: 3 },
  smaragd: { name: 'Smaragde', bloecke: ['emerald_ore', 'deepslate_emerald_ore'], standard: 3 },
  redstone: { name: 'Redstone', bloecke: ['redstone_ore', 'deepslate_redstone_ore'], standard: 16 },
  lapis: { name: 'Lapislazuli', bloecke: ['lapis_ore', 'deepslate_lapis_ore'], standard: 16 },
  quarz: { name: 'Netherquarz', bloecke: ['nether_quartz_ore'], standard: 16 },
  sand: { name: 'Sand', bloecke: ['sand', 'red_sand'], standard: 32 },
  erde: { name: 'Erde', bloecke: ['dirt', 'grass_block', 'coarse_dirt'], standard: 32 },
  kies: { name: 'Kies', bloecke: ['gravel'], standard: 16 },
  ton: { name: 'Ton', bloecke: ['clay'], standard: 16 },
  laub: { name: 'Laub / Blaetter', bloecke: n => n.endsWith('_leaves'), standard: 16 }
}

// Davon behaelt er immer so viele (auch bei "gib alles")
const RESERVE = { totem_of_undying: 2 }

const passt = (spec, name) => typeof spec === 'function' ? spec(name) : spec.includes(name)
const SUCHRADIUS = 64
const UNENDLICH = Infinity

// Reife Feldfruechte -> Saatgut zum Nachpflanzen
const PFLANZEN = {
  wheat: { reif: 7, saat: 'wheat_seeds' },
  carrots: { reif: 7, saat: 'carrot' },
  potatoes: { reif: 7, saat: 'potato' },
  beetroots: { reif: 3, saat: 'beetroot_seeds' },
  nether_wart: { reif: 3, saat: 'nether_wart' }
}

// Womit man welches Tier fuettert/zuechtet
const FUTTER = {
  cow: ['wheat'], mooshroom: ['wheat'], sheep: ['wheat'], goat: ['wheat'],
  pig: ['carrot', 'potato', 'beetroot'], rabbit: ['carrot', 'dandelion'],
  chicken: ['wheat_seeds', 'melon_seeds', 'pumpkin_seeds', 'beetroot_seeds'],
  horse: ['golden_carrot', 'golden_apple'], donkey: ['golden_carrot', 'golden_apple'],
  llama: ['hay_block'], wolf: ['beef', 'porkchop', 'chicken', 'mutton'], cat: ['cod', 'salmon'],
  fox: ['sweet_berries'], bee: ['dandelion', 'poppy'], turtle: ['seagrass'], frog: ['slime_ball'],
  armadillo: ['spider_eye'], camel: ['cactus'], sniffer: ['torchflower_seeds'], panda: ['bamboo'],
  axolotl: ['tropical_fish_bucket'], strider: ['warped_fungus'], hoglin: ['crimson_fungus']
}

// Brennstoff fuer den Ofen, bestes zuerst
const BRENNSTOFF = ['coal', 'charcoal', 'coal_block', 'blaze_rod', 'lava_bucket']
const BRENNSTOFF_HOLZ = n => n.endsWith('_planks') || n.endsWith('_log') || n === 'stick'

// Was beim Einlagern im Inventar bleibt
function behalten (item, mcData) {
  return /sword|axe|pickaxe|shovel|hoe|helmet|chestplate|leggings|boots|shield|bow|trident|shears|fishing_rod|torch|totem_of_undying|bucket|elytra|mace|spear|arrow|firework_rocket|wind_charge|ender_pearl|potion/.test(item.name) ||
    !!mcData.foodsByName[item.name]
}

function erstelleAufgaben (bot, mcData, { log, fluestern, bewegungNormal, bewegungArbeit, ort, speichereOrt, beiFertig, lootPause = () => {} }) {
  let aktuell = null // { art, ...parameter, gesammelt, pausiert }
  let laeuft = false
  let abbruch = false
  const warteschlange = []

  const items = () => bot.inventory.items()
  const itemName = id => mcData.items[id]?.displayName ?? mcData.blocks[id]?.displayName ?? String(id)
  const hat = name => items().find(i => i.name === name)
  const anzahlItem = name => items().filter(i => i.name === name).reduce((s, i) => s + i.count, 0)
  const warte = ms => new Promise(resolve => setTimeout(resolve, ms))
  const pruefen = () => { if (abbruch) throw Object.assign(new Error('abgebrochen'), { abbruch: true }) }
  const mengeText = n => n === UNENDLICH ? 'ohne Ende' : String(n)

  async function hingehen (ziel, abstand = 1) {
    pruefen()
    await bot.pathfinder.goto(new goals.GoalNear(ziel.x, ziel.y, ziel.z, abstand))
    pruefen()
  }

  function naechsterBlock (matching, radius = SUCHRADIUS) {
    return bot.findBlock({ matching, maxDistance: radius })
  }

  // Block aus dem Inventar neben den Bot stellen (Werkbank, Ofen ...)
  async function hinstellen (name) {
    const item = hat(name)
    if (!item) return null
    const p = bot.entity.position.floored()
    for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, -1], [2, 0], [0, 2]]) {
      const boden = bot.blockAt(p.offset(dx, -1, dz))
      const platz = bot.blockAt(p.offset(dx, 0, dz))
      if (boden?.boundingBox === 'block' && platz?.name === 'air') {
        await bot.equip(item, 'hand')
        await bot.placeBlock(boden, new Vec3(0, 1, 0))
        return bot.blockAt(p.offset(dx, 0, dz))
      }
    }
    return null
  }

  function kannAbbauen (blockId) {
    const werkzeuge = mcData.blocks[blockId].harvestTools
    return !werkzeuge || items().some(i => werkzeuge[i.type])
  }

  // Flüssigkeit neben einer Stelle, an der gegraben werden soll?
  function gefahrNeben (pos) {
    for (const o of [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]) {
      const b = bot.blockAt(pos.offset(...o))
      if (b && (b.name === 'lava' || b.name === 'water')) return b.name
    }
    return null
  }

  async function graben (pos) {
    const b = bot.blockAt(pos)
    if (!b || b.boundingBox === 'empty' || b.name === 'air') return
    if (!bot.canDigBlock(b)) throw new Error(`kann ${b.displayName} nicht abbauen`)
    const gefahr = gefahrNeben(pos)
    if (gefahr === 'lava') throw new Error('Lava dahinter, ich grabe da nicht weiter')
    await bot.tool.equipForBlock(b, {})
    await bot.dig(b, true)
  }

  // Verteilt Drops im Umkreis einsammeln
  async function dropsAufheben (radius = 8) {
    const drops = Object.values(bot.entities).filter(e => e.name === 'item' && e.position.distanceTo(bot.entity.position) < radius)
    if (drops.length) await bot.collectBlock.collect(drops, { ignoreNoPath: true }).catch(() => {})
  }

  // Genau einen Slot abwerfen (Inventar-Oberflaeche der Mod), auch Ruestung (5-8) und Nebenhand (45).
  // Teilmenge: Stapel aufnehmen, einzeln per Rechtsklick ausserhalb des Fensters werfen, Rest zuruecklegen.
  async function slotGeben (a) {
    lootPause()
    const item = bot.inventory.slots[a.slot]
    if (!item) return 'Der Platz ist leer.'
    if (a.item && item.name !== a.item) return `Da liegt jetzt ${item.name} statt ${a.item}.`
    let gesamt = 0
    for (let s = 5; s <= 45; s++) if (bot.inventory.slots[s]?.name === item.name) gesamt += bot.inventory.slots[s].count
    const menge = Math.min(a.menge === UNENDLICH ? item.count : (a.menge ?? item.count), item.count, gesamt - (a.reserve ?? RESERVE[item.name] ?? 0))
    if (menge <= 0) return `Von ${item.name} habe ich nur ${gesamt} - die behalte ich.`
    if (menge === item.count) {
      await bot.tossStack(item)
    } else {
      await bot.clickWindow(item.slot, 0, 0)
      for (let k = 0; k < menge; k++) await bot.clickWindow(-999, 1, 0)
      await bot.clickWindow(a.slot, 0, 0)
    }
    await wegTreten()
    return `${menge}x ${item.name} abgeworfen.`
  }

  // Wurfbahn wie in Vanilla (Player.drop): Start 0,3 unter Augenhoehe, 0,3 Bloecke/Tick in Blickrichtung plus
  // 0,1 nach oben, dann je Tick Schwerkraft 0,04 und Luftwiderstand 0,98. Gesucht: der Winkel, bei dem das Item
  // auf der Oberkante des Blocks landet, auf dem der Besitzer steht.
  function wurfZielen (besitzer) {
    const start = bot.entity.position.offset(0, 1.62 - 0.3, 0)
    const ziel = besitzer.position // Fuesse = Oberkante des Standblocks
    const dx = ziel.x - start.x
    const dz = ziel.z - start.z
    const weite = Math.hypot(dx, dz)
    const yaw = Math.atan2(-dx, -dz)
    const rx = weite > 0 ? dx / weite : 0
    const rz = weite > 0 ? dz / weite : 0
    // Stoesst das Item (0,25 gross) unterwegs an einen Block? Dann faellt es irgendwo hin, nur nicht zu dir
    const blockiert = (x, y) => [0, 0.25].some(dy => [-0.13, 0, 0.13].some(dx => {
      const b = bot.blockAt(new Vec3(start.x + rx * (x + dx), y + dy, start.z + rz * (x + dx)))
      return b && b.boundingBox === 'block'
    }))
    let best = { fehler: Infinity, pitch: 0 }
    for (let grad = -70; grad <= 85; grad += 1) { // Minecraft-Pitch: + = nach unten
      const p = grad * Math.PI / 180
      let h = Math.cos(p) * 0.3
      let vy = -Math.sin(p) * 0.3 + 0.1
      let x = 0
      let y = start.y
      let fehler = 0
      for (let t = 0; t < 120; t++) {
        vy -= 0.04
        x += h
        y += vy
        h *= 0.98
        vy *= 0.98
        if (vy < 0 && y <= ziel.y + 0.01) break
        if (blockiert(x, y)) { fehler = 100; break }
      }
      fehler += Math.abs(x - weite)
      if (fehler < best.fehler) best = { fehler, pitch: p }
    }
    bot.look(yaw, -best.pitch, true) // Mineflayer: + = nach oben
    return best
  }

  // Nach dem Werfen zwei Schritte zurueck (Aufheb-Reichweite der Spieler ~1 Block um die Hitbox)
  let zuruecktreten = false
  async function wegTreten () {
    if (!zuruecktreten) return
    zuruecktreten = false
    bot.setControlState('back', true)
    await new Promise(resolve => setTimeout(resolve, 700))
    bot.setControlState('back', false)
  }

  function blickRichtung (yaw = bot.entity.yaw) {
    // Yaw 0 = Norden (-z) in mineflayer
    const dx = Math.round(-Math.sin(yaw))
    const dz = Math.round(-Math.cos(yaw))
    return Math.abs(dx) >= Math.abs(dz) ? new Vec3(Math.sign(dx) || 1, 0, 0) : new Vec3(0, 0, Math.sign(dz) || 1)
  }

  // ---------------- Aufgaben-Arten ----------------

  const ARTEN = {
    // Beliebige Bloecke oder Rohstoff-Gruppen abbauen, auch ohne Ende
    async abbauen (a) {
      const ids = a.blockIds
      const gesperrt = new Set()
      let fehlschlaege = 0
      while (a.gesammelt < a.menge) {
        pruefen()
        if (bot.inventory.emptySlotCount() === 0) {
          if (!ort.truhe) return `Inventar voll (${a.gesammelt}x ${a.name}). Keine Truhe gesetzt.`
          await ARTEN.einlagern(a)
          if (bot.inventory.emptySlotCount() === 0) return `Inventar voll und nichts mehr einzulagern (${a.gesammelt}x ${a.name}).`
          continue
        }
        const abbaubar = ids.filter(kannAbbauen)
        if (abbaubar.length === 0) return `Ich brauche ein besseres Werkzeug fuer ${a.name}.`
        const pos = bot.findBlocks({ matching: abbaubar, maxDistance: SUCHRADIUS, count: 32 }).find(p => !gesperrt.has(p.toString()) && gefahrNeben(p) !== 'lava')
        if (!pos) return `Keine erreichbaren ${a.name} mehr in ${SUCHRADIUS} Bloecken (${a.gesammelt} abgebaut).`
        try {
          await bot.collectBlock.collect(bot.blockAt(pos), { ignoreNoPath: true })
          if (!abbaubar.includes(bot.blockAt(pos)?.type)) a.gesammelt++
          fehlschlaege = 0
          // Nach einem Baum einen Setzling pflanzen
          if (a.setzlinge) await setzlingPflanzen(pos).catch(() => {})
        } catch (e) {
          pruefen()
          gesperrt.add(pos.toString())
          log(`Abbauen bei ${pos} fehlgeschlagen: ${e.message}`)
          if (++fehlschlaege >= 5) return `Komme an ${a.name} nicht heran (${a.gesammelt} abgebaut).`
        }
      }
      return `${a.gesammelt}x ${a.name} abgebaut.`
    },

    async einlagern () {
      if (!ort.truhe) throw new Error('keine Truhe gesetzt - stell dich an eine Truhe und sag !heim')
      const pos = new Vec3(ort.truhe.x, ort.truhe.y, ort.truhe.z)
      await bot.pathfinder.goto(new goals.GoalGetToBlock(pos.x, pos.y, pos.z))
      pruefen()
      const truhe = await bot.openContainer(bot.blockAt(pos))
      let n = 0
      try {
        for (const item of items()) {
          if (behalten(item, mcData)) continue
          await truhe.deposit(item.type, item.metadata, item.count)
          n++
        }
      } catch (e) {
        log('Einlagern gestoppt:', e.message) // meist: Truhe voll
      } finally {
        truheMerken(truhe)
        truhe.close()
      }
      return `${n} Stapel eingelagert.`
    },

    // Bestimmtes Item aus der Truhe holen
    async holen (a) {
      const truhePos = ort.truhe ? new Vec3(ort.truhe.x, ort.truhe.y, ort.truhe.z) : naechsterBlock(['chest', 'barrel', 'trapped_chest'].map(n => mcData.blocksByName[n]?.id), 32)?.position
      if (!truhePos) throw new Error('keine Truhe bekannt')
      await bot.pathfinder.goto(new goals.GoalGetToBlock(truhePos.x, truhePos.y, truhePos.z))
      pruefen()
      const truhe = await bot.openContainer(bot.blockAt(truhePos))
      try {
        const vorrat = truhe.containerItems().filter(i => i.name === a.item).reduce((s, i) => s + i.count, 0)
        if (vorrat === 0) return `Keine ${itemName(mcData.itemsByName[a.item].id)} in der Truhe.`
        const n = Math.min(vorrat, a.menge === UNENDLICH ? vorrat : a.menge)
        await truhe.withdraw(mcData.itemsByName[a.item].id, null, n)
        return `${n}x ${itemName(mcData.itemsByName[a.item].id)} geholt.`
      } finally {
        truheMerken(truhe)
        truhe.close()
      }
    },

    async heim () {
      if (!ort.heim) throw new Error('kein Zuhause gesetzt - sag !heim, wo du stehst')
      await hingehen(ort.heim, 2)
      return 'Bin zu Hause.'
    },

    // Beliebiges Pfadfinder-Ziel (fuer /bot baritone): a.goalFn() liefert das Ziel. folgen = dynamisch bis Stopp.
    async ziel (a) {
      const goal = a.goalFn()
      if (!goal) return a.fehlerText ?? 'Kein Ziel.'
      if (a.folgen) {
        bot.pathfinder.setGoal(goal, true)
        await new Promise(resolve => {
          const t = setInterval(() => { if (abbruch || !a.goalFn()) { clearInterval(t); resolve() } }, 250)
        })
        return a.fertigText ?? 'Folgen beendet.'
      }
      await bot.pathfinder.goto(goal)
      return a.fertigText ?? 'Ziel erreicht.'
    },

    // Erkunden wie Baritone "explore": in einer Spirale immer weiter nach aussen, bis Stopp
    async erkunden (a) {
      // Mitte einmal festhalten - nach einer Kampfpause geht es um dieselbe Mitte weiter
      const mitte = a.mitte ??= bot.entity.position.floored()
      for (let i = 1; !abbruch; i++) {
        pruefen()
        const winkel = i * 2.4 // ungefaehr goldener Winkel -> gleichmaessig verteilt
        const r = 32 + i * 24
        const x = Math.round(mitte.x + Math.cos(winkel) * r)
        const z = Math.round(mitte.z + Math.sin(winkel) * r)
        a.gesammelt = i
        await bot.pathfinder.goto(new goals.GoalXZ(x, z)).catch(e => log('Erkunden:', e.message))
      }
      return 'Erkunden beendet.'
    },

    async gehen (a) {
      if (a.y == null) await bot.pathfinder.goto(new goals.GoalXZ(a.x, a.z))
      else await hingehen(new Vec3(a.x, a.y, a.z), 1)
      return `Bin bei ${a.x} ${a.y ?? ''} ${a.z}.`
    },

    // Item herstellen; baut Zwischenprodukte (Bretter, Stoecke, Werkbank ...) selbst
    async craften (a) {
      const id = mcData.itemsByName[a.item].id
      const name = itemName(id)
      const gemacht = await herstellen(id, a.menge)
      if (gemacht >= a.menge) return `${gemacht}x ${name} hergestellt.`
      if (gemacht > 0) return `${gemacht}x ${name} hergestellt, dann ging das Material aus.`
      return `Kann ${name} nicht herstellen, mir fehlt: ${fehlendeZutaten(id) || 'ein Rezept'}.`
    },

    // Erze/Essen im Ofen schmelzen und das Ergebnis abholen
    async schmelzen (a) {
      const eingabe = hat(a.item) ?? items().find(i => /^raw_|_ore$|^(beef|porkchop|chicken|mutton|rabbit|cod|salmon|potato|kelp|sand|cobblestone|clay_ball)$/.test(i.name))
      if (!eingabe) return 'Ich habe nichts zum Schmelzen.'
      let ofen = naechsterBlock(['furnace', 'blast_furnace', 'smoker'].map(n => mcData.blocksByName[n]?.id).filter(Boolean), 32)
      if (!ofen) ofen = await hinstellen('furnace')
      if (!ofen) return 'Kein Ofen in der Naehe und keiner im Inventar.'
      await hingehen(ofen.position, 2)
      const f = await bot.openFurnace(ofen)
      try {
        const n = Math.min(eingabe.count, a.menge === UNENDLICH ? 64 : a.menge)
        if (!f.fuelItem()) {
          const brenn = items().find(i => BRENNSTOFF.includes(i.name)) ?? items().find(i => BRENNSTOFF_HOLZ(i.name))
          if (!brenn) return 'Kein Brennstoff (Kohle oder Holz) im Inventar.'
          await f.putFuel(brenn.type, null, Math.min(brenn.count, Math.ceil(n / (BRENNSTOFF.includes(brenn.name) ? 8 : 1.5))))
        }
        await f.putInput(eingabe.type, null, n)
        let fertig = 0
        const ende = Date.now() + n * 11000 + 15000
        while (Date.now() < ende) {
          pruefen()
          await warte(2000)
          if (f.outputItem()) { fertig += f.outputItem().count; await f.takeOutput() }
          if (!f.inputItem() && !f.outputItem()) break
        }
        return `${fertig}x ${itemName(eingabe.type)} geschmolzen.`
      } finally {
        f.close()
      }
    },

    // Mobs einer Art jagen und die Drops aufheben
    async jagen (a) {
      let erledigt = 0
      while (erledigt < a.menge) {
        pruefen()
        const ziel = bot.nearestEntity(e => e.name === a.mob && e.position.distanceTo(bot.entity.position) < 48)
        if (!ziel) return erledigt ? `${erledigt}x ${a.mobName} erledigt, keine mehr in der Naehe.` : `Kein ${a.mobName} in der Naehe.`
        await ausruestenWaffe()
        bot.pvp.attack(ziel)
        await new Promise(resolve => {
          const fertig = () => { clearInterval(t); bot.removeListener('stoppedAttacking', fertig); resolve() }
          const t = setInterval(() => { if (abbruch || !bot.entities[ziel.id]) { bot.pvp.stop(); fertig() } }, 250)
          bot.once('stoppedAttacking', fertig)
        })
        pruefen()
        if (!bot.entities[ziel.id]) erledigt++
        await warte(500)
        await dropsAufheben()
      }
      return `${erledigt}x ${a.mobName} erledigt.`
    },

    // Reife Felder ernten und neu bepflanzen, bei "ohne Ende" immer wieder
    async farmen (a) {
      let geerntet = 0
      do {
        pruefen()
        const reif = bot.findBlocks({
          matching: b => PFLANZEN[b.name] && b.getProperties().age >= PFLANZEN[b.name].reif,
          maxDistance: 24,
          count: 64
        })
        for (const pos of reif) {
          pruefen()
          const b = bot.blockAt(pos)
          const art = b.name
          await hingehen(pos, 2)
          await bot.dig(b, true)
          geerntet++
          const saat = hat(PFLANZEN[art].saat)
          const boden = bot.blockAt(pos.offset(0, -1, 0))
          if (saat && boden && ['farmland', 'soul_sand'].includes(boden.name)) {
            await bot.equip(saat, 'hand')
            await bot.placeBlock(boden, new Vec3(0, 1, 0)).catch(() => {})
          }
        }
        await dropsAufheben(12)
        if (a.menge === UNENDLICH) await warte(20000)
      } while (a.menge === UNENDLICH)
      return geerntet ? `${geerntet} Pflanzen geerntet und neu gepflanzt.` : 'Nichts Reifes in der Naehe.'
    },

    async schlafen () {
      const bett = naechsterBlock(mcData.blocksArray.filter(b => b.name.endsWith('_bed')).map(b => b.id), 32)
      if (!bett) return 'Kein Bett in der Naehe.'
      await hingehen(bett.position, 1)
      await bot.sleep(bett)
      await new Promise(resolve => {
        const t = setInterval(() => { if (abbruch || !bot.isSleeping) { clearInterval(t); resolve() } }, 250)
      })
      if (abbruch && bot.isSleeping) await bot.wake().catch(() => {})
      pruefen()
      return 'Guten Morgen!'
    },

    // Items dem Besitzer bringen
    async geben (a) {
      let besitzer = bot.players[a.an]?.entity
      const pos = besitzer?.position ?? a.posFn?.()
      if (!pos) return 'Ich sehe dich nicht.'
      if (!besitzer) await bot.pathfinder.goto(new goals.GoalNear(pos.x, pos.y, pos.z, 4))
      besitzer = bot.players[a.an]?.entity
      if (!besitzer) return 'Ich finde dich nicht.'
      // hoechstens 15 s laufen, dann aufgeben (sonst haengt die Aufgabe, wenn der Weg nicht aufgeht)
      const limit = setTimeout(() => bot.pathfinder.setGoal(null), 15000)
      await bot.pathfinder.goto(new goals.GoalFollow(besitzer, 2)).catch(() => {})
      clearTimeout(limit)
      pruefen()
      // Nicht von unten/weit weg werfen - das Item faellt sonst irgendwohin, wo du es nicht findest
      besitzer = bot.players[a.an]?.entity
      if (!besitzer) return 'Ich finde dich nicht.'
      // Auf den Block werfen, auf dem du stehst (Wurfbahn berechnet, nicht "durch dich durch"); danach
      // zuruecktreten, sonst hebt der Bot es nach der Aufhebe-Sperre (2 s) selbst wieder auf
      const wurf = wurfZielen(besitzer)
      if (wurf.fehler > 0.35) return 'Ich komme nicht an dich ran (kein sicherer Wurf auf deinen Block) - ich behalte es.'
      await new Promise(resolve => setTimeout(resolve, 150)) // Blickrichtung beim Server ankommen lassen
      zuruecktreten = true
      lootPause() // das Geworfene nicht gleich selbst wieder aufheben
      if (a.slot != null) return slotGeben(a)
      // Je Item-Art die Reserve abziehen - auch bei "alles" behaelt er seine 2 Totems
      let n = 0
      const rest = new Map()
      for (const i of items().filter(i => !a.item || i.name === a.item)) rest.set(i.name, (rest.get(i.name) ?? 0) + i.count)
      for (const name of rest.keys()) rest.set(name, rest.get(name) - (a.item ? (a.reserve ?? RESERVE[name] ?? 0) : (RESERVE[name] ?? 0)))
      for (const i of items().filter(i => !a.item || i.name === a.item)) {
        const menge = Math.min(i.count, rest.get(i.name), a.menge === UNENDLICH ? i.count : a.menge - n)
        if (a.menge !== UNENDLICH && n >= a.menge) break
        if (menge <= 0) continue
        rest.set(i.name, rest.get(i.name) - menge)
        await bot.toss(i.type, null, menge)
        n += menge
      }
      await wegTreten()
      return n ? `${n} Items abgeworfen.` : 'Davon habe ich nichts.'
    },

    // Tunnel (Standard 1x2) in Blickrichtung des Besitzers (a.yaw) bzw. des Bots, Fackeln alle 8 Bloecke
    async tunnel (a) {
      const dir = blickRichtung(a.yaw)
      const quer = new Vec3(-dir.z, 0, dir.x)
      const breite = a.breite ?? 1
      const hoehe = a.hoehe ?? 2
      const start = bot.entity.position.floored()
      let i = 0
      for (i = 1; i <= a.menge; i++) {
        pruefen()
        const p = start.plus(dir.scaled(i))
        for (let q = 0; q < breite; q++) {
          for (let h = hoehe - 1; h >= 0; h--) await graben(p.plus(quer.scaled(q - Math.floor((breite - 1) / 2))).offset(0, h, 0))
        }
        if (bot.blockAt(p.offset(0, -1, 0))?.boundingBox !== 'block') await brueckeLegen(p.offset(0, -1, 0))
        await bot.pathfinder.goto(new goals.GoalBlock(p.x, p.y, p.z))
        if (i % 8 === 0) await fackelSetzen(p).catch(() => {})
      }
      await dropsAufheben()
      return `Tunnel ${i - 1} Bloecke lang gegraben.`
    },

    // Treppe schraeg nach unten bis zur Zielhoehe
    async treppe (a) {
      const dir = blickRichtung(a.yaw)
      let p = bot.entity.position.floored()
      while (p.y > a.zielY) {
        pruefen()
        const n = p.plus(dir).offset(0, -1, 0)
        await graben(n.offset(0, 2, 0))
        await graben(n.offset(0, 1, 0))
        await graben(n)
        await bot.pathfinder.goto(new goals.GoalBlock(n.x, n.y, n.z))
        p = n
        if (p.y % 8 === 0) await fackelSetzen(p).catch(() => {})
      }
      await dropsAufheben()
      return `Treppe bis Hoehe ${p.y} gegraben.`
    },

    // Saeule unter sich hochbauen
    async saeule (a) {
      const block = bauBlock()
      if (!block) return 'Ich habe keine Bloecke zum Bauen.'
      const startY = Math.floor(bot.entity.position.y)
      let versuche = 0
      while (Math.floor(bot.entity.position.y) < startY + a.menge) {
        pruefen()
        const vorher = Math.floor(bot.entity.position.y)
        const b = bauBlock()
        if (!b) return 'Bloecke sind alle.'
        await bot.equip(b, 'hand')
        await bot.look(bot.entity.yaw, -Math.PI / 2, true)
        const unten = bot.blockAt(bot.entity.position.offset(0, -1, 0))
        bot.setControlState('jump', true)
        await warte(350)
        await bot.placeBlock(unten, new Vec3(0, 1, 0)).catch(() => {})
        bot.setControlState('jump', false)
        await warte(250)
        if (Math.floor(bot.entity.position.y) > vorher) versuche = 0
        else if (++versuche >= 5) return `Komme nicht hoeher (${Math.floor(bot.entity.position.y) - startY} Bloecke gebaut).`
      }
      return `Saeule ${a.menge} hoch gebaut.`
    },

    // Zwei Tiere einer Art fuettern, damit sie ein Junges bekommen
    async zuechten (a) {
      const futter = (FUTTER[a.mob] ?? []).map(hat).find(Boolean)
      if (!futter) return `Ich brauche Futter fuer ${a.mobName}: ${(FUTTER[a.mob] ?? ['?']).join(' oder ')}.`
      const tiere = Object.values(bot.entities)
        .filter(e => e.name === a.mob && e.position.distanceTo(bot.entity.position) < 32)
        .sort((x, y) => x.position.distanceTo(bot.entity.position) - y.position.distanceTo(bot.entity.position))
        .slice(0, a.menge === UNENDLICH ? 20 : Math.max(2, a.menge))
      if (tiere.length < 2) return `Ich finde keine zwei ${a.mobName} in der Naehe.`
      for (const t of tiere) {
        pruefen()
        await bot.pathfinder.goto(new goals.GoalFollow(t, 2))
        await bot.equip(hat(futter.name) ?? futter, 'hand')
        await bot.activateEntity(t)
        await warte(300)
      }
      return `${tiere.length}x ${a.mobName} gefuettert.`
    },

    async scheren (a) {
      if (!hat('shears')) return 'Ich habe keine Schere.'
      let n = 0
      while (n < a.menge) {
        pruefen()
        const schaf = bot.nearestEntity(e => e.name === 'sheep' && !(e.metadata?.[17] & 0x10) && e.position.distanceTo(bot.entity.position) < 32 && !a.geschoren?.has(e.id))
        if (!schaf) break
        ;(a.geschoren ??= new Set()).add(schaf.id)
        await bot.pathfinder.goto(new goals.GoalFollow(schaf, 2))
        await bot.equip(hat('shears'), 'hand')
        await bot.activateEntity(schaf)
        n++
        await warte(300)
      }
      await dropsAufheben()
      return n ? `${n} Schafe geschoren.` : 'Keine Schafe zum Scheren in der Naehe.'
    },

    async angeln (a) {
      const rute = hat('fishing_rod')
      if (!rute) return 'Ich habe keine Angel.'
      const wasser = naechsterBlock(mcData.blocksByName.water.id, 16)
      if (!wasser) return 'Kein Wasser in der Naehe.'
      await hingehen(wasser.position, 3)
      let n = 0
      while (n < a.menge) {
        pruefen()
        await bot.equip(hat('fishing_rod'), 'hand')
        await bot.lookAt(wasser.position.offset(0.5, 0.5, 0.5))
        try { await bot.fish(); n++ } catch (e) { if (!hat('fishing_rod')) return `Angel kaputt nach ${n} Fischen.`; log('Angeln:', e.message) }
      }
      return `${n}x geangelt.`
    },

    async ausruesten () {
      const n = await ruestungAnlegen()
      return n ? `${n} Ruestungsteile angezogen.` : 'Ich trage schon die beste Ruestung, die ich habe.'
    }
  }

  // ---------------- Hilfen ----------------

  const anzahlId = id => items().filter(i => i.type === id).reduce((s, i) => s + i.count, 0)
  const brauchtTisch = id => !bot.recipesAll(id, null, null).length && bot.recipesAll(id, null, true).length > 0

  // Werkbank in der Naehe, sonst aus dem Inventar hinstellen, sonst bauen und hinstellen
  async function werkbank (tiefe) {
    const da = naechsterBlock(mcData.blocksByName.crafting_table.id, 16)
    if (da) return da
    if (!hat('crafting_table')) await herstellen(mcData.itemsByName.crafting_table.id, 1, tiefe + 1)
    return hinstellen('crafting_table')
  }

  // Stellt `menge` Stueck her und gibt zurueck, wie viele es wurden.
  // Fehlen Zutaten, die sich selbst herstellen lassen, werden die zuerst gebaut (max. 3 Ebenen tief).
  async function herstellen (id, menge, tiefe = 0) {
    let gemacht = 0
    let zwischenVersucht = false
    while (gemacht < menge) {
      pruefen()
      const tisch = brauchtTisch(id) ? await werkbank(tiefe) : null
      if (brauchtTisch(id) && !tisch) return gemacht
      const rezept = bot.recipesFor(id, null, 1, tisch)[0]
      if (!rezept) {
        if (tiefe >= 3 || zwischenVersucht) return gemacht
        zwischenVersucht = true
        const rest = menge - gemacht
        for (const variante of bot.recipesAll(id, null, true)) {
          const mal = Math.ceil(rest / variante.result.count)
          const fehlend = variante.delta.filter(d => d.count < 0)
            .map(d => ({ id: d.id, n: -d.count * mal - anzahlId(d.id) })).filter(f => f.n > 0)
          if (!fehlend.every(f => f.id !== id && bot.recipesAll(f.id, null, true).length)) continue
          let ok = true
          for (const f of fehlend) if (await herstellen(f.id, f.n, tiefe + 1) < f.n) { ok = false; break }
          if (ok) break
        }
        continue
      }
      if (tisch) await hingehen(tisch.position, 3)
      const mal = Math.max(1, Math.min(64, Math.ceil((menge - gemacht) / rezept.result.count)))
      const moeglich = bot.recipesFor(id, null, mal * rezept.result.count, tisch).length ? mal : 1
      await bot.craft(rezept, moeglich, tisch ?? undefined)
      gemacht += moeglich * rezept.result.count
      log(`Hergestellt: ${moeglich * rezept.result.count}x ${itemName(id)}`)
    }
    return gemacht
  }

  function fehlendeZutaten (id) {
    const r = bot.recipesAll(id, null, true)[0]
    if (!r) return null
    return r.delta.filter(d => d.count < 0)
      .map(d => ({ name: itemName(d.id), fehlt: -d.count - items().filter(i => i.type === d.id).reduce((s, i) => s + i.count, 0) }))
      .filter(z => z.fehlt > 0)
      .map(z => `${z.fehlt}x ${z.name}`).join(', ')
  }

  function truheMerken (truhe) {
    const inhalt = {}
    for (const i of truhe.containerItems()) inhalt[i.name] = (inhalt[i.name] ?? 0) + i.count
    ort.truheInhalt = inhalt
    speichereOrt?.()
  }

  async function setzlingPflanzen (stammPos) {
    const setzling = items().find(i => i.name.endsWith('_sapling'))
    const boden = bot.blockAt(stammPos.offset(0, -1, 0))
    if (!setzling || !['dirt', 'grass_block', 'podzol', 'coarse_dirt', 'rooted_dirt', 'moss_block'].includes(boden?.name)) return
    if (bot.blockAt(stammPos)?.name !== 'air') return
    await bot.equip(setzling, 'hand')
    await bot.placeBlock(boden, new Vec3(0, 1, 0))
  }

  function bauBlock () {
    return items().find(i => ['cobblestone', 'dirt', 'cobbled_deepslate', 'netherrack', 'stone', 'andesite', 'diorite', 'granite'].includes(i.name))
  }

  async function brueckeLegen (pos) {
    const b = bauBlock()
    if (!b) throw new Error('Loch im Boden und keine Bloecke zum Fuellen')
    await bot.equip(b, 'hand')
    const nachbar = [[0, -1, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1]]
      .map(o => [bot.blockAt(pos.offset(...o)), new Vec3(-o[0], -o[1], -o[2])]).find(([bl]) => bl?.boundingBox === 'block')
    if (nachbar) await bot.placeBlock(nachbar[0], nachbar[1])
  }

  async function fackelSetzen (pos) {
    const fackel = hat('torch')
    const boden = bot.blockAt(pos.offset(0, -1, 0))
    if (!fackel || boden?.boundingBox !== 'block') return
    await bot.equip(fackel, 'hand')
    await bot.placeBlock(boden, new Vec3(0, 1, 0))
  }

  async function ausruestenWaffe () {
    const waffen = items().filter(i => /sword|_axe/.test(i.name))
    if (!waffen.length) return
    const rang = n => ['netherite', 'diamond', 'iron', 'stone', 'golden', 'wooden'].findIndex(m => n.startsWith(m))
    waffen.sort((x, y) => rang(x.name) - rang(y.name) || (y.name.includes('sword') - x.name.includes('sword')))
    if (bot.heldItem?.name !== waffen[0].name) await bot.equip(waffen[0], 'hand')
  }

  async function ruestungAnlegen () {
    const rang = n => ['leather', 'golden', 'chainmail', 'iron', 'diamond', 'netherite'].findIndex(m => n.startsWith(m))
    const slots = { helmet: 'head', chestplate: 'torso', leggings: 'legs', boots: 'feet' }
    let n = 0
    for (const [teil, slot] of Object.entries(slots)) {
      const bestes = items().filter(i => i.name.endsWith('_' + teil)).sort((x, y) => rang(y.name) - rang(x.name))[0]
      if (!bestes) continue
      const aktuellesTeil = bot.inventory.slots[bot.getEquipmentDestSlot(slot)]
      if (aktuellesTeil && rang(aktuellesTeil.name) >= rang(bestes.name)) continue
      await bot.equip(bestes, slot)
      n++
    }
    return n
  }

  // ---------------- Ablauf ----------------

  function fertig (a, text) {
    if (aktuell !== a) return
    aktuell = null
    fluestern(text)
    log(`Aufgabe fertig: ${text}`)
    const naechste = warteschlange.shift()
    if (naechste) { aktuell = { ...naechste, gesammelt: 0 }; setImmediate(weiter) } else beiFertig?.()
  }

  async function weiter () {
    const a = aktuell
    if (!a || laeuft) return
    a.pausiert = false
    a.manuell = false
    abbruch = false
    laeuft = true
    bot.collectBlock.movements = bewegungArbeit
    bot.pathfinder.setMovements(bewegungArbeit)
    try {
      const text = await ARTEN[a.art](a)
      if (!abbruch) fertig(a, text)
    } catch (e) {
      if (!abbruch && !e.abbruch) fertig(a, `${beschreibung(a)} abgebrochen: ${e.message}`)
    } finally {
      laeuft = false
      bot.clearControlStates()
      bot.pathfinder.setMovements(bewegungNormal)
      // Wurde waehrenddessen eine neue Aufgabe gestartet, jetzt loslegen
      if (aktuell && aktuell !== a && !aktuell.pausiert) weiter()
    }
  }

  async function anhalten () {
    abbruch = true
    await bot.collectBlock.cancelTask().catch(() => {})
    bot.pvp.stop()
    bot.pathfinder.setGoal(null)
    bot.clearControlStates()
  }

  function beschreibung (a = aktuell) {
    if (!a) return 'keine'
    const zaehler = a.menge != null && a.art !== 'treppe' ? ` ${a.gesammelt ?? 0}/${mengeText(a.menge)}` : ''
    return `${a.art}${a.name || a.mobName || a.item ? ' ' + (a.name ?? a.mobName ?? a.item) : ''}${zaehler}`
  }

  return {
    ARTEN: Object.keys(ARTEN),
    starten (auftrag, anhaengen = false) {
      if (anhaengen && aktuell) { warteschlange.push(auftrag); return }
      warteschlange.length = 0
      const a = { ...auftrag, gesammelt: 0 }
      anhalten().then(() => { aktuell = a; weiter() })
    },
    // Fuer einen Kampf unterbrechen, danach mit weiter() fortsetzen
    // manuell (Baritone "pause"): nicht nach dem Kampf von selbst weitermachen, nur mit weiter()
    async pausieren (manuell = false) {
      if (!aktuell) return
      if (manuell) aktuell.manuell = true
      if (aktuell.pausiert) return
      aktuell.pausiert = true
      await anhalten()
    },
    async stoppen () {
      aktuell = null
      warteschlange.length = 0
      await anhalten()
    },
    weiter,
    laeuft: () => laeuft,
    pausiert: () => !!aktuell?.pausiert && !aktuell.manuell && !laeuft,
    angehalten: () => !!aktuell?.pausiert && !laeuft,
    aktuell: () => aktuell,
    beschreibung: () => beschreibung() + (warteschlange.length ? ` (+${warteschlange.length} danach)` : ''),
    blockIdsGruppe (rohstoff) { return mcData.blocksArray.filter(b => passt(ROHSTOFFE[rohstoff].bloecke, b.name)).map(b => b.id) },
    vorrat (ids, radius = 32) {
      const n = ids.length ? bot.findBlocks({ matching: ids, maxDistance: radius, count: 64 }).length : 0
      return { n, abbaubar: ids.some(kannAbbauen) }
    },
    anzahlItem,
    behalten: item => behalten(item, mcData),
    ruestungAnlegen,
    FUTTER
  }
}

// Mengen aus Freitext ("20 eisen", "zwei stacks holz"); Jev waehlt nur, Zahlen liest der Code
const ZAHLWOERTER = { zwei: 2, drei: 3, vier: 4, fuenf: 5, 'fünf': 5, sechs: 6, sieben: 7, acht: 8, neun: 9, zehn: 10, elf: 11, zwoelf: 12, 'zwölf': 12, zwanzig: 20, dreissig: 30, 'dreißig': 30, vierzig: 40, fuenfzig: 50, 'fünfzig': 50, hundert: 100, tausend: 1000 }
function mengeLesen (text) {
  const t = text.toLowerCase()
  const zahl = t.replace(/-?\d+[\s,]+-?\d+([\s,]+-?\d+)?/g, '').match(/\d+/)?.[0] // Koordinaten sind keine Menge
  const wort = t.split(/[^a-zäöüß]+/).find(w => ZAHLWOERTER[w])
  let n = zahl ? parseInt(zahl, 10) : wort ? ZAHLWOERTER[wort] : null
  if (/stack|stapel/.test(t)) n = (n ?? 1) * 64
  return n && n > 0 ? n : null
}

// "geh zu 100 64 -200" / "geh zu 100 -200"
function koordinatenLesen (text) {
  const m = text.match(/(-?\d+)[\s,]+(-?\d+)(?:[\s,]+(-?\d+))?/)
  if (!m) return null
  return m[3] != null ? { x: +m[1], y: +m[2], z: +m[3] } : { x: +m[1], z: +m[2] }
}

module.exports = { ROHSTOFFE, FUTTER, PFLANZEN, UNENDLICH, RESERVE, erstelleAufgaben, mengeLesen, koordinatenLesen }
