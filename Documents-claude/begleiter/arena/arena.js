// Kampf-Arena fuer den Begleiter: Gegner-Bots mit verschiedenen Ausruestungen, Kits, Wald-Spawn.
// Steuerung im Spielchat (nur vom Besitzer), alles mit # davor, damit der Begleiter es ignoriert:
//   #kit          Kits fuer dich und den Bot        #welle [typen]  Gegnerwelle (Standard: alle)
//   #schild #mace #bogen #tank #rauf  einzelner Gegner   #stop  Gegner weg
//   #hunger       Bot bekommt Hunger (muss essen)  #heil  beide heilen   #wald  beide in den Wald
//   #flug         Elytra + Raketen fuer beide      #hilfe
// Start: node arena/arena.js   (RCON-Passwort in daten/kampfserver-rcon.txt)
const fs = require('fs')
const path = require('path')
const mineflayer = require('mineflayer')
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder')
const { Vec3 } = require('vec3')
const { Rcon } = require('./rcon')

const HOST = process.env.ARENA_HOST ?? '127.0.0.1'
const PORT = +(process.env.ARENA_PORT ?? 25520)
const RCON_PORT = +(process.env.ARENA_RCON_PORT ?? PORT + 1)
const HTTP_PORT = +(process.env.ARENA_HTTP ?? 47812)
const ICH = process.env.ARENA_ICH ?? 'L0rdr3spawn'
const BOT = process.env.ARENA_BOT ?? 'NotL0rdr3spawn'
const PASSWORT = process.env.ARENA_RCON_PW ?? fs.readFileSync(path.join(__dirname, '..', 'daten', 'kampfserver-rcon.txt'), 'utf8').trim()

const log = (...a) => console.log(`[${new Date().toLocaleTimeString('de-DE')}] [arena]`, ...a)
const warte = ms => new Promise(resolve => setTimeout(resolve, ms))
let rcon

// Befehle strikt nacheinander (gleichzeitige Pakete beantwortet der Server mit Verbindungsabbruch),
// bei Abbruch neu verbinden
let schlange = Promise.resolve()
function cmd (c) {
  const lauf = schlange.then(async () => {
    try {
      if (!rcon || rcon.sock.destroyed) rcon = await new Rcon({ host: HOST, port: RCON_PORT, passwort: PASSWORT }).verbinden()
      return await rcon.befehl(c)
    } catch (e) {
      log('RCON-Fehler:', c, e.message)
      rcon?.schliessen()
      rcon = null
      return ''
    }
  })
  schlange = lauf
  return lauf
}
const sag = text => cmd(`tellraw ${ICH} ${JSON.stringify({ text: `[Arena] ${text}`, color: 'gold' })}`)

// ---------------------------------------------------------------- Ausruestung
const P4 = '[enchantments={protection:4,unbreaking:3}]'
const RUESTUNG = (mat, ench = P4) => ['helmet', 'chestplate', 'leggings', 'boots'].map(s => `${mat}_${s}${ench}`)
const SLOT = { helmet: 'armor.head', chestplate: 'armor.chest', leggings: 'armor.legs', boots: 'armor.feet' }

async function anziehen (name, teile) {
  for (const t of teile) {
    const art = t.match(/_(helmet|chestplate|leggings|boots)/)[1]
    await cmd(`item replace entity ${name} ${SLOT[art]} with ${t}`)
  }
}

async function spielerKit (name) {
  await cmd(`clear ${name}`)
  await anziehen(name, RUESTUNG('netherite'))
  for (const g of ['netherite_sword[enchantments={sharpness:5,unbreaking:3}]', 'netherite_axe[enchantments={sharpness:5,efficiency:5}]',
    'mace[enchantments={density:5,wind_burst:1}]', 'iron_spear[enchantments={lunge:3}]', 'wind_charge 64', 'elytra[enchantments={unbreaking:3}]',
    'firework_rocket 64', 'golden_apple 16', 'enchanted_golden_apple 2', 'cooked_beef 64', 'totem_of_undying 3', 'shield',
    'splash_potion[potion_contents={potion:"minecraft:strong_healing"}] 4', 'potion[potion_contents={potion:"minecraft:strength"}] 2',
    'potion[potion_contents={potion:"minecraft:fire_resistance"}] 2', 'rotten_flesh 16', 'oak_planks 64', 'water_bucket', 'bucket']) {
    await cmd(`give ${name} ${g}`)
  }
  await heilen(name)
}

