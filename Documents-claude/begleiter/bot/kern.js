// Baut den gemeinsamen Kontext aller Module und die beiden Takte:
// physicsTick (20/s) fuer Kampf und Flug, Gehirn (4/s) fuer Entscheidungen.
const { Movements } = require('mineflayer-pathfinder')

function erstellen ({ bot, konfig, server, serverName, verhalten, einst, ich, log, melden, register, ausloggen }) {
  const mcData = require('minecraft-data')(bot.version)
  const ctx = {
    bot, mcData, konfig, server, serverName, verhalten, einst, ich, log, melden, register,
    eigenerServer: server.typ === 'eigen',
    letzterKanal: 'api',
    timer: []
  }

  // Mineflayer teilt entity_velocity durch 8000 (altes Format). Seit 1.21.9 (lpVec3) kommen die Werte schon
  // in Bloecken/Tick -> ohne Korrektur gibt es keinen Rueckstoss, keinen Lunge-Schub und falsche Gegner-Tempi.
  // Dieser Listener laeuft nach Mineflayers eigenem und ueberschreibt den Wert.
  bot._client.on('entity_velocity', p => {
    const e = bot.entities[p.entityId]
    if (e && p.velocity) e.velocity.set(p.velocity.x, p.velocity.y, p.velocity.z)
  })

  ctx.besitzer = () => bot.players[ctx.ich]?.entity ?? null
  ctx.tode = 0
  bot.on('death', () => { ctx.tode++; log(`Gestorben (${ctx.tode}. Mal)`) })
  // Dimension immer als "minecraft:overworld" usw. (Mineflayer liefert je nach Version mit/ohne Namensraum)
  ctx.dimNorm = d => d ? (String(d).includes(':') ? String(d) : `minecraft:${d}`) : null
  ctx.dimension = () => ctx.dimNorm(bot.game?.dimension)
  ctx.warte = ms => new Promise(resolve => setTimeout(resolve, ms))

  // Meldungen gehen immer lokal an den Manager (Log, spaeter die Mod). Per /msg im Spiel nur als
  // Antwort auf einen Befehl des Besitzers (antwort = true) - sonst wuerde er dich zuspammen.
  let letzteAntwort = { text: '', zeit: 0 }
  ctx.sagen = (text, antwort = false) => {
    melden({ typ: 'sagen', text })
    log('>>', text)
    if (!antwort || ctx.letzterKanal === 'api') return // Mod/Kommandozeile zeigen es selbst an
    if (text === letzteAntwort.text && Date.now() - letzteAntwort.zeit < 5000) return
    letzteAntwort = { text, zeit: Date.now() }
    if (!bot.players[ctx.ich]) return
    if (!ctx.eigenerServer && ctx.letzterKanal !== 'fluestern') return
    const max = 230 - ctx.ich.length
    for (let i = 0; i < text.length; i += max) bot.chat(`/msg ${ctx.ich} ${text.slice(i, i + max)}`)
  }

  // Wer darf gerade die Hand benutzen (Essen, Trank, Waffe, Rakete ...)? Hoehere Prioritaet gewinnt.
  const hand = { wer: null, prio: 0, bis: 0 }
  ctx.handNehmen = (wer, prio, ms = 2500) => {
    const jetzt = Date.now()
    if (hand.wer && hand.wer !== wer && jetzt < hand.bis && hand.prio >= prio) return false
    Object.assign(hand, { wer, prio, bis: jetzt + ms })
    return true
  }
  ctx.handFrei = (wer) => { if (hand.wer === wer) Object.assign(hand, { wer: null, prio: 0, bis: 0 }) }
  ctx.handBelegt = (ausser) => hand.wer && hand.wer !== ausser && Date.now() < hand.bis ? hand.wer : null

  // Bewegungsregeln fuer den Pathfinder
  ctx.bewegungNormal = new Movements(bot)
  ctx.bewegungNormal.allowSprinting = true
  ctx.bewegungNormal.canDig = false
  ctx.bewegungNormal.allow1by1towers = false
  ctx.bewegungArbeit = new Movements(bot)
  ctx.bewegungArbeit.allowSprinting = true
  bot.pathfinder.setMovements(ctx.bewegungNormal)
  bot.pathfinder.thinkTimeout = 3000

  // Module, Reihenfolge = Abhaengigkeiten
  ctx.inv = require('./inventar').erstellen(ctx)
  ctx.wahr = require('./wahrnehmung').erstellen(ctx)
  ctx.aufgaben = require('./aufgaben-bruecke').erstellen(ctx)
  ctx.portal = require('./portal').erstellen(ctx)
  ctx.bew = require('./bewegung').erstellen(ctx)
  ctx.elytra = require('./elytra').erstellen(ctx)
  ctx.speer = require('./speer').erstellen(ctx)
  ctx.wasser = require('./wasser').erstellen(ctx)
  ctx.mace = require('./mace').erstellen(ctx)
  ctx.fern = require('./fernkampf').erstellen(ctx)
  ctx.kampf = require('./kampf').erstellen(ctx)
  ctx.ueber = require('./ueberleben').erstellen(ctx)
  ctx.sprache = require('./sprache').erstellen(ctx)
  ctx.baritone = require('./baritone').erstellen(ctx)
  ctx.befehle = require('./befehle').erstellen(ctx)

  // Ausloggen mit Begruendung (die Mod zeigt sie dir im Chat)
  ctx.ausloggen = async (grund) => {
    if (ctx.ausloggenLaeuft) return
    ctx.ausloggenLaeuft = true
    ctx.sagen(`Logge aus: ${grund}`)
    await ausloggen(grund)
  }

  // ---------------------------------------------------------------- Takte
  const physik = () => {
    if (!bot.entity) return
    try {
      ctx.wahr.physikTick()
      if (ctx.wasser.physikTick()) return // Wassereimer-MLG
      if (ctx.mace.physikTick()) return // Windladungs-Sprung / Sturz steuert selbst
      if (ctx.elytra.physikTick()) return
      ctx.kampf.physikTick()
    } catch (e) { log('Fehler im Physiktakt:', e.stack) }
  }
  bot.on('physicsTick', physik)

  let gehirnLaeuft = false
  const gehirn = async () => {
    if (!bot.entity || gehirnLaeuft || ctx.ausloggenLaeuft) return
    gehirnLaeuft = true
    try {
      ctx.wahr.aktualisieren()
      if (await ctx.ueber.logoutPruefen()) return
      ctx.ueber.totemWaechter()
      ctx.ueber.tick()
      const kaempft = ctx.kampf.gehirnTick()
      if (ctx.elytra.aktiv() || kaempft) return
      if (ctx.aufgaben.laeuft()) return
      // Pausierte Aufgabe (Kampf/Beschuss) erst fortsetzen, wenn 5 s Ruhe ist - auch im Modus "stehen"
      // (z.B. Baritone-Aufgabe). Bis dahin beim Besitzer bleiben statt stehend weiter beschossen zu werden.
      if (ctx.aufgaben.pausiert()) {
        const ruhig = Date.now() - ctx.wahr.zuletztGetroffen(bot.entity.id) > 5000 && !ctx.wahr.imKampf()
        if (ruhig) return ctx.aufgaben.weiter()
        return ctx.bew.folgenTick()
      }
      if (einst.modus === 'stehen') return
      if (einst.modus === 'selbst') return ctx.sprache.selbstEntscheiden()
      // Eimer nachfuellen laeuft im Hintergrund; solange nicht folgen (Kampf/Logout oben laufen weiter)
      if (ctx.wasser.nachfuellenLaeuft() || ctx.wasser.nachfuellenStarten()) return
      ctx.bew.folgenTick()
    } catch (e) {
      log('Fehler im Gehirn:', e.stack)
    } finally {
      gehirnLaeuft = false
    }
  }
  ctx.timer.push(setInterval(gehirn, 250))

  // Status fuer Manager, Mod und Kommandozeile
  ctx.status = () => ({
    bot: bot.username,
    besitzer: ctx.ich,
    server: serverName,
    typ: server.typ,
    leben: Math.round(bot.health ?? 0),
    hunger: bot.food ?? 0,
    modus: einst.modus,
    kampf: einst.kampf,
    pvp: einst.pvp,
    ziel: ctx.kampf.zielName(),
    aufgabe: ctx.aufgaben.beschreibung(),
    fliegt: ctx.elytra.aktiv(),
    pos: bot.entity ? bot.entity.position.floored().toArray() : null,
    tode: ctx.tode,
    dim: ctx.dimension(),
    freunde: einst.freunde,
    // Schalter fuer das Einstellungs-Menue der Mod
    einstellungen: {
      kampf: einst.kampf, pvp: einst.pvp, nimm: einst.loot, mace: einst.mace !== false, speer: einst.speer !== false,
      elytra: einst.elytra !== false, farmt: ctx.aufgaben.aktuell()?.art === 'farmen', fliegt: ctx.elytra.aktiv(),
      logoutLeben: einst.logoutLeben, logoutTod: einst.logoutBeiTodBesitzer, logoutUebermacht: einst.logoutBeiUebermacht
    }
  })
  ctx.timer.push(setInterval(() => melden({ typ: 'status', status: ctx.status() }), 1000))
  // Inventar-Schnappschuss fuer die Mod (GET /inventar): bei Aenderung sofort, sonst alle 5 s
  let letzterStand = ''
  let standZeit = 0
  ctx.timer.push(setInterval(() => {
    const stand = ctx.inv.schnappschuss()
    const text = JSON.stringify(stand.slots)
    if (text === letzterStand && Date.now() - standZeit < 5000) return
    letzterStand = text
    standZeit = Date.now()
    melden({ typ: 'inventarStand', stand })
  }, 400))

  ctx.beenden = () => {
    for (const t of ctx.timer) clearInterval(t)
    bot.removeListener('physicsTick', physik)
  }

  ctx.sagen(`${bot.username} ist da. !hilfe fuer Befehle.`)
  return ctx
}

module.exports = { erstellen }
