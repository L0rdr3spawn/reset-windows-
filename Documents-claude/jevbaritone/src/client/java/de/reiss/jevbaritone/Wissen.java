package de.reiss.jevbaritone;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Minecraft-Wissen fuer den Planer, aus den echten Spieldaten erzeugt (wissen-erzeugen.js): Rezepte, welcher Block
 * einen Rohstoff droppt und welche Spitzhacke er braucht, was man schmilzt. Pro Anfrage wird nur der Rezeptbaum
 * der gemeinten Items als kurzer Text mitgegeben, damit auch ein kleines lokales LLM richtig plant.
 */
final class Wissen {
	/** Allgemeine Fakten, die in keinem Rezept stehen (wie im Wiki). */
	static final String FAKTEN = """
		Allgemeines Minecraft-Wissen (26.x):
		- Holz: Baumstamm -> 4 Bretter; 2 Bretter -> 4 Stoecke; 4 Bretter -> Werkbank. Holz faellen geht ohne Werkzeug.
		- Spitzhacken-Stufen: Holz < Stein < Eisen < Diamant < Netherit. Ohne passende Spitzhacke droppt ein Block nichts.
		- Ofen: 8 Bruchstein. Schmelzen dauert 10 s pro Item. 1 Kohle schmilzt 8 Items, 1 Brett/Stamm 1,5 Items.
		- Erz-Hoehen: Kohle Y 0 bis 190 (meist Berge), Eisen Y -24 bis 56 und in Bergen, Kupfer Y -16 bis 112,
		  Gold Y -64 bis 32, Redstone Y -64 bis 15, Lapis Y -64 bis 64, Diamant Y -64 bis 16 (am meisten bei Y -58).
		- Eisenerz droppt Roheisen, das man im Ofen zu Eisenbarren schmilzt. Gold und Kupfer genauso.
		- Diamantwerkzeug: 3 Diamanten (Spitzhacke/Axt), 2 (Schwert), 1 (Schaufel), dazu Stoecke.
		- Netherit: Antiker Schrott (nur im Nether, Y 8 bis 22) schmelzen -> 4 Schrott + 4 Gold -> Netheritbarren,
		  dann Schmiedetisch mit Aufwertungsvorlage.
		- Bett: 3 Wolle + 3 Bretter. Wolle von Schafen (scheren oder toeten).
		- Nachts spawnen Monster; Creeper explodieren, Skelette schiessen.""";

	private static final Map<String, String> DEUTSCH = new LinkedHashMap<>();

	static {
		// Deutsche/umgangssprachliche Woerter -> Namensteile der Spiel-IDs
		String[][] w = {
			{"spitzhacke", "pickaxe"}, {"pickaxe", "pickaxe"}, {"picke", "pickaxe"}, {"axt", "axe"}, {"schwert", "sword"},
			{"schaufel", "shovel"}, {"hacke", "hoe"}, {"helm", "helmet"}, {"brustpanzer", "chestplate"}, {"harnisch", "chestplate"},
			{"hose", "leggings"}, {"beinschutz", "leggings"}, {"stiefel", "boots"}, {"schild", "shield"},
			{"holz", "wooden"}, {"hoelzern", "wooden"}, {"stein", "stone"}, {"eisen", "iron"}, {"gold", "golden"},
			{"diamant", "diamond"}, {"diamanten", "diamond"}, {"netherit", "netherite"},
			{"ofen", "furnace"}, {"werkbank", "crafting_table"}, {"fackel", "torch"}, {"fackeln", "torch"}, {"truhe", "chest"},
			{"stock", "stick"}, {"stoecke", "stick"}, {"stöcke", "stick"}, {"bretter", "oak_planks"}, {"eimer", "bucket"},
			{"schere", "shears"}, {"bett", "white_bed"}, {"bogen", "bow"}, {"pfeil", "arrow"}, {"pfeile", "arrow"},
			{"angel", "fishing_rod"}, {"brot", "bread"}, {"leiter", "ladder"}, {"boot", "oak_boat"}, {"kompass", "compass"},
			{"eisenbarren", "iron_ingot"}, {"goldbarren", "gold_ingot"}, {"glas", "glass"}, {"kohle", "coal"}
		};
		for (String[] p : w) DEUTSCH.put(p[0], p[1]);
	}

	private final JsonObject rezepte;
	private final JsonObject quellen;
	private final JsonObject schmelzen;

	Wissen() {
		var in = Wissen.class.getResourceAsStream("/assets/jevbaritone/wissen.json");
		JsonObject w = JsonParser.parseReader(new InputStreamReader(Objects.requireNonNull(in), StandardCharsets.UTF_8)).getAsJsonObject();
		rezepte = w.getAsJsonObject("rezepte");
		quellen = w.getAsJsonObject("quellen");
		schmelzen = w.getAsJsonObject("schmelzen");
	}

