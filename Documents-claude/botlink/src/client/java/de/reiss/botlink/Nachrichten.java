package de.reiss.botlink;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;

import java.net.URI;

/**
 * Zeigt Nachrichten des Bots lokal im Chat (nur du siehst sie). Inventar-Eintraege und Angebote sind
 * anklickbar: ein Klick fuehrt den Client-Befehl /bot gib ... aus, der ebenfalls nur lokal bleibt.
 */
public final class Nachrichten {
	private int seit = -1; // -1 = noch nie abgefragt -> alte Nachrichten ueberspringen

	public int seit() {
		return Math.max(seit, 0);
	}

	public static MutableComponent praefix() {
		return Component.literal("[Bot] ").withStyle(ChatFormatting.AQUA);
	}

	public void anzeigen(Minecraft mc, JsonObject antwort) {
		if (!antwort.has("nr") || !antwort.has("nachrichten")) return;
		int nr = antwort.get("nr").getAsInt();
		boolean ersterAbruf = seit < 0;
		int alt = seit;
		if (nr < seit) {
			// Manager neu gestartet (Zaehler wieder bei 0): ab jetzt von vorn
			seit = 0;
			return;
		}
		seit = nr;
		if (ersterAbruf || mc.player == null) return;
		var liste = antwort.getAsJsonArray("nachrichten").asList();
		// Rueckstau (z.B. lange im Menue gewesen) nicht komplett in den Chat kippen
		if (liste.size() > 30) liste = liste.subList(liste.size() - 30, liste.size());
		for (JsonElement el : liste) {
			JsonObject n = el.getAsJsonObject();
			// Ueberlappende Abrufe liefern dieselben Nachrichten - nur neue zeigen
			if (n.has("nr") && n.get("nr").getAsInt() <= alt) continue;
			String typ = n.has("typ") ? n.get("typ").getAsString() : "";
			String text = n.has("text") ? n.get("text").getAsString() : "";
			switch (typ) {
				case "inventar" -> inventar(mc, n);
				case "angebot" -> angebot(mc, n, text);
				case "login" -> login(mc, n, text);
				case "sagen" -> zeigen(mc, Component.literal(text).withStyle(ChatFormatting.GRAY));
				case "log" -> { } // Protokollzeilen nicht im Chat
				default -> zeigen(mc, Component.literal(text).withStyle(ChatFormatting.GOLD));
			}
		}
	}

	private static void zeigen(Minecraft mc, Component c) {
		mc.player.sendSystemMessage(praefix().append(c));
	}

	private static MutableComponent knopf(String text, String befehl, String hover, ChatFormatting farbe) {
		return Component.literal(text).withStyle(Style.EMPTY
				.withColor(farbe)
				.withClickEvent(new ClickEvent.RunCommand(befehl))
				.withHoverEvent(new HoverEvent.ShowText(Component.literal(hover))));
	}

	// items: [{ name, anzeige, anzahl, verz, abgebbar }]
	private static void inventar(Minecraft mc, JsonObject n) {
		zeigen(mc, Component.literal("Inventar (anklicken = er bringt dir 1 davon, mehr: /bot gib <item> <menge>):").withStyle(ChatFormatting.YELLOW));
		MutableComponent zeile = Component.empty();
		int inZeile = 0;
		for (JsonElement el : n.getAsJsonArray("items")) {
			JsonObject i = el.getAsJsonObject();
			String name = i.get("name").getAsString();
			String anzeige = i.has("anzeige") ? i.get("anzeige").getAsString() : name;
			int anzahl = i.get("anzahl").getAsInt();
			String verz = i.has("verz") ? i.get("verz").getAsString() : "";
			int abgebbar = i.has("abgebbar") ? i.get("abgebbar").getAsInt() : anzahl;
			String hover = anzeige + " x" + anzahl + (verz.isEmpty() ? "" : "\n" + verz)
					+ (abgebbar < anzahl ? "\nbehaelt " + (anzahl - abgebbar) + " selbst" : "")
					+ (abgebbar > 0 ? "\nKlick: 1 geben" : "\n(gibt er nicht ab)");
			ChatFormatting farbe = verz.isEmpty() ? ChatFormatting.WHITE : ChatFormatting.LIGHT_PURPLE;
			MutableComponent teil = abgebbar > 0
					? knopf("[" + anzeige + " x" + anzahl + "]", "/bot gib " + name + " 1", hover, farbe)
					: Component.literal("[" + anzeige + " x" + anzahl + "]").withStyle(Style.EMPTY.withColor(ChatFormatting.DARK_GRAY)
							.withHoverEvent(new HoverEvent.ShowText(Component.literal(hover))));
			zeile.append(teil).append(" ");
			if (++inZeile == 3) {
				zeigen(mc, zeile);
				zeile = Component.empty();
				inZeile = 0;
			}
		}
		if (inZeile > 0) zeigen(mc, zeile);
	}

	private static void angebot(Minecraft mc, JsonObject n, String text) {
		String item = n.get("item").getAsString();
		zeigen(mc, Component.literal(text + " ").withStyle(ChatFormatting.YELLOW)
				.append(knopf("[Ja, gib mir eins]", "/bot gib " + item + " 1", "Der Bot kommt zu dir und wirft es dir zu", ChatFormatting.GREEN)));
	}

	private static void login(Minecraft mc, JsonObject n, String text) {
		MutableComponent c = Component.literal(text + " ").withStyle(ChatFormatting.GOLD);
		if (n.has("url")) {
			try {
				c.append(Component.literal("[Seite oeffnen]").withStyle(Style.EMPTY.withColor(ChatFormatting.GREEN)
						.withClickEvent(new ClickEvent.OpenUrl(new URI(n.get("url").getAsString())))));
			} catch (Exception ignored) {
				// ungueltige URL: nur Text zeigen
			}
		}
		zeigen(mc, c);
	}
}
