// Baritone-Befehle fuer den Mineflayer-Bot nachgebaut: gleiche Syntax wie Baritone (#goto, #mine ...), ausgefuehrt mit
// mineflayer-pathfinder und den vorhandenen Aufgaben. Aufruf: "!baritone <befehl>" bzw. in der Mod "/bot baritone <befehl>".
const { goals } = require('mineflayer-pathfinder')
const { Vec3 } = require('vec3')

const UNENDLICH = Infinity

// Befehl -> Kurzhilfe (auch fuer die Tab-Vorschlaege in der Mod)
const HILFE = {
  goto: 'goto <x y z> | <x z> | <y> | <block> - hinlaufen',
  goal: 'goal <x y z> | <x z> | <y> | clear - Ziel merken (mit "path" loslaufen)',
  path: 'path - zum gemerkten Ziel laufen',
  mine: 'mine <block> [block ...] [anzahl] - abbauen (ohne Anzahl: bis stop)',
  follow: 'follow player <name> | players | entity <typ> | entities - folgen bis stop',
  farm: 'farm - Felder ernten und neu pflanzen (bis stop)',
  explore: 'explore [x z] - Gegend erkunden (bis stop)',
  tunnel: 'tunnel [hoehe breite laenge] - Tunnel in deine Blickrichtung',
  come: 'come - zu dir kommen',
  thisway: 'thisway <bloecke> - in deine Blickrichtung laufen',
  surface: 'surface - an die Oberflaeche',
  find: 'find <block> - Fundorte in der Naehe nennen',
  stop: 'stop | cancel - alles abbrechen',
  pause: 'pause - anhalten',
  resume: 'resume - weitermachen',
  set: 'set <allowBreak|allowPlace|allowSprint|allowParkour> <true|false>',
  status: 'status - was laeuft gerade',
  help: 'help - diese Liste'
}
const EINSTELLUNGEN = { allowBreak: 'canDig', allowPlace: 'allow1by1towers', allowSprint: 'allowSprinting', allowParkour: 'allowParkour' }

