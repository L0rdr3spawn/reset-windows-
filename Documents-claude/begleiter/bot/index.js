// Ein Begleitbot-Prozess. Wird vom Manager gestartet (fork + IPC), geht aber auch allein:
//   node bot/index.js --server test --bot NotL0rdr3spawn --ich L0rdr3spawn
const fs = require('fs')
const path = require('path')
const mineflayer = require('mineflayer')
const { pathfinder } = require('mineflayer-pathfinder')
const { plugin: pvp } = require('mineflayer-pvp')
const { plugin: collectBlock } = require('mineflayer-collectblock')
const { einstellungenLaden } = require('./einstellungen')

const WURZEL = path.join(__dirname, '..')
const konfig = JSON.parse(fs.readFileSync(path.join(WURZEL, 'konfig.json'), 'utf8'))

function argumente () {
  const a = {}
  const argv = process.argv.slice(2)
  for (let i = 0; i < argv.length; i++) if (argv[i].startsWith('--')) a[argv[i].slice(2)] = argv[i + 1]
  if (process.env.BEGLEITER_START) Object.assign(a, JSON.parse(process.env.BEGLEITER_START))
  return a
}

const start = argumente()
const serverName = start.server ?? 'eigen'
// Profil aus konfig.json oder (bei host:port ohne Profil) vom Manager mitgegeben
const server = { ...(start.profil ?? konfig.server[serverName]), ...(start.host ? { host: start.host } : {}), ...(start.port ? { port: +start.port } : {}) }
if (!server.typ) throw new Error(`Unbekanntes Server-Profil "${serverName}"`)
const ich = start.ich ?? konfig.ich
const botAccount = start.bot ?? konfig.accounts.find(a => a.toLowerCase() !== ich.toLowerCase() && a.toLowerCase() !== konfig.ich.toLowerCase())
const verhalten = konfig.verhalten[server.typ]

// Test-Besitzer (nicht der Hauptaccount) bekommen eigene Einstellungen, damit Tests nie deine veraendern
const einst = einstellungenLaden(botAccount + (ich.toLowerCase() === konfig.ich.toLowerCase() ? '' : '-test'), konfig.standard)

let bot = null
let ctx = null
let absichtlichRaus = false
let reconnectTimer = null

function log (...args) {
  const zeile = `[${new Date().toLocaleTimeString('de-DE')}] ${args.join(' ')}`
  console.log(zeile)
  melden({ typ: 'log', zeile })
}

function melden (nachricht) {
  // Nach dem Beenden des Managers ist der Kanal zu - dann wuerde send() werfen (auch im Fehler-Handler)
  if (process.send && process.connected) process.send(nachricht)
}

