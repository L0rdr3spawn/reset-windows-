package de.reiss.botlink;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.client.Minecraft;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;

/**
 * Startet ueber "node bc.js join" den Manager (falls noetig) und schickt den Bot los. Ziel ist entweder ein
 * Profil aus begleiter/konfig.json oder eine Serveradresse (host:port) - fuer unbekannte Server legt der Manager
 * selbst ein Profil an (fremder Server, ueber ViaProxy). Du bist dabei immer der Besitzer.
 */
public final class BotStarter {
	static final Path BEGLEITER = Path.of(System.getProperty("user.home"), "Documents", "claude", "begleiter");

	private BotStarter() {
	}

	/** /bot join [profil]: ohne Profil der Server, auf dem du gerade bist. */
	public static void join(Minecraft mc, String profil, BiConsumer<Minecraft, String> melden) {
		if (!profil.isEmpty()) {
			starten(mc, List.of(profil), profil, melden);
			return;
		}
		if (mc.hasSingleplayerServer()) {
			melden.accept(mc, "Singleplayer: Pausenmenue -> \"Bot holen\" oeffnet die Welt im LAN und holt ihn.");
			return;
		}
		if (mc.getCurrentServer() == null) {
			melden.accept(mc, "Du bist auf keinem Server. /bot join <profil> (siehe begleiter/konfig.json)");
			return;
		}
		adresse(mc, mc.getCurrentServer().ip, false, melden);
	}

	/** Bot auf eine Serveradresse schicken (Profil aus konfig.json, falls es eins gibt). */
	public static void adresse(Minecraft mc, String adresse, boolean singleplayer, BiConsumer<Minecraft, String> melden) {
		List<String> args = new ArrayList<>();
		if (singleplayer) args.add("singleplayer");
		args.add("--adresse");
		args.add(adresse);
		starten(mc, args, adresse, melden);
	}

	private static void starten(Minecraft mc, List<String> ziel, String anzeige, BiConsumer<Minecraft, String> melden) {
		String ich = mc.player != null ? mc.player.getName().getString() : mc.getUser().getName();
		List<String> cmd = new ArrayList<>(List.of("node", "bc.js", "join"));
		cmd.addAll(ziel);
		cmd.add("--ich");
		cmd.add(ich);
		Thread t = new Thread(() -> {
			try {
				ProcessBuilder pb = new ProcessBuilder(cmd)
						.directory(BEGLEITER.toFile())
						.redirectErrorStream(true)
						.redirectOutput(new File(BEGLEITER.toFile(), "daten/botlink-join.log"));
				int code = pb.start().waitFor();
				String log = Files.exists(BEGLEITER.resolve("daten/botlink-join.log")) ? Files.readString(BEGLEITER.resolve("daten/botlink-join.log")).trim() : "";
				melden.accept(mc, code == 0 && !log.contains("\"fehler\"") ? "Bot kommt (" + anzeige + ")."
						: "Start fehlgeschlagen: " + (log.length() > 160 ? log.substring(0, 160) : log));
			} catch (Exception e) {
				melden.accept(mc, "Start fehlgeschlagen: " + e.getMessage());
			}
		}, "botlink-join");
		t.setDaemon(true);
		t.start();
	}

	/** Profilnamen aus begleiter/konfig.json (fuer Tab-Vorschlaege). */
	public static List<String> profile() {
		List<String> namen = new ArrayList<>();
		try {
			JsonObject konfig = JsonParser.parseString(Files.readString(BEGLEITER.resolve("konfig.json"))).getAsJsonObject();
			for (Map.Entry<String, com.google.gson.JsonElement> e : konfig.getAsJsonObject("server").entrySet()) namen.add(e.getKey());
		} catch (Exception ignored) {
			// keine Konfig lesbar
		}
		return namen;
	}
}
