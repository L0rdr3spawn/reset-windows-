package de.reiss.jevbaritone;

import baritone.api.BaritoneAPI;
import baritone.api.IBaritone;
import com.google.gson.JsonObject;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.message.v1.ClientReceiveMessageEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Macht diesen Client zum Begleitbot. Der Besitzer schreibt normal in den Chat (oder fluestert),
 * Jev entscheidet, was gemeint ist, und Baritone fuehrt es aus. Nachrichten mit "#" gehen direkt an Baritone.
 */
public class JevBaritoneClient implements ClientModInitializer {
	static final Logger LOG = LoggerFactory.getLogger("jevbaritone");

	private static final Pattern CHAT = Pattern.compile("^<([^>]+)> (.*)$");
	private static final Pattern FLUESTERN = Pattern.compile("^(\\S+) whispers to you: (.*)$");
	private static final Pattern KOORDS = Pattern.compile("(-?\\d+)[\\s,]+(-?\\d+)(?:[\\s,]+(-?\\d+))?");
	private static final Pattern ZAHL = Pattern.compile("\\b(\\d+)\\b");

	// Rohstoff-Gruppe -> Beschreibung fuer Jev, Bloecke fuer Baritone, Standardmenge
	private record Gruppe(String name, int standard, String... bloecke) {}

	private static final Map<String, Gruppe> GRUPPEN = new LinkedHashMap<>();

	static {
		GRUPPEN.put("holz", new Gruppe("Holz (Baumstaemme faellen)", 16, "oak_log", "spruce_log", "birch_log", "jungle_log", "acacia_log", "dark_oak_log", "mangrove_log", "cherry_log", "pale_oak_log"));
		GRUPPEN.put("stein", new Gruppe("Stein bzw. Bruchstein", 32, "stone", "cobblestone"));
		GRUPPEN.put("kohle", new Gruppe("Kohle", 16, "coal_ore", "deepslate_coal_ore"));
		GRUPPEN.put("eisen", new Gruppe("Eisenerz", 8, "iron_ore", "deepslate_iron_ore"));
		GRUPPEN.put("kupfer", new Gruppe("Kupfererz", 16, "copper_ore", "deepslate_copper_ore"));
		GRUPPEN.put("gold", new Gruppe("Golderz", 8, "gold_ore", "deepslate_gold_ore", "nether_gold_ore"));
		GRUPPEN.put("diamant", new Gruppe("Diamanten", 3, "diamond_ore", "deepslate_diamond_ore"));
		GRUPPEN.put("smaragd", new Gruppe("Smaragde", 3, "emerald_ore", "deepslate_emerald_ore"));
		GRUPPEN.put("redstone", new Gruppe("Redstone", 16, "redstone_ore", "deepslate_redstone_ore"));
		GRUPPEN.put("lapis", new Gruppe("Lapislazuli", 16, "lapis_ore", "deepslate_lapis_ore"));
		GRUPPEN.put("quarz", new Gruppe("Netherquarz", 16, "nether_quartz_ore"));
		GRUPPEN.put("antiker_schrott", new Gruppe("Antiker Schrott (Netherit)", 4, "ancient_debris"));
		GRUPPEN.put("sand", new Gruppe("Sand", 32, "sand", "red_sand"));
		GRUPPEN.put("erde", new Gruppe("Erde", 32, "dirt", "grass_block", "coarse_dirt"));
		GRUPPEN.put("kies", new Gruppe("Kies", 16, "gravel"));
		GRUPPEN.put("ton", new Gruppe("Ton", 16, "clay"));
		GRUPPEN.put("obsidian", new Gruppe("Obsidian", 10, "obsidian"));
	}

	private static final Map<String, String> AKTIONEN = new LinkedHashMap<>();