function erstellen (ctx) {
  const { bot, einst, log, mcData } = ctx
  const s = t => ctx.sagen(t, true)
  let gemerktesZiel = null

  const zahl = x => x != null && x !== '' && !isNaN(Number(x))
  const blockName = n => String(n ?? '').replace(/^minecraft:/, '').toLowerCase()
  const block = n => mcData.blocksByName[blockName(n)]

  // Baritone-Zielsyntax: "x y z" | "x z" | "y" | "<block>"
  function zielAus (args) {
    if (args.length >= 3 && args.slice(0, 3).every(zahl)) {
      const [x, y, z] = args.slice(0, 3).map(Number)
      return { text: `${x} ${y} ${z}`, goal: () => new goals.GoalBlock(x, y, z) }
    }
    if (args.length >= 2 && args.slice(0, 2).every(zahl)) {
      const [x, z] = args.slice(0, 2).map(Number)
      return { text: `${x} ${z}`, goal: () => new goals.GoalXZ(x, z) }
    }
    if (args.length === 1 && zahl(args[0])) {
      const y = Number(args[0])
      return { text: `Hoehe ${y}`, goal: () => new goals.GoalY(y) }
    }
    const b = block(args[0])
    if (b) {
      return {
        text: b.name,
        goal: () => {
          const pos = bot.findBlock({ matching: b.id, maxDistance: 64 })?.position
          return pos ? new goals.GoalGetToBlock(pos.x, pos.y, pos.z) : null
        },
        fehler: `Kein ${b.name} im Umkreis von 64 Bloecken.`
      }
    }
    return null
  }

  function besitzerPos () {
    const b = ctx.besitzer()
    if (b) return { pos: b.position, yaw: b.yaw }
    const m = ctx.wahr.besitzerModPos()
    // Mod meldet Yaw in Grad (Minecraft: 0 = Sueden); Mineflayer: Bogenmass, 0 = Norden
    return m ? { pos: new Vec3(m.x, m.y, m.z), yaw: m.yaw != null ? Math.PI - m.yaw * Math.PI / 180 : null } : null
  }

  // Baritone-Befehle bewegen den Bot weg vom Besitzer: danach bleibt er dort (wie Baritone), bis "/bot folge"
  function starten (auftrag, text) {
    einst.modus = 'stehen'
    ctx.aufgaben.starten(auftrag)
    s(`${text} (danach bleibe ich dort - /bot folge holt mich zurueck)`)
  }

  const BEFEHLE = {
    help () { for (const z of Object.values(HILFE)) s(z) },
    status () { s(`Aufgabe: ${ctx.aufgaben.beschreibung()}${gemerktesZiel ? ', Ziel: ' + gemerktesZiel.text : ''}, Modus: ${einst.modus}`) },

    goto (a) {
      const z = zielAus(a)
      if (!z) return s(HILFE.goto)
      starten({ art: 'ziel', name: z.text, goalFn: z.goal, fehlerText: z.fehler, fertigText: `Bin bei ${z.text}.` }, `Gehe zu ${z.text}.`)
    },
    goal (a) {
      if (a[0] === 'clear' || a[0] === 'reset' || a[0] === 'none') { gemerktesZiel = null; return s('Ziel geloescht.') }
      const hier = (besitzerPos()?.pos ?? bot.entity.position).floored()
      const args = a.length ? a : [hier.x, hier.y, hier.z].map(String)
      const z = zielAus(args)
      if (!z) return s(HILFE.goal)
      gemerktesZiel = { ...z, args }
      s(`Ziel gesetzt: ${z.text}. "path" laeuft los.`)
    },
    path () {
      if (!gemerktesZiel) return s('Kein Ziel gesetzt (goal ...).')
      BEFEHLE.goto(gemerktesZiel.args)
    },

    mine (a) {
      const namen = a.filter(x => !zahl(x))
      const bloecke = namen.map(block).filter(Boolean)
      if (!bloecke.length) return s(`${HILFE.mine} - Block nicht gefunden: ${namen.join(' ')}`)
      // Erze auch als Tiefenschiefer-Variante, wie Baritone
      const ids = new Set()
      for (const b of bloecke) {
        ids.add(b.id)
        const tief = mcData.blocksByName['deepslate_' + b.name]
        if (b.name.endsWith('_ore') && tief) ids.add(tief.id)
      }
      const menge = a.find(zahl) ? Number(a.find(zahl)) : UNENDLICH
      starten({ art: 'abbauen', blockIds: [...ids], name: bloecke.map(b => b.name).join('/'), menge }, `Baue ${bloecke.map(b => b.name).join(', ')} ab${menge === UNENDLICH ? ' (bis stop)' : ` (${menge})`}.`)
    },

    follow (a) {
      const art = a[0]
      if (art === 'player' && a[1]) {
        const name = a[1]
        const e = () => bot.players[name]?.entity ?? Object.values(bot.players).find(p => p.username.toLowerCase() === name.toLowerCase())?.entity
        if (!e()) return s(`Spieler ${name} sehe ich nicht.`)
        return starten({ art: 'ziel', name: `folgt ${name}`, folgen: true, goalFn: () => e() ? new goals.GoalFollow(e(), 2) : null }, `Folge ${name}.`)
      }
      if (art === 'players' || art === 'entities' || art === 'entity') {
        const typ = art === 'entity' ? blockName(a[1]) : null
        const naechster = () => {
          let best = null
          for (const x of Object.values(bot.entities)) {
            if (x === bot.entity || !x.position) continue
            if (art === 'players' && x.type !== 'player') continue
            if (typ && x.name !== typ) continue
            if (art !== 'players' && !ctx.wahr.lebendig(x)) continue
            if (!best || x.position.distanceTo(bot.entity.position) < best.position.distanceTo(bot.entity.position)) best = x
          }
          return best
        }
        if (!naechster()) return s('Niemanden zum Folgen gefunden.')
        return starten({ art: 'ziel', name: `folgt ${typ ?? art}`, folgen: true, goalFn: () => { const e = naechster(); return e ? new goals.GoalFollow(e, 2) : null } }, `Folge ${typ ?? art}.`)
      }
      s(HILFE.follow)
    },

    farm () { starten({ art: 'farmen', menge: UNENDLICH }, 'Farme (bis stop).') },

    explore (a) {
      const mitte = a.length >= 2 && zahl(a[0]) && zahl(a[1]) ? new Vec3(Number(a[0]), 0, Number(a[1])) : null
      starten({ art: 'erkunden', mitte }, 'Erkunde die Gegend (bis stop).')
    },

    tunnel (a) {
      const [h, b, l] = a.map(Number)
      const bp = besitzerPos()
      starten({ art: 'tunnel', menge: l > 0 ? l : 64, hoehe: h > 0 ? h : 2, breite: b > 0 ? b : 1, yaw: bp?.yaw ?? bot.entity.yaw },
        `Grabe einen Tunnel ${b > 0 ? b : 1}x${h > 0 ? h : 2}, ${l > 0 ? l : 64} lang.`)
    },

    come () {
      const bp = besitzerPos()
      if (!bp) return s('Ich weiss nicht, wo du bist.')
      const p = bp.pos.floored()
      starten({ art: 'ziel', name: 'zu dir', goalFn: () => new goals.GoalNear(p.x, p.y, p.z, 1), fertigText: 'Bin da.' }, 'Komme zu dir.')
    },

    thisway (a) {
      const bp = besitzerPos()
      if (!bp || bp.yaw == null || !zahl(a[0])) return s(HILFE.thisway)
      const d = Number(a[0])
      const x = Math.round(bp.pos.x - Math.sin(bp.yaw) * d)
      const z = Math.round(bp.pos.z - Math.cos(bp.yaw) * d)
      starten({ art: 'ziel', name: `${d} Bloecke`, goalFn: () => new goals.GoalXZ(x, z), fertigText: `Bin ${d} Bloecke in deine Richtung gelaufen (${x} ${z}).` }, `Laufe ${d} Bloecke in deine Blickrichtung.`)
    },

    surface () {
      const p = bot.entity.position.floored()
      // Hoechster fester Block in dieser Spalte -> darauf stellen
      let oben = null
      for (let y = p.y + 1; y < Math.min(p.y + 200, 320); y++) {
        const b = bot.blockAt(new Vec3(p.x, y, p.z))
        if (b && b.boundingBox === 'block') oben = y
      }
      if (oben == null) return s('Ich bin schon an der Oberflaeche.')
      starten({ art: 'ziel', name: 'Oberflaeche', goalFn: () => new goals.GoalBlock(p.x, oben + 1, p.z), fertigText: 'Bin oben.' }, 'Gehe an die Oberflaeche.')
    },

    find (a) {
      const b = block(a[0])
      if (!b) return s(HILFE.find)
      const funde = bot.findBlocks({ matching: b.id, maxDistance: 64, count: 5 })
      if (!funde.length) return s(`Kein ${b.name} im Umkreis von 64 Bloecken.`)
      s(`${b.name}: ${funde.map(f => `${f.x} ${f.y} ${f.z}`).join(' | ')}`)
    },

    stop () { ctx.aufgaben.stoppen(); bot.pathfinder.setGoal(null); einst.modus = 'stehen'; s('Gestoppt. /bot folge holt mich zurueck.') },
    cancel () { BEFEHLE.stop() },
    pause () {
      if (!ctx.aufgaben.aktuell()) return s('Es laeuft nichts.')
      ctx.aufgaben.pausieren(true)
      s('Pausiert. "resume" macht weiter.')
    },
    resume () {
      if (!ctx.aufgaben.angehalten()) return s('Nichts pausiert.')
      ctx.aufgaben.weiter()
      s('Mache weiter.')
    },

    set (a) {
      const name = Object.keys(EINSTELLUNGEN).find(k => k.toLowerCase() === String(a[0]).toLowerCase())
      if (!name || !['true', 'false'].includes(String(a[1]).toLowerCase())) return s(HILFE.set)
      const wert = String(a[1]).toLowerCase() === 'true'
      for (const m of [ctx.bewegungNormal, ctx.bewegungArbeit]) m[EINSTELLUNGEN[name]] = wert
      s(`${name} = ${wert}`)
    }
  }

  function ausfuehren (text) {
    const [cmd, ...args] = String(text).trim().replace(/^#/, '').split(/\s+/)
    if (!cmd) return BEFEHLE.help()
    const f = BEFEHLE[String(cmd).toLowerCase()]
    if (!f) return s(`Unbekannter Baritone-Befehl "${cmd}". Gibt es: ${Object.keys(HILFE).join(', ')}`)
    log(`Baritone: ${text}`)
    try { f(args) } catch (e) { log('Baritone-Fehler:', e.stack); s(`Fehler: ${e.message}`) }
  }

  // Zu einem angeschauten Block gehen (Taste G): moeglichst oben drauf, sonst direkt daneben
  function geheZu (x, y, z) {
    starten({
      art: 'ziel',
      name: `${x} ${y} ${z}`,
      goalFn: () => new goals.GoalNear(x + 0.5, y + 1, z + 0.5, 1.5),
      fertigText: `Bin bei ${x} ${y} ${z}.`
    }, `Gehe zu ${x} ${y} ${z}.`)
  }

  return { ausfuehren, geheZu, HILFE }
}

module.exports = { erstellen, HILFE }
