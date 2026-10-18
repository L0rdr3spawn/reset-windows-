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
  return /sword|axe|pickaxe|shovel|hoe|helmet|chestplate|leggings|boots|shield|bow|trident|shears|fishing_rod|torch/.test(item.name) ||
    !!mcData.foodsByName[item.name]
}

function erstelleAufgaben (bot, mcData, { log, fluestern, bewegungNormal, bewegungArbeit, ort, speichereOrt, beiFertig }) {
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

  function blickRichtung () {
    // Yaw 0 = Norden (-z) in mineflayer
    const yaw = bot.entity.yaw
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
          continue
        }
        const abbaubar = ids.filter(kannAbbauen)
        if (abbaubar.length === 0) return `Ich brauche ein besseres Werkzeug fuer ${a.name}.`
        const pos = bot.findBlocks({ matching: abbaubar, maxDistance: SUCHRADIUS, count: 32 }).find(p => !gesperrt.has(p.toString()))
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
      // Ohne Abbruch-Pruefung haengt die Aufgabe bei !stop im Bett fest (laeuft bleibt true, nichts geht mehr)
      await new Promise(resolve => {
        const ende = () => { clearInterval(t); bot.removeListener('wake', ende); resolve() }
        const t = setInterval(() => { if (abbruch || !bot.isSleeping) { if (bot.isSleeping) bot.wake().catch(() => {}); ende() } }, 500)
        bot.once('wake', ende)
      })
      pruefen()
      return 'Guten Morgen!'
    },

    // Items dem Besitzer bringen
    async geben (a) {
      const besitzer = bot.players[a.an]?.entity
      if (!besitzer) return 'Ich sehe dich nicht.'
      await bot.pathfinder.goto(new goals.GoalFollow(besitzer, 2))
      await bot.lookAt(besitzer.position.offset(0, 1.6, 0))
      let n = 0
      for (const i of items().filter(i => !a.item || i.name === a.item)) {
        const menge = Math.min(i.count, a.menge === UNENDLICH ? i.count : a.menge - n)
        if (menge <= 0) break
        await bot.toss(i.type, null, menge)
        n += menge
      }
      return n ? `${n} Items abgeworfen.` : 'Davon habe ich nichts.'
    },

    // 1x2-Tunnel in Blickrichtung, Fackeln alle 8 Bloecke
    async tunnel (a) {
      const dir = blickRichtung()
      const start = bot.entity.position.floored()
      let i = 0
      for (i = 1; i <= a.menge; i++) {
        pruefen()
        const p = start.plus(dir.scaled(i))
        await graben(p.offset(0, 1, 0))
        await graben(p)
        if (bot.blockAt(p.offset(0, -1, 0))?.boundingBox !== 'block') await brueckeLegen(p.offset(0, -1, 0))
        await bot.pathfinder.goto(new goals.GoalBlock(p.x, p.y, p.z))
        if (i % 8 === 0) await fackelSetzen(p).catch(() => {})
      }
      await dropsAufheben()
      return `Tunnel ${i - 1} Bloecke lang gegraben.`
    },

    // Treppe schraeg nach unten bis zur Zielhoehe
    async treppe (a) {
      const dir = blickRichtung()
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
      while (Math.floor(bot.entity.position.y) < startY + a.menge) {
        pruefen()
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
    async pausieren () {
      if (!aktuell || aktuell.pausiert) return
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
    pausiert: () => !!aktuell?.pausiert && !laeuft,
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

module.exports = { ROHSTOFFE, FUTTER, PFLANZEN, UNENDLICH, erstelleAufgaben, mengeLesen, koordinatenLesen }
