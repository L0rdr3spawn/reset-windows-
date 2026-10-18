const fs = require('fs')
const path = require('path')
const mineflayer = require('mineflayer')
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder')
const { plugin: pvp } = require('mineflayer-pvp')
const { plugin: collectBlock } = require('mineflayer-collectblock')
const { ROHSTOFFE, FUTTER, PFLANZEN, UNENDLICH, erstelleAufgaben, mengeLesen, koordinatenLesen } = require('./aufgaben')
const jev = require('./jev')

// node bot.js [config-datei], z.B. config-test.json fuer den lokalen Testserver
const CFG_DATEI = process.argv[2] ?? 'config.json'
const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, CFG_DATEI), 'utf8'))
const offline = cfg.auth === 'offline'

// Zuhause und Truhe, gesetzt mit !heim, ueberleben einen Neustart (je Server eigene Datei)
const ORT_DATEI = path.join(__dirname, CFG_DATEI === 'config.json' ? 'ort.json' : `ort-${path.basename(CFG_DATEI, '.json')}.json`)
const ort = fs.existsSync(ORT_DATEI) ? JSON.parse(fs.readFileSync(ORT_DATEI, 'utf8')) : {}

// Laufzeit-Zustand, ueberlebt einen Reconnect
const zustand = {
  modus: 'folgen', // 'folgen' | 'stehen' | 'selbst'
  kampf: true,
  loot: true
}

let bot = null
let mcData = null
let aufgaben = null
let tickTimer = null

function log (...args) {
  const t = new Date().toLocaleTimeString('de-DE')
  console.log(`[${t}]`, ...args)
}

function starten () {
  log(`Verbinde zu ${cfg.host}:${cfg.port} als Protokoll ${cfg.version} ...`)

  bot = mineflayer.createBot({
    host: cfg.host,
    port: cfg.port,
    username: offline ? cfg.botName : cfg.botEmail,
    auth: offline ? 'offline' : 'microsoft',
    version: cfg.version,
    profilesFolder: path.join(__dirname, '.auth'),
    onMsaCode (data) {
      console.log('\n=============================================')
      console.log(' MICROSOFT-LOGIN FUER DEN ZWEITACCOUNT')
      console.log(' Seite oeffnen:', data.verification_uri)
      console.log(' Code eingeben:', data.user_code)
      console.log(' (Nur einmal noetig, danach liegt das Token in .auth/)')
      console.log('=============================================\n')
    }
  })

  bot.loadPlugin(pathfinder)
  bot.loadPlugin(pvp)
  bot.loadPlugin(collectBlock)

  bot.once('spawn', () => {
    mcData = require('minecraft-data')(bot.version)

    const bewegungNormal = new Movements(bot)
    bewegungNormal.allowSprinting = true
    bewegungNormal.canDig = false // beim Folgen nicht durch die Welt graben
    bewegungNormal.allow1by1towers = false // keine Cobble-Tuerme bauen
    bot.pathfinder.setMovements(bewegungNormal)

    // Bei Aufgaben darf er graben und sich aus Loechern hochbauen
    const bewegungArbeit = new Movements(bot)
    bewegungArbeit.allowSprinting = true

    entsperrenEinrichten([bewegungNormal, bewegungArbeit])

    aufgaben = erstelleAufgaben(bot, mcData, {
      log,
      fluestern,
      bewegungNormal,
      bewegungArbeit,
      ort,
      speichereOrt,
      beiFertig: () => { naechsteEntscheidung = Date.now() + 3000 }
    })

    log(`Eingeloggt als ${bot.username}. Besitzer: ${cfg.besitzer}`)
    fluestern('Bot ist da. !hilfe fuer Befehle' + (jev.aktiv ? ' - oder sag es einfach normal.' : '.'))
    if (!jev.aktiv) log('Kein TYPESAFE_API_KEY gesetzt: nur !-Befehle aktiv, kein selbststaendiger Modus.')

    if (tickTimer) clearInterval(tickTimer)
    tickTimer = setInterval(tick, 500)
  })

  bot.on('chat', (username, message) => {
    if (username !== cfg.besitzer) return
    nachricht(message.trim(), false)
  })

  bot.on('whisper', (username, message) => {
    if (username !== cfg.besitzer) return
    nachricht(message.trim(), true)
  })

  // Spieler gelten nur als Angreifer, wenn sie gerade zugeschlagen haben (sonst reicht Fallschaden)
  bot.on('entitySwingArm', (entity) => { letzterSchlag.set(entity.id, Date.now()) })

  // Wer den Besitzer schlaegt, kriegt Aerger
  bot.on('entityHurt', (entity) => {
    if (!zustand.kampf || !mcData) return
    const besitzer = bot.players[cfg.besitzer]?.entity
    if (!besitzer || entity.id !== besitzer.id) return
    const angreifer = naechsterAngreifer(besitzer)
    if (angreifer && !bot.pvp.target) {
      log(`${cfg.besitzer} wurde getroffen -> greife ${angreifer.username || angreifer.name} an`)
      kampfBeginnen(angreifer)
    }
  })

  bot.on('death', () => {
    log('Bot ist gestorben.')
    fluestern('Ich bin gestorben, respawne.')
    aufgaben?.stoppen()
  })

  bot.on('kicked', (grund) => log('Gekickt:', typeof grund === 'string' ? grund : JSON.stringify(grund)))
  bot.on('error', (err) => log('Fehler:', err.message))

  bot.on('end', (grund) => {
    if (tickTimer) clearInterval(tickTimer)
    aufgaben = null
    log(`Verbindung beendet (${grund}). Neuer Versuch in ${cfg.reconnectSekunden}s.`)
    setTimeout(starten, cfg.reconnectSekunden * 1000)
  })
}