async function heilen (name) {
  await cmd(`effect clear ${name}`)
  await cmd(`effect give ${name} instant_health 1 10 true`)
  await cmd(`effect give ${name} saturation 1 20 true`)
}

// ---------------------------------------------------------------- Gegner
const TYPEN = {
  schild: {
    name: 'Schildwache',
    ruestung: RUESTUNG('netherite'),
    items: ['netherite_sword[enchantments={sharpness:3}]'],
    offhand: 'shield',
    beschreibung: 'Netherite + Schild, blockt fast immer -> mit der Axt knacken'
  },
  mace: {
    name: 'Macer',
    ruestung: RUESTUNG('diamond', '[enchantments={protection:2}]'),
    items: ['mace[enchantments={density:3,wind_burst:1}]'],
    offhand: 'wind_charge 64',
    beschreibung: 'springt mit Windladungen und smasht von oben'
  },
  bogen: {
    name: 'Bogenschuetze',
    ruestung: RUESTUNG('chainmail', ''),
    items: ['bow[enchantments={power:3,infinity:1}]', 'arrow 1', 'iron_sword'],
    beschreibung: 'haelt Abstand und schiesst'
  },
  tank: {
    name: 'Tank',
    ruestung: RUESTUNG('netherite'),
    items: ['diamond_sword[enchantments={sharpness:2}]', 'golden_apple 8', 'totem_of_undying 1'],
    effekte: ['regeneration 9999 0'],
    beschreibung: 'viel Ruestung, isst Goldaepfel, hat ein Totem -> zaeher Kampf'
  },
  rauf: {
    name: 'Raufbold',
    ruestung: RUESTUNG('iron', ''),
    items: ['diamond_axe'],
    effekte: ['speed 9999 0'],
    beschreibung: 'schnell mit Axt, bricht Schilde'
  }
}

const gegner = new Map() // name -> { bot, typ, ... }
let wald = null // Waldposition

function gegnerStarten (typKey) {
  const typ = TYPEN[typKey]
  if (gegner.has(typ.name)) return
  const b = mineflayer.createBot({ host: HOST, port: PORT, username: typ.name, auth: 'offline', version: '26.1', checkTimeoutInterval: 60000 })
  b.once('inject_allowed', () => { const o = b.supportFeature; b.supportFeature = f => f === 'entityActionUsesStringMapper' || o(f) })
  // Gleiche Mineflayer-Korrektur wie beim Begleiter: entity_velocity kommt seit 1.21.9 schon in Bloecken/Tick
  // (Mineflayer teilt durch 8000 -> kein Rueckstoss, kein Windladungs-Sprung)
  b._client.on('entity_velocity', p => {
    const e = b.entities[p.entityId]
    if (e && p.velocity) e.velocity.set(p.velocity.x, p.velocity.y, p.velocity.z)
  })
  b.loadPlugin(pathfinder)
  const g = { b, typ, typKey, ladung: 0, ziel: null, phase: null, hoechstesY: null, essenBis: 0, schussTicks: 0, schildHoch: 0, tot: false }
  gegner.set(typ.name, g)
  b.on('error', e => log(typ.name, 'Fehler:', e.message))
  b.on('kicked', r => log(typ.name, 'gekickt:', JSON.stringify(r)))
  // Erst nach dem Austragen pruefen, ob die Welle geschafft ist (quit() ist asynchron)
  b.on('end', () => { gegner.delete(typ.name); log(typ.name, 'weg'); if (g.tot) pruefeWelle() })
  b.once('spawn', async () => {
    const m = new Movements(b)
    m.canDig = false
    m.allow1by1towers = false
    m.allowSprinting = true
    b.pathfinder.setMovements(m)
    await cmd(`clear ${typ.name}`)
    await anziehen(typ.name, typ.ruestung)
    for (const it of typ.items) await cmd(`give ${typ.name} ${it}`)
    if (typ.offhand) await cmd(`item replace entity ${typ.name} weapon.offhand with ${typ.offhand}`)
    for (const e of typ.effekte ?? []) await cmd(`effect give ${typ.name} ${e} true`)
    await cmd(`effect give ${typ.name} instant_health 1 10 true`)
    // Im Kreis um den Besitzer herum absetzen
    const w = Math.random() * Math.PI * 2
    // spreadplayers setzt nie ins Wasser; 12-16 Bloecke vom Besitzer weg
    const p = await posVon(ICH)
    if (p) await cmd(`spreadplayers ${(p.x + Math.cos(w) * 14).toFixed(1)} ${(p.z + Math.sin(w) * 14).toFixed(1)} 0 3 false ${typ.name}`)
    await warte(800)
    const waffe = b.inventory.items().find(i => /sword|axe|mace|bow/.test(i.name))
    if (waffe) await b.equip(waffe, 'hand').catch(() => {})
    log(`${typ.name} kaempft (${typ.beschreibung})`)
    sag(`${typ.name}: ${typ.beschreibung}`)
    b.on('physicsTick', () => { try { gegnerTick(g) } catch (e) { log(typ.name, e.message) } })
  })
  b.on('death', () => {
    g.tot = true
    sag(`${typ.name} besiegt!`)
    log(typ.name, 'besiegt')
    setTimeout(() => b.quit(), 1500)
  })
}