	static {
		AKTIONEN.put("folgen", "Der Bot soll mitkommen bzw. dem Spieler dauerhaft folgen.");
		AKTIONEN.put("komm", "Der Bot soll einmal zum Spieler herkommen.");
		AKTIONEN.put("stopp", "Der Bot soll aufhoeren, anhalten, stehen bleiben oder warten.");
		AKTIONEN.put("abbauen", "Der Bot soll Bloecke oder Rohstoffe abbauen, faellen, graben oder sammeln (Holz, Erze, Stein, Sand ...).");
		AKTIONEN.put("craften", "Der Bot soll ein Item herstellen bzw. craften (Werkzeug, Stoecke, Bretter, Werkbank, Fackeln, Truhe ...).");
		AKTIONEN.put("schmelzen", "Der Bot soll etwas im Ofen schmelzen, brennen oder braten (Erz zu Barren, Fleisch braten, Sand zu Glas).");
		AKTIONEN.put("gehen", "Der Bot soll zu bestimmten Koordinaten gehen.");
		AKTIONEN.put("farmen", "Der Bot soll Felder ernten und neu bepflanzen bzw. farmen.");
		AKTIONEN.put("erkunden", "Der Bot soll die Gegend erkunden bzw. herumlaufen und neue Gebiete entdecken.");
		AKTIONEN.put("tunnel", "Der Bot soll einen geraden Tunnel graben.");
		AKTIONEN.put("oberflaeche", "Der Bot soll aus einer Hoehle bzw. unter der Erde an die Oberflaeche kommen.");
		AKTIONEN.put("heim", "Der Bot soll nach Hause bzw. zur Basis gehen.");
		AKTIONEN.put("heim_setzen", "Der Spieler erklaert die Stelle, an der er gerade steht, zum Zuhause bzw. zur Basis des Bots.");
		AKTIONEN.put("beschuetzen", "Der Bot soll den Spieler beschuetzen, kaempfen oder Monster angreifen.");
		AKTIONEN.put("kampf_aus", "Der Bot soll nicht mehr kaempfen bzw. Monster in Ruhe lassen.");
		AKTIONEN.put("sagen", "Der Bot soll etwas Bestimmtes oeffentlich in den Chat schreiben bzw. sagen (z.B. \"sag hallo\").");
		AKTIONEN.put("status", "Der Spieler fragt, wie es dem Bot geht oder was er gerade tut.");
		AKTIONEN.put("keine", "Keine dieser Aktionen, z.B. Smalltalk, eine Frage zu etwas anderem oder eine Nachricht an andere Spieler.");
	}

	private String besitzer = "L0rdr3spawn";
	private BlockPos heim;
	private String apiKey;
	private volatile boolean jevLaeuft;
	private boolean warAktiv;
	private int inaktivTicks;
	private boolean warTot;
	private String letzterAuftrag = "nichts";
	private String llmUrl = "http://127.0.0.1:1234/v1/chat/completions";
	private String llmModell = "google/gemma-4-e4b";
	private Werkbank werkbank;
	private Planer planer;
	// Einzelschritte aus dem Plan des lokalen LLM, nacheinander abgearbeitet
	private final Deque<String> schritte = new ArrayDeque<>();
	private boolean schrittLaeuft;
	private int schrittTicks;
	// Rueckfrage des Bots ("Was soll ich herstellen?"), damit die naechste Antwort im Zusammenhang verstanden wird
	private String offeneFrage;
	private String letzteNachricht = "";
	private Kampf kampf;
	private Ofen ofen;
	private Wissen wissen;
	private String jevItem;
	private boolean folgeModus;
	private int ticks;