function fluestern (text) {
  // Chatnachrichten sind auf 256 Zeichen begrenzt
  const max = 240 - cfg.besitzer.length
  for (let i = 0; i < text.length; i += max) bot.chat(`/msg ${cfg.besitzer} ${text.slice(i, i + max)}`)
}

// Der Pathfinder plant manchmal Spruenge (v.a. diagonal hoch auf Schnee/Eis), prueft sie mit einer zu
// grosszuegigen Simulation ("erreicht", sobald weniger als 1 Block darunter), laeuft dann ohne zu springen
// gegen die Kante und plant nach 3,5 s "stuck" denselben Weg wieder - endlos. Abhilfe:
// 1. Fehlschlag an einem Wegpunkt: selbst hinspringen (unsere Tasten ueberschreiben die des Pathfinders)
// 2. Fehlschlag am selben Punkt: Punkt fuer die Wegplanung teuer machen, damit er einen anderen Weg nimmt
function entsperrenEinrichten (bewegungen) {
  let pfad = []
  let sprungZiel = null
  let sprungTicks = 0
  const fehlschlaege = new Map()
  const schluessel = p => `${Math.floor(p.x)},${Math.floor(p.y)},${Math.floor(p.z)}`
  bot.on('path_update', r => { pfad = r.path })
  bot.on('path_reset', grund => {
    if (grund !== 'stuck' || !pfad.length) return
    const ziel = pfad[0]
    const key = schluessel(ziel)
    const n = (fehlschlaege.get(key) ?? 0) + 1
    fehlschlaege.set(key, n)
    if (n <= 2) {
      log(`Haenge vor ${key}, springe selbst hin (Versuch ${n}).`)
      sprungZiel = ziel
      sprungTicks = 14
    } else if (n === 3) {
      log(`Komme nicht auf ${key}, plane drumherum.`)
      const [x, y, z] = key.split(',').map(Number)
      const meiden = b => (b.position.x === x && b.position.z === z && (b.position.y === y || b.position.y === y + 1)) ? 100 : 0
      for (const m of bewegungen) {
        m.exclusionAreasStep.push(meiden)
        if (m.exclusionAreasStep.length > 40) m.exclusionAreasStep.shift()
      }
    }
    if (fehlschlaege.size > 200) fehlschlaege.clear()
  })
  // Nach dem Pathfinder registriert, deshalb gewinnen diese Tasten im selben Tick
  bot.on('physicsTick', () => {
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
  // Waehrend Aufgaben darf er sich zur Not freigraben
  bot.on('path_reset', async grund => {
    if (grund !== 'stuck' || !aufgaben?.laeuft() || !pfad.length) return
    const n = fehlschlaege.get(schluessel(pfad[0])) ?? 0
    if (n < 2) return
    const kopf = bot.blockAt(bot.entity.position.floored().offset(0, 2, 0))
    if (kopf && kopf.boundingBox === 'block' && bot.canDigBlock(kopf) && !['lava', 'water'].includes(bot.blockAt(kopf.position.offset(0, 1, 0))?.name)) {
      await bot.dig(kopf, true).catch(() => {})
    }
  })
}

const BEFEHLE = ['!folge', '!komm', '!stop', '!bleib', '!selbst', '!sammel', '!heim', '!nachhause', '!lager',
  '!kampf', '!loot', '!gib', '!status', '!hilfe', '!was']

function nachricht (text, gefluestert) {
  if (!text || !aufgaben) return
  log(`${gefluestert ? 'Gefluestert' : 'Chat'} von ${cfg.besitzer}: ${text}`)
  if (BEFEHLE.includes(text.toLowerCase().split(/\s+/)[0])) return befehl(text.toLowerCase())
  // Unbekannte !-Befehle ("!get wood") versteht Jev wie normalen Text
  const frei = text.replace(/^!+/, '').trim()
  if (jev.aktiv) freieSprache(frei, gefluestert || text.startsWith('!'))
  else if (text.startsWith('!')) befehl('!hilfe')
}

// ---------- Kandidaten fuer Jev: der Code sagt, was es gibt, Jev waehlt ----------

const WICHTIGE_ITEMS = ['crafting_table', 'stick', 'torch', 'chest', 'furnace', 'ladder', 'bucket', 'shears', 'shield',
  'bread', 'white_bed', 'fishing_rod', 'bow', 'arrow', 'iron_ingot', 'gold_ingot', 'iron_block', 'boat', 'oak_boat',
  ...['wooden', 'stone', 'iron', 'golden', 'diamond'].flatMap(m => ['pickaxe', 'axe', 'shovel', 'sword', 'hoe'].map(w => `${m}_${w}`)),
  ...['iron', 'diamond'].flatMap(m => ['helmet', 'chestplate', 'leggings', 'boots'].map(w => `${m}_${w}`))]

function kandidatenSammeln () {
  const bloecke = {}
  for (const [k, r] of Object.entries(ROHSTOFFE)) bloecke[`gruppe:${k}`] = r.name
  // Alle Blocksorten in der Naehe, damit "bau das Glas ab" oder "hol Kuerbisse" auch geht
  const gesehen = new Map()
  for (const p of bot.findBlocks({ matching: b => b.name !== 'air' && b.name !== 'cave_air' && b.name !== 'water' && b.name !== 'lava' && b.name !== 'bedrock', maxDistance: 24, count: 4000 })) {
    const b = bot.blockAt(p)
    if (b) gesehen.set(b.name, (gesehen.get(b.name) ?? 0) + 1)
  }
  for (const [name, n] of [...gesehen].sort((a, b) => b[1] - a[1]).slice(0, 60)) {
    bloecke[`block:${name}`] = `${mcData.blocksByName[name].displayName} (${n}x in der Naehe)`
  }

  // Herstellbar: was jetzt geht (mit Werkbank) plus die wichtigsten Items
  const items = {}
  const namen = new Set(WICHTIGE_ITEMS.filter(n => mcData.itemsByName[n]))
  for (const it of mcData.itemsArray) {
    if (namen.size >= 90) break
    if (bot.recipesFor(it.id, null, 1, true).length) namen.add(it.name)
  }
  for (const n of namen) items[`item:${n}`] = mcData.itemsByName[n].displayName + (bot.recipesFor(mcData.itemsByName[n].id, null, 1, true).length ? ' (Material reicht)' : '')

  const mobs = {}
  for (const e of Object.values(bot.entities)) {
    if (!e.position || e === bot.entity || e.type === 'player' || e.name === 'item' || e.name === 'experience_orb') continue
    if (e.position.distanceTo(bot.entity.position) > 48) continue
    mobs[`mob:${e.name}`] = mcData.entitiesByName[e.name]?.displayName ?? e.name
  }
  // Nutztiere auch, wenn gerade keins zu sehen ist
  for (const n of Object.keys(FUTTER)) mobs[`mob:${n}`] ??= mcData.entitiesByName[n]?.displayName ?? n

  const dinge = {}
  for (const i of bot.inventory.items()) dinge[`ding:${i.name}`] = `${i.displayName} (${aufgaben.anzahlItem(i.name)} im Inventar)`
  for (const [n, c] of Object.entries(ort.truheInhalt ?? {})) dinge[`ding:${n}`] ??= `${mcData.itemsByName[n]?.displayName ?? n} (${c} in der Truhe)`

  return { bloecke, items, mobs, dinge }
}

let jevLaeuft = false
async function freieSprache (text, gefluestert) {
  if (jevLaeuft) return fluestern('Moment, ich denke noch ueber das Letzte nach.')
  jevLaeuft = true
  try {
    // "hol holz und dann bau eine spitzhacke": nacheinander ausfuehren
    const teile = text.split(/\s*(?:,?\s*und dann|,?\s*danach|;|\bthen\b)\s*/i).filter(Boolean)
    const kandidaten = kandidatenSammeln()
    for (const [i, teil] of teile.entries()) {
      const j = await jev.befehlVerstehen(teil, gefluestert, {
        botName: bot.username,
        besitzer: cfg.besitzer,
        zustand: { ...zustand, aufgabe: aufgaben.beschreibung() }
      }, kandidaten)
      log(`Jev: "${teil}" -> an_bot ${j.anBot.toFixed(2)}, ${j.aktion} (${j.aktionSicherheit.toFixed(2)}), ` +
        `ohne_ende ${j.ohneEnde.toFixed(2)}, block ${j.block.wert}, item ${j.item.wert}, mob ${j.mob.wert}, ding ${j.ding.wert}`)

      // Fluestern ist schon an den Bot gerichtet, im offenen Chat strenger sein
      if (i === 0 && j.anBot < (gefluestert ? 0.3 : cfg.jevSchwelle ?? 0.5)) return
      if (j.aktion === 'keine' || j.aktionSicherheit < 0.45) {
        // Klar an mich gerichtet, aber unklar was: lieber nachfragen als schweigen
        if (gefluestert || j.anBot >= 0.8) fluestern(`"${teil}" hab ich nicht verstanden. Sag !was fuer Beispiele.`)
        return
      }
      aktionAusfuehren(j, teil, i > 0)
    }
  } catch (e) {
    log('Jev-Fehler:', e.message)
  } finally {
    jevLaeuft = false
  }
}

// Aus Jevs Urteil einen Auftrag machen. Mengen und Koordinaten liest der Code selbst.
function aktionAusfuehren (j, text, anhaengen) {
  const ohneEnde = j.ohneEnde >= 0.6
  const menge = standard => ohneEnde ? UNENDLICH : (mengeLesen(text) ?? standard)
  const sicher = (w, was) => {
    if (w.wert !== 'unklar' && w.sicherheit >= 0.4) return w.wert.split(':')[1]
    fluestern(`Welche${was} meinst du?`)
    return null
  }
  const auftrag = a => {
    if (zustand.modus === 'stehen') zustand.modus = 'folgen'
    aufgaben.starten(a, anhaengen)
    fluestern(`${anhaengen ? 'Danach: ' : 'Mache: '}${a.art}${a.name || a.mobName || a.itemName ? ' ' + (a.name ?? a.mobName ?? a.itemName) : ''}` +
      (a.menge != null && a.art !== 'treppe' ? ` (${a.menge === UNENDLICH ? 'ohne Ende' : a.menge})` : ''))
  }
  const itemAnzeige = n => mcData.itemsByName[n]?.displayName ?? n

  switch (j.aktion) {
    case 'folgen': return befehl('!folge')
    case 'stehen': return befehl('!stop')
    case 'selbst': return befehl('!selbst')
    case 'heim_setzen': return befehl('!heim')
    case 'status': return befehl('!status')
    case 'kampf_an': case 'kampf_aus':
      if (zustand.kampf !== (j.aktion === 'kampf_an')) befehl('!kampf')
      else fluestern(`Kampf ist schon ${zustand.kampf ? 'an' : 'aus'}.`)
      return
    case 'loot_an': case 'loot_aus':
      if (zustand.loot !== (j.aktion === 'loot_an')) befehl('!loot')
      else fluestern(`Looten ist schon ${zustand.loot ? 'an' : 'aus'}.`)
      return
    case 'abbauen': {
      const w = sicher(j.block, 'n Block')
      if (!w) return
      if (j.block.wert.startsWith('gruppe:')) return abbauenStarten(w, menge(ROHSTOFFE[w].standard), anhaengen)
      return auftrag({ art: 'abbauen', blockIds: [mcData.blocksByName[w].id], name: mcData.blocksByName[w].displayName, menge: menge(16) })
    }
    case 'craften': {
      const w = sicher(j.item, 's Item')
      if (w) auftrag({ art: 'craften', item: w, itemName: itemAnzeige(w), menge: ohneEnde ? 64 : (mengeLesen(text) ?? 1) })
      return
    }
    case 'schmelzen':
      return auftrag({ art: 'schmelzen', item: j.ding.wert.startsWith('ding:') ? j.ding.wert.slice(5) : null, menge: menge(64) })
    case 'jagen': case 'zuechten': {
      const w = sicher(j.mob, 's Tier')
      if (w) auftrag({ art: j.aktion, mob: w, mobName: mcData.entitiesByName[w]?.displayName ?? w, menge: menge(j.aktion === 'jagen' ? 1 : 2) })
      return
    }
    case 'geben': {
      const ding = j.ding.wert.startsWith('ding:') && j.ding.sicherheit >= 0.4 ? j.ding.wert.slice(5) : null
      return auftrag({ art: 'geben', an: cfg.besitzer, item: ding, itemName: ding ? itemAnzeige(ding) : 'alles', menge: ding ? menge(UNENDLICH) : UNENDLICH })
    }
    case 'holen': {
      const w = sicher(j.ding, 's Item')
      if (w && w !== 'alles') auftrag({ art: 'holen', item: w, itemName: itemAnzeige(w), menge: menge(UNENDLICH) })
      return
    }
    case 'gehen': {
      const k = koordinatenLesen(text)
      if (!k) return fluestern('Wohin? Sag z.B. "geh zu 100 64 -200".')
      return auftrag({ art: 'gehen', ...k })
    }
    case 'treppe': {
      const y = text.match(/-?\d+/)?.[0]
      return auftrag({ art: 'treppe', zielY: y != null ? +y : Math.floor(bot.entity.position.y) - 20 })
    }
    case 'tunnel': return auftrag({ art: 'tunnel', menge: menge(32) })
    case 'saeule': return auftrag({ art: 'saeule', menge: mengeLesen(text) ?? 5 })
    case 'farmen': return auftrag({ art: 'farmen', menge: ohneEnde ? UNENDLICH : 1 })
    case 'scheren': return auftrag({ art: 'scheren', menge: menge(UNENDLICH) })
    case 'angeln': return auftrag({ art: 'angeln', menge: menge(10) })
    case 'einlagern': case 'heim': case 'schlafen': case 'ausruesten':
      if (j.aktion === 'einlagern' && !ort.truhe) return fluestern('Keine Truhe gesetzt. Stell dich an eine Truhe und sag !heim.')
      if (j.aktion === 'heim' && !ort.heim) return fluestern('Kein Zuhause gesetzt. Stell dich hin und sag !heim.')
      return auftrag({ art: j.aktion })
  }
}

function abbauenStarten (rohstoff, menge, anhaengen = false) {
  if (zustand.modus === 'stehen') zustand.modus = 'folgen'
  aufgaben.starten({ art: 'abbauen', blockIds: aufgaben.blockIdsGruppe(rohstoff), name: ROHSTOFFE[rohstoff].name, menge, setzlinge: rohstoff === 'holz' }, anhaengen)
  fluestern(`${anhaengen ? 'Danach: ' : ''}Baue ${menge === UNENDLICH ? 'ohne Ende' : menge + 'x'} ${ROHSTOFFE[rohstoff].name} ab.`)
}

function befehl (text) {
  const [cmd, ...args] = text.split(/\s+/)
  if (cmd === '!folge' || cmd === '!komm') {
    zustand.modus = 'folgen'
    aufgaben.stoppen()
    fluestern('Folge dir.')
  } else if (cmd === '!stop' || cmd === '!bleib') {
    zustand.modus = 'stehen'
    aufgaben.stoppen()
    bot.pvp.stop()
    bot.pathfinder.setGoal(null)
    fluestern('Bleibe stehen.')
  } else if (cmd === '!selbst') {
    if (!jev.aktiv) return fluestern('Selbststaendig geht nur mit TYPESAFE_API_KEY.')
    zustand.modus = 'selbst'
    naechsteEntscheidung = 0
    fluestern('Arbeite selbststaendig. !folge oder !stop beendet das.')
  } else if (cmd === '!sammel') {
    const rohstoff = args.find(a => ROHSTOFFE[a])
    if (!rohstoff) return fluestern(`!sammel <${Object.keys(ROHSTOFFE).join('|')}> [menge|unendlich]`)
    abbauenStarten(rohstoff, args.includes('unendlich') ? UNENDLICH : (mengeLesen(args.join(' ')) ?? ROHSTOFFE[rohstoff].standard))
  } else if (cmd === '!heim') {
    heimSetzen()
  } else if (cmd === '!nachhause') {
    if (!ort.heim) return fluestern('Kein Zuhause gesetzt. Stell dich hin und sag !heim.')
    aufgaben.starten({ art: 'heim' })
    fluestern('Gehe nach Hause.')
  } else if (cmd === '!lager') {
    if (!ort.truhe) return fluestern('Keine Truhe gesetzt. Stell dich an eine Truhe und sag !heim.')
    aufgaben.starten({ art: 'einlagern' })
    fluestern('Bringe alles in die Truhe.')
  } else if (cmd === '!kampf') {
    zustand.kampf = !zustand.kampf
    if (!zustand.kampf) bot.pvp.stop()
    fluestern(`Kampf ${zustand.kampf ? 'an' : 'aus'}.`)
  } else if (cmd === '!loot') {
    zustand.loot = !zustand.loot
    fluestern(`Looten ${zustand.loot ? 'an' : 'aus'}.`)
  } else if (cmd === '!gib') {
    allesAbgeben()
  } else if (cmd === '!status') {
    fluestern(`Modus ${zustand.modus}, Aufgabe ${aufgaben.beschreibung()}, Kampf ${zustand.kampf ? 'an' : 'aus'}, ` +
      `Loot ${zustand.loot ? 'an' : 'aus'}, Leben ${Math.round(bot.health)}/20, Hunger ${bot.food}/20, freie Slots ${freieSlots()}`)
  } else if (cmd === '!hilfe') {
    fluestern('!folge !stop !selbst !sammel <rohstoff> [menge|unendlich] !heim !nachhause !lager !kampf !loot !gib !status !was')
  } else if (cmd === '!was') {
    fluestern('Sag es normal, z.B.: "hol 20 eisen" | "faell baeume ohne ende" | "bau mir eine steinspitzhacke" | ' +
      '"brat das fleisch" | "toete die zombies" | "zuechte kuehe" | "ernte das feld immer wieder" | "grab einen tunnel 50 lang" | ' +
      '"grab runter bis y 11" | "geh zu 100 70 -50" | "gib mir das holz" | "hol 10 brot aus der truhe" | "zieh deine ruestung an" | ' +
      '"hol holz und dann bau eine werkbank"')
  }
}

function speichereOrt () {
  fs.writeFileSync(ORT_DATEI, JSON.stringify(ort, null, 2))
}

function heimSetzen () {
  const besitzer = bot.players[cfg.besitzer]?.entity
  if (!besitzer) return fluestern('Ich sehe dich nicht.')
  const p = besitzer.position.floored()
  ort.heim = { x: p.x, y: p.y, z: p.z }
  const truhe = bot.findBlock({
    point: besitzer.position,
    matching: ['chest', 'barrel', 'trapped_chest'].map(n => mcData.blocksByName[n]?.id).filter(id => id != null),
    maxDistance: 8
  })
  ort.truhe = truhe ? { x: truhe.position.x, y: truhe.position.y, z: truhe.position.z } : null
  speichereOrt()
  fluestern(`Zuhause gesetzt bei ${p.x} ${p.y} ${p.z}. ` +
    (truhe ? `Truhe bei ${truhe.position.x} ${truhe.position.y} ${truhe.position.z}.` : 'Keine Truhe im Umkreis von 8 Bloecken gefunden.'))
}

function tick () {
  if (!bot?.entity || !mcData || !aufgaben) return

  const besitzer = bot.players[cfg.besitzer]?.entity

  essenWennNoetig()

  // Waehrend eines laufenden Kampfes steuert mineflayer-pvp den Pathfinder
  if (bot.pvp.target) {
    if (bot.health <= cfg.fluchtLeben) {
      log('Leben zu niedrig, breche Kampf ab.')
      bot.pvp.stop()
      fluestern(`Leben zu niedrig (${Math.round(bot.health)}), ziehe mich zurueck.`)
    }
    return
  }

  if (zustand.modus === 'stehen') return

  if (zustand.kampf && bot.health > cfg.fluchtLeben) {
    const ziel = naechstesMonster(besitzer)
    // Waehrend einer Aufgabe nur wehren, wenn es wirklich nah ist
    if (ziel && (!aufgaben.aktuell() || ziel.position.distanceTo(bot.entity.position) < 8)) {
      kampfBeginnen(ziel)
      return
    }
  }

  if (aufgaben.laeuft()) return
  if (aufgaben.pausiert()) {
    aufgaben.weiter()
    return
  }

  if (zustand.modus === 'selbst') return selbstEntscheiden(besitzer)

  if (!besitzer) return // Besitzer offline oder ausser Sichtweite

  if (zustand.loot) {
    const drop = naechsterDrop(besitzer)
    if (drop) {
      bot.pathfinder.setGoal(new goals.GoalNear(drop.position.x, drop.position.y, drop.position.z, 0), false)
      return
    }
  }

  folgen(besitzer)
}

// ---------- Selbststaendiger Modus: Code sammelt die Lage und die Optionen, Jev waehlt ----------

let naechsteEntscheidung = 0
let entscheidungLaeuft = false
const letzteAufgaben = []

async function selbstEntscheiden (besitzer) {
  if (entscheidungLaeuft || Date.now() < naechsteEntscheidung) return
  entscheidungLaeuft = true
  naechsteEntscheidung = Date.now() + (cfg.selbstPauseSekunden ?? 15) * 1000
  try {
    // Feste Regeln zuerst, dafuer braucht es kein Urteil
    if (freieSlots() === 0 && ort.truhe) return waehle({ art: 'einlagern' }, 'Inventar voll')
    if (bot.health <= cfg.fluchtLeben) return waehle(besitzer ? { art: 'zum_besitzer' } : ort.heim ? { art: 'heim' } : { art: 'warten' }, 'wenig Leben')

    const { lage, optionen, auftraege } = lageErfassen(besitzer)
    const { aufgabe, sicherheit } = await jev.naechsteAufgabe(lage, optionen)
    if (zustand.modus !== 'selbst' || aufgaben.aktuell()) return // waehrenddessen umentschieden
    waehle(auftraege[aufgabe], `Jev ${sicherheit.toFixed(2)}`, aufgabe)
  } catch (e) {
    log('Jev-Fehler (selbststaendig):', e.message)
  } finally {
    entscheidungLaeuft = false
  }
}

const WERKZEUG_ZIELE = ['wooden_pickaxe', 'stone_pickaxe', 'iron_pickaxe', 'diamond_pickaxe', 'stone_axe', 'iron_axe',
  'stone_sword', 'iron_sword', 'diamond_sword', 'furnace', 'torch', 'crafting_table', 'chest', 'bread',
  'iron_helmet', 'iron_chestplate', 'iron_leggings', 'iron_boots', 'shield', 'bucket']

// Nur Optionen, die gerade wirklich gehen; jede Option ist direkt ein fertiger Auftrag
function lageErfassen (besitzer) {
  const optionen = {}
  const auftraege = {}
  const add = (key, text, auftrag) => { optionen[key] = text; auftraege[key] = auftrag }
  const naehe = {}

  for (const [key, r] of Object.entries(ROHSTOFFE)) {
    const ids = aufgaben.blockIdsGruppe(key)
    const { n, abbaubar } = aufgaben.vorrat(ids)
    if (n === 0) continue
    naehe[key] = abbaubar ? n : `${n} (fehlendes Werkzeug)`
    if (abbaubar && key !== 'laub') {
      add(`abbauen_${key}`, `${r.name} abbauen (${n >= 64 ? 'viele' : n} Bloecke in der Naehe).`,
        { art: 'abbauen', blockIds: ids, name: r.name, menge: r.standard, setzlinge: key === 'holz' })
    }
  }
  const hat = n => aufgaben.anzahlItem(n) > 0
  for (const ziel of WERKZEUG_ZIELE) {
    const id = mcData.itemsByName[ziel]?.id
    if (id == null || (hat(ziel) && ziel !== 'torch')) continue
    if (bot.recipesFor(id, null, 1, true).length) {
      add(`craften_${ziel}`, `${mcData.items[id].displayName} herstellen (Material ist da).`, { art: 'craften', item: ziel, itemName: mcData.items[id].displayName, menge: ziel === 'torch' ? 16 : 1 })
    }
  }
  const roh = bot.inventory.items().find(i => /^raw_(iron|gold|copper)$|^(beef|porkchop|chicken|mutton)$/.test(i.name))
  if (roh && bot.inventory.items().some(i => /coal|_planks|_log/.test(i.name))) {
    add('schmelzen', `${roh.displayName} im Ofen schmelzen/braten.`, { art: 'schmelzen', item: roh.name, menge: 64 })
  }
  const reif = bot.findBlocks({ matching: b => PFLANZEN[b.name] && b.getProperties().age >= PFLANZEN[b.name].reif, maxDistance: 24, count: 5 }).length
  if (reif) add('farmen', `Reife Felder ernten und neu pflanzen (${reif}+ reif).`, { art: 'farmen', menge: 1 })
  const zeit = bot.time.timeOfDay
  const nacht = zeit >= 12500 && zeit < 23000
  if (nacht && bot.findBlock({ matching: b => b.name.endsWith('_bed'), maxDistance: 32 })) add('schlafen', 'Ins Bett gehen und schlafen.', { art: 'schlafen' })
  if (bot.inventory.items().some(i => /_(helmet|chestplate|leggings|boots)$/.test(i.name))) add('ausruesten', 'Ruestung aus dem Inventar anziehen.', { art: 'ausruesten' })
  const tiere = Object.values(bot.entities).filter(e => ['cow', 'pig', 'sheep', 'chicken'].includes(e.name) && e.position.distanceTo(bot.entity.position) < 24)
  if (tiere.length && !nacht) {
    const t = tiere[0]
    add(`jagen_${t.name}`, `${mcData.entitiesByName[t.name].displayName} fuer Essen jagen (${tiere.filter(x => x.name === t.name).length} in der Naehe).`,
      { art: 'jagen', mob: t.name, mobName: mcData.entitiesByName[t.name].displayName, menge: 2 })
  }
  const einlagerbar = bot.inventory.items().filter(i => !aufgaben.behalten(i)).length
  if (ort.truhe && einlagerbar > 0) add('einlagern', `Zur Truhe gehen und ${einlagerbar} Stapel einlagern (${freieSlots()} freie Slots).`, { art: 'einlagern' })
  const heimDist = ort.heim ? Math.round(bot.entity.position.distanceTo(ort.heim)) : null
  if (heimDist > 10) add('heim', `Nach Hause gehen (${heimDist} Bloecke entfernt).`, { art: 'heim' })
  const besitzerDist = besitzer ? Math.round(bot.entity.position.distanceTo(besitzer.position)) : null
  if (besitzerDist > 6) add('zum_besitzer', `Zum Spieler gehen (${besitzerDist} Bloecke entfernt).`, { art: 'zum_besitzer' })
  add('warten', 'Nichts tun und eine Weile abwarten.', { art: 'warten' })

  const lage = {
    bot: {
      name: bot.username,
      leben: `${Math.round(bot.health)}/20`,
      hunger: `${bot.food}/20`,
      freie_slots: freieSlots(),
      inventar: inventarKurz(),
      werkzeuge: bot.inventory.items().filter(i => /pickaxe|_axe|shovel|sword/.test(i.name)).map(i => i.name)
    },
    besitzer: besitzer ? { name: cfg.besitzer, entfernung: besitzerDist } : { name: cfg.besitzer, sichtbar: false },
    tageszeit: zeit < 12000 ? 'Tag' : zeit < 13000 ? 'Abenddaemmerung' : zeit < 23000 ? 'Nacht' : 'Morgendaemmerung',
    zuhause: ort.heim ? { entfernung: heimDist, truhe: !!ort.truhe } : 'nicht gesetzt',
    rohstoffe_in_der_naehe: naehe,
    monster_in_der_naehe: feindeZaehlen(16),
    letzte_aufgaben: letzteAufgaben
  }
  return { lage, optionen, auftraege }
}

function waehle (auftrag, grund, key = auftrag.art) {
  log(`Selbststaendig: ${key} (${grund})`)
  letzteAufgaben.push(key)
  if (letzteAufgaben.length > 5) letzteAufgaben.shift()

  if (auftrag.art === 'zum_besitzer') {
    const besitzer = bot.players[cfg.besitzer]?.entity
    if (besitzer) bot.pathfinder.setGoal(new goals.GoalFollow(besitzer, cfg.folgeAbstand), false)
  } else if (auftrag.art !== 'warten') {
    aufgaben.starten(auftrag)
  }
}

function inventarKurz () {
  const summe = {}
  for (const i of bot.inventory.items()) summe[i.name] = (summe[i.name] ?? 0) + i.count
  return summe
}

function feindeZaehlen (radius) {
  return Object.values(bot.entities).filter(e => e.position &&
    mcData.entitiesByName[e.name]?.category === 'Hostile mobs' &&
    e.position.distanceTo(bot.entity.position) < radius).length
}

// ---------- Kampf, Folgen, Loot ----------

function kampfBeginnen (ziel) {
  // Laufende Aufgabe anhalten, nach dem Kampf setzt tick() sie fort
  if (aufgaben?.laeuft()) aufgaben.pausieren().then(() => angreifen(ziel))
  else angreifen(ziel)
}

function folgen (besitzer) {
  const ziel = bot.pathfinder.goal
  // Nur neu setzen, wenn nicht schon dasselbe Folge-Ziel laeuft
  if (ziel instanceof goals.GoalFollow && ziel.entity?.id === besitzer.id) return
  bot.pathfinder.setGoal(new goals.GoalFollow(besitzer, cfg.folgeAbstand), true)
}

function angreifen (ziel) {
  besteWaffeAnlegen()
    .catch(() => {})
    .then(() => bot.pvp.attack(ziel))
}

function naechstesMonster (besitzer) {
  let best = null
  let bestDist = cfg.kampfRadius
  for (const e of Object.values(bot.entities)) {
    if (e === bot.entity || !e.position) continue
    if (mcData.entitiesByName[e.name]?.category !== 'Hostile mobs') continue
    // Nur was in der Naehe von dir oder mir ist
    const d = Math.min(besitzer ? e.position.distanceTo(besitzer.position) : Infinity, e.position.distanceTo(bot.entity.position))
    if (d < bestDist) {
      best = e
      bestDist = d
    }
  }
  return best
}

const letzterSchlag = new Map()

function naechsterAngreifer (besitzer) {
  let best = null
  let bestDist = 6
  for (const e of Object.values(bot.entities)) {
    if (e === bot.entity || !e.position) continue
    if (e.username === cfg.besitzer || e.username === bot.username) continue
    if (e.type === 'player') {
      if (Date.now() - (letzterSchlag.get(e.id) ?? 0) > 1000) continue
    } else if (mcData.entitiesByName[e.name]?.category !== 'Hostile mobs') continue
    const d = e.position.distanceTo(besitzer.position)
    if (d < bestDist) {
      best = e
      bestDist = d
    }
  }
  return best
}

function naechsterDrop (besitzer) {
  if (freieSlots() === 0) return null
  let best = null
  let bestDist = cfg.lootRadius
  for (const e of Object.values(bot.entities)) {
    if (!e.position) continue
    if (e.name !== 'item') continue
    const d = e.position.distanceTo(besitzer.position)
    if (d < bestDist) {
      best = e
      bestDist = d
    }
  }
  return best
}

async function besteWaffeAnlegen () {
  const waffen = bot.inventory.items().filter(i => /sword|axe/.test(i.name))
  if (waffen.length === 0) return
  const wert = (i) => (i.name.includes('netherite') ? 5
    : i.name.includes('diamond') ? 4
      : i.name.includes('iron') ? 3
        : i.name.includes('stone') ? 2
          : i.name.includes('golden') ? 1 : 0) + (i.name.includes('sword') ? 0.5 : 0)
  waffen.sort((a, b) => wert(b) - wert(a))
  if (bot.heldItem?.name !== waffen[0].name) await bot.equip(waffen[0], 'hand')
}

let amEssen = false
async function essenWennNoetig () {
  if (amEssen || bot.food > cfg.essenAb) return
  const essen = bot.inventory.items().find(i => mcData.foodsByName[i.name])
  if (!essen) return
  amEssen = true
  try {
    await bot.equip(essen, 'hand')
    await bot.consume()
    log(`Gegessen: ${essen.name} (Hunger jetzt ${bot.food}/20)`)
  } catch (e) {
    log('Essen fehlgeschlagen:', e.message)
  } finally {
    amEssen = false
  }
}

async function allesAbgeben () {
  const besitzer = bot.players[cfg.besitzer]?.entity
  if (!besitzer) return fluestern('Ich sehe dich nicht.')
  const items = bot.inventory.items()
  if (items.length === 0) return fluestern('Inventar ist leer.')
  aufgaben.stoppen()
  bot.pvp.stop()
  await bot.lookAt(besitzer.position.offset(0, 1.6, 0))
  for (const i of items) {
    try {
      await bot.tossStack(i)
    } catch (e) {
      log('Wegwerfen fehlgeschlagen:', e.message)
    }
  }
  fluestern(`${items.length} Stapel abgeworfen.`)
}

function freieSlots () {
  return bot.inventory.emptySlotCount()
}

if (!offline && cfg.botEmail.startsWith('HIER_')) {
  console.error('Bitte zuerst botEmail und besitzer in config.json eintragen.')
  process.exit(1)
}

starten()