function pruefeWelle () {
  if (gegner.size === 0) sag('Welle geschafft! #welle fuer die naechste.')
}

// Ziel: naechster von Besitzer und Begleitbot
function zielFinden (b) {
  const kandidaten = [ICH, BOT].map(n => b.players[n]?.entity).filter(Boolean)
  return kandidaten.sort((x, y) => x.position.distanceTo(b.entity.position) - y.position.distanceTo(b.entity.position))[0] ?? null
}

// Ziel nur setzen, wenn es sich aendert - ein neues Goal in jedem Tick laesst den Pathfinder
// dauernd neu planen, und der Gegner bleibt stehen
function folgen (b, z, abstand) {
  const alt = b.pathfinder.goal
  if (alt instanceof goals.GoalFollow && alt.entity?.id === z.id && alt.rangeSq === abstand * abstand) return
  b.pathfinder.setGoal(new goals.GoalFollow(z, abstand), true)
}
function stehen (b) {
  if (b.pathfinder.goal) b.pathfinder.setGoal(null)
}

function gegnerTick (g) {
  const b = g.b
  if (!b.entity || g.tot) return
  g.ladung++
  if (process.env.ARENA_DEBUG && g.ladung % 40 === 0) {
    const zz = zielFinden(b)
    log(`[${g.typ.name}] pos ${b.entity.position.toArray().map(v => v.toFixed(1)).join(' ')} boden ${b.entity.onGround} block ${b.blockAt(b.entity.position)?.name ?? 'NICHT GELADEN'} ziel ${zz ? zz.username + ' ' + zz.position.distanceTo(b.entity.position).toFixed(1) : '-'} spieler ${Object.keys(b.players).join(',')}`)
  }
  const z = zielFinden(b)
  if (!z) { stehen(b); return }
  const d = z.position.distanceTo(b.entity.position)
  const kopf = z.position.offset(0, 1.5, 0)

  // Fallhoehe fuer Mace/Krits
  if (b.entity.onGround) g.hoechstesY = b.entity.position.y
  else if (g.hoechstesY == null || b.entity.position.y > g.hoechstesY) g.hoechstesY = b.entity.position.y
  const fall = (g.hoechstesY ?? b.entity.position.y) - b.entity.position.y

  // Tank: Goldapfel bei wenig Leben
  if (g.typKey === 'tank') {
    if (Date.now() < g.essenBis) return
    if (b.health <= 10 && !g.isst) {
      const apfel = b.inventory.items().find(i => i.name === 'golden_apple')
      if (apfel) {
        g.isst = true
        g.essenBis = Date.now() + 1800
        b.equip(apfel, 'hand').then(() => { b.activateItem(); setTimeout(() => { b.deactivateItem(); g.isst = false; const w = b.inventory.items().find(i => /sword/.test(i.name)); if (w) b.equip(w, 'hand').catch(() => {}) }, 1700) }).catch(() => { g.isst = false })
        return
      }
    }
  }

  // Bogenschuetze: Abstand 8-16 halten und schiessen
  if (g.typKey === 'bogen') {
    const bogen = b.inventory.items().find(i => i.name === 'bow')
    if (bogen && b.heldItem?.name !== 'bow') { b.equip(bogen, 'hand').catch(() => {}); return }
    if (d < 7) {
      if (!(b.pathfinder.goal instanceof goals.GoalInvert)) b.pathfinder.setGoal(new goals.GoalInvert(new goals.GoalFollow(z, 10)), true)
    } else if (d > 18) {
      folgen(b, z, 12)
    } else if (d > 9 && d < 16) {
      stehen(b)
    }
    // Vorhalt + Pfeilbogen grob ausgleichen
    const v = z.velocity ?? new Vec3(0, 0, 0)
    b.lookAt(kopf.plus(v.scaled(d / 3)).offset(0, d * d * 0.0025, 0), true)
    g.schussTicks++
    if (g.schussTicks === 1) b.activateItem()
    if (g.schussTicks >= 24) { b.deactivateItem(); g.schussTicks = -10 }
    return
  }

  // Anlaufen
  if (d > 3) folgen(b, z, 1.5)
  else stehen(b)
  b.lookAt(kopf, true)

  const tempo = /mace/.test(b.heldItem?.name) ? 0.6 : /axe/.test(b.heldItem?.name) ? 1.0 : 1.6
  const bereit = g.ladung >= Math.ceil(20 / tempo)

  // Schildwache: Schild oben, nur zum Schlagen runter
  if (g.typKey === 'schild') {
    const schildGesperrt = b.entity && b.inventory.slots[45]?.name !== 'shield'
    if (d < 3 && bereit) {
      b.deactivateItem()
      b.attack(z)
      g.ladung = 0
      g.schildHoch = 3 // Ticks bis Schild wieder hoch
    } else if (!schildGesperrt && --g.schildHoch <= 0 && !b.usingHeldItem) {
      b.activateItem(true)
    }
    return
  }

  // Macer: Windladung vor die Fuesse (steil nach unten) -> Sprung; in der Luft zum Ziel lenken; im Fall smashen
  if (g.typKey === 'mace') {
    if (d < 3.4 && fall > 1.6 && b.entity.velocity.y < 0) { b.attack(z); g.ladung = 0; g.hoechstesY = b.entity.position.y; return }
    if (b.entity.onGround && d < 5 && Date.now() > (g.windBis ?? 0)) {
      g.windBis = Date.now() + 2500
      stehen(b)
      b.clearControlStates()
      b.entity.pitch = -Math.PI / 2
      b.look(b.entity.yaw, -Math.PI / 2, true)
      b.activateItem(true) // Windladung in der Nebenhand
      b.deactivateItem()
      g.inLuft = true
      return
    }
    if (!b.entity.onGround) {
      // Waehrend des Flugs Richtung Ziel steuern (kein Pathfinder in der Luft)
      stehen(b)
      b.lookAt(z.position.offset(0, 1, 0), true)
      b.setControlState('forward', Math.hypot(z.position.x - b.entity.position.x, z.position.z - b.entity.position.z) > 0.8)
      return
    }
    b.setControlState('forward', false)
  }

  // Alle anderen: Krit-Spruenge, Schlag bei voller Ladung
  if (d < 3.1 && bereit) {
    if (b.entity.onGround && g.typKey !== 'rauf') { b.setControlState('jump', true); return }
    b.setControlState('jump', false)
    if (b.entity.onGround || b.entity.velocity.y < 0) { b.attack(z); g.ladung = 0 }
  } else {
    b.setControlState('jump', false)
  }
}

