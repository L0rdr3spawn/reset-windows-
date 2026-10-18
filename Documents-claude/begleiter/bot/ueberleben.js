// Ueberleben: Totem/Schild in der Nebenhand, Ruestung, Essen mit Verstand, Goldaepfel, Traenke, Ausloggen.
function erstellen (ctx) {
  const { bot, mcData, einst, log, wahr, inv } = ctx
  let laeuft = false
  let letzteRuestung = 0
  let besitzerTotZeit = 0 // wann der Besitzer zuletzt gestorben ist
  const effekt = n => mcData.effectsByName[n]?.id
  const hatEffekt = n => bot.entity.effects?.[effekt(n)] != null
  const brennt = () => !!((bot.entity.metadata?.[0] ?? 0) & 0x01) || bot.entity.isInLava

  wahr.on('besitzerTot', () => { besitzerTotZeit = Date.now() })

  // ---------------------------------------------------------------- Ausloggen
  async function logoutPruefen () {
    let grund = null
    if (bot.health <= 0 || bot.isAlive === false) return false // tot: Mineflayer respawnt, kein Ausloggen mit Blackbox
    // Wenig Leben zaehlt nur bei Gefahr (Kampf, frischer Schaden, Feuer) - sonst regeneriert er einfach,
    // statt nach jedem Neu-Einloggen mit wenig Leben sofort wieder rauszugehen
    // Mit Totem erst bei sehr wenig Leben (das Totem faengt den Rest), ohne Totem schon frueh.
    const gefahr = wahr.imKampf() || Date.now() - wahr.zuletztGetroffen(bot.entity.id) < 10000 || brennt()
    const totems = totemAnzahl()
    const grenze = totems > 0 ? Math.min(einst.logoutLeben, 3) : einst.logoutLeben
    if (einst.logoutLeben > 0 && bot.health > 0 && bot.health <= grenze && gefahr) {
      grund = `wenig Leben (${Math.round(bot.health)}/20, ${totems ? totems + ' Totem(s)' : 'keine Totems mehr'}) - Schaden von: ${wahr.ursache() ?? 'unklar'}`
    } else if (einst.logoutHunger > 0 && bot.food <= einst.logoutHunger && !inv.bestesEssen({ notfall: true }) && !inv.goldapfel(false)) {
      grund = `verhungert (Hunger ${bot.food}, nichts zu essen)`
    } else if (einst.logoutBeiTodBesitzer && Date.now() - besitzerTotZeit < 30000) {
      // Nur ein frischer Tod zaehlt - sonst loggt er Stunden spaeter aus, sobald jemand die Option anschaltet
      grund = `${ctx.ich} ist gestorben`
    } else if (einst.logoutBeiUebermacht > 0) {
      const b = ctx.besitzer()
      const gegner = new Set()
      for (const o of [bot.entity, b].filter(Boolean)) {
        for (const e of wahr.angreiferVon(o.id, 10000)) if (wahr.istSpieler(e) && !wahr.istFreund(e) && !wahr.istBesitzer(e)) gegner.add(e.username)
      }
      if (gegner.size >= einst.logoutBeiUebermacht) grund = `Uebermacht (${[...gegner].join(', ')})`
    }
    // Ein Totem im Inventar kommt sofort per totemWaechter in die Nebenhand - dann kein Ausloggen
    if (!grund && einst.logoutLeben > 0 && bot.health <= 10 && totemAnzahl() === 0) {
      // Kann mich ein Gegner in der Naehe mit einem Schlag toeten (und kein Totem)?
      const gefahr = wahr.bedrohungen(5).find(b => b.griffAn && b.schaden >= bot.health)
      const bumm = wahr.sprengstoff(5)
      if (gefahr) grund = `Lebensgefahr: ${wahr.anzeigeName(gefahr.e)} kann ${Math.round(gefahr.schaden)} Schaden machen, ich habe nur ${Math.round(bot.health)}`
      else if (bumm) grund = `Lebensgefahr: ${bumm.name} ${bumm.d.toFixed(0)} Bloecke neben mir, ich habe nur ${Math.round(bot.health)} Leben`
      if (grund) { const u = wahr.ursache(); if (u) grund += ` (bisher: ${u})` }
    }
    if (!grund) return false
    await ctx.ausloggen(grund)
    return true
  }

  const totemAnzahl = () => inv.anzahl('totem_of_undying') + (inv.offhand()?.name === 'totem_of_undying' ? 1 : 0)

  // Sofort pruefen, wenn sich das Leben aendert (nicht erst im naechsten Gehirn-Takt).
  // Grosser Treffer (> 6 Schaden): 10 s lang Totem halten, falls gleich der naechste Smash kommt.
  let pruefLaeuft = false
  let lebenVorher = 20
  bot.on('health', () => {
    if (lebenVorher - bot.health > 6) { totemBis = Date.now() + 10000; log(`Grosser Treffer (${Math.round(lebenVorher - bot.health)}) - Totem bereithalten`) }
    lebenVorher = bot.health
    if (pruefLaeuft || ctx.ausloggenLaeuft) return
    totemWaechter()
    pruefLaeuft = true
    logoutPruefen().catch(() => {}).finally(() => { pruefLaeuft = false })
  })

  // ---------------------------------------------------------------- Totem vorausschauend
  // Ein Totem wirkt nur in der Hand. Kann ihn gleich etwas mit einem Schlag toeten (Mace von oben,
  // Kristall/Anker, Creeper, sehr starker Gegner), kommt das Totem SOFORT in die Nebenhand - egal wie viel Leben.
  let totemBis = 0
  function oneShotGefahr () {
    const p = bot.entity.position
    if (ctx.wasser.toedlicherSturz()) return 'toedlicher Sturz'
    for (const e of Object.values(bot.entities)) {
      if (e === bot.entity || !e.position) continue
      const d = e.position.distanceTo(p)
      if (d > 12) continue
      if (e.name === 'creeper' && d < 5) return 'Creeper'
      if ((e.name === 'tnt_minecart' || e.name === 'tnt' || e.name === 'end_crystal') && d < 6) return wahr.anzeigeName(e)
      if (!wahr.istSpieler(e)) continue
      const haelt = e.equipment?.[0]?.name ?? ''
      const horizontal = Math.hypot(e.position.x - p.x, e.position.z - p.z)
      // Besitzer/Freunde nur, wenn sie mich vorher selbst angegriffen haben (z.B. zum Testen)
      const harmlos = (wahr.istBesitzer(e) || wahr.istFreund(e)) && !wahr.hatAngegriffen(e.id, bot.entity.id, 60000)
      if (!harmlos && haelt === 'mace' && horizontal < 8 && (e.position.y - p.y > 1.5 || e.onGround === false)) return `${e.username} mit Mace in der Luft`
      // Attribut-Swap: die Mace ist nur im Schlag-Tick in der Hand. Deshalb zaehlt jeder Spieler, der von
      // oben nah auf mich faellt, als moeglicher Smash - egal, was er gerade haelt.
      const faellt = e.onGround === false && e.position.y - p.y > 2.5
      if (!harmlos && faellt && horizontal < 6) return `${e.username} stuerzt von oben auf mich`
      if (/end_crystal|respawn_anchor|tnt/.test(haelt) && d < 8) return `${e.username} mit ${haelt}`
      if (!wahr.istFreund(e) && !wahr.istBesitzer(e) && d < 5 && wahr.maxSchaden(e) >= bot.health - 1) return `${e.username} kann mich one-shotten`
    }
    return null
  }
  let totemWechselLaeuft = false
  function totemWaechter () {
    if (!bot.entity) return
    const grund = oneShotGefahr()
    if (grund) totemBis = Date.now() + 4000
    const brauchtTotem = Date.now() < totemBis || bot.health <= 10 || (!inv.offhand() && bot.health <= 16)
    if (!brauchtTotem || totemWechselLaeuft || inv.offhand()?.name === 'totem_of_undying') return
    const t = inv.totem()
    if (!t) return
    totemWechselLaeuft = true
    letzterWechsel = Date.now() // nebenhand() soll nicht gleichzeitig den Schild zuruecklegen
    ctx.kampf.schildRunter?.()
    bot.equip(t, 'off-hand')
      .then(() => log(`Totem in die Nebenhand${grund ? ' (' + grund + ')' : ''}`))
      .catch(e => log('Totem anlegen:', e.message))
      .finally(() => { totemWechselLaeuft = false })
  }
  // Totem ausgeloest (Status 35): sofort das naechste nachlegen
  bot._client.on('entity_status', p => {
    if (p.entityId !== bot.entity?.id || p.entityStatus !== 35) return
    log(`Totem verbraucht! Noch ${inv.anzahl('totem_of_undying')} uebrig.`)
    totemBis = Date.now() + 8000
    setTimeout(totemWaechter, 100)
  })

  // ---------------------------------------------------------------- Laufende Pflege
  function tick () {
    if (laeuft || bot.health <= 0) return
    laeuft = true
    pflege().catch(e => log('Ueberleben:', e.message)).finally(() => { laeuft = false })
  }

  // Besitzer hat kein Totem mehr (weiss nur die Mod) und ich mehr als meine 2 Reserve -> anbieten
  let letztesAngebot = 0
  function totemAnbieten () {
    const seine = wahr.besitzerTotems()
    const meine = totemAnzahl()
    if (seine !== 0 || meine <= 2 || Date.now() - letztesAngebot < 90000) return
    letztesAngebot = Date.now()
    ctx.melden({ typ: 'angebot', item: 'totem_of_undying', text: `Du hast kein Totem mehr - ich habe ${meine}. Willst du eins?` })
  }

  async function pflege () {
    totemAnbieten()
    const imKampf = wahr.imKampf()
    const gefahren = wahr.bedrohungen(8)
    const maxTreffer = Math.max(0, ...gefahren.filter(g => g.d < 6).map(g => g.schaden))

    // 1. Nebenhand: bei wenig Leben oder Explosionsgefahr Totem, sonst Schild (falls vorhanden)
    await nebenhand(gefahren)

    // 2. Brennen -> Feuerresistenz
    if (brennt() && !hatEffekt('FireResistance') && await trank(['fire_resistance', 'long_fire_resistance'], 85)) return

    // 3. Wenig Leben: heilen. Goldapfel nur, wenn mich keiner waehrend des Essens (1,6 s) umhauen kann
    if (bot.health <= 10) {
      if (await trank(['strong_healing', 'healing'], 90, { nurWerfen: imKampf })) return
      const kannOneshot = maxTreffer >= bot.health && !inv.offhand()?.name?.includes('totem')
      if (!kannOneshot && !hatEffekt('Regeneration')) {
        const verzaubert = bot.health <= 6 && inv.goldapfel(true)
        const apfel = verzaubert || inv.goldapfel(false)
        if (apfel && !hatEffekt('Absorption')) return essen(apfel, 80, 'Goldapfel')
      }
      if (kannOneshot) ctx.log(`Goldapfel zu riskant: Gegner kann ${Math.round(maxTreffer)} Schaden machen`)
    }

    // 4. Kampf gegen Spieler: Staerke/Tempo vorher trinken, wenn der Gegner noch weg ist
    const ziel = ctx.kampf.ziel()
    if (ziel && wahr.istSpieler(ziel) && ziel.position.distanceTo(bot.entity.position) > 6) {
      if (!hatEffekt('Strength') && await trank(['strong_strength', 'long_strength', 'strength'], 60)) return
      if (!hatEffekt('Speed') && await trank(['strong_swiftness', 'long_swiftness', 'swiftness'], 60)) return
    }

    // 5. Normales Essen: nie im Kampf, nichts Schlechtes (ausser bei echtem Hunger)
    if (!imKampf && bot.food < 20) {
      const regen = bot.health < 20 && bot.food < 18
      if (bot.food <= 14 || regen) {
        const e = inv.bestesEssen({ notfall: bot.food <= 4 })
        if (e) return essen(e, 40, e.displayName)
      }
    }
    if (imKampf && bot.food <= 6 && gefahren.every(g => g.d > 8)) {
      const e = inv.bestesEssen({ notfall: bot.food <= 3 })
      if (e) return essen(e, 45, e.displayName)
    }

    // 6. Ruestung (nicht mitten im Kampf, alle 5 s); Waffe statt Essen in der Hand
    if (!imKampf && Date.now() - letzteRuestung > 5000 && !ctx.elytra.aktiv() && !ctx.mace.aktiv()) {
      letzteRuestung = Date.now()
      if (await inv.ruestungAnlegen()) log('Ruestung verbessert.')
      // nicht waehrend Flug/Mace: da liegt der Brustpanzer fuer den Schnelltausch in der Hotbar
      if (!ctx.handBelegt() && !ctx.aufgaben.laeuft() && !ctx.elytra.aktiv() && !ctx.mace.aktiv()) await inv.hotbarOrdnen()
      if (!ctx.handBelegt() && !ctx.aufgaben.laeuft()) waffeInDieHand()
    }
  }

  // Nebenhand mit Hysterese: Totem ab <= 10 Leben (oder Explosionsgefahr) und dann so lange,
  // bis er wieder >= 16 hat; sonst Schild. Das Item in der Nebenhand zaehlt mit (liegt nicht im Inventar),
  // sonst wechselt er endlos hin und her.
  let letzterWechsel = 0
  async function nebenhand (gefahren) {
    if (ctx.handBelegt() || totemWechselLaeuft || Date.now() - letzterWechsel < 3000) return
    const off = inv.offhand()?.name
    const explosion = gefahren.some(g => g.e.name === 'creeper' && g.d < 6) || gefahren.some(g => wahr.istSpieler(g.e) && /crystal|anchor/.test(g.e.equipment?.[0]?.name ?? ''))
    const hatTotem = off === 'totem_of_undying' || !!inv.totem()
    const hatSchild = off === 'shield' || !!inv.schild()
    let will
    if (off === 'totem_of_undying') will = (bot.health >= 16 && !explosion && hatSchild && Date.now() > totemBis) ? 'shield' : 'totem_of_undying'
    else will = hatTotem && (bot.health <= 10 || explosion || !hatSchild) ? 'totem_of_undying' : hatSchild ? 'shield' : null
    if (!will || off === will) return
    const item = will === 'shield' ? inv.schild() : inv.totem()
    if (!item) return
    letzterWechsel = Date.now()
    ctx.kampf.schildRunter?.()
    await bot.equip(item, 'off-hand')
    log(`Nebenhand: ${will === 'shield' ? 'Schild' : 'Totem'} (Leben ${Math.round(bot.health)})`)
  }

  // Eigenes Verbrauchen statt bot.consume(): das endet bei jedem Slot-Update des Servers zu frueh.
  // Fertig ist es erst, wenn der Stapel kleiner geworden ist.
  async function verbrauchen (item, maxMs = 2600) {
    const vorher = inv.anzahl(item.name)
    await bot.equip(item, 'hand')
    bot.activateItem()
    const start = Date.now()
    while (Date.now() - start < maxMs) {
      await ctx.warte(100)
      if (inv.anzahl(item.name) < vorher) break
      if (bot.heldItem?.name !== item.name) break
    }
    bot.deactivateItem()
    return inv.anzahl(item.name) < vorher
  }

  let letztesEssen = 0
  async function essen (item, prio, was) {
    if (Date.now() - letztesEssen < 1500) return false
    if (!ctx.handNehmen('essen', prio, 3500)) return false
    try {
      bot.pathfinder.setGoal(null)
      const ok = await verbrauchen(item)
      letztesEssen = Date.now()
      log(ok ? `Gegessen: ${was} (Leben ${Math.round(bot.health)}, Hunger ${bot.food})` : `Essen (${was}) nicht fertig geworden`)
      return ok
    } catch (e) {
      log(`Essen (${was}) fehlgeschlagen: ${e.message}`)
      return false
    } finally {
      ctx.handFrei('essen')
      // Hat inzwischen ein anderer (Kampf, Elytra, MLG) die Hand, nicht dazwischenfunken
      if (!ctx.handBelegt()) waffeInDieHand()
    }
  }

  function waffeInDieHand () {
    const w = inv.besteWaffe(ctx.kampf.ziel())
    if (w && bot.heldItem?.name !== w.name) inv.halten(w)
  }

  // Trank trinken oder werfen (Wurftraenke vor die Fuesse)
  const trankSperre = new Map() // art -> bis (nach Fehlversuch nicht sofort nochmal)
  async function trank (arten, prio, { nurWerfen = false } = {}) {
    if (arten.some(a => (trankSperre.get(a) ?? 0) > Date.now())) return false
    const alle = inv.traenke()
    const t = arten.map(a => alle.find(x => x.art === a && (x.werfen || !nurWerfen))).find(Boolean)
    if (!t) return false
    if (!ctx.handNehmen('trank', prio, t.werfen ? 600 : 3500)) return false
    try {
      await bot.equip(t.item, 'hand')
      if (t.werfen) {
        await bot.look(bot.entity.yaw, -Math.PI / 2, true)
        bot.activateItem()
        bot.deactivateItem()
      } else if (!await verbrauchen(t.item)) {
        trankSperre.set(t.art, Date.now() + 15000)
        log(`Trank ${t.art} nicht fertig getrunken`)
        return false
      }
      log(`Trank: ${t.art}${t.werfen ? ' (geworfen)' : ''}`)
      trankSperre.set(t.art, Date.now() + 5000)
      return true
    } catch (e) {
      log(`Trank ${t.art} fehlgeschlagen: ${e.message}`)
      return false
    } finally {
      ctx.handFrei('trank')
      if (!ctx.handBelegt()) waffeInDieHand()
    }
  }

  return { tick, logoutPruefen, essen, trank, brennt, totemWaechter }
}

module.exports = { erstellen }