function verbinden () {
  const ziel = server.weg === 'viaproxy' ? { host: '127.0.0.1', port: start.proxyPort ?? 25599 } : { host: server.host, port: server.port }
  log(`Verbinde ${botAccount} -> ${serverName} (${ziel.host}:${ziel.port}, Profil ${server.typ}) ...`)

  bot = mineflayer.createBot({
    ...ziel,
    username: botAccount,
    auth: server.offline ? 'offline' : 'microsoft',
    version: '26.1', // Mineflayer kann maximal 26.1; neuere Server uebersetzt ViaBackwards bzw. ViaProxy
    profilesFolder: path.join(WURZEL, 'daten', '.auth'),
    checkTimeoutInterval: 60000,
    onMsaCode (data) {
      log(`MICROSOFT-LOGIN fuer ${botAccount}: ${data.verification_uri} Code ${data.user_code}`)
      melden({ typ: 'login', account: botAccount, url: data.verification_uri, code: data.user_code })
    }
  })
  // minecraft-data kennt das Feature fuer 26.1 nicht -> Mineflayer schickt Zahlen aus alten Versionen
  // (Sprinten = 3/4 = Pferdesprung, Elytra = 8 = ungueltig -> Kick). Mit dem Namens-Mapper stimmt es.
  bot.once('inject_allowed', () => {
    const original = bot.supportFeature
    bot.supportFeature = f => f === 'entityActionUsesStringMapper' || original(f)
  })
  // Nur ein normaler Spieler: auf Paketebene gehen als Befehl ausschliesslich Privatnachrichten raus.
  // Alles andere (/tp, /give, /gamemode ...) wird verworfen - egal, welcher Codeteil es versucht.
  const erlaubt = /^(msg|tell|w|r)\s/i
  const schreiben = bot._client.write.bind(bot._client)
  // 26.3 wirft den Bot bei NaN/Unendlich in Position oder Blickwinkel sofort raus (invalid_player_movement).
  // Solche Werte nie senden: durch die letzten gueltigen ersetzen und die Ursache einmal protokollieren.
  const gueltig = { x: 0, y: 0, z: 0, yaw: 0, pitch: 0 }
  let nanGemeldet = 0
  const BEWEGUNG = new Set(['position', 'position_look', 'look', 'use_item'])
  const pruefen = (name, daten) => {
    const felder = name === 'use_item' ? [] : ['x', 'y', 'z', 'yaw', 'pitch']
    for (const f of felder) {
      if (!(f in daten)) continue
      if (Number.isFinite(daten[f])) { gueltig[f] = daten[f]; continue }
      if (Date.now() - nanGemeldet > 10000) {
        nanGemeldet = Date.now()
        log(`Ungueltiger Wert ${f}=${daten[f]} in ${name} ersetzt | ${new Error().stack.split('\n').slice(2, 9).map(z => z.trim()).join(' < ')}`)
      }
      daten[f] = gueltig[f]
      if (bot.entity) { if (f === 'yaw' || f === 'pitch') bot.entity[f] = 0; else bot.entity.position[f] = gueltig[f] }
    }
    if (name === 'use_item' && daten.rotation) {
      for (const k of ['x', 'y']) if (!Number.isFinite(daten.rotation[k])) { log(`Ungueltige Blickrichtung in use_item ersetzt`); daten.rotation[k] = 0 }
    }
  }
  bot._client.write = (name, daten) => {
    if ((name === 'chat_command' || name === 'chat_command_signed') && !erlaubt.test(String(daten?.command ?? ''))) {
      log(`BLOCKIERT (kein Server-Befehl erlaubt): /${daten?.command}`)
      return
    }
    if (BEWEGUNG.has(name) && daten) pruefen(name, daten)
    const r = schreiben(name, daten)
    // 26.3 erlaubt nur EIN Positionspaket pro Client-Tick (zurueckgesetzt durch "tick_end", das Mineflayer nie
    // schickt). Die Antwort auf einen Server-Teleport ist ein zweites -> Kick "invalid_player_movement".
    // Deshalb nach jedem Positionspaket das Tick-Ende melden, wie es ein normaler Client am Ende des Ticks tut.
    if (name === 'position' || name === 'position_look') schreiben('tick_end', {})
    return r
  }
  bot.loadPlugin(pathfinder)
  bot.loadPlugin(pvp)
  bot.loadPlugin(collectBlock)

  // Datengetriebene Register (Schadensarten, Verzauberungen, Traenke ...) kommen nur in der Konfigurationsphase;
  // die Nummern darin sind die, die der Server spaeter in Paketen benutzt
  const register = {}
  bot._client.on('registry_data', p => {
    const name = String(p.id).replace('minecraft:', '')
    register[name] = (p.entries ?? []).map(e => String(e.key).replace('minecraft:', ''))
  })

  bot.once('spawn', () => {
    ctx = require('./kern').erstellen({ bot, konfig, server, serverName, verhalten, einst, ich, log, melden, register, ausloggen })
    log(`Eingeloggt als ${bot.username}. Besitzer: ${ich}. Profil: ${server.typ}`)
    melden({ typ: 'online', bot: bot.username })
  })

  bot.on('kicked', grund => {
    const text = typeof grund === 'string' ? grund : JSON.stringify(grund)
    log('Gekickt:', text)
    // Dauerhafte Gruende: nicht alle 15 s neu versuchen, sondern sagen, was zu tun ist
    const hinweis = /online mode/i.test(text)
      ? 'Die Welt verlangt eine Microsoft-Anmeldung. Im Singleplayer: Pausenmenue -> "Bot holen" (Botlink-Mod), nicht der normale LAN-Knopf.'
      : /protocol detection failed|Connection refused|ECONNREFUSED/i.test(text)
        ? 'Der Server bzw. die LAN-Welt ist nicht mehr offen.'
        : /white-?list|not whitelisted|banned/i.test(text)
          ? 'Ich stehe nicht auf der Whitelist dieses Servers.'
          // Zweiter Prozess mit demselben Account: sonst werfen sich beide alle 15 s gegenseitig raus
          : /logged in from another location|duplicate_login/i.test(text)
            ? 'Mein Account wurde woanders eingeloggt.'
            : null
    if (hinweis) {
      melden({ typ: 'sagen', text: `Kann nicht rein: ${hinweis}` })
      absichtlichRaus = true
      melden({ typ: 'ausgeloggt', grund: hinweis })
    }
  })
  bot.on('error', err => log('Fehler:', err.message))
  bot.on('end', grund => {
    ctx?.beenden()
    ctx = null
    melden({ typ: 'offline', grund })
    if (absichtlichRaus) {
      log(`Ausgeloggt (${grund}).`)
      setTimeout(() => process.exit(0), 300)
      return
    }
    log(`Verbindung beendet (${grund}). Neuer Versuch in ${einst.reconnectSekunden}s.`)
    reconnectTimer = setTimeout(verbinden, einst.reconnectSekunden * 1000)
  })
}

