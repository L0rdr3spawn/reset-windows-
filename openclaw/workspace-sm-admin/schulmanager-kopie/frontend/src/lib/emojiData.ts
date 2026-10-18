/**
 * Emoji für die Auswahl (Chats, Postfach): reine Unicode-Zeichen, nichts wird nachgeladen. Je Zeile
 * „Emoji Suchwörter …“ (deutsch, klein geschrieben); die Suche vergleicht Teilwörter.
 */
export interface EmojiCategory {
  id: string;
  label: string;
  icon: string;
  items: { e: string; k: string }[];
}

const parse = (block: string): { e: string; k: string }[] =>
  block
    .trim()
    .split('\n')
    .map((line) => {
      const [e, ...rest] = line.trim().split(' ');
      return { e, k: rest.join(' ') };
    })
    .filter((x) => x.e);

export const EMOJI_CATEGORIES: EmojiCategory[] = [
  {
    id: 'smileys',
    label: 'Smileys',
    icon: '😀',
    items: parse(`
😀 lachen grinsen froh
😃 lachen freude
😄 lachen glücklich
😁 grinsen strahlen
😆 lachen kichern
😅 schweiß erleichtert lachen
😂 tränen lachen lol
🤣 rollen lachen
🙂 lächeln
🙃 kopfstand umgedreht
😉 zwinkern
😊 lächeln erröten
😇 engel heilig
🥰 verliebt herzen
😍 herzaugen verliebt
🤩 begeistert sterne wow
😘 kuss
😗 kuss
😚 kuss
😙 kuss
😋 lecker zunge
😛 zunge
😜 zunge zwinkern verrückt
🤪 verrückt
😝 zunge
🤑 geld
🤗 umarmung
🤭 kichern hand
🤫 pst leise
🤔 nachdenken hmm
🤐 mund zu reißverschluss
🤨 skeptisch augenbraue
😐 neutral
😑 ausdruckslos
😶 sprachlos
😏 grinsen schmunzeln
😒 genervt
🙄 augen rollen
😬 grimasse
😮‍💨 ausatmen seufzen
🤥 lügen nase
😌 erleichtert ruhig
😔 traurig nachdenklich
😪 müde
🤤 sabbern
😴 schlafen müde
😷 maske krank
🤒 fieber krank
🤕 verband verletzt
🤢 übel
🤮 erbrechen
🤧 niesen
🥵 heiß schwitzen
🥶 kalt frieren
🥴 benommen
😵 schwindel
🤯 explodiert kopf
🤠 cowboy
🥳 party feiern
😎 cool sonnenbrille
🤓 streber brille nerd
🧐 monokel
😕 verwirrt
😟 besorgt
🙁 traurig
☹️ traurig
😮 überrascht offen
😯 überrascht
😲 erstaunt
😳 erröten peinlich
🥺 bitte flehen
😦 entsetzt
😧 ängstlich
😨 angst
😰 angst schweiß
😥 traurig erleichtert
😢 weinen träne
😭 heulen weinen
😱 schreien schock
😖 verzweifelt
😣 durchhalten
😞 enttäuscht
😓 schweiß
😩 erschöpft
😫 müde
🥱 gähnen langweilig
😤 schnaufen wütend
😡 wütend sauer
😠 böse
🤬 fluchen
😈 teufel
👿 teufel wütend
💀 totenkopf
☠️ totenkopf
💩 haufen
🤡 clown
👻 geist
👽 alien
🤖 roboter
🙈 affe nicht sehen
🙉 affe nicht hören
🙊 affe nicht sprechen
`),
  },
  {
    id: 'gesten',
    label: 'Gesten & Menschen',
    icon: '👍',
    items: parse(`
👍 daumen hoch gut ok
👎 daumen runter schlecht
👌 ok perfekt
🤌 italienisch
✌️ victory frieden
🤞 daumen drücken glück
🤟 liebe
🤘 rock
🤙 ruf mich an
👈 links zeigen
👉 rechts zeigen
👆 hoch zeigen
👇 runter zeigen
☝️ eins zeigen
✋ stopp hand
🤚 hand
🖐️ hand
🖖 vulkanier
👋 winken hallo tschüss
🤝 handschlag
👏 klatschen applaus
🙌 hurra hände
👐 offene hände
🤲 hände
🙏 bitte danke beten
✍️ schreiben
💪 stark muskel
🦾 roboterarm
🧠 gehirn
👀 augen schauen
👁️ auge
👂 ohr
👃 nase
👄 mund
🫶 herz hände
🫡 salut
🫠 schmelzen
🫣 spähen
👶 baby
🧒 kind
👦 junge
👧 mädchen
🧑 person
👨 mann
👩 frau
🧑‍🎓 schüler student
🧑‍🏫 lehrer lehrerin
👨‍👩‍👧 familie
🧑‍💻 computer entwickler
🦸 held
🧙 zauberer
🧛 vampir
🧜 meerjungfrau
🧞 geist dschinn
🤷 schulterzucken keine ahnung
🤦 facepalm
🙋 melden hand heben
💁 hinweis
🙅 nein
🙆 ja
🏃 laufen rennen
💃 tanzen
🕺 tanzen
🚶 gehen
🧘 yoga ruhe
`),
  },
  {
    id: 'herzen',
    label: 'Herzen & Symbole',
    icon: '❤️',
    items: parse(`
❤️ herz liebe rot
🧡 herz orange
💛 herz gelb
💚 herz grün
💙 herz blau
💜 herz lila
🖤 herz schwarz
🤍 herz weiß
🤎 herz braun
💔 gebrochenes herz
❣️ herz ausrufezeichen
💕 zwei herzen
💞 herzen
💓 herzschlag
💗 herz wachsend
💖 herz funkeln
💘 herz pfeil
💝 herz geschenk
💯 hundert punkte
💢 wut
💥 knall
💫 schwindel stern
💦 tropfen schweiß
💨 wind sausen
💤 schlafen zzz
🔥 feuer heiß
✨ funkeln glitzer
⭐ stern
🌟 stern glänzend
💡 idee glühbirne
🎉 party konfetti
🎊 konfetti
🎈 luftballon
🎁 geschenk
🏆 pokal sieg
🥇 gold erster
🥈 silber zweiter
🥉 bronze dritter
🏅 medaille
✅ erledigt haken
❌ falsch kreuz
❗ ausrufezeichen
❓ fragezeichen
⚠️ warnung
🚫 verboten
⛔ eintritt verboten
➕ plus
➖ minus
➡️ pfeil rechts
⬅️ pfeil links
⬆️ pfeil hoch
⬇️ pfeil runter
🔔 glocke benachrichtigung
🔕 stumm
🔒 schloss
🔓 offen
🔑 schlüssel
📌 pinnnadel
📎 büroklammer
🔗 link
✔️ haken
♻️ recycling
🇩🇪 deutschland flagge
🇦🇹 österreich flagge
🇨🇭 schweiz flagge
🇪🇺 europa flagge
🏳️‍🌈 regenbogen flagge
`),
  },
  {
    id: 'tiere',
    label: 'Tiere & Natur',
    icon: '🐶',
    items: parse(`
🐶 hund
🐱 katze
🐭 maus
🐹 hamster
🐰 hase kaninchen
🦊 fuchs
🐻 bär
🐼 panda
🐨 koala
🐯 tiger
🦁 löwe
🐮 kuh
🐷 schwein
🐸 frosch
🐵 affe
🐔 huhn
🐧 pinguin
🐦 vogel
🐤 küken
🦆 ente
🦉 eule
🦇 fledermaus
🐺 wolf
🐴 pferd
🦄 einhorn
🐝 biene
🐛 raupe käfer
🦋 schmetterling
🐌 schnecke
🐞 marienkäfer
🐢 schildkröte
🐍 schlange
🦖 dinosaurier
🐙 krake
🐠 fisch
🐬 delfin
🐳 wal
🦈 hai
🐘 elefant
🦒 giraffe
🌵 kaktus
🌲 baum tanne
🌳 baum
🌴 palme
🌱 pflanze setzling
🍀 kleeblatt glück
🍁 ahorn herbst blatt
🌸 blüte kirschblüte
🌹 rose
🌻 sonnenblume
🌷 tulpe
🌍 erde welt
🌙 mond
☀️ sonne
⛅ wolke sonne
☁️ wolke
🌧️ regen
⛈️ gewitter
❄️ schnee
☃️ schneemann
🌈 regenbogen
⚡ blitz
🌊 welle wasser
`),
  },
  {
    id: 'essen',
    label: 'Essen & Trinken',
    icon: '🍕',
    items: parse(`
🍎 apfel
🍐 birne
🍊 orange mandarine
🍋 zitrone
🍌 banane
🍉 wassermelone
🍇 trauben
🍓 erdbeere
🫐 blaubeeren
🍒 kirschen
🍑 pfirsich
🥭 mango
🍍 ananas
🥝 kiwi
🍅 tomate
🥑 avocado
🥕 karotte möhre
🌽 mais
🥔 kartoffel
🍞 brot
🥐 croissant
🥨 brezel
🧀 käse
🥚 ei
🍳 spiegelei
🥓 speck
🍔 burger hamburger
🍟 pommes
🍕 pizza
🌭 hotdog
🥪 sandwich
🌮 taco
🌯 wrap döner
🍝 nudeln spaghetti
🍜 suppe nudelsuppe
🍣 sushi
🍦 eis
🍩 donut
🍪 keks
🎂 geburtstag torte kuchen
🍰 kuchen
🍫 schokolade
🍬 bonbon süßigkeit
🍿 popcorn
☕ kaffee
🍵 tee
🥛 milch
🧃 saft
🥤 getränk becher
🍺 bier
🍻 prost bier
🥂 sekt prost
🍷 wein
🍽️ teller essen
`),
  },
  {
    id: 'aktivitaeten',
    label: 'Aktivitäten & Schule',
    icon: '⚽',
    items: parse(`
⚽ fußball
🏀 basketball
🏈 football
⚾ baseball
🎾 tennis
🏐 volleyball
🏓 tischtennis
🏸 badminton
🥊 boxen
🏊 schwimmen
🚴 radfahren
⛷️ ski
🏂 snowboard
🎮 videospiel zocken
🕹️ joystick
🎲 würfel spiel
♟️ schach
🎯 ziel treffer
🎨 malen kunst
🎭 theater
🎤 mikrofon singen
🎧 kopfhörer musik
🎵 musik note
🎶 musik noten
🎸 gitarre
🎹 klavier
🥁 schlagzeug
🎬 film klappe
📚 bücher lernen schule
📖 buch lesen
📝 notizen schreiben hausaufgabe
✏️ bleistift
🖊️ stift
📐 geodreieck mathe
📏 lineal
🧮 abakus rechnen
🔬 mikroskop biologie
🧪 chemie reagenzglas
🔭 teleskop physik
🌐 globus erdkunde
🎒 schulranzen rucksack schule
🏫 schule
🎓 abschluss hut
🧑‍🎓 schüler
🧑‍🏫 lehrer
📅 kalender termin
⏰ wecker
⌛ sanduhr
🕒 uhr
💻 laptop computer
🖥️ computer
📱 handy smartphone
📷 kamera foto
📸 foto blitz
📧 mail email
✉️ brief umschlag
📞 telefon
📢 lautsprecher durchsage
📊 diagramm statistik
📁 ordner
🗂️ ablage
💰 geld
🧾 quittung
`),
  },
  {
    id: 'reisen',
    label: 'Reisen & Orte',
    icon: '🚌',
    items: parse(`
🚗 auto
🚕 taxi
🚌 bus
🚎 trolleybus
🚑 krankenwagen
🚒 feuerwehr
🚓 polizei
🚲 fahrrad
🛴 roller
🚂 zug lokomotive
🚆 zug
🚇 u-bahn
🚉 bahnhof
✈️ flugzeug
🚀 rakete
🛸 ufo
⛵ segelboot
🚢 schiff
⚓ anker
🏠 haus zuhause
🏡 haus garten
🏢 büro gebäude
🏥 krankenhaus
🏫 schule
🏰 burg schloss
🗼 turm
🗽 freiheitsstatue
⛪ kirche
🕌 moschee
🕍 synagoge
🏖️ strand urlaub
🏕️ camping zelt
⛰️ berg
🌋 vulkan
🗺️ karte
🧭 kompass
🏔️ berge schnee
🌅 sonnenaufgang
🌃 nacht stadt
🎡 riesenrad
🎢 achterbahn
⛺ zelt
`),
  },
];

/** Alle Emoji der Suchfunktion, einmal berechnet. */
const ALL = EMOJI_CATEGORIES.flatMap((c) => c.items);

/** Suche über Suchwörter (Teilwörter, Groß-/Kleinschreibung egal); höchstens `limit` Treffer. */
export function searchEmoji(query: string, limit = 96): { e: string; k: string }[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const words = q.split(/\s+/);
  const seen = new Set<string>();
  const out: { e: string; k: string }[] = [];
  for (const item of ALL) {
    if (seen.has(item.e)) continue;
    if (words.every((w) => item.k.includes(w) || item.e === w)) {
      seen.add(item.e);
      out.push(item);
      if (out.length >= limit) break;
    }
  }
  return out;
}
