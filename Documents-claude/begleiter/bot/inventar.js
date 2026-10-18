// Was hat der Bot, was taugt es? Waffen, Ruestung, Essen, Traenke, Spezialitems.

// [Schaden, Angriffe pro Sekunde]
const WAFFEN = {
  wooden_sword: [4, 1.6], golden_sword: [4, 1.6], stone_sword: [5, 1.6], copper_sword: [5, 1.6], iron_sword: [6, 1.6], diamond_sword: [7, 1.6], netherite_sword: [8, 1.6],
  wooden_axe: [7, 0.8], golden_axe: [7, 1.0], stone_axe: [9, 0.8], copper_axe: [9, 0.8], iron_axe: [9, 0.9], diamond_axe: [9, 1.0], netherite_axe: [10, 1.0],
  mace: [6, 0.6], trident: [9, 1.1],
  wooden_spear: [2, 1.5], golden_spear: [2, 1.5], stone_spear: [3, 1.4], copper_spear: [3, 1.4], iron_spear: [4, 1.3], diamond_spear: [5, 1.2], netherite_spear: [6, 1.1]
}

// Ruestungspunkte je Slot [Kopf, Brust, Beine, Fuesse] und Haerte
const RUESTUNG = {
  leather: [[1, 3, 2, 1], 0], golden: [[2, 5, 3, 1], 0], chainmail: [[2, 5, 4, 1], 0], copper: [[2, 4, 3, 1], 0],
  iron: [[2, 6, 5, 2], 0], diamond: [[3, 8, 6, 3], 2], netherite: [[3, 8, 6, 3], 3], turtle: [[2, 0, 0, 0], 0]
}
const SLOTS = ['helmet', 'chestplate', 'leggings', 'boots']
const SLOT_ZIEL = { helmet: 'head', chestplate: 'torso', leggings: 'legs', boots: 'feet' }
const RUESTUNG_SLOTNR = { head: 5, torso: 6, legs: 7, feet: 8 }

// Essen, das Nachteile hat: nur im Notfall (Hunger) bzw. nie
const SCHLECHTES_ESSEN = new Set(['rotten_flesh', 'spider_eye', 'poisonous_potato', 'pufferfish', 'chicken', 'suspicious_stew'])
const NIE_ESSEN = new Set(['chorus_fruit']) // teleportiert zufaellig
const GOLDAEPFEL = new Set(['golden_apple', 'enchanted_golden_apple'])

// Vanilla-Reihenfolge des Trank-Registers (Fallback, falls der Server kein Register schickt)
const TRAENKE = ['water', 'mundane', 'thick', 'awkward', 'night_vision', 'long_night_vision', 'invisibility', 'long_invisibility',
  'leaping', 'long_leaping', 'strong_leaping', 'fire_resistance', 'long_fire_resistance', 'swiftness', 'long_swiftness', 'strong_swiftness',
  'slowness', 'long_slowness', 'strong_slowness', 'turtle_master', 'long_turtle_master', 'strong_turtle_master', 'water_breathing',
  'long_water_breathing', 'healing', 'strong_healing', 'harming', 'strong_harming', 'poison', 'long_poison', 'strong_poison',
  'regeneration', 'long_regeneration', 'strong_regeneration', 'strength', 'long_strength', 'strong_strength', 'weakness', 'long_weakness',
  'luck', 'slow_falling', 'long_slow_falling', 'wind_charged', 'weaving', 'oozing', 'infested']

