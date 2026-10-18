// Befehle vom Besitzer: Chat (nur eigener Server), Fluestern, Manager-API/Mod. Unbekanntes geht an Jev (freie Sprache).
const { Vec3 } = require('vec3')
const { ROHSTOFFE, UNENDLICH, RESERVE, mengeLesen } = require('./aufgaben')

// Verzauberungen auf Deutsch fuer die Inventar-Anzeige
const VERZ = {
  sharpness: 'Schaerfe', smite: 'Bann', bane_of_arthropods: 'Nemesis der Gliederfuesser', knockback: 'Rueckstoss', fire_aspect: 'Verbrennung',
  looting: 'Pluenderung', sweeping_edge: 'Schwungkraft', protection: 'Schutz', fire_protection: 'Feuerschutz', blast_protection: 'Explosionsschutz',
  projectile_protection: 'Schusssicher', feather_falling: 'Federfall', thorns: 'Dornen', respiration: 'Atmung', aqua_affinity: 'Wasseraffinitaet',
  depth_strider: 'Wasserlaeufer', frost_walker: 'Eislaeufer', soul_speed: 'Seelenlaeufer', swift_sneak: 'Huschen', unbreaking: 'Haltbarkeit',
  mending: 'Reparatur', efficiency: 'Effizienz', fortune: 'Glueck', silk_touch: 'Behutsamkeit', power: 'Staerke', punch: 'Schlag', flame: 'Flamme',
  infinity: 'Unendlichkeit', multishot: 'Mehrfachschuss', piercing: 'Durchschuss', quick_charge: 'Schnellladen', loyalty: 'Treue',
  riptide: 'Sog', channeling: 'Entladung', impaling: 'Harpune', density: 'Dichte', breach: 'Bresche', wind_burst: 'Windstoss', lunge: 'Ausfall',
  binding_curse: 'Fluch der Bindung', vanishing_curse: 'Fluch des Verschwindens'
}
const ROEMISCH = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

const HILFE = [
  '!folge !stop !wache | !kampf an/aus | !pvp an/aus | !greif [name] (ohne Name: was du anschaust) | !lass',
  '!freund <name> | !freund weg <name> | !freunde | !logout <leben> | !logout hunger <n> | !logout tod an/aus | !logout uebermacht <n> | !logout aus | !raus',
  '!tunnel [laenge] [BxH] | !treppe <y> | !farm [immer] | !sammel <rohstoff> [menge] | !such <block> [menge] | !heim | !nachhause | !lager',
  '!inv (Inventar + Verzauberungen) | !gib <item> [menge] (behaelt immer 2 Totems) | !nimm an/aus (Sachen aufheben)',
  '!mace/!speer/!elytra an/aus | !flieg [aus] | !land | !status | !inv | !selbst | !b <baritone-befehl> (!b help) | oder einfach normal sagen'
]

