// Entscheidungen per Jev (TypeSafe System One). Code fuehrt aus, Jev urteilt nur.
const { TypeSafeClient, choice, noul } = require('@typesafe-ai/sdk')

const client = process.env.TYPESAFE_API_KEY ? new TypeSafeClient({ timeout: 8000 }) : null

const AKTIONEN = {
  folgen: 'Der Bot soll mitkommen, zum Spieler kommen oder ihm folgen.',
  stehen: 'Der Bot soll stehen bleiben, warten, hierbleiben oder aufhoeren, was er gerade tut.',
  selbst: 'Der Bot soll selbststaendig arbeiten, sich nuetzlich machen oder sein eigenes Ding machen, ohne konkreten Auftrag.',
  abbauen: 'Der Bot soll Bloecke oder Rohstoffe abbauen, faellen, graben oder sammeln (Holz, Erze, Stein, Sand, Blumen ...).',
  craften: 'Der Bot soll ein Item oder Werkzeug herstellen bzw. craften (z.B. Spitzhacke, Fackeln, Bretter, Truhe).',
  schmelzen: 'Der Bot soll etwas im Ofen schmelzen, braten oder brennen (Erz zu Barren, Fleisch braten).',
  jagen: 'Der Bot soll bestimmte Tiere oder Monster jagen oder toeten.',
  farmen: 'Der Bot soll reife Felder ernten und neu anpflanzen.',
  schlafen: 'Der Bot soll ins Bett gehen bzw. schlafen.',
  geben: 'Der Bot soll dem Spieler etwas geben, bringen oder herueberwerfen.',
  holen: 'Der Bot soll etwas aus der Truhe holen.',
  einlagern: 'Der Bot soll sein Inventar in die Truhe zu Hause einlagern oder wegraeumen.',
  heim: 'Der Bot soll nach Hause, zur Basis oder zur Truhe gehen.',
  heim_setzen: 'Der Spieler erklaert die Stelle, an der er gerade steht, zum Zuhause bzw. zur Basis des Bots.',
  gehen: 'Der Bot soll zu bestimmten Koordinaten gehen.',
  tunnel: 'Der Bot soll einen geraden Tunnel graben bzw. einen Gang mienen.',
  treppe: 'Der Bot soll eine Treppe nach unten graben, in die Tiefe graben oder zu einer Hoehe (Y-Level) hinuntergraben.',
  saeule: 'Der Bot soll eine Saeule bauen bzw. sich nach oben bauen (Pillar).',
  zuechten: 'Der Bot soll Tiere fuettern oder zuechten.',
  scheren: 'Der Bot soll Schafe scheren bzw. Wolle holen.',
  angeln: 'Der Bot soll angeln bzw. fischen.',
  ausruesten: 'Der Bot soll seine Ruestung anziehen oder sich ausruesten.',
  kampf_an: 'Der Bot soll Monster angreifen, kaempfen oder den Spieler beschuetzen.',
  kampf_aus: 'Der Bot soll nicht mehr kaempfen oder Monster in Ruhe lassen.',
  loot_an: 'Der Bot soll herumliegende, schon gedroppte Items vom Boden aufheben.',
  loot_aus: 'Der Bot soll keine Items mehr vom Boden aufheben.',
  pvp_an: 'PvP-Modus an: Der Bot soll auch Spieler angreifen, die der Spieler angreift.',
  pvp_aus: 'PvP-Modus aus: Der Bot soll keine Spieler mehr angreifen (nur noch Monster und Notwehr).',
  angreifen: 'Der Bot soll jetzt einen bestimmten Spieler oder ein bestimmtes Wesen angreifen (z.B. "hau den da", "greif Steve an").',
  ausloggen: 'Der Bot soll sich jetzt ausloggen, den Server verlassen oder rausgehen.',
  logout_regel: 'Der Spieler legt fest, ab wie wenig Leben (Herzen) oder Hunger sich der Bot automatisch ausloggen soll.',
  fliegen: 'Der Bot soll mit der Elytra abheben, fliegen oder dem Spieler hinterherfliegen.',
  wache: 'Der Bot soll hier Wache halten bzw. diesen Ort bewachen.',
  status: 'Der Spieler fragt, wie es dem Bot geht oder was er gerade tut: Leben, Hunger, Inventar, Aufgabe.',
  keine: 'Keine dieser Aktionen, z.B. Smalltalk, eine Frage zu etwas anderem oder eine Nachricht an andere Spieler.'
}