// Absichtliches Ausloggen: kein Reconnect, Prozess endet
async function ausloggen (grund) {
  if (absichtlichRaus) return
  absichtlichRaus = true
  // Gehirn anhalten, sonst meldet logoutPruefen in den letzten Sekunden noch einen zweiten (falschen) Grund
  if (ctx) ctx.ausloggenLaeuft = true
  log(`Logge aus: ${grund}`)
  melden({ typ: 'ausgeloggt', grund })
  clearTimeout(reconnectTimer)
  try { bot?.quit(grund) } catch {}
  setTimeout(() => process.exit(0), 3000)
}

process.on('message', m => {
  if (m.typ === 'raus') return ausloggen(m.grund ?? 'auf Befehl')
  if (m.typ === 'eval') {
    // Nur zum Testen (konfig.debug oder BEGLEITER_DEBUG=1 vom Manager): JS im Bot-Kontext ausfuehren
    if (!konfig.debug && process.env.BEGLEITER_DEBUG !== '1') return melden({ typ: 'evalErgebnis', nr: m.nr, ergebnis: 'EVAL AUS' })
    if (!ctx) return melden({ typ: 'evalErgebnis', nr: m.nr, ergebnis: 'NICHT ONLINE' })
    const bot = ctx.bot // eslint-disable-line no-unused-vars
    Promise.resolve().then(() => eval(`(async () => { ${m.code} })()`)) // eslint-disable-line no-eval
      .then(r => melden({ typ: 'evalErgebnis', nr: m.nr, ergebnis: r }), e => melden({ typ: 'evalErgebnis', nr: m.nr, ergebnis: 'FEHLER ' + e.stack }))
    return
  }
  if (!ctx) return
  if (m.typ === 'befehl') ctx.befehle.ausfuehren(m.text, { kanal: 'api' })
  else if (m.typ === 'ereignis') ctx.wahr.modEreignis(m)
})
process.on('disconnect', () => ausloggen('Manager beendet'))
process.on('uncaughtException', e => log('Unerwarteter Fehler:', e.stack))
process.on('unhandledRejection', e => log('Unerwarteter Fehler (async):', e?.stack ?? e))

verbinden()