function erstellen (ctx) {
  const { bot, einst, log, wahr, inv } = ctx
  const s = t => ctx.sagen(t, true) // Antworten auf Befehle gehen per /msg an den Besitzer
  const anAus = (arg, jetzt) => arg === 'an' || arg === 'on' ? true : arg === 'aus' || arg === 'off' ? false : !jetzt

  bot.on('chat', (user, text) => {
    if (user?.toLowerCase() !== ctx.ich.toLowerCase()) return
    if (!ctx.verhalten.oeffentlicheBefehle) return // auf fremden Servern nie im offenen Chat reagieren
    ausfuehren(text, { kanal: 'chat' })
  })
  bot.on('whisper', (user, text) => {
    if (user?.toLowerCase() !== ctx.ich.toLowerCase()) return
    ausfuehren(text, { kanal: 'fluestern' })
  })

  function ausfuehren (roh, { kanal }) {
    const text = roh.trim()
    if (!text || text.startsWith('#')) return // #... sind Arena-Befehle, nicht fuer den Bot
    ctx.letzterKanal = kanal
    log(`Befehl (${kanal}): ${text}`)
    if (!text.startsWith('!')) {
      if (kanal === 'chat' && !ctx.verhalten.jevImChat) return
      return ctx.sprache.verstehen(text, kanal !== 'chat')
    }
    const [cmd, ...args] = text.slice(1).split(/\s+/)
    const a = args.map(x => x.toLowerCase())
    const f = BEFEHLE[cmd.toLowerCase()]
    if (!f) return ctx.sprache.verstehen(text.slice(1), true)
    try {
      f(a, args)
    } catch (e) {
      log('Befehl fehlgeschlagen:', e.stack)
      s(`Fehler: ${e.message}`)
    }
  }

  // Was schaut der Besitzer an? (kleinster Winkel zur Blickrichtung, max 32 Bloecke)
  function angeschaut () {
    const b = ctx.besitzer()
    if (!b) return null
    const blick = new Vec3(-Math.sin(b.yaw) * Math.cos(b.pitch), Math.sin(b.pitch), -Math.cos(b.yaw) * Math.cos(b.pitch))
    const auge = b.position.offset(0, 1.62, 0)
    let best = null
    let bestWinkel = 0.25
    for (const e of Object.values(bot.entities)) {
      if (e === b || e === bot.entity || !wahr.lebendig(e)) continue
      const d = e.position.offset(0, (e.height ?? 1) / 2, 0).minus(auge)
      const len = d.norm()
      if (len > 32 || len < 0.5) continue
      const winkel = Math.acos(Math.max(-1, Math.min(1, d.dot(blick) / len)))
      if (winkel < bestWinkel) { best = e; bestWinkel = winkel }
    }
    return best
  }

  const aufgabe = (auftrag, text) => {
    if (einst.modus === 'stehen' || einst.modus === 'wache') einst.modus = 'folgen'
    ctx.aufgaben.starten(auftrag)
    s(text)
  }

  const BEFEHLE = {
    hilfe: () => HILFE.forEach(z => s(z)),
    folge: () => { einst.modus = 'folgen'; ctx.aufgaben.stoppen(); s('Folge dir.') },
    komm: () => BEFEHLE.folge(),
    stop: () => {
      einst.modus = 'stehen'
      ctx.aufgaben.stoppen()
      ctx.kampf.manuellSetzen(null)
      ctx.bew.stehen()
      s('Bleibe stehen.')
    },
    bleib: () => BEFEHLE.stop(),
    wache: () => { ctx.aufgaben.stoppen(); ctx.bew.wacheSetzen(); s('Halte hier Wache.') },
    selbst: () => {
      if (!ctx.sprache.jevAktiv) return s('Selbststaendig geht nur mit TYPESAFE_API_KEY.')
      einst.modus = 'selbst'
      s('Arbeite selbststaendig. !folge oder !stop beendet das.')
    },

    kampf: (a) => { einst.kampf = anAus(a[0], einst.kampf); if (!einst.kampf) ctx.kampf.stoppen(); s(`Kampf ${einst.kampf ? 'an' : 'aus'}.`) },
    pvp: (a) => { einst.pvp = anAus(a[0], einst.pvp); s(`PvP ${einst.pvp ? 'an: ich greife an, was du angreifst (ausser Freunde)' : 'aus: nur Monster und Notwehr'}.`) },
    greif: (a, orig) => {
      if (orig[0]) {
        ctx.kampf.manuellSetzen(orig[0])
        return s(`Greife ${orig[0]} an.`)
      }
      const e = angeschaut()
      if (!e) return s('Ich sehe nicht, was du anschaust.')
      ctx.kampf.manuellEntity(e)
      s(`Greife ${wahr.name(e)} an.`)
    },
    lass: () => { ctx.kampf.manuellSetzen(null); s('Lasse ab.') },

    freund: (a, orig) => {
      if (a[0] === 'weg' || a[0] === 'entfernen') {
        const n = orig[1]
        einst.freunde = einst.freunde.filter(x => x.toLowerCase() !== n?.toLowerCase())
        return s(`${n} ist kein Freund mehr.`)
      }
      if (!orig[0]) return BEFEHLE.freunde()
      if (!einst.freunde.some(x => x.toLowerCase() === orig[0].toLowerCase())) einst.freunde = [...einst.freunde, orig[0]]
      s(`${orig[0]} ist jetzt Freund. Den greife ich nicht an (ausser im Notfall).`)
    },
    freunde: () => s(einst.freunde.length ? `Freunde: ${einst.freunde.map(f => f + (wahr.gesperrt(f) ? ' (gesperrt)' : '')).join(', ')}` : 'Keine Freunde eingetragen.'),

    logout: (a) => {
      const zahl = a.map(Number).find(n => !isNaN(n))
      if (a[0] === 'aus') { einst.logoutLeben = 0; einst.logoutHunger = 0; einst.logoutBeiTodBesitzer = false; einst.logoutBeiUebermacht = 0; return s('Automatisches Ausloggen komplett aus.') }
      if (a[0] === 'hunger' && zahl != null) { einst.logoutHunger = zahl; return s(`Logge aus, wenn Hunger <= ${zahl} und nichts zu essen da ist.`) }
      if (a[0] === 'tod') { einst.logoutBeiTodBesitzer = anAus(a[1], einst.logoutBeiTodBesitzer); return s(`Ausloggen wenn du stirbst: ${einst.logoutBeiTodBesitzer ? 'an' : 'aus'}.`) }
      if ((a[0] === 'uebermacht' || a[0] === 'übermacht') && zahl != null) { einst.logoutBeiUebermacht = zahl; return s(zahl ? `Logge aus ab ${zahl} Gegnern.` : 'Uebermacht-Logout aus.') }
      if (zahl != null) { einst.logoutLeben = zahl; return s(zahl ? `Logge aus bei ${zahl} Leben oder weniger (${zahl / 2} Herzen).` : 'Leben-Logout aus.') }
      s(`Logout: Leben <= ${einst.logoutLeben}, Hunger <= ${einst.logoutHunger}, wenn du stirbst: ${einst.logoutBeiTodBesitzer ? 'ja' : 'nein'}, Uebermacht ab ${einst.logoutBeiUebermacht || 'aus'}.`)
    },
    raus: () => ctx.ausloggen('auf Befehl'),

    tunnel: (a) => {
      const laenge = a.map(Number).find(n => n > 0) ?? 32
      const mass = a.find(x => /^\d+x\d+$/.test(x))
      const [breite, hoehe] = mass ? mass.split('x').map(Number) : [1, 2]
      const b = ctx.besitzer()
      aufgabe({ art: 'tunnel', menge: laenge, breite, hoehe, yaw: b?.yaw }, `Grabe einen ${breite}x${hoehe}-Gang, ${laenge} lang${b ? ' in deine Blickrichtung' : ''}.`)
    },
    gang: (a) => BEFEHLE.tunnel(a),
    treppe: (a) => {
      const y = a.map(Number).find(n => !isNaN(n))
      aufgabe({ art: 'treppe', zielY: y ?? Math.floor(bot.entity.position.y) - 20, yaw: ctx.besitzer()?.yaw }, `Grabe eine Treppe bis Y ${y ?? 'minus 20'}.`)
    },
    farm: (a) => {
      if (a[0] === 'aus' || a[0] === 'off' || a[0] === 'stop') {
        if (ctx.aufgaben.aktuell()?.art === 'farmen') ctx.aufgaben.stoppen()
        return s('Farmen aus.')
      }
      const immer = a.includes('immer') || a[0] === 'an' || a[0] === 'on'
      aufgabe({ art: 'farmen', menge: immer ? UNENDLICH : 1 }, `Farme${immer ? ' ohne Ende (/bot farm aus beendet es)' : ''}.`)
    },
    baritone: (a, orig) => ctx.baritone.ausfuehren(orig.join(' ')),
    b: (a, orig) => ctx.baritone.ausfuehren(orig.join(' ')),
    sammel: (a) => {
      const r = a.find(x => ROHSTOFFE[x])
      if (!r) return s(`!sammel <${Object.keys(ROHSTOFFE).join('|')}> [menge|unendlich]`)
      const menge = a.includes('unendlich') ? UNENDLICH : (mengeLesen(a.join(' ')) ?? ROHSTOFFE[r].standard)
      aufgabe({ art: 'abbauen', blockIds: ctx.aufgaben.blockIdsGruppe(r), name: ROHSTOFFE[r].name, menge, setzlinge: r === 'holz' }, `Baue ${ROHSTOFFE[r].name} ab.`)
    },
    heim: () => heimSetzen(),
    nachhause: () => ctx.aufgaben.ort.heim ? aufgabe({ art: 'heim' }, 'Gehe nach Hause.') : s('Kein Zuhause gesetzt (!heim).'),
    lager: () => ctx.aufgaben.ort.truhe ? aufgabe({ art: 'einlagern' }, 'Lagere ein.') : s('Keine Truhe gesetzt (!heim an einer Truhe).'),
    gib: (a) => {
      const posFn = () => { const m = ctx.wahr.besitzerModPos(); return m ? { x: m.x, y: m.y, z: m.z } : null }
      if (a[0] === 'slot') {
        // !gib slot <nr> [menge] [item]: genau dieser Platz (Klick in der Inventar-Oberflaeche der Mod)
        const slot = Number(a[1])
        const it = bot.inventory.slots[slot]
        if (!it) return s('Der Platz ist leer.')
        const zahl = Number(a[2]) > 0 ? Number(a[2]) : it.count
        return aufgabe({ art: 'geben', an: ctx.ich, slot, item: a[3] ?? it.name, itemName: it.name, menge: zahl, reserve: RESERVE[it.name] ?? 0, posFn },
          `Bringe dir ${zahl}x ${it.displayName}.`)
      }
      const suche = a.find(x => isNaN(Number(x)) && x !== 'alles' && x !== 'all')
      const zahl = a.map(Number).find(n => !isNaN(n) && n > 0)
      const items = inv.items()
      const item = suche ? (items.find(i => i.name === suche) ?? items.find(i => i.name.includes(suche)) ?? items.find(i => i.displayName.toLowerCase().includes(suche)))?.name : null
      if (suche && !item) return s(`Ich habe kein ${suche}.`)
      const reserve = item ? (RESERVE[item] ?? 0) : 0
      if (item && inv.anzahl(item) <= reserve) return s(`Von ${item} habe ich nur ${inv.anzahl(item)} - die behalte ich.`)
      aufgabe({ art: 'geben', an: ctx.ich, item, itemName: item ?? 'alles', menge: zahl ?? (item ? 1 : UNENDLICH), reserve, posFn },
        item ? `Bringe dir ${zahl ?? 1}x ${item}.` : 'Bringe dir alles (ausser meinen 2 Totems).')
    },

    mace: (a) => { einst.mace = anAus(a[0], einst.mace !== false); s(`Mace ${einst.mace ? 'an' : 'aus'}.`) },
    speer: (a) => { einst.speer = anAus(a[0], einst.speer !== false); s(`Speer ${einst.speer ? 'an' : 'aus'}.`) },
    elytra: (a) => { einst.elytra = anAus(a[0], einst.elytra !== false); s(`Elytra ${einst.elytra ? 'an' : 'aus'}.`) },
    flieg: (a) => {
      if (a[0] === 'aus' || a[0] === 'off') { ctx.elytra.landen(); return s('Lande.') }
      ctx.elytra.abheben({ fuer: 'befehl' }).then(() => s('Hebe ab.')).catch(e => s(`Kann nicht fliegen: ${e.message}`))
    },
    land: () => { ctx.elytra.landen(); s('Lande.') },

    status: () => {
      const st = ctx.status()
      s(`Leben ${st.leben}/20, Hunger ${st.hunger}/20, Modus ${st.modus}, Kampf ${st.kampf ? 'an' : 'aus'}, PvP ${st.pvp ? 'an' : 'aus'}, ` +
        `Ziel ${st.ziel ?? '-'}, Aufgabe ${st.aufgabe}, freie Slots ${inv.freieSlots()}`)
    },
    inv: () => {
      // Gruppiert nach Item + Verzauberungen; strukturiert an die Mod (anklickbar), als Text per /msg
      const gruppen = new Map()
      for (const i of inv.items()) {
        const v = inv.verzauberungen(i).map(e => `${VERZ[e.name] ?? e.name} ${ROEMISCH[e.lvl] ?? e.lvl}`).join(', ')
        const key = i.name + '|' + v
        const g = gruppen.get(key) ?? { name: i.name, anzeige: i.displayName, anzahl: 0, verz: v }
        g.anzahl += i.count
        gruppen.set(key, g)
      }
      const liste = [...gruppen.values()].map(g => ({ ...g, abgebbar: Math.max(0, g.anzahl - (RESERVE[g.name] ?? 0)) }))
      const getragen = ['head', 'torso', 'legs', 'feet'].map(sl => inv.getragen(sl)).filter(Boolean).map(i => i.displayName)
      ctx.melden({ typ: 'inventar', items: liste, text: 'Inventar' })
      if (ctx.letzterKanal !== 'api') {
        s(`Traegt: ${getragen.join(', ') || 'nichts'}; Nebenhand: ${inv.offhand()?.displayName ?? 'leer'}`)
        for (let i = 0; i < liste.length; i += 6) s(liste.slice(i, i + 6).map(g => `${g.anzeige} x${g.anzahl}${g.verz ? ' (' + g.verz + ')' : ''}`).join(' | '))
        s('Geben: !gib <item> [menge]')
      }
    },
    nimm: (a) => { einst.loot = anAus(a[0], einst.loot); s(einst.loot ? 'Ich hebe Sachen auf.' : 'Ich hebe nichts mehr auf.') },
    such: (a) => {
      // "Such mir X": Block in der Naehe finden und abbauen
      const n = a.find(x => isNaN(Number(x)))
      const menge = a.map(Number).find(x => !isNaN(x) && x > 0) ?? 8
      // "diamond" meint das Erz, nicht den Diamantblock: genauer Name, dann <name>_ore, dann Teiltreffer (Erze zuerst)
      const bl = n && (ctx.mcData.blocksByName[n] ?? ctx.mcData.blocksByName[n + '_ore'] ??
        ctx.mcData.blocksArray.find(b => b.name.includes(n) && b.name.endsWith('_ore')) ?? ctx.mcData.blocksArray.find(b => b.name.includes(n)))
      if (!bl) return s(`Welchen Block? z.B. !such diamond_ore 5`)
      const ids = ctx.mcData.blocksArray.filter(b => b.name === bl.name || (bl.name.endsWith('_ore') && b.name === 'deepslate_' + bl.name)).map(b => b.id)
      aufgabe({ art: 'abbauen', blockIds: ids, name: bl.displayName, menge }, `Suche ${menge}x ${bl.displayName}.`)
    },
  }

  function heimSetzen () {
    const b = ctx.besitzer()
    if (!b) return s('Ich sehe dich nicht.')
    const p = b.position.floored()
    const ort = ctx.aufgaben.ort
    ort.heim = { x: p.x, y: p.y, z: p.z }
    const truhe = bot.findBlock({ point: b.position, matching: ['chest', 'barrel', 'trapped_chest'].map(n => ctx.mcData.blocksByName[n]?.id).filter(id => id != null), maxDistance: 8 })
    ort.truhe = truhe ? { x: truhe.position.x, y: truhe.position.y, z: truhe.position.z } : null
    ctx.aufgaben.ort.heim = ort.heim
    require('fs').writeFileSync(require('path').join(__dirname, '..', 'daten', `ort-${ctx.serverName}.json`), JSON.stringify(ort, null, 2))
    s(`Zuhause gesetzt bei ${p.x} ${p.y} ${p.z}.${truhe ? ' Truhe gefunden.' : ' Keine Truhe im Umkreis 8.'}`)
  }

  return { ausfuehren, angeschaut, BEFEHLE }
}

module.exports = { erstellen }