async function posVon (name) {
  const a = await cmd(`data get entity ${name} Pos`)
  const m = a.match(/\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]/)
  return m ? { x: +m[1], y: +m[2], z: +m[3] } : null
}

// ---------------------------------------------------------------- Wald finden
async function waldSuchen () {
  const antwort = await cmd('execute in minecraft:overworld positioned 0 64 0 run locate biome minecraft:forest')
  const m = antwort.match(/\[(-?\d+), ~?-?\d*~?, (-?\d+)\]/) ?? antwort.match(/(-?\d+), ~, (-?\d+)/)
  if (!m) { log('Wald nicht gefunden:', antwort); return null }
  const [x, z] = [+m[1], +m[2]]
  await cmd(`forceload add ${x} ${z}`)
  await warte(1500)
  await cmd(`execute positioned ${x} 64 ${z} positioned over motion_blocking_no_leaves run setworldspawn ~ ~ ~`)
  log(`Wald bei ${x} ${z}`)
  return { x, z }
}

async function zumWald () {
  if (!wald) wald = await waldSuchen()
  if (!wald) return sag('Kein Wald gefunden.')
  // spreadplayers landet nie im Wasser (der Wald-Spawn lag an einem See)
  await cmd(`spreadplayers ${wald.x} ${wald.z} 2 12 false ${ICH} ${BOT}`)
  sag(`Ab in den Wald (${wald.x} ${wald.z}).`)
}

