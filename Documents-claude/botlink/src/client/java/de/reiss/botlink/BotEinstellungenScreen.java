package de.reiss.botlink;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * Einstellungen des Bots zum Anklicken (/bot einstellungen oder Taste B): Schalter fuer Kampf, PvP, Aufheben,
 * Mace/Speer/Elytra, Farmen, Fliegen, Modus, Logout-Regeln und die Freundesliste. Jeder Klick schickt den passenden
 * Befehl an den Bot; der aktuelle Stand kommt jede Sekunde aus dem Bot-Status.
 */
public final class BotEinstellungenScreen extends Screen {
	private static final int B = 150; // Knopfbreite
	private final BotLinkClient mod;
	private EditBox freundFeld;
	private String stand = ""; // zuletzt angezeigter Status, bei Aenderung neu aufbauen
	private int tick;

	public BotEinstellungenScreen(BotLinkClient mod) {
		super(Component.literal("Bot-Einstellungen"));
		this.mod = mod;
	}

	private JsonObject einst() {
		JsonObject s = mod.botStatus();
		return s != null && s.has("einstellungen") && s.get("einstellungen").isJsonObject() ? s.getAsJsonObject("einstellungen") : new JsonObject();
	}

	private static boolean an(JsonObject o, String k) {
		return o.has(k) && !o.get(k).isJsonNull() && o.get(k).getAsBoolean();
	}

	private static int zahl(JsonObject o, String k) {
		return o.has(k) && !o.get(k).isJsonNull() ? o.get(k).getAsInt() : 0;
	}

	private void befehl(String text) {
		mod.befehl("!" + text);
	}

	/** Schalter "Name: an/aus", Klick schickt "!befehl an|aus". */
	private void schalter(int x, int y, int breite, String name, String befehl, boolean wert, String hilfe) {
		addRenderableWidget(Button.builder(Component.literal(name + ": " + (wert ? "§aan" : "§caus")), b -> {
			befehl(befehl + (wert ? " aus" : " an"));
			b.setMessage(Component.literal(name + ": " + (!wert ? "§aan" : "§caus")));
		}).bounds(x, y, breite, 20).tooltip(Tooltip.create(Component.literal(hilfe))).build());
	}

