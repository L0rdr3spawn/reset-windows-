// Freie Sprache ueber Jev (TypeSafe): "hol 20 eisen", "hau den da", "logg dich aus, wenn du unter 3 herzen bist".
// Code sammelt Kandidaten, Jev waehlt, Code fuehrt aus. Ohne TYPESAFE_API_KEY nur !-Befehle.
const jev = require('./jev')
const { ROHSTOFFE, FUTTER, UNENDLICH, RESERVE, mengeLesen, koordinatenLesen } = require('./aufgaben')

function erstellen (ctx) {
  const { bot, mcData, einst, log, inv } = ctx
  const s = t => ctx.sagen(t, true)
  let laeuft = false

  function kandidaten () {
    const bloecke = {}
    for (const [k, r] of Object.entries(ROHSTOFFE)) bloecke[`gruppe:${k}`] = r.name
    const gesehen = new Map()
    for (const p of bot.findBlocks({ matching: b => !['air', 'cave_air', 'water', 'lava', 'bedrock'].includes(b.name), maxDistance: 24, count: 3000 })) {
      const b = bot.blockAt(p)
      if (b) gesehen.set(b.name, (gesehen.get(b.name) ?? 0) + 1)
    }
    for (const [name, n] of [...gesehen].sort((a, b) => b[1] - a[1]).slice(0, 50)) bloecke[`block:${name}`] = `${mcData.blocksByName[name].displayName} (${n}x in der Naehe)`
    const items = {}
    for (const it of mcData.itemsArray) {
      if (Object.keys(items).length >= 80) break
      if (bot.recipesFor(it.id, null, 1, true).length) items[`item:${it.name}`] = it.displayName + ' (Material reicht)'
    }
    for (const n of ['crafting_table', 'stick', 'torch', 'chest', 'furnace', 'iron_pickaxe', 'stone_pickaxe', 'iron_sword', 'shield', 'bread']) items[`item:${n}`] ??= mcData.itemsByName[n].displayName
    const mobs = {}
    for (const e of Object.values(bot.entities)) {
      if (!e.position || e === bot.entity || e.name === 'item' || e.name === 'experience_orb') continue
      if (e.position.distanceTo(bot.entity.position) > 48) continue
      if (e.type === 'player') mobs[`spieler:${e.username}`] = `Spieler ${e.username}`
      else mobs[`mob:${e.name}`] = mcData.entitiesByName[e.name]?.displayName ?? e.name
    }
    for (const n of Object.keys(FUTTER)) mobs[`mob:${n}`] ??= mcData.entitiesByName[n]?.displayName ?? n
    const dinge = {}
    for (const i of inv.items()) dinge[`ding:${i.name}`] = `${i.displayName} (${inv.anzahl(i.name)} im Inventar)`
    return { bloecke, items, mobs, dinge }
  }

  async function verstehen (text, gefluestert) {
    if (!jev.aktiv) { if (text.startsWith('!') || gefluestert) s('Das verstehe ich nicht. !hilfe zeigt die Befehle.'); return }
    if (laeuft) return gefluestert ? s('Moment, ich denke noch ueber das Letzte nach.') : undefined
    laeuft = true
    try {
      const teile = text.split(/\s*(?:,?\s*und dann|,?\s*danach|;)\s*/i).filter(Boolean)
      const k = kandidaten()
      for (const [i, teil] of teile.entries()) {
        const j = await jev.befehlVerstehen(teil, gefluestert, { botName: bot.username, besitzer: ctx.ich, zustand: { modus: einst.modus, kampf: einst.kampf, pvp: einst.pvp, aufgabe: ctx.aufgaben.beschreibung() } }, k)
        log(`Jev: "${teil}" -> an_bot ${j.anBot.toFixed(2)}, ${j.aktion} (${j.aktionSicherheit.toFixed(2)}), mob ${j.mob.wert}`)
        if (i === 0 && j.anBot < (gefluestert ? 0.3 : 0.5)) return
        if (j.aktion === 'keine' || j.aktionSicherheit < 0.45) {
          if (gefluestert || j.anBot >= 0.8) s(`"${teil}" hab ich nicht verstanden. !hilfe zeigt die Befehle.`)
          return
        }
        ausfuehren(j, teil, i > 0)
      }
    } catch (e) {
      log('Jev-Fehler:', e.message)
    } finally {
      laeuft = false
    }
  }

  function ausfuehren (j, text, anhaengen) {
    const B = ctx.befehle.BEFEHLE
    const ohneEnde = j.ohneEnde >= 0.6
    const menge = std => ohneEnde ? UNENDLICH : (mengeLesen(text) ?? std)
    const zahl = () => (text.match(/\d+(?:[.,]\d+)?/) ?? [])[0]?.replace(',', '.')
    const auftrag = a => { if (einst.modus === 'stehen') einst.modus = 'folgen'; ctx.aufgaben.starten(a, anhaengen); s(`${anhaengen ? 'Danach' : 'Mache'}: ${a.art}`) }
    const wert = (w, praefix) => w.wert.startsWith(praefix) && w.sicherheit >= 0.4 ? w.wert.slice(praefix.length) : null

    switch (j.aktion) {
      case 'folgen': return B.folge()
      case 'stehen': return B.stop()
      case 'selbst': return B.selbst()
      case 'wache': return B.wache()
      case 'heim_setzen': return B.heim()
      case 'status': return B.status()
      case 'kampf_an': return B.kampf(['an'])
      case 'kampf_aus': return B.kampf(['aus'])
      case 'pvp_an': return B.pvp(['an'])
      case 'pvp_aus': return B.pvp(['aus'])
      case 'loot_an': einst.loot = true; return s('Looten an.')
      case 'loot_aus': einst.loot = false; return s('Looten aus.')
      case 'fliegen': return B.flieg()
      case 'ausloggen': return B.raus()
      case 'logout_regel': {
        const n = zahl()
        if (!n) return B.logout([])
        // "Herzen" -> Lebenspunkte
        const leben = /herz/i.test(text) ? Math.round(+n * 2) : Math.round(+n)
        return /hunger|essen/i.test(text) ? B.logout(['hunger', String(leben)]) : B.logout([String(leben)])
      }
      case 'angreifen': {
        const sp = wert(j.mob, 'spieler:')
        if (sp) return B.greif([sp.toLowerCase()], [sp])
        const mob = wert(j.mob, 'mob:')
        if (mob) {
          const e = bot.nearestEntity(x => x.name === mob)
          if (e) { ctx.kampf.manuellEntity(e); return s(`Greife ${e.displayName ?? mob} an.`) }
        }
        return B.greif([], [])
      }
      case 'abbauen': {
        const g = wert(j.block, 'gruppe:')
        if (g) return auftrag({ art: 'abbauen', blockIds: ctx.aufgaben.blockIdsGruppe(g), name: ROHSTOFFE[g].name, menge: menge(ROHSTOFFE[g].standard), setzlinge: g === 'holz' })
        const bl = wert(j.block, 'block:')
        if (bl) return auftrag({ art: 'abbauen', blockIds: [mcData.blocksByName[bl].id], name: mcData.blocksByName[bl].displayName, menge: menge(16) })
        return s('Welchen Block meinst du?')
      }
      case 'craften': {
        const it = wert(j.item, 'item:')
        return it ? auftrag({ art: 'craften', item: it, itemName: mcData.itemsByName[it]?.displayName ?? it, menge: ohneEnde ? 64 : (mengeLesen(text) ?? 1) }) : s('Welches Item?')
      }
      case 'schmelzen': return auftrag({ art: 'schmelzen', item: wert(j.ding, 'ding:'), menge: menge(64) })
      case 'jagen': case 'zuechten': {
        const mob = wert(j.mob, 'mob:')
        return mob ? auftrag({ art: j.aktion, mob, mobName: mcData.entitiesByName[mob]?.displayName ?? mob, menge: menge(j.aktion === 'jagen' ? 1 : 2) }) : s('Welches Tier?')
      }
      case 'geben': {
        // Alles nur, wenn wirklich "alles" gemeint ist - bei Unklarheit nachfragen statt das Inventar auszuleeren
        const d = wert(j.ding, 'ding:')
        const alles = j.ding.wert === 'alles' && j.ding.sicherheit >= 0.6
        if (!d && !alles) return s('Was soll ich dir geben? z.B. /bot gib diamond 3')
        const posFn = () => { const m = ctx.wahr.besitzerModPos(); return m ? { x: m.x, y: m.y, z: m.z } : null }
        return auftrag({ art: 'geben', an: ctx.ich, item: d, itemName: d ?? 'alles', menge: mengeLesen(text) ?? (d && /\b(ein|eine|einen|eins)\b/i.test(text) ? 1 : UNENDLICH), reserve: d ? (RESERVE[d] ?? 0) : 0, posFn })
      }
      case 'holen': {
        const d = wert(j.ding, 'ding:')
        return d ? auftrag({ art: 'holen', item: d, itemName: d, menge: menge(UNENDLICH) }) : s('Was soll ich holen?')
      }
      case 'gehen': {
        const k = koordinatenLesen(text)
        return k ? auftrag({ art: 'gehen', ...k }) : s('Wohin? Sag z.B. "geh zu 100 64 -200".')
      }
      case 'treppe': { const y = text.match(/-?\d+/)?.[0]; return B.treppe(y ? [y] : []) }
      case 'tunnel': return B.tunnel([String(mengeLesen(text) ?? 32)])
      case 'saeule': return auftrag({ art: 'saeule', menge: mengeLesen(text) ?? 5 })
      case 'farmen': return B.farm(ohneEnde ? ['immer'] : [])
      case 'scheren': return auftrag({ art: 'scheren', menge: menge(UNENDLICH) })
      case 'angeln': return auftrag({ art: 'angeln', menge: menge(10) })
      case 'einlagern': return B.lager()
      case 'heim': return B.nachhause()
      case 'schlafen': case 'ausruesten': return auftrag({ art: j.aktion })
    }
  }

  // Selbststaendig: Code bietet machbare Aufgaben an, Jev waehlt
  let naechste = 0
  const letzte = [] // zuletzt gewaehlte Aufgaben (Jev soll abwechseln)
  async function selbstEntscheiden () {
    if (laeuft || Date.now() < naechste || !jev.aktiv) return
    naechste = Date.now() + 15000
    laeuft = true
    try {
      const optionen = {}
      const auftraege = {}
      for (const [key, r] of Object.entries(ROHSTOFFE)) {
        const ids = ctx.aufgaben.blockIdsGruppe(key)
        const { n, abbaubar } = ctx.aufgaben.vorrat(ids)
        if (n && abbaubar && key !== 'laub') {
          optionen[`abbauen_${key}`] = `${r.name} abbauen (${n} Bloecke in der Naehe).`
          auftraege[`abbauen_${key}`] = { art: 'abbauen', blockIds: ids, name: r.name, menge: r.standard, setzlinge: key === 'holz' }
        }
      }
      optionen.farmen = 'Felder ernten und neu pflanzen.'; auftraege.farmen = { art: 'farmen', menge: 1 }
      optionen.warten = 'Nichts tun.'; auftraege.warten = null
      const { aufgabe } = await jev.naechsteAufgabe({ bot: bot.username, besitzer: ctx.ich, leben: bot.health, hunger: bot.food, inventar: inv.kurz(), letzte_aufgaben: letzte.slice(-5) }, optionen)
      letzte.push(aufgabe)
      if (letzte.length > 20) letzte.shift()
      if (auftraege[aufgabe] && einst.modus === 'selbst') ctx.aufgaben.starten(auftraege[aufgabe])
    } catch (e) {
      log('Jev (selbst):', e.message)
    } finally {
      laeuft = false
    }
  }

  return { verstehen, selbstEntscheiden, jevAktiv: jev.aktiv }
}

module.exports = { erstellen }
