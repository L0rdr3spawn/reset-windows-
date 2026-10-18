// Kommandozeile fuer den Begleiter. Startet den Manager bei Bedarf selbst.
//   bc join [server] [--bot X] [--ich Y] [--host h --port p]   Bot auf Server schicken
//   bc leave [bot]                                             Bot ausloggen
//   bc sag <text...>                                           Befehl an den Bot (wie im Chat, z.B. "!pvp an")
//   bc status | bc log [bot] | bc nachrichten | bc stop
const http = require('http')
const path = require('path')
const fs = require('fs')
const { spawn } = require('child_process')

const konfig = JSON.parse(fs.readFileSync(path.join(__dirname, 'konfig.json'), 'utf8'))
const PORT = +(process.env.BEGLEITER_API_PORT || konfig.api.port)
// Ein Test-Manager auf anderem Port schreibt in ein eigenes Log
const LOG = PORT === +konfig.api.port ? 'manager.log' : `manager-${PORT}.log`

function anfrage (methode, pfad, body) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port: PORT, method: methode, path: pfad, headers: { 'Content-Type': 'application/json' } }, res => {
      let s = ''
      res.on('data', d => { s += d })
      res.on('end', () => { try { resolve(JSON.parse(s)) } catch { resolve({ roh: s }) } })
    })
    req.on('error', reject)
    if (body) req.write(JSON.stringify(body))
    req.end()
  })
}

async function managerSicherstellen () {
  try { return await anfrage('GET', '/status') } catch {}
  const logDatei = fs.openSync(path.join(__dirname, 'daten', LOG), 'a')
  spawn(process.execPath, [path.join(__dirname, 'manager.js')], { detached: true, stdio: ['ignore', logDatei, logDatei], windowsHide: true }).unref()
  for (let i = 0; i < 40; i++) {
    await new Promise(resolve => setTimeout(resolve, 250))
    try { return await anfrage('GET', '/status') } catch {}
  }
  throw new Error(`Manager startet nicht (daten/${LOG} ansehen)`)
}

async function main () {
  fs.mkdirSync(path.join(__dirname, 'daten'), { recursive: true })
  const [cmd = 'status', ...rest] = process.argv.slice(2)
  const opt = {}
  const frei = []
  for (let i = 0; i < rest.length; i++) {
    if (rest[i].startsWith('--')) opt[rest[i].slice(2)] = rest[++i]
    else frei.push(rest[i])
  }
  if (cmd === 'stop') {
    try { await anfrage('POST', '/beenden') } catch { return console.log('Manager lief nicht.') }
    // Warten, bis er wirklich weg ist (er loggt die Bots erst aus) - sonst erwischt ein direkt folgendes
    // "bc status" noch den alten Manager, und danach laeuft keiner mehr
    for (let i = 0; i < 40; i++) {
      await new Promise(resolve => setTimeout(resolve, 250))
      try { await anfrage('GET', '/status') } catch { return console.log('Manager beendet.') }
    }
    return console.log('Manager reagiert nicht aufs Beenden.')
  }
  await managerSicherstellen()
  let r
  switch (cmd) {
    case 'join': r = await anfrage('POST', '/join', { server: frei[0], ...opt }); break
    case 'leave': r = await anfrage('POST', '/leave', { bot: frei[0] }); break
    case 'sag': r = await anfrage('POST', '/befehl', { text: frei.join(' '), bot: opt.bot }); break
    case 'log': r = await anfrage('GET', `/log?bot=${encodeURIComponent(frei[0] ?? '')}&n=${opt.n ?? 60}`); return console.log(r.log.join('\n'))
    case 'nachrichten': r = await anfrage('GET', '/nachrichten'); return r.nachrichten.forEach(n => console.log(`[${n.bot}] ${n.text}`))
    default: r = await anfrage('GET', '/status')
  }
  console.log(JSON.stringify(r, null, 2))
}

main().catch(e => { console.error(e.message); process.exit(1) })
