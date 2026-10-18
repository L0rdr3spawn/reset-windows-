// Bot-Manager: startet/stoppt Bot-Prozesse, verwaltet ViaProxy, bietet eine lokale HTTP-Schnittstelle
// (nur 127.0.0.1) fuer die Mod, die Kommandozeile (bc.js) und alles andere.
const http = require('http')
const fs = require('fs')
const path = require('path')
const { fork, execSync } = require('child_process')
const viaproxy = require('./viaproxy')

const WURZEL = __dirname
const konfigLaden = () => JSON.parse(fs.readFileSync(path.join(WURZEL, 'konfig.json'), 'utf8'))
const PORT = +(process.env.BEGLEITER_API_PORT || konfigLaden().api.port)
// /eval nur zum Testen: konfig.debug oder BEGLEITER_DEBUG=1 (wird per Umgebung an die Bots weitergereicht)
const debugAn = () => process.env.BEGLEITER_DEBUG === '1' || !!konfigLaden().debug

const bots = new Map() // account -> { proc, status, log[], server, online }
const nachrichten = [] // { nr, zeit, bot, typ, text, ... } fuer die Mod
let nachrichtNr = 0

function merken (bot, eintrag) {
  nachrichten.push({ nr: ++nachrichtNr, zeit: Date.now(), bot, ...eintrag })
  if (nachrichten.length > 500) nachrichten.shift()
}

function log (...a) { console.log(`[${new Date().toLocaleTimeString('de-DE')}] [manager]`, ...a) }

// TYPESAFE_API_KEY fuer Jev: Umgebung, sonst Benutzer-Umgebung aus der Registry (neue Werte ohne Neuanmeldung)
function typesafeKey () {
  if (process.env.TYPESAFE_API_KEY) return process.env.TYPESAFE_API_KEY
  try {
    const out = execSync('reg query HKCU\\Environment /v TYPESAFE_API_KEY', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
    return out.match(/TYPESAFE_API_KEY\s+REG_\w+\s+(\S+)/)?.[1]
  } catch { return undefined }
}

// Profil zu host:port aus konfig.json suchen (localhost = 127.0.0.1, Standardport 25565)
function profilFuer (konfig, host, port) {
  const norm = h => String(h ?? '').toLowerCase().replace(/^localhost$/, '127.0.0.1')
  const p = +(port ?? 25565)
  return Object.entries(konfig.server).find(([, s]) => s.host && norm(s.host) === norm(host) && +(s.port ?? 25565) === p)?.[0] ?? null
}

// "host", "host:port" oder Profilname -> { server, profil, host, port }
function zielAufloesen (konfig, { server, host, port, adresse, offline }) {
  if (adresse && !host) {
    const m = String(adresse).trim().match(/^\[?([^\]]+?)\]?(?::(\d+))?$/)
    host = m?.[1]
    port = port ?? (m?.[2] ? +m[2] : undefined)
  }
  if (server && konfig.server[server]) return { server, profil: konfig.server[server], host, port }
  if (server && !host) throw new Error(`Unbekanntes Server-Profil "${server}" (vorhanden: ${Object.keys(konfig.server).join(', ')})`)
  if (!host) return { server: 'eigen', profil: konfig.server.eigen }
  const bekannt = profilFuer(konfig, host, port)
  if (bekannt) return { server: bekannt, profil: konfig.server[bekannt] }
  // Unbekannter Server: als fremder Server behandeln, ueber ViaProxy (uebersetzt jede Version), sonst direkt
  const weg = viaproxy.vorhanden() ? 'viaproxy' : 'direkt'
  const profil = { host, port: +(port ?? 25565), typ: 'fremd', weg, ...(offline ? { offline: true } : {}) }
  return { server: `${host}:${profil.port}`, profil, host, port: profil.port }
}

