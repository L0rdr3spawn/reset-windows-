// Verbindet die bewaehrten Aufgaben aus dem alten mc-bot (Abbauen, Tunnel, Farmen, Craften ...) mit dem Kontext.
const fs = require('fs')
const path = require('path')
const { erstelleAufgaben } = require('./aufgaben')

function erstellen (ctx) {
  // Zuhause/Truhe je Server getrennt
  const datei = path.join(__dirname, '..', 'daten', `ort-${ctx.serverName}.json`)
  const ort = fs.existsSync(datei) ? JSON.parse(fs.readFileSync(datei, 'utf8')) : {}
  const aufgaben = erstelleAufgaben(ctx.bot, ctx.mcData, {
    log: ctx.log,
    fluestern: t => ctx.sagen(t, true), // Aufgaben melden sich nur auf Befehl (Ergebnis/Rueckfrage)
    bewegungNormal: ctx.bewegungNormal,
    bewegungArbeit: ctx.bewegungArbeit,
    ort,
    speichereOrt: () => fs.writeFileSync(datei, JSON.stringify(ort, null, 2)),
    beiFertig: () => {},
    lootPause: () => { ctx.lootPauseBis = Date.now() + 15000 }
  })
  aufgaben.ort = ort
  return aufgaben
}

module.exports = { erstellen }
