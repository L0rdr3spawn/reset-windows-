// Erzeugt src/main/resources/assets/jevbaritone/wissen.json aus minecraft-data (Rezepte, Werkzeugstufen, Drops).
// Aufruf aus mc-bot/: node ../jevbaritone/wissen-erzeugen.js
const fs = require('fs')
const path = require('path')
const d = require('minecraft-data')('26.1')
const name = id => d.items[id]?.name

// Bei mehreren Rezeptvarianten die mit den gewoehnlichsten Zutaten nehmen
const GEWOEHNLICH = /^(oak_|cobblestone$|stick$|coal$|iron_ingot$|gold_ingot$|diamond$|string$|leather$|redstone$|copper_ingot$|stone$|sand$|glass$|white_wool$|paper$|feather$|flint$|wheat$|slime_ball$)/
function zutaten (r) {
  const z = {}
  const liste = r.inShape ? r.inShape.flat() : r.ingredients ?? []
  for (const id of liste) if (id != null) z[name(id)] = (z[name(id)] ?? 0) + 1
  return z
}
function breite (r) { return r.inShape ? Math.max(r.inShape.length, ...r.inShape.map(row => row.length)) : Math.ceil(Math.sqrt((r.ingredients ?? []).length)) }
function selten (r) { return Object.keys(zutaten(r)).filter(n => !GEWOEHNLICH.test(n)).length }

const rezepte = {}
for (const [id, varianten] of Object.entries(d.recipes)) {
  const n = name(+id)
  if (!n) continue
  // Barren aus Bloecken/Nuggets zurueck ist kein sinnvoller Weg
  const brauchbar = varianten.filter(r => !Object.keys(zutaten(r)).some(z => z === n.replace('_ingot', '_block') || z.endsWith('_nugget') && n.endsWith('_ingot')))
  const r = (brauchbar.length ? brauchbar : varianten).slice().sort((a, b) => selten(a) - selten(b))[0]
  rezepte[n] = { n: r.result.count, z: zutaten(r), tisch: breite(r) > 2 }
}

// Welcher Block droppt einen Rohstoff und welche Spitzhacke braucht er mindestens
const STUFE = ['wooden_pickaxe', 'stone_pickaxe', 'iron_pickaxe', 'diamond_pickaxe', 'netherite_pickaxe']
const quellen = {}
for (const b of d.blocksArray) {
  const tools = Object.keys(b.harvestTools ?? {}).map(name)
  const pick = STUFE.find(t => tools.includes(t))
  for (const dropId of b.drops ?? []) {
    const drop = name(dropId)
    if (!drop) continue
    // pro Drop die einfachste Quelle behalten (Erz vor Tiefenschiefer-Erz)
    if (!quellen[drop] || (quellen[drop].block.startsWith('deepslate_') && !b.name.startsWith('deepslate_'))) {
      quellen[drop] = { block: b.name, werkzeug: pick ?? null }
    }
  }
}

const schmelzen = {
  iron_ingot: 'raw_iron', gold_ingot: 'raw_gold', copper_ingot: 'raw_copper', glass: 'sand', stone: 'cobblestone',
  smooth_stone: 'stone', charcoal: 'oak_log', brick: 'clay_ball', cooked_beef: 'beef', cooked_porkchop: 'porkchop',
  cooked_chicken: 'chicken', cooked_mutton: 'mutton', cooked_cod: 'cod', cooked_salmon: 'salmon', baked_potato: 'potato',
  netherite_scrap: 'ancient_debris', dried_kelp: 'kelp', green_dye: 'cactus', terracotta: 'clay'
}

const ziel = path.join(__dirname, 'src/main/resources/assets/jevbaritone/wissen.json')
fs.writeFileSync(ziel, JSON.stringify({ rezepte, quellen, schmelzen }))
console.log('rezepte', Object.keys(rezepte).length, 'quellen', Object.keys(quellen).length, (fs.statSync(ziel).size / 1024).toFixed(0) + ' KB')
for (const n of ['diamond_pickaxe', 'stick', 'furnace', 'iron_ingot', 'torch', 'crafting_table', 'oak_planks']) console.log(n, JSON.stringify(rezepte[n]))
for (const n of ['diamond', 'raw_iron', 'cobblestone', 'coal', 'oak_log']) console.log(n, JSON.stringify(quellen[n]))