async function botStarten (body) {
  const konfig = konfigLaden()
  let { ich, bot } = body
  const { server, profil, host, port } = zielAufloesen(konfig, body)
  ich = ich ?? konfig.ich
  // Nie automatisch den Hauptaccount (konfig.ich) als Bot nehmen - auch nicht, wenn ein Test-Besitzer spielt
  bot = bot ?? konfig.accounts.find(a => a.toLowerCase() !== ich.toLowerCase() && a.toLowerCase() !== konfig.ich.toLowerCase())
  if (!bot) throw new Error('Kein Bot-Account frei (accounts in konfig.json)')
  const alt = bots.get(bot)
  if (alt?.proc?.connected && alt.raus) {
    // Wird gerade ausgeloggt (z.B. "Bot rausschicken" und gleich wieder "Bot holen"): kurz warten
    await new Promise(resolve => { alt.proc.once('exit', resolve); setTimeout(resolve, 8000) })
  }
  if (bots.get(bot)?.proc?.connected) throw new Error(`${bot} laeuft schon`)

  let proxyPort
  if (profil.weg === 'viaproxy') {
    const ziel = { host: host ?? profil.host, port: port ?? profil.port ?? 25565, offline: !!profil.offline }
    if (profil.lan && !host) Object.assign(ziel, await viaproxy.lanWeltFinden(8000))
    proxyPort = await viaproxy.starten(ziel, bot, log)
  }

  const start = { server, profil, ich, bot, host, port, proxyPort }
  const env = { ...process.env, BEGLEITER_START: JSON.stringify(start) }
  const key = typesafeKey()
  if (key) env.TYPESAFE_API_KEY = key
  // windowsHide: sonst bekommt jeder Bot ein eigenes Konsolenfenster (der Manager hat keins) - schliesst man
  // das, stirbt der Bot mit 0xC000013A
  const proc = fork(path.join(WURZEL, 'bot', 'index.js'), [], { env, stdio: ['ignore', 'pipe', 'pipe', 'ipc'], windowsHide: true })
  const eintrag = { proc, status: null, log: [], server, online: false, start }
  // Ohne Listener wuerde ein fehlgeschlagenes send() (Kanal gerade zu) den ganzen Manager abstuerzen lassen
  proc.on('error', e => log(`${bot}: ${e.message}`))
  bots.set(bot, eintrag)
  const zeile = z => { eintrag.log.push(z); if (eintrag.log.length > 300) eintrag.log.shift() }
  proc.stdout.on('data', d => d.toString().split('\n').filter(Boolean).forEach(z => { zeile(z); process.stdout.write(`[${bot}] ${z}\n`) }))
  proc.stderr.on('data', d => d.toString().split('\n').filter(Boolean).forEach(z => { zeile('FEHLER ' + z); process.stderr.write(`[${bot}] ${z}\n`) }))
  proc.on('message', m => {
    if (m.typ === 'status') eintrag.status = m.status
    else if (m.typ === 'online') { eintrag.online = true; merken(bot, { typ: 'online', text: `${bot} ist auf ${server}` }) }
    else if (m.typ === 'offline') { eintrag.online = false }
    else if (m.typ === 'sagen') merken(bot, { typ: 'sagen', text: m.text })
    else if (m.typ === 'login') merken(bot, { typ: 'login', text: `Microsoft-Login fuer ${m.account}: ${m.url} Code ${m.code}`, url: m.url, code: m.code })
    else if (m.typ === 'ausgeloggt') merken(bot, { typ: 'ausgeloggt', text: `${bot} hat sich ausgeloggt: ${m.grund}` })
    else if (m.typ === 'inventar' || m.typ === 'angebot') merken(bot, m)
    else if (m.typ === 'inventarStand') eintrag.inventar = { ...m.stand, zeit: Date.now() }
  })
  proc.on('exit', code => {
    log(`${bot} beendet (Code ${code})`)
    eintrag.online = false
    eintrag.proc = null
    merken(bot, { typ: 'beendet', text: `${bot}-Prozess beendet` })
    if (![...bots.values()].some(b => b.proc)) viaproxy.stoppen()
  })
  log(`Starte ${bot} -> ${server} (Besitzer ${ich})`)
  return { bot, server }
}

function botRaus (name, grund = 'auf Befehl') {
  const liste = name ? [bots.get(name)].filter(Boolean) : [...bots.values()]
  for (const b of liste) if (b.proc?.connected) { b.raus = true; b.proc.send({ typ: 'raus', grund }) }
  return liste.length
}

// Bots, deren Besitzer der Hauptaccount ist (konfig.ich). Laufen daneben Test-Bots, bekommen die nichts von deiner
// Mod ab - und du siehst ihre Meldungen nicht.
function hauptBots () {
  const ich = konfigLaden().ich.toLowerCase()
  return [...bots].filter(([, b]) => b.start?.ich?.toLowerCase() === ich)
}
function botsFuer (name, besitzer) {
  if (name) return [bots.get(name)].filter(Boolean)
  if (besitzer) return [...bots.values()].filter(b => b.start?.ich?.toLowerCase() === String(besitzer).toLowerCase())
  const haupt = hauptBots()
  return haupt.length ? haupt.map(([, b]) => b) : [...bots.values()]
}

function anBots (name, nachricht, besitzer) {
  const liste = botsFuer(name, besitzer)
  for (const b of liste) if (b.proc?.connected) b.proc.send(nachricht)
  return liste.length
}