// ---------------------------------------------------------------- Befehle
async function befehl (text) {
  const [c, ...args] = text.slice(1).toLowerCase().split(/\s+/)
  if (c === 'hilfe') return sag('#kit #welle [schild mace bogen tank rauf] #schild #mace #bogen #tank #rauf #stop #hunger #heil #wald #flug')
  if (c === 'kit') { await spielerKit(ICH); await spielerKit(BOT); return sag('Kits verteilt.') }
  if (c === 'heil') { await heilen(ICH); await heilen(BOT); return sag('Geheilt.') }
  if (c === 'hunger') { await cmd(`effect give ${BOT} hunger 20 60 true`); return sag(`${BOT} bekommt Hunger - er sollte gleich essen.`) }
  if (c === 'wald') return zumWald()
  if (c === 'flug') {
    for (const n of [ICH, BOT]) { await cmd(`give ${n} elytra`); await cmd(`give ${n} firework_rocket 64`) }
    return sag('Elytra + Raketen verteilt. Zieh deine an und flieg los - der Bot folgt dir (oder sag !flieg).')
  }
  if (c === 'stop') { for (const g of gegner.values()) g.b.quit(); return sag('Gegner weg.') }
  if (c === 'welle') {
    const typen = args.filter(a => TYPEN[a])
    for (const t of (typen.length ? typen : Object.keys(TYPEN))) { gegnerStarten(t); await warte(1200) }
    return
  }
  if (TYPEN[c]) return gegnerStarten(c)
}

async function main () {
  await cmd('list')
  if (!rcon) throw new Error('RCON nicht erreichbar - laeuft der Server?')
  log('RCON verbunden')
  // Einrichtung (idempotent)
  for (const n of [ICH, BOT, ...Object.values(TYPEN).map(t => t.name)]) await cmd(`whitelist add ${n}`)
  await cmd(`op ${ICH}`)
  for (const r of ['keep_inventory true', 'spawn_monsters false', 'spawn_phantoms false', 'advance_time false', 'advance_weather false', 'immediate_respawn true']) await cmd(`gamerule ${r}`)
  await cmd('time set 1000')
  await cmd('weather clear')
  if (!fs.existsSync(path.join(__dirname, '..', 'daten', 'arena-wald.json'))) {
    wald = await waldSuchen()
    if (wald) fs.writeFileSync(path.join(__dirname, '..', 'daten', 'arena-wald.json'), JSON.stringify(wald))
  } else {
    wald = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'daten', 'arena-wald.json'), 'utf8'))
  }

  // Chat lesen: ein unsichtbarer Schiedsrichter-Bot im Zuschauermodus
  await cmd('whitelist add Schiri')
  const schiri = mineflayer.createBot({ host: HOST, port: PORT, username: 'Schiri', auth: 'offline', version: '26.1', physicsEnabled: false })
  schiri.physicsEnabled = false
  // Kein Zuschauermodus: da schickt Mineflayers Physik ungueltige Positionen (Kick). Stattdessen kreativ, unsichtbar, ohne Physik.
  schiri.once('spawn', () => {
    cmd('gamemode creative Schiri'); cmd('effect give Schiri invisibility infinite 0 true')
    log('Schiri hoert zu. #hilfe im Chat.')
  })
  schiri.on('chat', (user, text) => {
    if (user !== ICH || !text.startsWith('#')) return
    log('Befehl:', text)
    befehl(text).catch(e => log('Befehl-Fehler:', e.message))
  })
  schiri.on('end', r => { log('Schiri weg:', r); process.exit(1) })

  // Lokale Steuerung zum Testen ohne Chat: POST http://127.0.0.1:47812 mit z.B. "#schild"
  require('http').createServer((req, res) => {
    // Webseiten im Browser schicken immer "Origin" mit - die duerfen die Arena nicht steuern
    if (req.headers.origin || req.method !== 'POST') { res.statusCode = 403; return res.end('nur lokal') }
    let t = ''
    req.on('data', d => { t += d })
    req.on('end', () => { befehl(t.trim()).catch(e => log(e.message)); res.end('ok') })
  }).listen(HTTP_PORT, '127.0.0.1')
}

main().catch(e => { log('Start fehlgeschlagen:', e.message); process.exit(1) })
