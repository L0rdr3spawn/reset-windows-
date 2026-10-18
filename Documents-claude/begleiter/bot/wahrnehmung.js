// Wahrnehmung: wer schlaegt wen, wie geht es dem Besitzer, was ist gefaehrlich, wie weit faellt der Bot.
const { EventEmitter } = require('events')

// Grobe Schaeden je Treffer (Schwierigkeit normal) fuer die "kann er mich one-shotten?"-Schaetzung
const MOB_SCHADEN = {
  zombie: 3, husk: 3, drowned: 3, zombie_villager: 3, skeleton: 4, stray: 4, bogged: 4, parched: 4, spider: 2, cave_spider: 2,
  creeper: 25, enderman: 7, witch: 6, pillager: 4, vindicator: 13, evoker: 6, ravager: 12, piglin: 8, piglin_brute: 13,
  hoglin: 6, zoglin: 6, blaze: 6, ghast: 17, wither_skeleton: 8, warden: 30, breeze: 5, iron_golem: 21, slime: 4,
  magma_cube: 6, phantom: 4, guardian: 6, elder_guardian: 8, silverfish: 1, vex: 9, wither: 12, ender_dragon: 15,
  zombified_piglin: 8, endermite: 2, shulker: 4, creaking: 3, polar_bear: 6, wolf: 4, llama: 1, bee: 2, goat: 3
}
// Stehen in minecraft-data unter "Hostile mobs", greifen aber nicht von selbst an
const NEUTRAL = new Set(['enderman', 'piglin', 'zombified_piglin', 'spider', 'cave_spider', 'wolf', 'bee', 'iron_golem',
  'llama', 'trader_llama', 'polar_bear', 'dolphin', 'panda', 'goat', 'creaking'])
const NIE_ANGREIFEN = new Set(['villager', 'wandering_trader', 'item', 'experience_orb', 'armor_stand', 'item_frame',
  'glow_item_frame', 'painting', 'arrow', 'spectral_arrow', 'trident', 'firework_rocket', 'wind_charge', 'fishing_bobber'])