// ---------------------------------------------------------------- HTTP
function antwort (res, code, daten) {
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(daten))
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x')
  // Nur lokale Programme (Mod, bc.js), nie Webseiten: ein Browser schickt immer "Origin" mit - sonst koennte
  // jede geoeffnete Seite per POST auf 127.0.0.1 den Bot steuern. POST nur als JSON (erzwingt beim Browser
  // eine CORS-Vorabfrage, die hier nie erlaubt wird).
  // Host pruefen gegen DNS-Rebinding (fremde Domain, die auf 127.0.0.1 zeigt, darf auch per GET nichts lesen)
  const host = String(req.headers.host ?? '').replace(/:\d+$/, '').toLowerCase()
  if ((host && !['127.0.0.1', 'localhost', '[::1]'].includes(host)) || req.headers.origin || (req.method === 'POST' && !/application\/json/i.test(req.headers['content-type'] ?? ''))) {
    return antwort(res, 403, { fehler: 'nur lokale Programme' })
  }
  let body = {}
  if (req.method === 'POST') {
    const roh = await new Promise(resolve => { let s = ''; req.on('data', d => { s += d }); req.on('end', () => resolve(s)) })
    try { body = roh ? JSON.parse(roh) : {} } catch { return antwort(res, 400, { fehler: 'kein JSON' }) }
  }
  try {
    switch (`${req.method} ${url.pathname}`) {
      case 'GET /status':
        return antwort(res, 200, {
          bots: [...hauptBots(), ...[...bots].filter(([n]) => !hauptBots().some(([h]) => h === n))]
            .map(([name, b]) => ({ name, server: b.server, laeuft: !!b.proc, online: b.online, status: b.status })),
          server: Object.keys(konfigLaden().server)
        })
      case 'GET /nachrichten': {
        const seit = +(url.searchParams.get('seit') ?? 0)
        // Laeuft ein Bot fuer den Hauptaccount, nur dessen Meldungen (keine von Test-Bots)
        const haupt = new Set(hauptBots().map(([n]) => n))
        return antwort(res, 200, { nr: nachrichtNr, nachrichten: nachrichten.filter(n => n.nr > seit && (!haupt.size || haupt.has(n.bot))) })
      }
      case 'GET /log': {
        const b = bots.get(url.searchParams.get('bot')) ?? [...bots.values()][0]
        return antwort(res, 200, { log: b?.log.slice(-(+(url.searchParams.get('n') ?? 60))) ?? [] })
      }
      case 'GET /inventar': {
        const name = url.searchParams.get('bot')
        const b = (name && bots.get(name)) || hauptBots().map(([, x]) => x).find(x => x.online) || [...bots.values()].find(x => x.online) || [...bots.values()][0]
        if (!b?.inventar) return antwort(res, 404, { fehler: 'kein Inventar (Bot nicht online?)' })
        return antwort(res, 200, { bot: [...bots].find(([, x]) => x === b)[0], ...b.inventar })
      }
      case 'POST /join': return antwort(res, 200, await botStarten(body))
      case 'POST /leave': return antwort(res, 200, { anzahl: botRaus(body.bot, body.grund) })
      case 'POST /befehl': return antwort(res, 200, { anzahl: anBots(body.bot, { typ: 'befehl', text: body.text }) })
      // Nur "zustand" traegt den Namen des Spielers (-> dessen Bots); bei "ziel" ist name das Ziel-Wesen
      case 'POST /ereignis': return antwort(res, 200, { anzahl: anBots(body.bot, { ...body, typ: 'ereignis' }, body.art === 'zustand' ? body.name : undefined) })
      case 'POST /eval': {
        if (!debugAn()) return antwort(res, 403, { fehler: 'eval aus (konfig.debug oder BEGLEITER_DEBUG=1)' })
        const b = bots.get(body.bot) ?? [...bots.values()].find(x => x.proc?.connected)
        if (!b?.proc?.connected) return antwort(res, 404, { fehler: 'kein Bot' })
        const nr = Math.random()
        const proc = b.proc
        const ergebnis = await new Promise(resolve => {
          let timer = null
          const ende = r => { proc.off('message', h); proc.off('exit', weg); clearTimeout(timer); resolve(r) }
          const h = m => { if (m.typ === 'evalErgebnis' && m.nr === nr) ende(m.ergebnis) }
          const weg = () => ende('BOT BEENDET')
          proc.on('message', h)
          proc.once('exit', weg)
          proc.send({ typ: 'eval', nr, code: body.code })
          timer = setTimeout(() => ende('TIMEOUT'), body.timeout ?? 15000)
        })
        return antwort(res, 200, { ergebnis })
      }
      case 'POST /beenden':
        antwort(res, 200, { ok: true })
        botRaus(null, 'Manager beendet')
        setTimeout(() => process.exit(0), 3500)
        return
      default: return antwort(res, 404, { fehler: 'unbekannt' })
    }
  } catch (e) {
    log('Fehler:', e.message)
    return antwort(res, 500, { fehler: e.message })
  }
})

server.on('error', e => {
  if (e.code === 'EADDRINUSE') { log(`Port ${PORT} belegt - laeuft der Manager schon?`); process.exit(1) }
  throw e
})
server.listen(PORT, '127.0.0.1', () => log(`Bereit auf http://127.0.0.1:${PORT}`))
process.on('SIGINT', () => { botRaus(null, 'Manager beendet'); setTimeout(() => process.exit(0), 3000) })
