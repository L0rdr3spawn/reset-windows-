// ViaProxy: uebersetzt zwischen Mineflayer (26.1) und beliebigen Serverversionen (auch 26.3-Singleplayer per LAN).
// Laeuft lokal auf 127.0.0.1:25599. Fuer Online-Server meldet sich ViaProxy selbst mit dem Bot-Account an
// (auth-method ACCOUNT) - dafuer muss der Account einmal in ViaProxy eingeloggt werden (siehe LIESMICH).
const fs = require('fs')
const path = require('path')
const dgram = require('dgram')
const { spawn } = require('child_process')

const ORDNER = path.join(__dirname, 'viaproxy')
// Eigener Port fuer einen Test-Manager (BEGLEITER_VIAPROXY_PORT), sonst teilen sich beide Manager einen Proxy
const PORT = +(process.env.BEGLEITER_VIAPROXY_PORT || 25599)
let proc = null
let aktuellesZiel = null

function java () {
  const prism = path.join(process.env.APPDATA ?? '', 'PrismLauncher', 'java', 'java-runtime-epsilon', 'bin', 'java.exe')
  return fs.existsSync(prism) ? prism : 'java'
}

function jar () {
  if (!fs.existsSync(ORDNER)) return null
  return fs.readdirSync(ORDNER).filter(f => /^ViaProxy-.*\.jar$/.test(f) && !f.includes('java8')).map(f => path.join(ORDNER, f))[0] ?? null
}

async function starten (ziel, account, log) {
  const j = jar()
  if (!j) throw new Error('ViaProxy fehlt (viaproxy/ViaProxy-*.jar) - fuer fremde Server und Singleplayer noetig')
  const zielText = `${ziel.host}:${ziel.port}`
  if (proc && aktuellesZiel === zielText) return PORT
  stoppen()
  aktuellesZiel = zielText
  const args = ['-jar', j, 'cli',
    '--bind-address', `127.0.0.1:${PORT}`,
    '--target-address', zielText,
    '--auth-method', ziel.offline ? 'NONE' : 'ACCOUNT',
    '--proxy-online-mode', 'false']
  log(`ViaProxy -> ${zielText}`)
  const p = spawn(java(), args, { cwd: ORDNER, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true })
  proc = p
  const bereit = new Promise((resolve, reject) => {
    const t = setTimeout(() => resolve(), 20000)
    const pruefen = d => {
      const s = d.toString()
      for (const z of s.split('\n').filter(Boolean)) log(`[ViaProxy] ${z.trim()}`)
      if (/started|listening|bound/i.test(s)) { clearTimeout(t); resolve() }
    }
    // z.B. java fehlt: ohne Listener stuerzt sonst der ganze Manager ab
    p.on('error', e => { clearTimeout(t); if (proc === p) { proc = null; aktuellesZiel = null } reject(e) })
    p.stdout.on('data', pruefen)
    p.stderr.on('data', pruefen)
    // Nur den eigenen Prozess austragen - ein alter, gerade beendeter darf den neuen nicht vergessen lassen
    p.on('exit', c => { clearTimeout(t); if (proc === p) { proc = null; aktuellesZiel = null } reject(new Error(`ViaProxy beendet (${c})`)) })
  })
  await bereit
  return PORT
}

function stoppen () {
  if (proc) { proc.kill(); proc = null; aktuellesZiel = null }
}

// Offene LAN-Welten kuendigen sich per Multicast an ([MOTD]..[/MOTD][AD]port[/AD])
function lanWeltFinden (timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    const sock = dgram.createSocket({ type: 'udp4', reuseAddr: true })
    let fertig = false
    const schliessen = () => { if (fertig) return false; fertig = true; clearTimeout(timer); try { sock.close() } catch {} return true }
    sock.on('error', e => { if (schliessen()) reject(e) })
    const timer = setTimeout(() => { if (schliessen()) reject(new Error('Keine offene LAN-Welt gefunden - im Spiel "Im LAN oeffnen"')) }, timeoutMs)
    sock.on('message', (msg, rinfo) => {
      const m = msg.toString().match(/\[MOTD\](.*?)\[\/MOTD\]\[AD\](\d+)\[\/AD\]/)
      if (!m || !schliessen()) return
      resolve({ host: rinfo.address === '0.0.0.0' ? '127.0.0.1' : rinfo.address, port: +m[2], motd: m[1] })
    })
    sock.bind(4445, () => { try { sock.addMembership('224.0.2.60') } catch {} })
  })
}

module.exports = { starten, stoppen, lanWeltFinden, PORT, vorhanden: () => !!jar() }