function erstellen (ctx) {
  const { bot, mcData, einst } = ctx
  const wahr = new EventEmitter()
  const jetzt = () => Date.now()

  const treffer = [] // { zeit, opfer, opferName, quelle, quelleName, art, pos }
  const MAX_TREFFER = 400
  let besitzerZiel = null // { id, zeit, quelle: 'schaden'|'mod' }
  const mod = { leben: null, hunger: null, tot: false, pos: null, zeit: 0 }
  let besitzerTotZeit = 0
  const portalSpuren = [] // { von, nach, pos, zeit }: wo der Besitzer die Dimension gewechselt hat
  let totSeitDim = false
  let hoechstesY = null // fuer Fallhoehe (Mace)
  // Tempo des Besitzers selbst messen (fuer Spieler schickt der Server kaum Geschwindigkeiten)
  const besitzerSpur = [] // [{ t, pos }]
  let besitzerV = { x: 0, y: 0, z: 0 } // Bloecke pro Tick, geglaettet

  const name = e => e ? (e.username ?? e.displayName ?? e.name ?? `#${e.id}`) : '?'
  const istSpieler = e => e?.type === 'player'
  const istBesitzer = e => istSpieler(e) && e.username?.toLowerCase() === ctx.ich.toLowerCase()
  const istFreund = e => istSpieler(e) && einst.freunde.some(f => f.toLowerCase() === e.username?.toLowerCase()) && !gesperrt(e.username)
  const kategorie = e => mcData.entitiesByName[e?.name]?.category
  const istMonster = e => kategorie(e) === 'Hostile mobs' && !NEUTRAL.has(e.name)
  const lebendig = e => e && e.isValid !== false && (e.type === 'mob' || e.type === 'player' || e.type === 'hostile' || e.type === 'animal' || e.type === 'passive' || e.type === 'water_creature' || e.type === 'ambient')

  // Metadaten (Index aus minecraft-data: 0 Flags, 6 Pose, 8 Hand-Flags, 9 Leben)
  const flags = e => e?.metadata?.[0] ?? 0
  const gleitet = e => e === bot.entity ? !!bot.entity.elytraFlying : !!(flags(e) & 0x80)
  const handAktiv = e => !!((e?.metadata?.[8] ?? 0) & 0x01)
  const lebenVon = e => {
    if (!e) return null
    if (e === bot.entity) return bot.health
    const h = e.metadata?.[9]
    return typeof h === 'number' ? h : null
  }
  // Schild hoch: Hand aktiv und Schild in einer Hand
  const blocktMitSchild = e => handAktiv(e) && (e.equipment?.[0]?.name === 'shield' || e.equipment?.[1]?.name === 'shield')

  // ---------------------------------------------------------------- Treffer
  bot.on('entityHurt', (opfer, quelle) => {
    if (!opfer) return
    const t = { zeit: jetzt(), opfer: opfer.id, opferName: name(opfer), quelle: quelle?.id ?? null, quelleName: quelle ? anzeigeName(quelle) : null, pos: opfer.position?.clone() }
    treffer.push(t)
    if (treffer.length > MAX_TREFFER) treffer.shift()
    if (quelle && istBesitzer(quelle) && opfer !== bot.entity) besitzerZiel = { id: opfer.id, zeit: t.zeit, quelle: 'schaden' }
    wahr.emit('treffer', t, opfer, quelle)
  })
  // Wie viel hat der Treffer gekostet? (Leben-Paket kommt direkt nach dem Schadens-Paket)
  let lebenAlt = null
  bot.on('health', () => {
    if (lebenAlt != null && bot.health < lebenAlt && bot.entity) {
      const t = [...treffer].reverse().find(x => x.opfer === bot.entity.id && jetzt() - x.zeit < 500 && x.schaden == null)
      if (t) t.schaden = lebenAlt - bot.health
      else {
        treffer.push({ zeit: jetzt(), opfer: bot.entity.id, quelle: null, quelleName: null, schaden: lebenAlt - bot.health })
        if (treffer.length > MAX_TREFFER) treffer.shift()
      }
    }
    lebenAlt = bot.health
  })

  // Schadensart aus dem Paket (Fall, Lava, Explosion ...) fuer die Begruendung beim Ausloggen
  bot._client.on('damage_event', p => {
    const art = ctx.register.damage_type?.[p.sourceTypeId]
    const t = treffer[treffer.length - 1]
    if (t && t.opfer === p.entityId && jetzt() - t.zeit < 50) t.art = art
  })

  bot.on('entityDead', e => {
    if (istBesitzer(e)) besitzerGestorben('Tod gesehen')
    wahr.emit('tot', e)
  })
  bot.on('entityUpdate', e => {
    if (istBesitzer(e) && lebenVon(e) === 0) besitzerGestorben('Leben 0')
  })

  function besitzerGestorben (wie) {
    if (jetzt() - besitzerTotZeit < 10000) return
    besitzerTotZeit = jetzt()
    ctx.log(`Besitzer ${ctx.ich} ist gestorben (${wie}).`)
    wahr.emit('besitzerTot')
  }

  // ---------------------------------------------------------------- Ursache (warum geht es mir schlecht?)
  const ART = {
    mob_attack: 'Nahkampf', mob_attack_no_aggro: 'Nahkampf', player_attack: 'Schlag', arrow: 'Pfeil', trident: 'Dreizack',
    explosion: 'Explosion', player_explosion: 'Explosion', fall: 'Sturz', lava: 'Lava', in_fire: 'Feuer', on_fire: 'Feuer',
    mace_smash: 'Mace-Smash', magic: 'Trank', indirect_magic: 'Trank', thorns: 'Dornen', drown: 'Ertrinken', starve: 'Hunger',
    cactus: 'Kaktus', fireball: 'Feuerball', wither: 'Wither-Effekt', sonic_boom: 'Schallwelle', spear: 'Speer', fly_into_wall: 'Aufprall'
  }
  const NAMEN = { tnt_minecart: 'TNT-Lore', tnt: 'gezuendetes TNT', end_crystal: 'Endkristall', creeper: 'Creeper' }
  function anzeigeName (e) { return NAMEN[e?.name] ?? name(e) }

  // Wer/was hat dem Bot in den letzten Sekunden am meisten Schaden gemacht? z.B. "Zombie Nahkampf 3x (14 Schaden)"
  function ursache (ms = 15000) {
    const grenze = jetzt() - ms
    const summe = new Map()
    for (const t of treffer) {
      if (t.zeit < grenze || t.opfer !== bot.entity?.id) continue
      const schluessel = [t.quelleName, ART[t.art] ?? t.art].filter(Boolean).join(' ') || 'unbekannte Ursache'
      const g = summe.get(schluessel) ?? { schaden: 0, anzahl: 0 }
      g.schaden += t.schaden ?? 0
      g.anzahl++
      summe.set(schluessel, g)
    }
    const teile = [...summe].sort((a, b) => b[1].schaden - a[1].schaden).slice(0, 3)
      .map(([k, g]) => `${k}${g.anzahl > 1 ? ` ${g.anzahl}x` : ''}${g.schaden ? ` (${Math.round(g.schaden)} Schaden)` : ''}`)
    return teile.length ? teile.join(', ') : null
  }

  // Sprengstoff in der Naehe (TNT-Lore, gezuendetes TNT, Creeper, Endkristall)
  function sprengstoff (radius = 6) {
    let best = null
    for (const e of Object.values(bot.entities)) {
      if (!e.position || !NAMEN[e.name]) continue
      const d = e.position.distanceTo(bot.entity.position)
      if (d <= radius && (!best || d < best.d)) best = { e, d, name: NAMEN[e.name] }
    }
    return best
  }

  // ---------------------------------------------------------------- Abfragen
  function angreiferVon (opferId, ms = 5000) {
    const grenze = jetzt() - ms
    const ids = new Set()
    for (let i = treffer.length - 1; i >= 0 && treffer[i].zeit >= grenze; i--) {
      if (treffer[i].opfer === opferId && treffer[i].quelle != null) ids.add(treffer[i].quelle)
    }
    return [...ids].map(id => bot.entities[id]).filter(Boolean)
  }
  const zuletztGetroffen = (opferId) => {
    for (let i = treffer.length - 1; i >= 0; i--) if (treffer[i].opfer === opferId) return treffer[i].zeit
    return 0
  }
  const hatAngegriffen = (quelleId, opferId, ms) => treffer.some(t => t.quelle === quelleId && t.opfer === opferId && jetzt() - t.zeit < ms)

  // Wie viel Schaden kann `e` dem Bot mit einem Schlag machen (nach Ruestung)?
  function maxSchaden (e) {
    let roh
    if (istSpieler(e)) {
      const waffe = e.equipment?.[0]
      roh = ctx.inv.WAFFEN[waffe?.name]?.[0] ?? 1
      roh += (ctx.inv.verzauberung(waffe, 'sharpness') ? 3 : 0)
      roh *= 1.5 // Krit
      if (waffe?.name === 'mace') {
        const fall = Math.max(0, (e.position.y - bot.entity.position.y)) + (e.onGround ? 0 : 3)
        roh += Math.min(fall, 3) * 4 + Math.min(Math.max(fall - 3, 0), 5) * 2 + Math.max(fall - 8, 0)
      }
      if (waffe?.name === 'end_crystal' || waffe?.name === 'respawn_anchor') roh = 30
    } else {
      roh = MOB_SCHADEN[e.name] ?? 5
      if (e.name === 'creeper' && e.position.distanceTo(bot.entity.position) > 5) roh = 0
    }
    const { punkte, haerte, epf } = ctx.inv.schutz()
    const nachRuestung = roh * (1 - Math.min(20, Math.max(punkte / 5, punkte - 4 * roh / (haerte + 8))) / 25)
    return nachRuestung * (1 - Math.min(epf * 4, 80) / 100)
  }

  // Alle, die gerade gefaehrlich sind: Monster in der Naehe, wer den Bot oder Besitzer angreift
  function bedrohungen (radius = 16) {
    const besitzer = ctx.besitzer()
    const res = []
    for (const e of Object.values(bot.entities)) {
      if (e === bot.entity || !e.position || !lebendig(e) || istBesitzer(e)) continue
      const d = e.position.distanceTo(bot.entity.position)
      if (d > radius) continue
      const griffAn = hatAngegriffen(e.id, bot.entity.id, 8000) || (besitzer && hatAngegriffen(e.id, besitzer.id, 8000))
      if (istMonster(e) || griffAn) res.push({ e, d, schaden: maxSchaden(e), griffAn })
    }
    return res.sort((a, b) => a.d - b.d)
  }

  function imKampf () {
    return jetzt() - zuletztGetroffen(bot.entity.id) < 4000 || bedrohungen(6).some(b => b.griffAn || (istMonster(b.e) && b.d < 5))
  }

  // ---------------------------------------------------------------- Freundesliste (Notfall-Sperre)
  const sperren = new Map() // name -> bis
  function gesperrt (n) {
    const bis = sperren.get(n?.toLowerCase())
    return bis && bis > jetzt()
  }
  function freundSperren (n, minuten) {
    sperren.set(n.toLowerCase(), jetzt() + minuten * 60000)
    ctx.sagen(`${n} hat dich angegriffen, als du wenig Leben hattest - ${minuten} min von der Freundesliste gestrichen.`)
  }

  // ---------------------------------------------------------------- Mod-Ereignisse (genauer als Schaetzen)
  function modEreignis (m) {
    // Zustand eines anderen Spielers (anderer Client mit der Mod) darf die Besitzer-Daten nicht auffrischen
    if (m.art === 'zustand' && m.name && m.name.toLowerCase() !== ctx.ich.toLowerCase()) return
    mod.zeit = jetzt()
    if (m.art === 'angriff') {
      const e = Object.values(bot.entities).find(x => (m.uuid && x.uuid === m.uuid) || x.id === m.id)
      if (e && !istBesitzer(e) && e !== bot.entity) besitzerZiel = { id: e.id, zeit: jetzt(), quelle: 'mod' }
    } else if (m.art === 'leben') {
      mod.leben = m.leben
      mod.hunger = m.hunger
    } else if (m.art === 'tod') {
      besitzerGestorben('Mod')
    } else if (m.art === 'pos') {
      mod.pos = m
    } else if (m.art === 'ziel') {
      ctx.letzterKanal = 'api' // Antwort zeigt die Mod, kein /msg
      // Angriffstaste der Mod: genau dieses Wesen angreifen (ausdruecklicher Befehl -> auch Freunde/PvP aus)
      const e = Object.values(bot.entities).find(x => (m.uuid && x.uuid === m.uuid) || x.id === m.id)
      if (!e || e === bot.entity || istBesitzer(e)) return ctx.sagen(`Ziel ${m.zielName ?? m.name ?? '?'} sehe ich nicht.`)
      ctx.kampf.manuellEntity(e, 120)
      ctx.sagen(`Greife ${name(e)} an.`)
    } else if (m.art === 'gehe') {
      ctx.letzterKanal = 'api'
      // Taste G auf einen Block: dorthin gehen (oben drauf bzw. so nah wie moeglich)
      ctx.baritone.geheZu(m.x, m.y, m.z)
    } else if (m.art === 'folgen') {
      ctx.letzterKanal = 'api'
      // Taste G in die Luft: wieder folgen
      ctx.befehle.BEFEHLE.folge()
    } else if (m.art === 'zustand') {
      // Botlink-Mod: exakter Zustand des Besitzers direkt aus seinem Client
      if (m.name && m.name.toLowerCase() !== ctx.ich.toLowerCase()) return
      const alt = { dim: mod.dim, pos: mod.pos }
      if (m.leben <= 0) totSeitDim = true
      Object.assign(mod, { leben: m.leben, hunger: m.hunger, totems: m.totems, gleitet: m.gleitet, dim: m.dim, pos: { x: m.x, y: m.y, z: m.z, yaw: m.yaw } })
      // Dimension gewechselt: wo war er zuletzt? (Dort steht das Portal.) Nach einem Tod ist es der Respawn, kein Portal.
      if (alt.dim && m.dim && alt.dim !== m.dim && alt.pos) {
        if (!totSeitDim) {
          portalSpuren.push({ von: alt.dim, nach: m.dim, pos: alt.pos, zeit: jetzt() })
          if (portalSpuren.length > 20) portalSpuren.shift()
          ctx.log(`Besitzer: ${alt.dim} -> ${m.dim} bei ${Math.floor(alt.pos.x)} ${Math.floor(alt.pos.y)} ${Math.floor(alt.pos.z)}`)
        }
        totSeitDim = false
      }
    }
  }

  // ---------------------------------------------------------------- Takte
  function physikTick () {
    const b = ctx.besitzer()
    if (b) {
      besitzerSpur.push({ t: jetzt(), pos: b.position.clone() })
      while (besitzerSpur.length > 12) besitzerSpur.shift()
      const a = besitzerSpur[0]
      const dt = (jetzt() - a.t) / 50
      if (dt >= 3) {
        const roh = { x: (b.position.x - a.pos.x) / dt, y: (b.position.y - a.pos.y) / dt, z: (b.position.z - a.pos.z) / dt }
        for (const k of ['x', 'y', 'z']) besitzerV[k] = besitzerV[k] * 0.5 + roh[k] * 0.5
      }
    } else {
      besitzerSpur.length = 0
    }
    const p = bot.entity.position
    if (bot.entity.onGround || bot.entity.isInWater || bot.entity.elytraFlying && bot.entity.velocity.y > -0.5) hoechstesY = p.y
    else if (hoechstesY == null || p.y > hoechstesY) hoechstesY = p.y
  }

  function aktualisieren () {
    // Ziel des Besitzers verfaellt nach 15 s ohne neuen Treffer
    if (besitzerZiel && (jetzt() - besitzerZiel.zeit > 15000 || !bot.entities[besitzerZiel.id])) besitzerZiel = null
  }

  Object.assign(wahr, {
    MOB_SCHADEN, NEUTRAL, NIE_ANGREIFEN,
    name, istSpieler, istBesitzer, istFreund, istMonster, lebendig, gleitet, blocktMitSchild, handAktiv, lebenVon,
    angreiferVon, zuletztGetroffen, hatAngegriffen, maxSchaden, bedrohungen, imKampf, freundSperren, gesperrt, ursache, sprengstoff, anzeigeName,
    modEreignis, physikTick, aktualisieren, treffer,
    besitzerZiel: () => besitzerZiel ? bot.entities[besitzerZiel.id] ?? null : null,
    besitzerLeben: () => {
      if (mod.leben != null && jetzt() - mod.zeit < 5000) return mod.leben
      return lebenVon(ctx.besitzer())
    },
    besitzerTempo: () => besitzerV, // Bloecke/Tick
    besitzerTempoHorizontal: () => Math.hypot(besitzerV.x, besitzerV.z) * 20, // Bloecke/s
    besitzerHunger: () => jetzt() - mod.zeit < 3000 ? mod.hunger : null,
    besitzerTotems: () => jetzt() - mod.zeit < 3000 ? mod.totems : null,
    besitzerGleitetMod: () => jetzt() - mod.zeit < 1000 && !!mod.gleitet,
    modAktiv: () => jetzt() - mod.zeit < 3000,
    besitzerModPos: () => mod.pos && jetzt() - mod.zeit < 3000 ? mod.pos : null,
    besitzerDim: () => mod.dim && jetzt() - mod.zeit < 3000 ? mod.dim : null,
    // Neuester Dimensionswechsel des Besitzers AUS dieser Dimension (letzte 30 min)
    portalSpur: (vonDim) => [...portalSpuren].reverse().find(p => p.von === vonDim && jetzt() - p.zeit < 1800000) ?? null,
    portalSpurVergessen: (spur) => { const i = portalSpuren.indexOf(spur); if (i >= 0) portalSpuren.splice(i, 1) },
    fallHoehe: () => hoechstesY == null ? 0 : Math.max(0, hoechstesY - bot.entity.position.y),
    fallZuruecksetzen: () => { hoechstesY = bot.entity.position.y }
  })
  return wahr
}

module.exports = { erstellen, NEUTRAL, NIE_ANGREIFEN }
