package de.reiss.botlink.gametest;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.suggestion.Suggestion;
import de.reiss.botlink.BotInventarScreen;
import de.reiss.botlink.BotLinkClient;
import de.reiss.botlink.BotWegweiser;
import net.fabricmc.fabric.api.client.command.v2.ClientCommands;
import net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.fabric.api.client.screen.v1.Screens;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.multiplayer.JoinMultiplayerScreen;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.resolver.ServerAddress;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Botlink im echten Spiel. Voraussetzungen (vom Test-Skript gestartet):
 * <ul>
 *   <li>Begleiter-Manager auf 127.0.0.1:47811</li>
 *   <li>Labor-Server (Paper 26.2, Flachwelt, offline) auf 127.0.0.1:25530, RCON 25531</li>
 *   <li>Umgebungsvariable BOTLINK_RC = Pfad zu rc.js (RCON-Helfer), BOTLINK_BOT = Bot-Account</li>
 * </ul>
 * Ergebnis im Log unter "==== botlink ====", Bildschirmfotos in build/run/clientGameTest/screenshots.
 */
public class BotLinkGameTest implements FabricClientGameTest {
	private static final Logger LOG = LoggerFactory.getLogger("botlink-gametest");
	private static final String LABOR = "127.0.0.1:25530";
	private static final String BOT = System.getenv().getOrDefault("BOTLINK_BOT", "NotL0rdr3spawn");
	private static final HttpClient HTTP = HttpClient.newHttpClient();
	private final List<String> bericht = new ArrayList<>();
	private String ich;
	private ClientGameTestContext testCtx;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		testCtx = ctx;
		String phasen = System.getenv().getOrDefault("BOTLINK_PHASEN", "server,menue,singleplayer");
		try {
			if (phasen.contains("server")) phase("Server", () -> serverTests(ctx));
			if (phasen.contains("menue")) phase("Mehrspieler-Menue", () -> mehrspielerMenue(ctx));
			if (phasen.contains("einstellungen")) phase("Einstellungen + Baritone", () -> einstellungen(ctx));
			// zuletzt: mit "offen" bleibt die Welt danach zum Selberspielen offen
			if (phasen.contains("singleplayer")) phase("Singleplayer", () -> singleplayer(ctx));
		} finally {
			post("/leave", "{\"bot\":\"" + BOT + "\"}");
			StringBuilder sb = new StringBuilder("\n==== botlink ====\n");
			for (String z : bericht) sb.append(z).append('\n');
			LOG.info(sb.toString());
		}
	}

	// ------------------------------------------------------------------ Mehrspieler (Labor-Server)
	private void serverTests(ClientGameTestContext ctx) {
		verbinden(ctx, LABOR);
		ich = ctx.computeOnClient(mc -> mc.player.getName().getString());
		pruefe("verbunden als " + ich, true);
		rcon("op " + ich, "gamemode survival " + ich, "effect give " + ich + " resistance infinite 4 true",
				"effect give " + ich + " saturation infinite 0 true",
				"gamerule keep_inventory true", "gamerule spawn_monsters false", "gamerule advance_time false", "time set 1000",
				"fill -20 -61 -20 20 -61 20 grass_block", "fill -20 -60 -20 20 -50 20 air",
				"tp " + ich + " 0 -60 0 0 0", "clear " + ich);
		ctx.waitTicks(20);

		// Bot holen (Besitzer = dieser Test-Spieler)
		String join = post("/join", "{\"server\":\"labor\",\"ich\":\"" + ich + "\",\"bot\":\"" + BOT + "\"}");
		pruefe("Manager /join antwortet (" + join + ")", join != null && join.contains(BOT));
		warte(ctx, mc -> botOnline(), 600);
		rcon("execute in minecraft:overworld run tp " + BOT + " 3 -60 0");
		boolean da = warte(ctx, mc -> BotLinkClient.instanz().botEntity(mc) != null, 900);
		pruefe("Bot ist in der Welt sichtbar", da);
		if (!da) return;
		rcon("clear " + BOT,
				"give " + BOT + " diamond_sword[enchantments={sharpness:5,unbreaking:3}]",
				"give " + BOT + " totem_of_undying 3", "give " + BOT + " cooked_beef 32",
				"give " + BOT + " potion[potion_contents={potion:\"minecraft:strong_healing\"}]",
				"item replace entity " + BOT + " armor.head with diamond_helmet[enchantments={protection:4}]",
				"item replace entity " + BOT + " weapon.offhand with shield");
		ctx.waitTicks(60);

		// 3. Leuchten
		boolean leuchtet = ctx.computeOnClient(mc -> {
			Player b = BotLinkClient.instanz().botEntity(mc);
			return b != null && mc.shouldEntityAppearGlowing(b) && b.getTeamColor() == 0x55FFFF;
		});
		pruefe("Bot leuchtet (tuerkis)", leuchtet);
		ctx.runOnClient(mc -> mc.player.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES,
				BotLinkClient.instanz().botEntity(mc).getEyePosition()));
		ctx.waitTicks(5);
		ctx.takeScreenshot("botlink-leuchten");

		// 1. Tab-Vorschlaege
		ctx.waitFor(mc -> BotLinkClient.instanz().inventarItemNamen().contains("diamond_sword"), 200);
		pruefe("Tab: /bot gib <item> schlaegt Bot-Items vor", vorschlaege(ctx, "bot gib ").contains("diamond_sword"));
		pruefe("Tab: /bot such dia -> diamond_ore", vorschlaege(ctx, "bot such dia").contains("diamond_ore"));
		pruefe("Tab: /bot pvp -> an/aus", vorschlaege(ctx, "bot pvp ").containsAll(List.of("an", "aus")));
		List<String> unter = vorschlaege(ctx, "bot ");
		pruefe("Tab: /bot hat alle Unterbefehle " + unter, unter.containsAll(List.of("folge", "stop", "wache", "pvp", "kampf", "greif", "freund",
				"logout", "gib", "such", "nimm", "tunnel", "farm", "flieg", "land", "status", "inv", "join", "leave")));
		pruefe("Tab: /arena hat Unterbefehle", vorschlaege(ctx, "arena ").containsAll(List.of("kit", "welle", "tank", "mace")));
		pruefe("Tab: /bot join -> Profile", vorschlaege(ctx, "bot join ").contains("labor"));

		// Echte Befehle ueber den Chat: stop / folge
		chat(ctx, "/bot stop");
		pruefe("/bot stop -> Modus stehen", warte(ctx, mc -> "stehen".equals(statusFeld("modus")), 100));
		chat(ctx, "/bot folge");
		pruefe("/bot folge -> Modus folgen", warte(ctx, mc -> "folgen".equals(statusFeld("modus")), 100));

		// 2. /bot inv
		chat(ctx, "/bot inv");
		boolean offen = warte(ctx, mc -> mc.gui.screen() instanceof BotInventarScreen, 100);
		pruefe("/bot inv oeffnet die Kisten-Oberflaeche", offen);
		if (offen) {
			ctx.waitTicks(20);
			String inhalt = ctx.computeOnClient(mc -> {
				BotInventarScreen s = (BotInventarScreen) mc.gui.screen();
				StringBuilder b = new StringBuilder();
				for (Slot sl : s.getMenu().slots) {
					if (sl.index >= 45 || !sl.hasItem()) continue;
					ItemStack st = sl.getItem();
					b.append(sl.index).append('=').append(BuiltInRegistries.ITEM.getKey(st.getItem()).getPath()).append('x').append(st.getCount());
					if (st.isEnchanted()) b.append("(verz)");
					b.append(' ');
				}
				return b.toString();
			});
			bericht.add("   Inhalt: " + inhalt);
			pruefe("Kiste zeigt Helm im Kopf-Platz", inhalt.contains("0=diamond_helmetx1(verz)"));
			pruefe("Kiste zeigt Schild in der Nebenhand", inhalt.contains("5=shieldx1"));
			pruefe("Kiste zeigt verzaubertes Schwert", inhalt.contains("diamond_swordx1(verz)"));
			// Maus ueber das Schwert -> Tooltip mit Verzauberungen
			int[] pos = ctx.computeOnClient(mc -> slotPos((BotInventarScreen) mc.gui.screen(), Items.DIAMOND_SWORD));
			if (pos != null) {
				ctx.getInput().setCursorPos(pos[0] * ctx.computeOnClient(mc -> mc.getWindow().getGuiScale()), pos[1] * ctx.computeOnClient(mc -> mc.getWindow().getGuiScale()));
				ctx.waitTicks(5);
				ctx.takeScreenshot("botlink-inventar");
				// Linksklick -> Bot bringt das Schwert
				ctx.getInput().pressMouse(0);
				boolean bekommen = warte(ctx, mc -> {
					for (int i = 0; i < mc.player.getInventory().getContainerSize(); i++) {
						ItemStack st = mc.player.getInventory().getItem(i);
						if (st.is(Items.DIAMOND_SWORD) && st.isEnchanted()) return true;
					}
					return false;
				}, 400);
				pruefe("Klick auf Schwert: Bot bringt es (liegt im eigenen Inventar)", bekommen);
			} else {
				pruefe("Schwert-Platz gefunden", false);
			}
			// Totems: 3 hat er, 2 behaelt er -> Rechtsklick gibt 1, danach nichts mehr
			ctx.runOnClient(mc -> mc.gui.setScreen(null));
		}

		// Taste G: das angeschaute Wesen soll der Bot angreifen
		rcon("tp " + ich + " 0 -60 0 0 0", "summon pig 0 -60 4 {NoAI:1b,Invulnerable:1b,CustomName:\"Zielschwein\"}");
		ctx.waitTicks(20);
		ctx.runOnClient(mc -> {
			for (net.minecraft.world.entity.Entity e : mc.level.entitiesForRendering()) {
				if (net.minecraft.world.entity.EntityType.getKey(e.getType()).getPath().equals("pig")) mc.player.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, e.getBoundingBox().getCenter());
			}
		});
		ctx.waitTicks(3);
		ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_G);
		pruefe("Taste G: Bot greift das angeschaute Wesen an", warte(ctx, mc -> { String z = statusFeld("ziel"); return z != null && z.startsWith("Pig"); }, 100));
		chat(ctx, "/bot lass");
		rcon("kill @e[type=pig]");

		// Totem-Angebot: der Knopf im Chat fuehrt "/bot gib totem_of_undying 1" aus; 2 behaelt er immer
		int totemsVorher = totems(ctx);
		chat(ctx, "/bot gib totem_of_undying 1");
		pruefe("Totem-Angebot: Bot gibt eins ab", warte(ctx, mc -> totems(mc) > totemsVorher, 300));
		chat(ctx, "/bot gib totem_of_undying 1");
		ctx.waitTicks(100);
		pruefe("Totem-Angebot: die letzten 2 behaelt er", totems(ctx) == totemsVorher + 1);

		// 3b. Wegweiser: weit weg teleportieren
		rcon("fill 150 -61 -10 170 -61 10 grass_block", "tp " + ich + " 160 -60 0 90 0");
		ctx.waitTicks(40);
		String weg = BotWegweiser.zuletzt;
		pruefe("Wegweiser erscheint, wenn der Bot weit weg ist (\"" + weg + "\")", weg.contains(BOT) && weg.contains("m"));
		ctx.takeScreenshot("botlink-wegweiser");
		// Der Bot kommt nach (Position von der Mod, ausser Sichtweite)
		pruefe("Bot laeuft dir nach (ausser Sichtweite)", warte(ctx, mc -> {
			Player b = BotLinkClient.instanz().botEntity(mc);
			return b != null && b.distanceTo(mc.player) < 8;
		}, 900));

		// 4. Portal: Netherportal bauen, durchgehen, Bot folgt
		rcon("fill 160 -60 4 163 -56 4 obsidian", "fill 161 -59 4 162 -57 4 air", "setblock 161 -59 4 fire");
		ctx.waitTicks(10);
		boolean portal = ctx.computeOnClient(mc -> mc.level.getBlockState(new net.minecraft.core.BlockPos(161, -59, 4)).getBlock().getDescriptionId().contains("nether_portal"));
		pruefe("Netherportal angezuendet", portal);
		rcon("tp " + ich + " 161.5 -59 4.5");
		boolean imNether = warte(ctx, mc -> mc.level.dimension().identifier().toString().equals("minecraft:the_nether"), 400);
		pruefe("Test-Spieler ist im Nether", imNether);
		if (imNether) {
			ctx.waitTicks(40);
			rcon("execute in minecraft:the_nether run fill ~-3 ~-1 ~-3 ~3 ~-1 ~3 netherrack");
			String wegNether = BotWegweiser.zuletzt;
			pruefe("Wegweiser zeigt andere Dimension (\"" + wegNether + "\")", wegNether.contains("Oberwelt") || "minecraft:the_nether".equals(statusFeld("dim")));
			ctx.takeScreenshot("botlink-wegweiser-dimension");
			boolean folgt = warte(ctx, mc -> "minecraft:the_nether".equals(statusFeld("dim")), 1200);
			pruefe("Bot folgt durchs Portal in den Nether", folgt);
			if (folgt) {
				pruefe("Bot steht im Nether bei dir", warte(ctx, mc -> {
					Player b = BotLinkClient.instanz().botEntity(mc);
					return b != null && b.distanceTo(mc.player) < 10;
				}, 600));
				ctx.takeScreenshot("botlink-nether");
			}
			// zurueck durch dasselbe Portal
			ctx.runOnClient(mc -> mc.player.connection.sendCommand("execute in minecraft:overworld run tp @s 161.5 -59 4.5"));
			boolean zurueck = warte(ctx, mc -> mc.level.dimension().identifier().toString().equals("minecraft:overworld"), 400);
			pruefe("Test-Spieler wieder in der Oberwelt", zurueck);
		}

		// 8. Pausenmenue-Knoepfe
		ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_ESCAPE);
		boolean pause = warte(ctx, mc -> mc.gui.screen() instanceof PauseScreen, 60);
		pruefe("Pausenmenue offen", pause);
		if (pause) {
			ctx.waitTicks(5);
			pruefe("Pausenmenue hat \"Bot holen\" und \"Bot rausschicken\"", ctx.computeOnClient(mc -> knopf(mc, "Bot holen") != null && knopf(mc, "Bot rausschicken") != null));
			ctx.takeScreenshot("botlink-pausenmenue");
			ctx.runOnClient(mc -> knopf(mc, "Bot rausschicken").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			pruefe("\"Bot rausschicken\" -> Bot geht", warte(ctx, mc -> !botOnline(), 200));
			ctx.runOnClient(mc -> knopf(mc, "Bot holen").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			pruefe("\"Bot holen\" -> Bot kommt wieder", warte(ctx, mc -> botOnline(), 600));
			ctx.runOnClient(mc -> mc.gui.setScreen(null));
		}
		post("/leave", "{\"bot\":\"" + BOT + "\"}");
		warte(ctx, mc -> !botOnline(), 200);
		trennen(ctx);
	}

	private static void trennen(ClientGameTestContext ctx) {
		ctx.runOnClient(mc -> { if (mc.level != null) mc.disconnectWithProgressScreen(); });
		warte(ctx, mc -> mc.level == null, 200);
		ctx.runOnClient(mc -> mc.gui.setScreen(new TitleScreen()));
		ctx.waitTicks(5);
	}

	// ------------------------------------------------------------------ Einstellungs-Menue + /bot baritone
	private void einstellungen(ClientGameTestContext ctx) {
		try {
			einstellungenTest(ctx);
		} finally {
			post("/leave", "{\"bot\":\"" + BOT + "\"}");
			warte(ctx, mc -> !botOnline(), 200);
			trennen(ctx);
		}
	}

	private void einstellungenTest(ClientGameTestContext ctx) {
		verbinden(ctx, LABOR);
		ich = ctx.computeOnClient(mc -> mc.player.getName().getString());
		rcon("gamemode creative " + ich, "tp " + ich + " 0 -60 0 0 0");
		post("/join", "{\"server\":\"labor\",\"ich\":\"" + ich + "\",\"bot\":\"" + BOT + "\"}");
		warte(ctx, mc -> botOnline(), 600);
		rcon("execute in minecraft:overworld run tp " + BOT + " 2 -60 2");
		warte(ctx, mc -> BotLinkClient.instanz().botStatus() != null && BotLinkClient.instanz().botStatus().has("einstellungen"), 200);

		// Taste B oeffnet das Menue
		ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_B);
		boolean offen = warte(ctx, mc -> mc.gui.screen() instanceof de.reiss.botlink.BotEinstellungenScreen, 100);
		pruefe("Taste B oeffnet die Bot-Einstellungen", offen);
		if (offen) {
			ctx.waitTicks(10);
			ctx.takeScreenshot("botlink-einstellungen");
			String pvpVorher = einstFeld("pvp");
			ctx.runOnClient(mc -> knopfBeginn(mc, "PvP:").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			pruefe("Schalter PvP wirkt (" + pvpVorher + " -> umgeschaltet)", warte(ctx, mc -> !java.util.Objects.equals(pvpVorher, einstFeld("pvp")), 100));
			ctx.runOnClient(mc -> knopfBeginn(mc, "PvP:").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			warte(ctx, mc -> java.util.Objects.equals(pvpVorher, einstFeld("pvp")), 100);
			String nimmVorher = einstFeld("nimm");
			pruefe("Items aufheben ist standardmaessig aus", "false".equals(nimmVorher));
			// Freund per Eingabefeld hinzufuegen und per x wieder entfernen
			ctx.runOnClient(mc -> {
				for (var w : Screens.getWidgets(mc.gui.screen())) if (w instanceof net.minecraft.client.gui.components.EditBox e) e.setValue("Testfreund");
				knopf(mc, "Freund dazu").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0));
			});
			pruefe("Freund hinzufuegen", warte(ctx, mc -> String.valueOf(statusFeldRoh("freunde")).contains("Testfreund"), 100));
			ctx.waitTicks(30);
			ctx.takeScreenshot("botlink-einstellungen-freund");
			ctx.runOnClient(mc -> knopfBeginn(mc, "Testfreund").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			pruefe("Freund per x entfernen", warte(ctx, mc -> !String.valueOf(statusFeldRoh("freunde")).contains("Testfreund"), 100));
			ctx.runOnClient(mc -> knopfMit(mc, "Stehen").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			pruefe("Modus-Knopf Stehen", warte(ctx, mc -> "stehen".equals(statusFeld("modus")), 100));
			ctx.runOnClient(mc -> knopfMit(mc, "Folgen").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			ctx.runOnClient(mc -> mc.gui.setScreen(null));
		}
		// /bot baritone mit Tab-Vorschlaegen
		pruefe("Tab: /bot baritone -> Befehle", vorschlaege(ctx, "bot baritone ").containsAll(List.of("goto", "mine", "follow", "farm", "explore", "stop")));
		pruefe("Tab: /bot baritone mine dia -> diamond_ore", vorschlaege(ctx, "bot baritone mine dia").contains("diamond_ore"));
		pruefe("Tab: /bot baritone follow player -> Spieler", vorschlaege(ctx, "bot baritone follow player ").contains(ich));
		chat(ctx, "/bot baritone goto 10 -60 0");
		pruefe("/bot baritone goto 10 -60 0", warte(ctx, mc -> {
			Player b = BotLinkClient.instanz().botEntity(mc);
			return b != null && b.blockPosition().getX() == 10 && b.blockPosition().getZ() == 0;
		}, 300));
		chat(ctx, "/bot folge");
	}

	private static Button knopfMit(Minecraft mc, String teil) {
		for (AbstractWidget w : Screens.getWidgets(mc.gui.screen())) {
			if (w instanceof Button b && b.getMessage().getString().contains(teil)) return b;
		}
		return null;
	}

	private static Button knopfBeginn(Minecraft mc, String anfang) {
		for (AbstractWidget w : Screens.getWidgets(mc.gui.screen())) {
			if (w instanceof Button b && b.getMessage().getString().startsWith(anfang)) return b;
		}
		return null;
	}

	private static String einstFeld(String feld) {
		JsonElement e = statusFeldRoh("einstellungen");
		if (e == null || !e.isJsonObject() || !e.getAsJsonObject().has(feld)) return null;
		return e.getAsJsonObject().get(feld).getAsString();
	}

	private static JsonElement statusFeldRoh(String feld) {
		String r = get("/status");
		if (r == null) return null;
		for (JsonElement e : JsonParser.parseString(r).getAsJsonObject().getAsJsonArray("bots")) {
			JsonObject b = e.getAsJsonObject();
			if (b.get("name").getAsString().equals(BOT) && b.get("online").getAsBoolean() && b.get("status").isJsonObject()) return b.getAsJsonObject("status").get(feld);
		}
		return null;
	}

	// ------------------------------------------------------------------ Mehrspieler-Menue
	private void mehrspielerMenue(ClientGameTestContext ctx) {
		ctx.runOnClient(mc -> {
			JoinMultiplayerScreen s = new JoinMultiplayerScreen(new TitleScreen());
			mc.gui.setScreen(s);
		});
		ctx.waitTicks(10);
		ctx.runOnClient(mc -> {
			JoinMultiplayerScreen s = (JoinMultiplayerScreen) mc.gui.screen();
			if (s.getServers().size() == 0) s.getServers().add(new ServerData("Labor", LABOR, ServerData.Type.OTHER), false);
			s.getServers().save();
			mc.gui.setScreen(new JoinMultiplayerScreen(new TitleScreen()));
		});
		ctx.waitTicks(10);
		pruefe("Mehrspieler-Menue hat \"Mit Bot beitreten\" + \"Nur Bot schicken\"",
				ctx.computeOnClient(mc -> knopf(mc, "Mit Bot beitreten") != null && knopf(mc, "Nur Bot schicken") != null));
		pruefe("Knoepfe aus, solange kein Server markiert ist", ctx.computeOnClient(mc -> !knopf(mc, "Nur Bot schicken").active));
		// ersten Server markieren (Klick in die Liste)
		ctx.runOnClient(mc -> {
			JoinMultiplayerScreen s = (JoinMultiplayerScreen) mc.gui.screen();
			var liste = ((de.reiss.botlink.mixin.JoinMultiplayerScreenAccessor) s).botlink$serverListe();
			liste.setSelected(liste.children().get(0));
		});
		ctx.waitTicks(5);
		ctx.takeScreenshot("botlink-mehrspieler");
		pruefe("Knoepfe an, wenn ein Server markiert ist", ctx.computeOnClient(mc -> knopf(mc, "Nur Bot schicken").active));
		if (ich == null) ich = ctx.computeOnClient(mc -> mc.getUser().getName());
		ctx.runOnClient(mc -> knopf(mc, "Nur Bot schicken").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
		boolean kommt = warte(ctx, mc -> botOnline(), 900);
		pruefe("\"Nur Bot schicken\" -> Bot ist auf dem Labor-Server (ohne Profilangabe, host:port)", kommt);
		post("/leave", "{\"bot\":\"" + BOT + "\"}");
		warte(ctx, mc -> !botOnline(), 200);
		// "Mit Bot beitreten": Bot + ich
		ctx.runOnClient(mc -> knopf(mc, "Mit Bot beitreten").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
		boolean beide = warte(ctx, mc -> mc.player != null && mc.level != null && botOnline(), 1200);
		pruefe("\"Mit Bot beitreten\" -> du und der Bot seid auf dem Server", beide);
		post("/leave", "{\"bot\":\"" + BOT + "\"}");
		warte(ctx, mc -> !botOnline(), 200);
		trennen(ctx);
	}

	// ------------------------------------------------------------------ Singleplayer + LAN + ViaProxy
	private void singleplayer(ClientGameTestContext ctx) {
		// Normale Survival-Welt (keine Flachwelt), wie beim User
		try (TestSingleplayerContext sp = ctx.worldBuilder().setUseConsistentSettings(false).create()) {
			ctx.waitFor(mc -> mc.player != null, 1200);
			ctx.waitTicks(40);
			var server = sp.getServer();
			String tester = ctx.computeOnClient(mc -> mc.player.getName().getString());
			zuschauerServer = server;
			server.runCommand("gamemode survival " + tester);
			server.runCommand("gamerule spawn_monsters false");
			server.runCommand("time set 1000");
			server.runCommand("give " + tester + " water_bucket");
			server.runCommand("effect give " + tester + " resistance infinite 4 true"); // Test-Spieler soll nicht sterben (Bot loggt dann aus)
			melden(ctx, "Singleplayer-Test startet (normale Welt)");

			// So hat es der User gemacht: Welt ueber den normalen LAN-Knopf geoeffnet -> mit Microsoft-Anmeldung
			ctx.runOnClient(mc -> {
				var is = mc.getSingleplayerServer();
				// fester Port (dort schaut der User zu), Befehle fuer Gaeste erlaubt (er soll selbst Befehle nutzen koennen)
				is.publishServer(net.minecraft.server.MinecraftServer.MultiplayerScope.LAN, true, 25580);
				is.setUsesAuthentication(true);
			});
			melden(ctx, "Welt normal im LAN geoeffnet (mit Anmeldung) - jetzt Pausenmenue -> Bot holen");
			ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_ESCAPE);
			boolean pause = warte(ctx, mc -> mc.gui.screen() instanceof PauseScreen, 60);
			pruefe("Singleplayer-Pausenmenue offen", pause);
			if (!pause) return;
			ctx.waitTicks(20);
			ctx.runOnClient(mc -> knopf(mc, "Bot holen").onPress(new net.minecraft.client.input.KeyEvent(0, 0, 0)));
			ctx.waitTicks(20);
			ctx.runOnClient(mc -> mc.gui.setScreen(null));
			pruefe("\"Bot holen\" schaltet die Anmeldung fuer den Bot ab", ctx.computeOnClient(mc -> !mc.getSingleplayerServer().usesAuthentication()));
			boolean da = warte(ctx, mc -> botIn(mc) != null, 2400);
			pruefe("Bot kommt ueber LAN + ViaProxy in die Singleplayer-Welt (26.1 -> 26.3)", da);
			if (!da) return;
			melden(ctx, "Bot ist da - er soll mir folgen");

			// Folgen: ein paar Bloecke weglaufen
			server.runCommand("execute as " + tester + " at @s run spreadplayers ~12 ~ 0 1 false @s"); // auf echten Boden, 12 Bloecke weiter
			pruefe("Bot folgt (Abstand < 8)", warte(ctx, mc -> botIn(mc) != null && botIn(mc).distanceTo(mc.player) < 8, 600));
			ctx.takeScreenshot("sp-folgen");

			// Inventar + Geben
			server.runCommand("give " + BOT + " diamond_sword[enchantments={sharpness:5}]");
			ctx.waitTicks(40);
			chat(ctx, "/bot inv");
			boolean offen = warte(ctx, mc -> mc.gui.screen() instanceof BotInventarScreen, 100);
			pruefe("/bot inv zeigt sein Inventar", offen);
			if (offen) {
				ctx.waitTicks(30);
				ctx.takeScreenshot("sp-inventar");
				ctx.runOnClient(mc -> mc.gui.setScreen(null));
			}
			server.runCommand("tp " + BOT + " " + tester); // erreichbar zu dir
			ctx.waitTicks(20);
			chat(ctx, "/bot gib diamond_sword 1");
			pruefe("/bot gib: Schwert kommt an", warte(ctx, mc -> {
				for (int i = 0; i < mc.player.getInventory().getContainerSize(); i++) if (mc.player.getInventory().getItem(i).is(Items.DIAMOND_SWORD)) return true;
				return false;
			}, 800));

			// Kampf auf freier Flaeche bei Nacht: Zombie und Schleim (am Schleim ist der Bot frueher rausgeflogen)
			melden(ctx, "Kampftest: Zombie + Schleim auf freier Flaeche");
			server.runCommand("time set 18000");
			server.runCommand("execute as " + tester + " at @s run fill ~-10 ~-1 ~-10 ~10 ~-1 ~10 stone");
			server.runCommand("execute as " + tester + " at @s run fill ~-10 ~ ~-10 ~10 ~6 ~10 air");
			server.runCommand("execute as " + tester + " at @s run tp " + BOT + " ~2 ~ ~2");
			ctx.waitTicks(20);
			String todeVorher = statusFeld("tode");
			server.runCommand("execute as " + tester + " at @s run summon zombie ~6 ~ ~6");
			server.runCommand("execute as " + tester + " at @s run summon slime ~-6 ~ ~5 {Size:1}");
			pruefe("Bot besiegt Zombie + Schleim", warte(ctx, mc -> {
				for (net.minecraft.world.entity.Entity e : mc.level.entitiesForRendering()) {
					String t = net.minecraft.world.entity.EntityType.getKey(e.getType()).getPath();
					// nur Gegner in deiner Naehe - weggehuepfte Schleime (> 12 Bloecke) laesst er bewusst in Ruhe
					if ((t.equals("zombie") || t.equals("slime")) && e.distanceTo(mc.player) < 12) return false;
				}
				return true;
			}, 900));
			pruefe("Bot bleibt dabei online und lebt", ctx.computeOnClient(mc -> botIn(mc) != null) && java.util.Objects.equals(todeVorher, statusFeld("tode")));
			server.runCommand("time set 1000");
			server.runCommand("kill @e[type=zombie]");
			server.runCommand("kill @e[type=slime]");
			ctx.takeScreenshot("sp-kampf");

			// MLG auf Stein und auf Laub (Laub nimmt Wasser auf -> erst Baublock, dann Wasser)
			for (String boden : new String[]{"stone", "oak_leaves[persistent=true]"}) {
				server.runCommand("clear " + BOT + " water_bucket");
				server.runCommand("clear " + BOT + " bucket");
				server.runCommand("give " + BOT + " water_bucket");
				server.runCommand("give " + BOT + " dirt 16");
				server.runCommand("effect give " + BOT + " instant_health 1 5");
				// ganzer Boden aus diesem Material: er driftet im Fallen etwas zur Seite
				server.runCommand("execute as " + tester + " at @s run fill ~-10 ~ ~-10 ~10 ~45 ~10 air");
				server.runCommand("execute as " + tester + " at @s run fill ~-10 ~-1 ~-10 ~10 ~-1 ~10 " + boden);
				ctx.waitTicks(60);
				String tode = statusFeld("tode");
				melden(ctx, "MLG-Test: Bot faellt auf " + boden);
				// Laub: Erdblock + Wasser brauchen zwei Ticks -> nur bis ~30 Bloecke machbar
				server.runCommand("execute as " + tester + " at @s run tp " + BOT + " ~8 ~" + (boden.startsWith("stone") ? 40 : 25) + " ~");
				ctx.waitTicks(160);
				float leben = ctx.computeOnClient(mc -> botIn(mc) != null ? botIn(mc).getHealth() : -1f);
				pruefe("MLG auf " + boden + ": ueberlebt ohne Tod (Leben " + leben + ")", leben > 0 && java.util.Objects.equals(tode, statusFeld("tode")));
			}

			pruefe("Bot ist nach allen Tests noch in der Welt", ctx.computeOnClient(mc -> botIn(mc) != null));
			ctx.takeScreenshot("botlink-singleplayer");

			// Offen lassen: der User kann jetzt selbst spielen (Fenster schliessen = Ende)
			if (System.getenv().getOrDefault("BOTLINK_PHASEN", "").contains("offen")) {
				melden(ctx, "Fertig! Du kannst jetzt selbst spielen - Fenster schliessen beendet den Test.");
				LOG.info("\n==== botlink ====\n{}", String.join("\n", bericht));
				while (true) { zuschauer(); ctx.waitTicks(100); }
			}
			post("/leave", "{\"bot\":\"" + BOT + "\"}");
			warte(ctx, mc -> !botOnline(), 200);
		}
	}

	private static Player botIn(Minecraft mc) {
		if (mc.level == null) return null;
		return mc.level.players().stream().filter(p -> p.getGameProfile().name().equals(BOT)).findFirst().orElse(null);
	}

	/** Der User schaut mit seinem eigenen Client zu (LAN 127.0.0.1:25580): Zuschauermodus + OP, stoert den Test nicht. */
	private static net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext zuschauerServer;
	private static final String ZUSCHAUER = System.getenv().getOrDefault("BOTLINK_ZUSCHAUER", "L0rdr3spawn");

	private static void zuschauer() {
		if (zuschauerServer == null) return;
		// nur beim ersten Betreten auf Zuschauer stellen - danach darf er selbst umschalten
		zuschauerServer.runCommand("execute as " + ZUSCHAUER + " unless entity @s[tag=botlink_zuschauer] run gamemode spectator @s");
		zuschauerServer.runCommand("tag " + ZUSCHAUER + " add botlink_zuschauer");
	}

	/** Schritt im Chat des Test-Clients anzeigen, damit man im Fenster mitlesen kann. */
	private static void melden(ClientGameTestContext ctx, String text) {
		zuschauer();
		if (zuschauerServer != null) zuschauerServer.runCommand("tellraw " + ZUSCHAUER + " {\"text\":\"[Test] " + text.replace("\"", "'") + "\",\"color\":\"light_purple\"}");
		LOG.info("[Test] {}", text);
		ctx.runOnClient(mc -> {
			if (mc.player != null) mc.player.sendSystemMessage(net.minecraft.network.chat.Component.literal("[Test] " + text).withStyle(net.minecraft.ChatFormatting.LIGHT_PURPLE));
		});
	}

	private static int totems(ClientGameTestContext ctx) {
		return ctx.computeOnClient(BotLinkGameTest::totems);
	}

	private static int totems(Minecraft mc) {
		int n = 0;
		for (int i = 0; i < mc.player.getInventory().getContainerSize(); i++) {
			ItemStack st = mc.player.getInventory().getItem(i);
			if (st.is(Items.TOTEM_OF_UNDYING)) n += st.getCount();
		}
		return n;
	}

	// ------------------------------------------------------------------ Hilfen
	private interface Schritt {
		void los() throws Exception;
	}

	private void phase(String name, Schritt s) {
		bericht.add("-- " + name);
		try {
			s.los();
		} catch (Throwable t) {
			bericht.add("FEHLER in " + name + ": " + t);
			LOG.error("Phase {} abgebrochen", name, t);
		}
	}

	private void pruefe(String was, boolean ok) {
		bericht.add((ok ? "OK    " : "FEHLT ") + was);
		if (zuschauerServer != null) zuschauerServer.runCommand("tellraw " + ZUSCHAUER + " {\"text\":\"" + (ok ? "[OK] " : "[FEHLT] ") + was.replace("\"", "'") + "\",\"color\":\"" + (ok ? "green" : "red") + "\"}");
		LOG.info("{} {}", ok ? "OK" : "FEHLT", was);
		if (testCtx != null) testCtx.runOnClient(mc -> {
			if (mc.player != null) mc.player.sendSystemMessage(net.minecraft.network.chat.Component.literal((ok ? "[OK] " : "[FEHLT] ") + was)
					.withStyle(ok ? net.minecraft.ChatFormatting.GREEN : net.minecraft.ChatFormatting.RED));
		});
	}

	private static boolean warte(ClientGameTestContext ctx, java.util.function.Predicate<Minecraft> p, int ticks) {
		try {
			ctx.waitFor(p, ticks);
			return true;
		} catch (AssertionError | RuntimeException e) {
			return false;
		}
	}

	private static void verbinden(ClientGameTestContext ctx, String adresse) {
		ctx.runOnClient(mc -> ConnectScreen.startConnecting(new TitleScreen(), mc, ServerAddress.parseString(adresse),
				new ServerData("Labor", adresse, ServerData.Type.OTHER), false, null));
		ctx.waitFor(mc -> mc.player != null && mc.level != null && mc.gui.screen() == null, 1200);
		ctx.waitTicks(40);
	}

	private static void chat(ClientGameTestContext ctx, String text) {
		ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_T);
		ctx.waitTicks(3);
		ctx.getInput().typeChars(text);
		ctx.waitTicks(2);
		ctx.getInput().pressKey(com.mojang.blaze3d.platform.InputConstants.KEY_RETURN);
		ctx.waitTicks(10);
	}

	private static List<String> vorschlaege(ClientGameTestContext ctx, String eingabe) {
		return ctx.computeOnClient(mc -> {
			CommandDispatcher<FabricClientCommandSource> d = ClientCommands.getActiveDispatcher();
			FabricClientCommandSource quelle = (FabricClientCommandSource) mc.getConnection().getSuggestionsProvider();
			List<String> l = new ArrayList<>();
			try {
				for (Suggestion s : d.getCompletionSuggestions(d.parse(eingabe, quelle)).get(2, TimeUnit.SECONDS).getList()) l.add(s.getText());
			} catch (Exception e) {
				l.add("FEHLER " + e);
			}
			return l;
		});
	}

	private static int[] slotPos(BotInventarScreen s, net.minecraft.world.item.Item item) {
		for (Slot sl : s.getMenu().slots) {
			if (sl.index < 45 && sl.getItem().is(item)) {
				int links = (s.width - 176) / 2;
				int oben = (s.height - (114 + 5 * 18)) / 2;
				return new int[]{links + sl.x + 8, oben + sl.y + 8};
			}
		}
		return null;
	}

	private static Button knopf(Minecraft mc, String text) {
		if (mc.gui.screen() == null) return null;
		for (AbstractWidget w : Screens.getWidgets(mc.gui.screen())) {
			if (w instanceof Button b && b.getMessage().getString().equals(text)) return b;
		}
		return null;
	}

	private static String statusFeld(String feld) {
		String r = get("/status");
		if (r == null) return null;
		JsonArray bots = JsonParser.parseString(r).getAsJsonObject().getAsJsonArray("bots");
		for (JsonElement e : bots) {
			JsonObject b = e.getAsJsonObject();
			if (b.get("name").getAsString().equals(BOT) && b.get("online").getAsBoolean() && b.get("status").isJsonObject()) {
				JsonElement v = b.getAsJsonObject("status").get(feld);
				return v == null || v.isJsonNull() ? null : v.getAsString();
			}
		}
		return null;
	}

	private static boolean botOnline() {
		String r = get("/status");
		if (r == null) return false;
		for (JsonElement e : JsonParser.parseString(r).getAsJsonObject().getAsJsonArray("bots")) {
			JsonObject b = e.getAsJsonObject();
			if (b.get("name").getAsString().equals(BOT) && b.get("online").getAsBoolean()) return true;
		}
		return false;
	}

	private static String get(String pfad) {
		try {
			return HTTP.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:47811" + pfad)).GET().build(), HttpResponse.BodyHandlers.ofString()).body();
		} catch (Exception e) {
			return null;
		}
	}

	private static String post(String pfad, String json) {
		try {
			return HTTP.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:47811" + pfad))
					.header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(json)).build(), HttpResponse.BodyHandlers.ofString()).body();
		} catch (Exception e) {
			return null;
		}
	}

	private static void rcon(String... befehle) {
		String rc = System.getenv("BOTLINK_RC");
		if (rc == null) throw new IllegalStateException("BOTLINK_RC fehlt");
		List<String> cmd = new ArrayList<>(List.of("node", rc));
		cmd.addAll(List.of(befehle));
		try {
			ProcessBuilder pb = new ProcessBuilder(cmd).redirectErrorStream(true);
			pb.environment().put("RC_PORT", "25531");
			pb.environment().put("RC_PW", "labor");
			Process p = pb.start();
			String aus = new String(p.getInputStream().readAllBytes());
			p.waitFor();
			LOG.info("RCON: {}", aus.replace('\n', ' '));
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
}