	/** Welche Items meint die Nachricht? Ein- bis Dreiwort-Gruppen, deutsch uebersetzt, gegen die Spiel-IDs. */
	Set<String> zieleFinden(String text) {
		List<String> woerter = new ArrayList<>();
		for (String roh : text.toLowerCase(Locale.ROOT).replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").split("[^a-z_]+")) {
			if (roh.isBlank()) continue;
			// "eisenspitzhacke" -> "eisen" + "spitzhacke"
			boolean geteilt = false;
			for (String de : DEUTSCH.keySet()) {
				if (roh.length() > de.length() + 2 && roh.endsWith(de)) {
					String vorne = roh.substring(0, roh.length() - de.length());
					if (DEUTSCH.containsKey(vorne)) { woerter.add(DEUTSCH.get(vorne)); woerter.add(DEUTSCH.get(de)); geteilt = true; break; }
				}
			}
			if (!geteilt) woerter.add(DEUTSCH.getOrDefault(roh, roh));
		}
		Set<String> ziele = new LinkedHashSet<>();
		for (int laenge = 3; laenge >= 1; laenge--) {
			for (int i = 0; i + laenge <= woerter.size(); i++) {
				String id = String.join("_", woerter.subList(i, i + laenge));
				if (bekannt(id)) ziele.add(id);
				if (laenge == 1 && bekannt(id + "s")) ziele.add(id + "s");
			}
		}
		// Einzelwoerter weglassen, die schon in einer laengeren ID stecken ("diamond" in "diamond_pickaxe")
		ziele.removeIf(z -> !z.contains("_") && ziele.stream().anyMatch(y -> !y.equals(z) && y.startsWith(z + "_")));
		return ziele;
	}

	private boolean bekannt(String id) {
		return rezepte.has(id) || quellen.has(id) || schmelzen.has(id);
	}

	/** Rezeptbaum als kurzer Text: was man braucht, woher es kommt, welches Werkzeug. */
	String erklaeren(Collection<String> ziele) {
		StringBuilder sb = new StringBuilder();
		Set<String> gesehen = new HashSet<>();
		for (String z : ziele) erklaeren(z, 0, gesehen, sb);
		return sb.toString();
	}

	private void erklaeren(String id, int tiefe, Set<String> gesehen, StringBuilder sb) {
		if (tiefe > 7 || !gesehen.add(id) || gesehen.size() > 40) return;
		String einzug = "  ".repeat(Math.min(tiefe, 4)) + "- ";
		if (schmelzen.has(id)) {
			String aus = schmelzen.get(id).getAsString();
			sb.append(einzug).append(id).append(": ").append(aus).append(" im Ofen schmelzen (Ofen + Brennstoff noetig)\n");
			erklaeren("furnace", tiefe + 1, gesehen, sb);
			erklaeren(aus, tiefe + 1, gesehen, sb);
			return;
		}
		if (quellen.has(id) && (!rezepte.has(id) || basis(id))) {
			JsonObject q = quellen.getAsJsonObject(id);
			String werkzeug = q.get("werkzeug").isJsonNull() ? null : q.get("werkzeug").getAsString();
			sb.append(einzug).append(id).append(": ").append(q.get("block").getAsString()).append(" abbauen")
				.append(werkzeug != null ? ", braucht mind. " + werkzeug : ", ohne Werkzeug").append('\n');
			if (werkzeug != null) erklaeren(werkzeug, tiefe + 1, gesehen, sb);
			return;
		}
		if (rezepte.has(id)) {
			JsonObject r = rezepte.getAsJsonObject(id);
			List<String> teile = new ArrayList<>();
			r.getAsJsonObject("z").entrySet().forEach(e -> teile.add(e.getValue().getAsInt() + "x " + e.getKey()));
			sb.append(einzug).append(id).append(" (").append(r.get("n").getAsInt()).append(" Stueck) = ").append(String.join(" + ", teile))
				.append(r.get("tisch").getAsBoolean() ? " an der Werkbank" : " im Inventar").append('\n');
			for (String zutat : r.getAsJsonObject("z").keySet()) erklaeren(zutat, tiefe + 1, gesehen, sb);
		}
	}

	/** Rohstoffe, die man abbaut statt herstellt, obwohl es ein (Rueckwaerts-)Rezept gibt. */
	private static boolean basis(String id) {
		return id.endsWith("_log") || id.equals("cobblestone") || id.equals("diamond") || id.equals("coal") || id.equals("redstone")
			|| id.equals("emerald") || id.equals("lapis_lazuli") || id.startsWith("raw_") || id.equals("clay_ball") || id.equals("string");
	}
}
