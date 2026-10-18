// Einstellungen je Bot-Account: Standardwerte aus konfig.json, Aenderungen per Befehl ueberleben Neustarts.
// Gespeichert wird nur der jeweils geaenderte Schluessel (Datei lesen, einen Wert setzen, schreiben) -
// so kann ein Prozess mit veralteten Werten im Speicher nie die ganze Datei zurueckschreiben.
const fs = require('fs')
const path = require('path')

// Nur fuer diese Sitzung, nie gespeichert: der Modus (folgen/stehen/wache ...) - sonst steht der Bot nach
// einem "stop" oder Baritone-Befehl beim naechsten Einloggen einfach herum
const FLUECHTIG = new Set(['modus'])

function einstellungenLaden (account, standard) {
  const datei = path.join(__dirname, '..', 'daten', `einstellungen-${account}.json`)
  const lesen = () => {
    try {
      const d = JSON.parse(fs.readFileSync(datei, 'utf8'))
      for (const k of FLUECHTIG) delete d[k]
      return d
    } catch { return {} }
  }
  const werte = { ...standard, ...lesen() }
  return new Proxy(werte, {
    set (ziel, key, wert) {
      ziel[key] = wert
      if (FLUECHTIG.has(key)) return true
      const gespeichert = lesen()
      if (JSON.stringify(wert) === JSON.stringify(standard[key])) delete gespeichert[key]
      else gespeichert[key] = wert
      fs.mkdirSync(path.dirname(datei), { recursive: true })
      // Erst in eine Nebendatei, dann umbenennen: eine halb geschriebene Datei wuerde beim naechsten Lesen
      // als {} gelten und mit dem naechsten Wert alle anderen Einstellungen loeschen
      fs.writeFileSync(datei + '.tmp', JSON.stringify(gespeichert, null, 2))
      try { fs.renameSync(datei + '.tmp', datei) } catch { fs.writeFileSync(datei, JSON.stringify(gespeichert, null, 2)) }
      return true
    }
  })
}

module.exports = { einstellungenLaden }