	@Override
	protected void init() {
		JsonObject e = einst();
		JsonObject status = mod.botStatus();
		stand = standVon(status);
		int gesamt = Math.min(2 * B + 8, width - 16);
		int links = (width - gesamt) / 2;
		int spalte = (gesamt - 8) / 3; // drei Spalten mit je 4 Pixel Abstand
		int y = 20;
		if (status == null) {
			addRenderableWidget(Button.builder(Component.literal("Kein Bot online - Schließen"), b -> onClose())
					.bounds(width / 2 - 100, height / 2, 200, 20).build());
			return;
		}
		String[][] schalter = {
				{"Kampf", "kampf", "kampf", "Greift Monster und Angreifer an"},
				{"PvP", "pvp", "pvp", "Greift auch Spieler an, die du angreifst (außer Freunde)"},
				{"Aufheben", "nimm", "nimm", "Hebt herumliegende Sachen auf (sonst nur auf Befehl)"},
				{"Mace", "mace", "mace", "Mace-Smash aus dem Fall / mit Windladung"},
				{"Speer", "speer", "speer", "Speer-Stich und Speer-Sprung"},
				{"Elytra", "elytra", "elytra", "Mit Elytra folgen und Elytra-Mace"},
				{"Farmen", "farm", "farmt", "Felder in der Nähe ernten und neu pflanzen"},
				{"Fliegen", "flieg", "fliegt", "Mit Elytra abheben bzw. landen"},
				{"Logout bei Tod", "logout tod", "logoutTod", "Loggt aus, wenn du stirbst"}};
		for (int i = 0; i < schalter.length; i++) {
			String[] sc = schalter[i];
			schalter(links + (i % 3) * (spalte + 4), y + (i / 3) * 22, spalte, sc[0], sc[1], an(e, sc[2]), sc[3]);
		}
		y += 3 * 22 + 4;

		// Modus
		String modus = status.has("modus") ? status.get("modus").getAsString() : "";
		String[][] modi = {{"folgen", "Folgen", "folge"}, {"stehen", "Stehen", "stop"}, {"wache", "Wache", "wache"}};
		for (int i = 0; i < 3; i++) {
			String[] md = modi[i];
			addRenderableWidget(Button.builder(Component.literal((md[0].equals(modus) ? "§e> " : "") + md[1]), b -> befehl(md[2]))
					.bounds(links + i * (spalte + 4), y, spalte, 20).build());
		}
		y += 26;

		// Logout-Regeln: [-] Leben <= 8 [+]   [-] Uebermacht 3 [+]
		int halb = (gesamt - 4) / 2;
		int leben = zahl(e, "logoutLeben");
		zaehler(links, y, halb, "Leben ≤ " + (leben == 0 ? "aus" : leben), "Loggt aus, wenn er in Gefahr so wenig Leben hat (mit Totem erst bei 3)",
				"logout " + Math.max(0, leben - 2), "logout " + Math.min(18, leben + 2));
		int ueber = zahl(e, "logoutUebermacht");
		zaehler(links + halb + 4, y, halb, "Übermacht " + (ueber == 0 ? "aus" : "ab " + ueber), "Loggt aus, wenn so viele Spieler ihn oder dich angreifen",
				"logout uebermacht " + Math.max(0, ueber - 1), "logout uebermacht " + (ueber + 1));
		y += 26;

		// Freunde
		int knopf = 90;
		freundFeld = new EditBox(font, links, y, gesamt - knopf - 4, 20, Component.literal("Freund"));
		freundFeld.setMaxLength(16);
		freundFeld.setHint(Component.literal("Spielername"));
		addRenderableWidget(freundFeld);
		addRenderableWidget(Button.builder(Component.literal("Freund dazu"), b -> {
			String n = freundFeld.getValue().trim();
			if (!n.isEmpty()) befehl("freund " + n);
			freundFeld.setValue("");
		}).bounds(links + gesamt - knopf, y, knopf, 20).build());
		y += 22;
		List<String> freunde = new ArrayList<>();
		if (status.has("freunde") && status.get("freunde").isJsonArray()) for (JsonElement f : status.getAsJsonArray("freunde")) freunde.add(f.getAsString());
		int fx = links;
		for (String f : freunde) {
			int w = font.width(f) + 22;
			if (fx + w > links + gesamt) { fx = links; y += 22; }
			addRenderableWidget(Button.builder(Component.literal(f + " §cx"), b -> befehl("freund weg " + f))
					.bounds(fx, y, w, 20).tooltip(Tooltip.create(Component.literal(f + " von der Freundesliste nehmen"))).build());
			fx += w + 4;
		}
		if (!freunde.isEmpty()) y += 22;
		y += 4;
		addRenderableWidget(Button.builder(Component.literal("Fertig"), b -> onClose()).bounds(width / 2 - 60, Math.min(y, height - 22), 120, 20).build());
	}

	/** [-] Text [+] */
	private void zaehler(int x, int y, int breite, String text, String hilfe, String minus, String plus) {
		addRenderableWidget(Button.builder(Component.literal("-"), b -> befehl(minus)).bounds(x, y, 20, 20).build());
		Button mitte = Button.builder(Component.literal(text), b -> { }).bounds(x + 22, y, breite - 44, 20)
				.tooltip(Tooltip.create(Component.literal(hilfe))).build();
		mitte.active = false;
		addRenderableWidget(mitte);
		addRenderableWidget(Button.builder(Component.literal("+"), b -> befehl(plus)).bounds(x + breite - 20, y, 20, 20).build());
	}

	@Override
	public void tick() {
		super.tick();
		// Stand vom Bot uebernehmen (ohne das Eingabefeld zu zerstoeren, wenn gerade getippt wird)
		if (++tick % 20 != 0) return;
		String neu = standVon(mod.botStatus());
		if (!neu.equals(stand) && (freundFeld == null || (freundFeld.getValue().isEmpty() && !freundFeld.isFocused()))) rebuildWidgets();
	}

	private static String standVon(JsonObject s) {
		return s == null ? "" : String.valueOf(s.get("einstellungen")) + s.get("freunde") + s.get("modus");
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float delta) {
		super.extractRenderState(g, mouseX, mouseY, delta);
		g.centeredText(font, title, width / 2, 7, 0xFFFFFFFF);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	public static void oeffnen(BotLinkClient mod) {
		Minecraft.getInstance().gui.setScreen(new BotEinstellungenScreen(mod));
	}
}
