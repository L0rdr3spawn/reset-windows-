// Fliegen-Bot: Ein Minecraft-Spieler, der vom simulierten Fliegenhirn (FlyWire) gesteuert wird.
//
// Der Bot "sieht" per Raycast in ~360 Richtungen (Himmel hell, Blöcke mittel, Mobs/Spieler dunkel),
// schickt das an flybrain/fly_server.py und führt aus, was die Flucht-/Lauf-/Dreh-Neuronen sagen.
//
// Start: erst fly_server.py, dann `node flybot.js` (oder flybot.cmd). Die LAN-Welt wird automatisch
// gefunden (Minecraft kündigt sie per Multicast an), alternativ: node flybot.js <host> <port>
//
// Befehle im Chat (nur vom Besitzer): !laufen (Laufdrang an/aus), !stop, !status
const fs = require('fs')
const path = require('path')
const net = require('net')
const dgram = require('dgram')
const mineflayer = require('mineflayer')
const { Vec3 } = require('vec3')

const cfg = {
  account: 'notL0rdr3spawn',
  version: '26.1', // Mineflayer kann max. 26.1 -> Host braucht ViaFabric + ViaBackwards
  besitzer: 'L0rdr3spawn',
  brainHost: '127.0.0.1',
  brainPort: 8765,
  sichtweite: 32
}

const zustand = { drive: false, aktiv: true, letzteAktion: null }

function log (...args) {
  console.log(`[${new Date().toLocaleTimeString('de-DE')}]`, ...args)
}

// ---------------------------------------------------------------- LAN-Welt finden
function lanWeltFinden (timeoutMs = 0) {
  return new Promise((resolve, reject) => {
    const sock = dgram.createSocket({ type: 'udp4', reuseAddr: true })
    const timer = timeoutMs && setTimeout(() => { sock.close(); reject(new Error('keine LAN-Welt gefunden')) }, timeoutMs) // 0 = ewig warten
    sock.on('message', (msg, rinfo) => {
      const m = msg.toString().match(/\[MOTD\](.*?)\[\/MOTD\]\[AD\](\d+)\[\/AD\]/)
      if (!m) return
      clearTimeout(timer)
      sock.close()
      resolve({ host: rinfo.address, port: Number(m[2]), motd: m[1] })
    })
    sock.bind(4445, () => sock.addMembership('224.0.2.60'))
  })
}

// ---------------------------------------------------------------- Verbindung zum Fliegenhirn
function hirnVerbinden () {
  return new Promise((resolve, reject) => {
    const sock = net.createConnection(cfg.brainPort, cfg.brainHost)
    let puffer = ''
    const warteschlange = []
    sock.setEncoding('utf8')
    sock.on('error', reject)
    sock.on('data', (chunk) => {
      puffer += chunk
      let i
      while ((i = puffer.indexOf('\n')) >= 0) {
        const zeile = puffer.slice(0, i)
        puffer = puffer.slice(i + 1)
        const msg = JSON.parse(zeile)
        if (msg.type === 'hello') resolve({ dirs: msg.dirs, frage })
        else if (warteschlange.length) warteschlange.shift()(msg)
      }
    })
    function frage (nachricht) {
      return new Promise((res) => {
        warteschlange.push(res)
        sock.write(JSON.stringify(nachricht) + '\n')
      })
    }
  })
}

// ---------------------------------------------------------------- Sehen
const rad = (d) => d * Math.PI / 180

// Mineflayer: yaw 0 = Norden (-Z), wachsender yaw = nach links drehen
function richtung (yaw, pitch) {
  return new Vec3(-Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch))
}

function blockHelligkeit (name, dist) {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0
  const grund = 0.35 + 0.35 * ((h % 1000) / 1000) // jede Blocksorte eigener Grauton -> Kanten
  return grund * (1 - 0.3 * Math.min(dist / cfg.sichtweite, 1)) // weit weg etwas dunkler
}

function sehen (bot, dirs) {
  const auge = bot.entity.position.offset(0, bot.entity.eyeHeight ?? 1.62, 0)
  const wesen = Object.values(bot.entities).filter(e =>
    e !== bot.entity && (e.type === 'mob' || e.type === 'hostile' || e.type === 'player' || e.type === 'animal') &&
    e.position.distanceTo(auge) < cfg.sichtweite)
    .map(e => {
      const mitte = e.position.offset(0, (e.height || 1.8) / 2, 0)
      const d = mitte.distanceTo(auge)
      const radius = Math.max(e.width || 0.6, e.height || 1.8) / 2
      return { dir: mitte.minus(auge).scaled(1 / d), d, winkel: Math.atan(radius / d) }
    })

  return dirs.map(([az, el]) => {
    const r = richtung(bot.entity.yaw + rad(az), rad(el))
    const block = bot.world.raycast(auge, r, cfg.sichtweite)
    const blockDist = block ? auge.distanceTo(block.intersect) : Infinity
    for (const w of wesen) {
      const cos = r.x * w.dir.x + r.y * w.dir.y + r.z * w.dir.z
      if (Math.acos(Math.min(1, cos)) < w.winkel && w.d < blockDist) return 0.02 // Wesen = dunkler Fleck
    }
    if (block) return blockHelligkeit(block.name, blockDist)
    return el >= 0 ? 1.0 : 0.6 // Himmel hell, Leere unten grau
  })
}