function erstellen (ctx) {
  const { bot, mcData, log } = ctx
  const items = () => bot.inventory.items()
  const anzahl = name => items().filter(i => i.name === name).reduce((s, i) => s + i.count, 0)
  const finde = pred => items().find(pred)
  const offhand = () => bot.inventory.slots[45]
  const getragen = slot => bot.inventory.slots[RUESTUNG_SLOTNR[slot]]

  function verzauberungen (item) {
    if (!item) return []
    const reg = ctx.register.enchantment
    try {
      const c = item.componentMap?.get('enchantments')?.data
      if (c?.enchantments) return c.enchantments.map(e => ({ name: String(reg?.[e.id] ?? mcData.enchantments[e.id]?.name).replace('minecraft:', ''), lvl: e.level }))
      return (item.enchants ?? []).map(e => ({ name: String(e.name).replace('minecraft:', ''), lvl: e.lvl }))
    } catch { return [] }
  }

  // Verzauberte Buecher tragen ihre Verzauberungen in "stored_enchantments"
  function buchVerzauberungen (item) {
    const c = item?.componentMap?.get('stored_enchantments')?.data
    if (!c?.enchantments) return []
    const reg = ctx.register.enchantment
    return c.enchantments.map(e => ({ name: String(reg?.[e.id] ?? mcData.enchantments[e.id]?.name).replace('minecraft:', ''), lvl: e.level }))
  }

  // Schnappschuss fuer die Mod-Oberflaeche (/bot inv). Slotnummern wie im Spieler-Inventarfenster:
  // 5-8 Ruestung (Kopf..Fuesse), 9-35 Rucksack, 36-44 Hotbar, 45 Nebenhand
  function schnappschuss () {
    const slots = []
    for (let s = 5; s <= 45; s++) {
      const i = bot.inventory.slots[s]
      if (!i) continue
      const d = { slot: s, name: i.name, anzahl: i.count }
      const v = verzauberungen(i)
      if (v.length) d.verz = v
      const b = buchVerzauberungen(i)
      if (b.length) d.buch = b
      if (i.durabilityUsed) d.schaden = i.durabilityUsed
      const t = trankArt(i)
      if (t) d.trank = t
      slots.push(d)
    }
    return { slots, gehalten: bot.quickBarSlot, leben: bot.health, hunger: bot.food }
  }

  function verzauberung (item, name) {
    if (!item) return 0
    const reg = ctx.register.enchantment
    let liste = []
    try {
      const c = item.componentMap?.get('enchantments')?.data
      if (c?.enchantments) liste = c.enchantments.map(e => ({ name: reg?.[e.id] ?? mcData.enchantments[e.id]?.name, lvl: e.level }))
      else liste = item.enchants ?? []
    } catch { liste = [] }
    return liste.find(e => e.name === name || e.name === `minecraft:${name}`)?.lvl ?? 0
  }

  function trankArt (item) {
    const c = item?.componentMap?.get('potion_contents')?.data
    if (c?.potionId == null) return null
    return (ctx.register.potion ?? TRAENKE)[c.potionId] ?? null
  }

  // Schaden eines Treffers mit voller Ladung (ohne Krit/Mace-Fall)
  function waffenSchaden (item, ziel) {
    const w = WAFFEN[item?.name]
    if (!w) return 1
    let s = w[0]
    const schaerfe = verzauberung(item, 'sharpness')
    if (schaerfe) s += 0.5 * schaerfe + 0.5
    if (ziel && UNTOT.has(ziel.name)) s += 2.5 * verzauberung(item, 'smite')
    if (ziel && GLIEDER.has(ziel.name)) s += 2.5 * verzauberung(item, 'bane_of_arthropods')
    return s
  }
  const angriffsTempo = item => WAFFEN[item?.name]?.[1] ?? 4

  // Beste Nahkampfwaffe: normalerweise nach Schaden pro Sekunde, gegen Schild die Axt
  function besteWaffe (ziel, { schildBrechen = false } = {}) {
    const kandidaten = items().filter(i => WAFFEN[i.name] && !i.name.endsWith('_spear') && i.name !== 'trident')
    if (schildBrechen) {
      const axt = kandidaten.filter(i => i.name.endsWith('_axe')).sort((a, b) => waffenSchaden(b, ziel) - waffenSchaden(a, ziel))[0]
      if (axt) return axt
    }
    // Mace nur fuer Fallangriffe, nicht als Dauerwaffe
    return kandidaten.filter(i => i.name !== 'mace')
      .sort((a, b) => waffenSchaden(b, ziel) * Math.min(angriffsTempo(b), 1.6) - waffenSchaden(a, ziel) * Math.min(angriffsTempo(a), 1.6))[0] ?? null
  }

  function ruestungWert (item) {
    const m = item.name.match(/^(\w+?)_(helmet|chestplate|leggings|boots)$/)
    if (!m || !RUESTUNG[m[1]]) return -1
    const [punkte, haerte] = RUESTUNG[m[1]]
    return punkte[SLOTS.indexOf(m[2])] + haerte * 0.5 + verzauberung(item, 'protection') * 0.75 +
      (verzauberung(item, 'binding_curse') ? -50 : 0)
  }

  // Aktuelle Ruestungspunkte und Haerte (fuer Schadensschaetzung)
  function schutz () {
    let punkte = 0; let haerte = 0; let epf = 0
    for (const slot of Object.keys(RUESTUNG_SLOTNR)) {
      const it = getragen(slot)
      const m = it?.name.match(/^(\w+?)_(helmet|chestplate|leggings|boots)$/)
      if (!m || !RUESTUNG[m[1]]) continue
      punkte += RUESTUNG[m[1]][0][SLOTS.indexOf(m[2])]
      haerte += RUESTUNG[m[1]][1]
      epf += verzauberung(it, 'protection')
    }
    return { punkte, haerte, epf: Math.min(epf, 20) }
  }

  let ruestenLaeuft = false
  async function ruestungAnlegen ({ ausserBrust = false } = {}) {
    if (ruestenLaeuft) return false
    ruestenLaeuft = true
    let geaendert = false
    try {
      for (const typ of SLOTS) {
        // Flug/Mace-Sturz tauschen Brustpanzer und Elytra selbst - nicht gleichzeitig daran ziehen
        if (ctx.elytra?.aktiv() || ctx.mace?.aktiv()) break
        const ziel = SLOT_ZIEL[typ]
        if (ausserBrust && ziel === 'torso') continue
        const an = getragen(ziel)
        if (an?.name === 'elytra') continue // Elytra verwaltet das Flugmodul
        const bestes = items().filter(i => i.name.endsWith('_' + typ)).sort((a, b) => ruestungWert(b) - ruestungWert(a))[0]
        // Fluch der Bindung (Wert < 0) nie anziehen, auch nicht in einen leeren Slot
        if (bestes && ruestungWert(bestes) > 0 && (!an || ruestungWert(bestes) > ruestungWert(an))) {
          await bot.equip(bestes, ziel)
          geaendert = true
        }
      }
    } catch (e) {
      log('Ruestung anlegen fehlgeschlagen:', e.message)
    } finally {
      ruestenLaeuft = false
    }
    return geaendert
  }

  function bestesEssen ({ notfall = false } = {}) {
    const essbar = items().filter(i => mcData.foodsByName[i.name] && !NIE_ESSEN.has(i.name) && !GOLDAEPFEL.has(i.name))
    const gut = essbar.filter(i => !SCHLECHTES_ESSEN.has(i.name))
    const auswahl = gut.length ? gut : (notfall ? essbar : [])
    // Hoechste Saettigung zuerst, aber nichts verschwenden: bei wenig Hunger lieber Kleines
    return auswahl.sort((a, b) => mcData.foodsByName[b.name].effectiveQuality - mcData.foodsByName[a.name].effectiveQuality)[0] ?? null
  }

  const goldapfel = (verzaubert) => finde(i => i.name === (verzaubert ? 'enchanted_golden_apple' : 'golden_apple'))
  const traenke = () => items().filter(i => /^(splash_|lingering_)?potion$/.test(i.name)).map(i => ({ item: i, art: trankArt(i), werfen: i.name !== 'potion' }))

  // Item in eine Hotbar-Position bringen, damit spaeter blitzschnell gewechselt werden kann
  async function inHotbar (item, bevorzugt = 8) {
    if (!item) return null
    if (item.slot >= 36 && item.slot <= 44) return item.slot - 36
    const frei = [bevorzugt, 7, 6, 5, 4, 3, 2, 1, 0].find(n => !bot.inventory.slots[36 + n]) ?? bevorzugt
    await bot.moveSlotItem(item.slot, 36 + frei)
    return frei
  }

  // Sofortiger Hotbar-Wechsel ohne Warten (fuer Kampf, Mace, Raketen)
  function halten (item) {
    if (!item) return false
    if (item.slot >= 36 && item.slot <= 44) {
      if (bot.quickBarSlot !== item.slot - 36) bot.setQuickBarSlot(item.slot - 36)
      return true
    }
    bot.equip(item, 'hand').catch(() => {})
    return false
  }

  // Feste Hotbar, damit Wechsel im Kampf ohne Inventar-Klicks gehen:
  // 0 Nahkampf, 1 Axt, 2 Mace, 3 Windladung, 4 Speer, 5 Goldapfel, 6 Essen, 7 Wassereimer, 8 Raketen
  let ordnenLaeuft = false
  async function hotbarOrdnen () {
    if (ordnenLaeuft) return
    ordnenLaeuft = true
    try {
      // Funktionen statt Items: nach jedem Tausch liegen die Items woanders
      const plan = [
        [() => besteWaffe(null), 0], [() => besteWaffe(null, { schildBrechen: true }), 1], [() => inv.mace(), 2], [() => inv.windladung(), 3],
        [() => inv.speer(), 4], [() => goldapfel(false), 5], [() => bestesEssen(), 6],
        [() => finde(i => i.name === 'water_bucket') ?? finde(i => i.name === 'bucket'), 7], [() => inv.raketen(), 8]
      ]
      const erledigt = new Set()
      for (const [holen, slot] of plan) {
        const item = holen()
        if (!item || erledigt.has(item.slot)) continue // gleiches Item doppelt im Plan (z.B. keine Axt)
        if (item.slot !== 36 + slot) await bot.moveSlotItem(item.slot, 36 + slot)
        erledigt.add(36 + slot)
      }
    } catch (e) {
      log('Hotbar ordnen:', e.message)
    } finally {
      ordnenLaeuft = false
    }
  }

  const inv = {
    hotbarOrdnen,
    WAFFEN, SCHLECHTES_ESSEN, GOLDAEPFEL,
    items, anzahl, finde, offhand, getragen, verzauberung, verzauberungen, buchVerzauberungen, trankArt, schnappschuss,
    waffenSchaden, angriffsTempo, besteWaffe, ruestungWert, schutz, ruestungAnlegen,
    bestesEssen, goldapfel, traenke, inHotbar, halten,
    elytra: () => finde(i => i.name === 'elytra') ?? (getragen('torso')?.name === 'elytra' ? getragen('torso') : null),
    raketen: () => finde(i => i.name === 'firework_rocket'),
    windladung: () => finde(i => i.name === 'wind_charge'),
    mace: () => finde(i => i.name === 'mace'),
    speer: () => items().filter(i => i.name.endsWith('_spear')).sort((a, b) => verzauberung(b, 'lunge') - verzauberung(a, 'lunge') || waffenSchaden(b) - waffenSchaden(a))[0] ?? null,
    totem: () => finde(i => i.name === 'totem_of_undying'),
    schild: () => finde(i => i.name === 'shield'),
    freieSlots: () => bot.inventory.emptySlotCount(),
    kurz () {
      const summe = {}
      for (const i of items()) summe[i.name] = (summe[i.name] ?? 0) + i.count
      return summe
    }
  }
  return inv
}

const UNTOT = new Set(['zombie', 'zombie_villager', 'husk', 'drowned', 'skeleton', 'stray', 'wither_skeleton', 'bogged', 'phantom',
  'zombified_piglin', 'zoglin', 'wither', 'skeleton_horse', 'zombie_horse', 'parched', 'camel_husk', 'zombie_nautilus'])
const GLIEDER = new Set(['spider', 'cave_spider', 'silverfish', 'endermite', 'bee'])

module.exports = { erstellen, UNTOT }