const UNKLAR = { unklar: 'Nicht genannt, oder keine dieser Optionen passt.' }

// Eine Anfrage: Adressat, Aktion und (spekulativ) jeder moegliche Parameter.
// `kandidaten` erzeugt der Code aus Umgebung, Inventar und Rezepten; Jev waehlt nur aus.
async function befehlVerstehen (text, gefluestert, lage, kandidaten) {
  const questions = {
    an_bot: noul(
      'Richtet sich `nachricht` von `spieler` an seinen Begleitbot `bot_name` ' +
      '(Aufforderung oder Frage an den Bot), und nicht an andere Spieler oder an niemanden bestimmten?'
    ),
    aktion: choice(
      'Welche Aktion will `spieler` mit `nachricht` vom Minecraft-Begleitbot? `bot_zustand` ist, was der Bot gerade tut.',
      AKTIONEN
    ),
    ohne_ende: noul(
      'Soll der Bot laut `nachricht` dauerhaft bzw. ohne Ende weitermachen, bis man ihn stoppt ' +
      '(z.B. "immer", "unendlich", "hoer nicht auf", "so viel du kannst")?'
    )
  }
  if (Object.keys(kandidaten.bloecke).length) {
    questions.block = choice('Angenommen, der Bot soll laut `nachricht` etwas abbauen: welcher Block bzw. Rohstoff ist gemeint?', { ...kandidaten.bloecke, ...UNKLAR })
  }
  if (Object.keys(kandidaten.items).length) {
    questions.item = choice('Angenommen, der Bot soll laut `nachricht` etwas herstellen: welches Item ist gemeint?', { ...kandidaten.items, ...UNKLAR })
  }
  if (Object.keys(kandidaten.mobs).length) {
    questions.mob = choice('Angenommen, es geht in `nachricht` um ein Tier oder Monster (jagen, toeten, fuettern, zuechten): welches?', { ...kandidaten.mobs, ...UNKLAR })
  }
  if (Object.keys(kandidaten.dinge).length) {
    questions.ding = choice(
      'Angenommen, der Bot soll laut `nachricht` ein bestimmtes Item geben, holen oder schmelzen: welches? "alles" nur, wenn ausdruecklich alles gemeint ist.',
      { alles: 'Alles bzw. das ganze Inventar.', ...kandidaten.dinge, ...UNKLAR }
    )
  }

  const { answers } = await client.systemOne({
    state: {
      nachricht: text,
      kanal: gefluestert ? 'Fluesternachricht direkt an den Bot' : 'oeffentlicher Server-Chat',
      bot_name: lage.botName,
      spieler: lage.besitzer,
      bot_zustand: lage.zustand
    },
    questions
  })
  const wahl = q => answers[q] ? { wert: answers[q].choice, sicherheit: answers[q].confidence } : { wert: 'unklar', sicherheit: 0 }
  return {
    anBot: answers.an_bot.noul,
    aktion: answers.aktion.choice,
    aktionSicherheit: answers.aktion.confidence,
    ohneEnde: answers.ohne_ende.noul,
    block: wahl('block'),
    item: wahl('item'),
    mob: wahl('mob'),
    ding: wahl('ding')
  }
}

// Selbststaendiger Modus: Code erzeugt die moeglichen Aufgaben, Jev waehlt eine davon
async function naechsteAufgabe (lage, optionen) {
  const { answers } = await client.systemOne({
    state: lage,
    questions: {
      naechste: choice(
        'Der Minecraft-Begleitbot `bot` arbeitet selbststaendig fuer seinen Spieler `besitzer`. ' +
        'Welche der moeglichen Aufgaben ist jetzt die nuetzlichste? Beruecksichtige Inventar, Werkzeuge, ' +
        'Leben, Tageszeit, Gefahr und `letzte_aufgaben`: Abwechslung ist gut, bessere Werkzeuge helfen bei allem, ' +
        'Rohstoffe, die schon reichlich im Inventar sind, sind weniger wichtig, und nachts ist es draussen gefaehrlich.',
        optionen
      )
    }
  })
  return { aufgabe: answers.naechste.choice, sicherheit: answers.naechste.confidence }
}

module.exports = { aktiv: !!client, befehlVerstehen, naechsteAufgabe }