// ---------------------------------------------------------------- Handeln
function ausfuehren (bot, act) {
  const an = zustand.aktiv
  bot.setControlState('forward', an && act.forward)
  bot.setControlState('back', an && act.back)
  bot.setControlState('sprint', an && act.sprint)
  bot.setControlState('jump', an && (act.jump || bot.entity.isInWater)) // im Wasser nicht ertrinken
  if (an && Math.abs(act.yaw) > 1) bot.look(bot.entity.yaw + rad(act.yaw), 0, true)
  if (!zustand.letzteAktion || zustand.letzteAktion.why !== act.why) log('Fliege:', act.why)
  zustand.letzteAktion = act
}

async function schleife (bot, hirn) {
  while (bot.entity && !bot._beendet) {
    const lum = sehen(bot, hirn.dirs)
    const act = await hirn.frage({ type: 'view', lum, drive: zustand.drive })
    ausfuehren(bot, act)
  }
}

function befehl (bot, text) {
  if (text === '!laufen') {
    zustand.drive = !zustand.drive
    bot.whisper(cfg.besitzer, `Laufdrang (P9-Neuronen) ${zustand.drive ? 'an' : 'aus'}`)
  } else if (text === '!stop') {
    zustand.aktiv = !zustand.aktiv
    if (!zustand.aktiv) bot.clearControlStates()
    bot.whisper(cfg.besitzer, zustand.aktiv ? 'Fliege steuert wieder' : 'Fliege angehalten (!stop = weiter)')
  } else if (text === '!status') {
    const a = zustand.letzteAktion
    bot.whisper(cfg.besitzer, a ? `${a.why} | ${JSON.stringify(a.rates)}` : 'noch keine Daten')
  }
}

// ---------------------------------------------------------------- Start
async function main () {
  let [host, port] = process.argv.slice(2)
  if (!host) {
    log('Suche LAN-Welt ... (im Spiel: Esc -> "Im LAN öffnen")')
    const lan = await lanWeltFinden()
    host = lan.host
    port = lan.port
    log(`LAN-Welt gefunden: "${lan.motd}" auf ${host}:${port}`)
  }

  log('Verbinde mit Fliegenhirn ...')
  const hirn = await hirnVerbinden()
  log(`Fliegenhirn da, ${hirn.dirs.length} Sehstrahlen`)

  const bot = mineflayer.createBot({
    host,
    port: Number(port),
    username: cfg.account,
    auth: 'microsoft',
    version: cfg.version,
    profilesFolder: path.join(__dirname, '.auth'),
    onMsaCode (data) {
      console.log('\n=============================================')
      console.log(` MICROSOFT-LOGIN FUER ${cfg.account}`)
      console.log(' Seite oeffnen:', data.verification_uri)
      console.log(' Code eingeben:', data.user_code)
      console.log(' (Nur einmal noetig, danach liegt das Token in .auth/)')
      console.log('=============================================\n')
    }
  })

  bot.once('spawn', () => {
    log(`Eingeloggt als ${bot.username}`)
    if (bot.username !== cfg.account) log(`ACHTUNG: erwartet war ${cfg.account} - beim Login anderes Konto gewählt?`)
    bot.whisper(cfg.besitzer, 'Fliegenhirn online. Befehle: !laufen !stop !status')
    schleife(bot, hirn).catch(e => log('Schleife beendet:', e.message))
  })
  bot.on('chat', (u, m) => { if (u === cfg.besitzer) befehl(bot, m.trim().toLowerCase()) })
  bot.on('whisper', (u, m) => { if (u === cfg.besitzer) befehl(bot, m.trim().toLowerCase()) })
  bot.on('kicked', (r) => log('Gekickt:', typeof r === 'string' ? r : JSON.stringify(r)))
  bot.on('error', (e) => log('Fehler:', e.message))
  bot.on('end', (r) => { bot._beendet = true; log('Verbindung beendet:', r); process.exit(0) })
}

main().catch(e => { log('Abbruch:', e.message); process.exit(1) })