	@Override
	public void onInitializeClient() {
		configLaden();
		apiKey = Jev.apiKeyFinden();
		werkbank = new Werkbank(this::fluestern, this::herstellenFehlgeschlagen, this::baritone, this::baritoneAktiv);
		planer = new Planer(llmUrl, llmModell);
		wissen = new Wissen();
		ofen = new Ofen(werkbank, this::fluestern, this::baritone, this::baritoneAktiv);
		kampf = new Kampf(this::besitzerFinden, () -> { if (folgeModus) baritone("follow player " + besitzer); });
		LOG.info("Jev-Baritone-Bot: Besitzer {}, Jev {}", besitzer, apiKey != null ? "aktiv" : "OHNE Key (nur #-Befehle)");

		ClientReceiveMessageEvents.CHAT.register((message, signed, sender, params, zeit) -> {
			String text = message.getString();
			Matcher f = FLUESTERN.matcher(text);
			if (f.matches()) { eingang(f.group(1), f.group(2), true); return; }
			String name = sender != null ? sender.name() : null;
			String inhalt = signed != null ? signed.signedContent() : text;
			Matcher c = CHAT.matcher(inhalt);
			if (name == null && c.matches()) { name = c.group(1); inhalt = c.group(2); }
			eingang(name, inhalt, false);
		});
		// Manche Server schicken Chat als Systemnachricht
		ClientReceiveMessageEvents.GAME.register((message, overlay) -> {
			if (overlay) return;
			String text = message.getString();
			Matcher f = FLUESTERN.matcher(text);
			if (f.matches()) { eingang(f.group(1), f.group(2), true); return; }
			Matcher c = CHAT.matcher(text);
			if (c.matches()) eingang(c.group(1), c.group(2), false);
		});

		// Wenn Baritone mit einem Auftrag fertig wird, Bescheid geben
		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			if (mc.player == null) return;
			// Tot: sofort wiederbeleben (sonst haengt der Bot im Todesbildschirm und darf nicht chatten)
			if (mc.player.isDeadOrDying()) {
				if (!warTot) {
					warTot = true;
					LOG.info("Bot ist gestorben, respawne.");
					allesStoppen();
					baritone("stop");
				}
				mc.player.respawn();
				return;
			}
			if (warTot) {
				warTot = false;
				fluestern("Ich bin gestorben und wieder da. Meine Sachen liegen dort, wo ich gestorben bin.");
			}
			werkbank.tick();
			ofen.tick();
			kampf.tick();
			if (++ticks % 10 == 0 && !kampf.kaempft()) kampf.creeperMeiden();
			if (kampf.kaempft()) return; // Plan und Fertig-Meldung warten, bis der Kampf vorbei ist
			boolean aktiv = baritoneAktiv();
			// Fertig erst melden, wenn Baritone 2 s lang nichts mehr tut (Folgen stoppt kurz bei jedem Aufholen)
			if (aktiv) { warAktiv = true; inaktivTicks = 0; }
			else if (warAktiv && ++inaktivTicks >= 40) {
				warAktiv = false;
				if (!werkbank.aktiv() && !ofen.aktiv() && schritte.isEmpty() && !schrittLaeuft) fluestern("Fertig mit: " + letzterAuftrag);
			}
			naechsterSchritt(aktiv);
		});
	}

	// ---------------- Eingang ----------------

	private void eingang(String name, String text, boolean gefluestert) {
		Minecraft mc = Minecraft.getInstance();
		if (name == null || mc.player == null || !name.equals(besitzer) || name.equals(mc.player.getName().getString())) return;
		text = text.trim();
		if (text.isEmpty()) return;
		LOG.info("{} von {}: {}", gefluestert ? "Gefluestert" : "Chat", name, text);

		String frei = text.replaceFirst("^!+", "").trim();
		if (frei.startsWith("#")) { // direkt an Baritone
			if (frei.equals("#stop") || frei.equals("#cancel")) allesStoppen();
			baritone(frei.substring(1).trim());
			return;
		}
		if (apiKey == null) {
			if (gefluestert || text.startsWith("!")) fluestern("Kein TYPESAFE_API_KEY - nur #-Baritone-Befehle gehen.");
			return;
		}
		if (jevLaeuft) { fluestern("Moment, ich denke noch ueber das Letzte nach."); return; }
		letzteNachricht = frei;
		verstehen(frei, gefluestert || text.startsWith("!"), false);
	}

	/** Material fehlt: das lokale LLM soll planen, wie der Bot es besorgt (nur einmal, nicht in einem Plan). */
	private void herstellenFehlgeschlagen(String grund) {
		if (!schritte.isEmpty() || schrittLaeuft) {
			fluestern(grund + " Ich breche den Plan ab.");
			schritte.clear();
			schrittLaeuft = false;
			return;
		}
		fluestern(grund);
		planen(letzteNachricht + " (Hinweis: " + grund + " Besorge zuerst das Material.)");
	}

	/** Arbeitet den Plan ab: naechster Schritt erst, wenn Baritone und Werkbank fertig sind. */
	private void naechsterSchritt(boolean baritoneLaeuft) {
		if (schrittLaeuft) {
			if (++schrittTicks < 30 || baritoneLaeuft || werkbank.aktiv() || ofen.aktiv() || jevLaeuft) return;
			schrittLaeuft = false;
		}
		if (schritte.isEmpty() || jevLaeuft) return;
		String s = schritte.poll();
		schrittLaeuft = true;
		schrittTicks = 0;
		fluestern("Schritt: " + s + (schritte.isEmpty() ? "" : " (noch " + schritte.size() + ")"));
		verstehen(s, true, true);
	}

	private void allesStoppen() {
		schritte.clear();
		schrittLaeuft = false;
		werkbank.abbrechen();
		ofen.abbrechen();
	}

	private Map<String, Integer> inventar() {
		Map<String, Integer> inv = new TreeMap<>();
		var i = Minecraft.getInstance().player.getInventory();
		for (int n = 0; n < i.getContainerSize(); n++) {
			var st = i.getItem(n);
			if (!st.isEmpty()) inv.merge(BuiltInRegistries.ITEM.getKey(st.getItem()).getPath(), st.getCount(), Integer::sum);
		}
		return inv;
	}

	/** System 2: lokales LLM zerlegt die Nachricht, jeder Schritt geht danach einzeln an Jev. */
	private void planen(String text) {
		fluestern("Ich plane das kurz ...");
		jevLaeuft = true;
		Set<String> ziele = wissen.zieleFinden(text);
		if (jevItem != null) ziele.add(jevItem);
		String rezeptbaum = wissen.erklaeren(ziele);
		LOG.info("Wissen fuer Plan (Ziele {}):\n{}", ziele, rezeptbaum);
		planer.planen(text, inventar(), rezeptbaum).whenComplete((plan, fehler) -> Minecraft.getInstance().execute(() -> {
			jevLaeuft = false;
			if (fehler != null) {
				LOG.warn("Planer-Fehler", fehler);
				fluestern("Das lokale LLM (LM Studio) antwortet nicht: " + fehler.getMessage());
				return;
			}
			LOG.info("Plan fuer \"{}\": {}", text, plan);
			if (plan.isEmpty()) { fluestern("Dafuer habe ich keinen Plan gefunden."); return; }
			fluestern("Plan: " + String.join(" -> ", plan));
			schritte.addAll(plan);
		}));
	}

	// ---------------- Jev ----------------

	private void verstehen(String text, boolean direkt, boolean ausPlan) {
		Map<String, String> bloecke = blockKandidaten();
		Map<String, String> items = werkbank.kandidaten();
		Map<String, Object> state = new LinkedHashMap<>();
		state.put("nachricht", text);
		state.put("kanal", direkt ? "Fluesternachricht direkt an den Bot" : "oeffentlicher Server-Chat");
		state.put("bot_name", Minecraft.getInstance().player.getName().getString());
		state.put("spieler", besitzer);
		state.put("bot_zustand", zustand());
		if (offeneFrage != null && !ausPlan) {
			state.put("rueckfrage_des_bots", offeneFrage);
			state.put("hinweis", "`nachricht` ist vermutlich die Antwort auf `rueckfrage_des_bots`.");
		}
		offeneFrage = null;

		jevLaeuft = true;
		Jev anfrage = Jev.anfrage(apiKey);
		if (!ausPlan) {
			anfrage.noul("mehrschritt", "Verlangt `nachricht` mehrere Schritte nacheinander oder ein Ziel, fuer das der Bot erst "
				+ "Material besorgen oder etwas vorbereiten muss (z.B. \"hol holz und dann ...\", \"mach mir eine Steinspitzhacke\", "
				+ "\"bau dir Werkzeug und geh dann Eisen suchen\")? Nein bei einem einzelnen einfachen Befehl.");
		}
		anfrage
			.noul("an_bot", "Richtet sich `nachricht` von `spieler` an seinen Begleitbot `bot_name` "
				+ "(Aufforderung oder Frage an den Bot), und nicht an andere Spieler oder an niemanden bestimmten?")
			.choice("aktion", "Welche Aktion will `spieler` mit `nachricht` vom Minecraft-Begleitbot? `bot_zustand` ist, was der Bot gerade tut.", AKTIONEN)
			.noul("ohne_ende", "Soll der Bot laut `nachricht` dauerhaft bzw. ohne Ende weitermachen, bis man ihn stoppt "
				+ "(z.B. \"immer\", \"unendlich\", \"hoer nicht auf\", \"so viel du kannst\")?")
			.choice("block", "Angenommen, der Bot soll laut `nachricht` etwas abbauen: welcher Block bzw. Rohstoff ist gemeint?", bloecke)
			.choice("item", "Angenommen, der Bot soll laut `nachricht` etwas herstellen: welches Item ist gemeint?", items)
			.choice("schmelzgut", "Angenommen, der Bot soll laut `nachricht` etwas schmelzen oder braten: welches Item aus seinem Inventar?", ofen.kandidaten())
			.senden(state)
			.whenComplete((antworten, fehler) -> Minecraft.getInstance().execute(() -> {
				jevLaeuft = false;
				if (fehler != null) {
					LOG.warn("Jev-Fehler", fehler);
					fluestern("Jev antwortet gerade nicht: " + fehler.getMessage());
					return;
				}
				ausfuehren(text, direkt, ausPlan, antworten);
			}));
	}

	private void ausfuehren(String text, boolean direkt, boolean ausPlan, JsonObject a) {
		double anBot = Jev.noul(a, "an_bot");
		String aktion = Jev.wahl(a, "aktion");
		double sicher = Jev.sicherheit(a, "aktion");
		boolean ohneEnde = Jev.noul(a, "ohne_ende") >= 0.6;
		String block = Jev.wahl(a, "block");
		LOG.info("Jev: \"{}\" -> an_bot {}, {} ({}), ohne_ende {}, block {} ({})", text, fmt(anBot), aktion, fmt(sicher),
			ohneEnde, block, fmt(Jev.sicherheit(a, "block")));

		if (anBot < (direkt ? 0.3 : 0.5)) return;
		double mehrschritt = ausPlan ? 0 : Jev.noul(a, "mehrschritt");
		String itemWahl = Jev.wahl(a, "item");
		jevItem = itemWahl.startsWith("item:") && Jev.sicherheit(a, "item") >= 0.3 ? itemWahl.substring(5) : null;
		if (!ausPlan) LOG.info("Jev: mehrschritt {}", fmt(mehrschritt));
		// Herstellen erst direkt versuchen: Vorprodukte macht die Werkbank selbst, geplant wird nur bei fehlendem Material
		boolean direktCraften = aktion.equals("craften") && Jev.sicherheit(a, "item") >= 0.4 && !Jev.wahl(a, "item").equals("unklar");
		if ((mehrschritt >= 0.5 && !direktCraften) || (!ausPlan && sicher < 0.45 && anBot >= 0.7)) {
			planen(text);
			return;
		}
		if (aktion.equals("keine") || sicher < 0.45) {
			if (direkt || anBot >= 0.8) fluestern("\"" + text + "\" hab ich nicht verstanden. Z.B. \"hol 20 eisen\", \"folg mir\", \"erkunde\", \"geh zu 100 70 -50\" - oder #baritone-befehl.");
			return;
		}

		Player ich = Minecraft.getInstance().player;
		// Eine echte neue Aufgabe ersetzt einen laufenden Plan (Smalltalk, Status und Sagen nicht)
		if (!ausPlan && !List.of("status", "sagen", "beschuetzen", "kampf_aus").contains(aktion)) {
			schritte.clear();
			schrittLaeuft = false;
			werkbank.abbrechen();
		}
		folgeModus = aktion.equals("folgen") || (folgeModus && List.of("status", "sagen", "beschuetzen", "kampf_aus").contains(aktion));
		switch (aktion) {
			case "folgen" -> auftrag("follow player " + besitzer, "folge dir");
			case "komm" -> {
				Player b = besitzerFinden();
				if (b == null) { fluestern("Ich sehe dich nicht."); return; }
				BlockPos p = b.blockPosition();
				auftrag("goto " + p.getX() + " " + p.getY() + " " + p.getZ(), "komme zu dir");
			}
			case "stopp" -> { allesStoppen(); baritone("stop"); fluestern("Halte an."); }
			case "craften" -> {
				String item = Jev.wahl(a, "item");
				if (item.equals("unklar") || Jev.sicherheit(a, "item") < 0.4) { frage("Was soll ich herstellen?"); return; }
				var it = BuiltInRegistries.ITEM.getValue(net.minecraft.resources.Identifier.withDefaultNamespace(item.substring(5)));
				String name = new net.minecraft.world.item.ItemStack(it).getHoverName().getString();
				int menge = zahlIn(text).orElse(1);
				letzterAuftrag = menge + "x " + name + " herstellen";
				fluestern("Okay, stelle " + menge + "x " + name + " her.");
				werkbank.starten(it, menge);
			}
			case "abbauen" -> {
				if (block.equals("unklar") || Jev.sicherheit(a, "block") < 0.4) { frage("Was soll ich abbauen?"); return; }
				List<String> ziele;
				String name;
				Integer standard;
				if (block.startsWith("gruppe:")) {
					Gruppe g = GRUPPEN.get(block.substring(7));
					ziele = List.of(g.bloecke());
					name = g.name();
					standard = g.standard();
				} else {
					String id = block.substring(6);
					ziele = List.of(id);
					name = blockName(id);
					standard = 16;
				}
				Integer menge = ohneEnde ? null : zahlIn(text).orElse(standard);
				auftrag("mine " + (menge != null ? menge + " " : "") + String.join(" ", ziele),
					(menge != null ? menge + "x " : "ohne Ende ") + name + " abbauen");
			}
			case "gehen" -> {
				Matcher k = KOORDS.matcher(text);
				if (!k.find()) { fluestern("Wohin? Sag z.B. \"geh zu 100 64 -200\"."); return; }
				String ziel = k.group(3) != null ? k.group(1) + " " + k.group(2) + " " + k.group(3) : k.group(1) + " " + k.group(2);
				auftrag("goto " + ziel, "gehe zu " + ziel);
			}
			case "farmen" -> auftrag("farm", "farme");
			case "erkunden" -> auftrag("explore", "erkunde die Gegend");
			case "tunnel" -> auftrag("tunnel", "grabe einen Tunnel");
			case "oberflaeche" -> auftrag("surface", "gehe an die Oberflaeche");
			case "heim_setzen" -> {
				Player b = besitzerFinden();
				if (b == null) { fluestern("Ich sehe dich nicht."); return; }
				heim = b.blockPosition();
				configSpeichern();
				fluestern("Zuhause gesetzt bei " + heim.getX() + " " + heim.getY() + " " + heim.getZ() + ".");
			}
			case "heim" -> {
				if (heim == null) { fluestern("Kein Zuhause gesetzt. Stell dich hin und sag \"hier ist zuhause\"."); return; }
				auftrag("goto " + heim.getX() + " " + heim.getY() + " " + heim.getZ(), "gehe nach Hause");
			}
			case "schmelzen" -> {
				String w = Jev.wahl(a, "schmelzgut");
				var it = !w.startsWith("ding:") || Jev.sicherheit(a, "schmelzgut") < 0.4 ? null
					: BuiltInRegistries.ITEM.getValue(net.minecraft.resources.Identifier.withDefaultNamespace(w.substring(5)));
				letzterAuftrag = "schmelzen";
				ofen.starten(it, zahlIn(text).orElse(64));
			}
			case "beschuetzen" -> { kampf.setAn(true); fluestern("Ich beschuetze dich und kaempfe gegen Monster."); }
			case "kampf_aus" -> { kampf.setAn(false); fluestern("Okay, ich kaempfe nicht mehr."); }
			case "sagen" -> {
				Matcher m = Pattern.compile("^(?i)(sag|sage|say|schreib|schreibe|write)\s+(.+)$").matcher(text);
				String was = m.matches() ? m.group(2) : text;
				Minecraft.getInstance().player.connection.sendChat(was.length() > 250 ? was.substring(0, 250) : was);
			}
			case "status" -> fluestern(zustand() + ", Leben " + Math.round(ich.getHealth()) + "/20, Hunger " + ich.getFoodData().getFoodLevel() + "/20");
			default -> fluestern("Das kann ich noch nicht: " + aktion);
		}
	}

	// ---------------- Kandidaten und Zustand ----------------

	/** Rohstoff-Gruppen plus alle Blocksorten im Umkreis, damit Jev auch "bau das Glas ab" zuordnen kann. */
	private Map<String, String> blockKandidaten() {
		Map<String, String> k = new LinkedHashMap<>();
		GRUPPEN.forEach((id, g) -> k.put("gruppe:" + id, g.name()));
		Minecraft mc = Minecraft.getInstance();
		Map<Block, Integer> anzahl = new HashMap<>();
		BlockPos mitte = mc.player.blockPosition();
		int r = 10;
		for (BlockPos p : BlockPos.betweenClosed(mitte.offset(-r, -r, -r), mitte.offset(r, r, r))) {
			Block b = mc.level.getBlockState(p).getBlock();
			if (b == Blocks.AIR || b == Blocks.CAVE_AIR || b == Blocks.WATER || b == Blocks.LAVA || b == Blocks.BEDROCK) continue;
			anzahl.merge(b, 1, Integer::sum);
		}
		anzahl.entrySet().stream()
			.sorted(Map.Entry.<Block, Integer>comparingByValue().reversed())
			.limit(50)
			.forEach(e -> k.putIfAbsent("block:" + BuiltInRegistries.BLOCK.getKey(e.getKey()).getPath(),
				e.getKey().getName().getString() + " (" + e.getValue() + "x in der Naehe)"));
		k.put("unklar", "Nicht genannt, oder keine dieser Optionen passt.");
		return k;
	}

	private String zustand() {
		IBaritone b = BaritoneAPI.getProvider().getPrimaryBaritone();
		List<String> aktiv = new ArrayList<>();
		if (b.getMineProcess().isActive()) aktiv.add("baut ab");
		if (b.getFollowProcess().isActive()) aktiv.add("folgt");
		if (b.getFarmProcess().isActive()) aktiv.add("farmt");
		if (b.getExploreProcess().isActive()) aktiv.add("erkundet");
		if (b.getCustomGoalProcess().isActive()) aktiv.add("laeuft zu einem Ziel");
		if (kampf != null && kampf.kaempft()) aktiv.add("kaempft");
		String s = aktiv.isEmpty() ? "tut nichts" : String.join(", ", aktiv) + " (" + letzterAuftrag + ")";
		return s + (kampf != null && kampf.istAn() ? ", Beschuetzen an" : ", Beschuetzen aus");
	}

	private boolean baritoneAktiv() {
		try {
			IBaritone b = BaritoneAPI.getProvider().getPrimaryBaritone();
			return b.getPathingBehavior().isPathing() || b.getMineProcess().isActive() || b.getFarmProcess().isActive() || b.getFollowProcess().isActive()
				|| b.getExploreProcess().isActive() || b.getCustomGoalProcess().isActive();
		} catch (Throwable t) {
			return false;
		}
	}

	// ---------------- Ausfuehren ----------------

	private void auftrag(String befehl, String beschreibung) {
		letzterAuftrag = beschreibung;
		if (baritone(befehl)) fluestern("Okay, " + beschreibung + ".");
		else fluestern("Baritone kann \"" + befehl + "\" nicht ausfuehren.");
	}

	private boolean baritone(String befehl) {
		LOG.info("Baritone: #{}", befehl);
		try {
			return BaritoneAPI.getProvider().getPrimaryBaritone().getCommandManager().execute(befehl);
		} catch (Throwable t) {
			LOG.warn("Baritone-Fehler bei #{}", befehl, t);
			return false;
		}
	}

	private void frage(String text) {
		offeneFrage = text + " (vorherige Nachricht des Spielers: \"" + letzteNachricht + "\")";
		fluestern(text);
	}

	private void fluestern(String text) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null) return;
		int max = 200;
		for (int i = 0; i < text.length(); i += max) {
			mc.player.connection.sendCommand("msg " + besitzer + " " + text.substring(i, Math.min(text.length(), i + max)));
		}
	}

	private Player besitzerFinden() {
		return Minecraft.getInstance().level.players().stream()
			.filter(p -> p.getName().getString().equals(besitzer)).findFirst().orElse(null);
	}

	private static String blockName(String id) {
		return BuiltInRegistries.BLOCK.stream().filter(b -> BuiltInRegistries.BLOCK.getKey(b).getPath().equals(id))
			.map(b -> b.getName().getString()).findFirst().orElse(id);
	}

	/** Mengen liest der Code, nicht Jev: "20 eisen", "2 stacks holz". Koordinaten zaehlen nicht. */
	private static Optional<Integer> zahlIn(String text) {
		String t = KOORDS.matcher(text).replaceAll("");
		Matcher m = ZAHL.matcher(t);
		Integer n = m.find() ? Integer.parseInt(m.group(1)) : null;
		if (t.toLowerCase(Locale.ROOT).matches(".*\\b(stack|stacks|stapel)\\b.*")) n = (n == null ? 1 : n) * 64;
		return Optional.ofNullable(n);
	}

	private static String fmt(double d) {
		return String.format(Locale.ROOT, "%.2f", d);
	}

	// ---------------- Config ----------------

	private Path configDatei() {
		return FabricLoader.getInstance().getConfigDir().resolve("jevbaritone.properties");
	}

	private void configLaden() {
		Properties p = new Properties();
		try (Reader r = Files.newBufferedReader(configDatei())) {
			p.load(r);
		} catch (Exception e) {
			configSpeichern(); // Datei mit Standardwerten anlegen
			return;
		}
		besitzer = p.getProperty("besitzer", besitzer).trim();
		String h = p.getProperty("heim", "").trim();
		if (!h.isEmpty()) {
			try {
				int[] xyz = Arrays.stream(h.split("\\s+")).mapToInt(Integer::parseInt).toArray();
				heim = new BlockPos(xyz[0], xyz[1], xyz[2]);
			} catch (RuntimeException e) {
				LOG.warn("Ungueltiges heim in der Config: {}", h);
			}
		}
	}

	private void configSpeichern() {
		Properties p = new Properties();
		p.setProperty("besitzer", besitzer);
		if (heim != null) p.setProperty("heim", heim.getX() + " " + heim.getY() + " " + heim.getZ());
		try (Writer w = Files.newBufferedWriter(configDatei())) {
			p.store(w, "Jev-Baritone-Bot: wer den Bot steuern darf, und sein Zuhause");
		} catch (Exception e) {
			LOG.warn("Config nicht gespeichert", e);
		}
	}
}
