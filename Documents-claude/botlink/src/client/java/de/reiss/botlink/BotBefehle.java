package de.reiss.botlink;

import com.google.gson.JsonObject;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import net.fabricmc.fabric.api.client.command.v2.ClientCommands;
import net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.PlayerInfo;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;

import java.util.ArrayList;
import java.util.List;

/**
 * Echte Client-Befehle mit Tab-Vorschlaegen. Nichts davon geht an den Server:
 * /bot ... wird zum Befehl an den lokalen Manager (POST /befehl "!..."), /arena ... an die Test-Arena (127.0.0.1:47812).
 */
public final class BotBefehle {
	private static final String[] ARENA_GEGNER = {"schild", "mace", "bogen", "tank", "rauf"};
	private static final String[] AN_AUS = {"an", "aus"};
	private static final String[] ROHSTOFFE = {"holz", "stein", "kohle", "eisen", "kupfer", "gold", "diamant", "smaragd", "redstone",
			"lapis", "quarz", "sand", "erde", "kies", "ton", "laub"};

	private final BotLinkClient mod;

	public BotBefehle(BotLinkClient mod) {
		this.mod = mod;
	}

	public void registrieren(CommandDispatcher<FabricClientCommandSource> d) {
		LiteralArgumentBuilder<FabricClientCommandSource> bot = ClientCommands.literal("bot")
				.executes(c -> bot("status"));
		for (String einfach : new String[]{"folge", "stop", "wache", "land", "status", "hilfe", "lass", "heim", "nachhause", "lager", "selbst", "raus"}) {
			bot.then(ClientCommands.literal(einfach).executes(c -> bot(einfach)));
		}
		for (String schalter : new String[]{"pvp", "kampf", "nimm", "mace", "speer", "elytra"}) {
			bot.then(ClientCommands.literal(schalter)
					.executes(c -> bot(schalter))
					.then(ClientCommands.argument("an_aus", StringArgumentType.word()).suggests(vorschlag(AN_AUS))
							.executes(c -> bot(schalter + " " + wort(c, "an_aus")))));
		}
		bot.then(ClientCommands.literal("greif")
				.executes(c -> greifAngeschaut())
				.then(ClientCommands.argument("spieler", StringArgumentType.word()).suggests(spieler())
						.executes(c -> bot("greif " + wort(c, "spieler")))));
		bot.then(ClientCommands.literal("freund")
				.executes(c -> bot("freunde"))
				.then(ClientCommands.literal("weg")
						.then(ClientCommands.argument("name", StringArgumentType.word()).suggests(freunde())
								.executes(c -> bot("freund weg " + wort(c, "name")))))
				.then(ClientCommands.argument("name", StringArgumentType.word()).suggests(spieler())
						.executes(c -> bot("freund " + wort(c, "name")))));
		bot.then(ClientCommands.literal("logout")
				.executes(c -> bot("logout"))
				.then(ClientCommands.literal("aus").executes(c -> bot("logout aus")))
				.then(ClientCommands.literal("tod")
						.executes(c -> bot("logout tod"))
						.then(ClientCommands.argument("an_aus", StringArgumentType.word()).suggests(vorschlag(AN_AUS))
								.executes(c -> bot("logout tod " + wort(c, "an_aus")))))
				.then(ClientCommands.literal("hunger").then(ClientCommands.argument("n", IntegerArgumentType.integer(0, 20))
						.executes(c -> bot("logout hunger " + IntegerArgumentType.getInteger(c, "n")))))
				.then(ClientCommands.literal("uebermacht").then(ClientCommands.argument("n", IntegerArgumentType.integer(0, 50))
						.executes(c -> bot("logout uebermacht " + IntegerArgumentType.getInteger(c, "n")))))
				.then(ClientCommands.argument("leben", IntegerArgumentType.integer(0, 20))
						.executes(c -> bot("logout " + IntegerArgumentType.getInteger(c, "leben")))));
		bot.then(ClientCommands.literal("gib")
				.executes(c -> bot("gib"))
				.then(ClientCommands.argument("item", StringArgumentType.word()).suggests(botItems())
						.executes(c -> bot("gib " + wort(c, "item")))
						.then(ClientCommands.argument("menge", IntegerArgumentType.integer(1, 2304))
								.executes(c -> bot("gib " + wort(c, "item") + " " + IntegerArgumentType.getInteger(c, "menge"))))));
		bot.then(ClientCommands.literal("such")
				.then(ClientCommands.argument("block", StringArgumentType.word()).suggests(bloecke())
						.executes(c -> bot("such " + wort(c, "block")))
						.then(ClientCommands.argument("menge", IntegerArgumentType.integer(1, 999))
								.executes(c -> bot("such " + wort(c, "block") + " " + IntegerArgumentType.getInteger(c, "menge"))))));
		bot.then(ClientCommands.literal("tunnel")
				.executes(c -> bot("tunnel"))
				.then(ClientCommands.argument("laenge", IntegerArgumentType.integer(1, 512))
						.executes(c -> bot("tunnel " + IntegerArgumentType.getInteger(c, "laenge")))
						.then(ClientCommands.argument("mass", StringArgumentType.word()).suggests(vorschlag(new String[]{"1x2", "2x2", "3x3"}))
								.executes(c -> bot("tunnel " + IntegerArgumentType.getInteger(c, "laenge") + " " + wort(c, "mass"))))));
		bot.then(ClientCommands.literal("treppe")
				.executes(c -> bot("treppe"))
				.then(ClientCommands.argument("y", IntegerArgumentType.integer(-64, 320))
						.executes(c -> bot("treppe " + IntegerArgumentType.getInteger(c, "y")))));
		bot.then(ClientCommands.literal("sammel")
				.executes(c -> bot("sammel"))
				.then(ClientCommands.argument("rohstoff", StringArgumentType.word()).suggests(vorschlag(ROHSTOFFE))
						.executes(c -> bot("sammel " + wort(c, "rohstoff")))
						.then(ClientCommands.argument("menge", StringArgumentType.word()).suggests(vorschlag(new String[]{"16", "64", "unendlich"}))
								.executes(c -> bot("sammel " + wort(c, "rohstoff") + " " + wort(c, "menge"))))));
		bot.then(ClientCommands.literal("farm")
				.executes(c -> bot("farm"))
				.then(ClientCommands.literal("immer").executes(c -> bot("farm immer")))
				.then(ClientCommands.literal("an").executes(c -> bot("farm an")))
				.then(ClientCommands.literal("aus").executes(c -> bot("farm aus"))));
		bot.then(ClientCommands.literal("flieg")
				.executes(c -> bot("flieg"))
				.then(ClientCommands.literal("an").executes(c -> bot("flieg")))
				.then(ClientCommands.literal("aus").executes(c -> bot("flieg aus"))));
		bot.then(ClientCommands.literal("einstellungen").executes(c -> {
			mod.einstellungenOeffnen();
			return 1;
		}));
		// Baritone-Befehle (im Bot nachgebaut), z.B. /bot baritone mine diamond_ore 10
		for (String b : new String[]{"baritone", "b"}) {
			bot.then(ClientCommands.literal(b)
					.executes(c -> bot("baritone help"))
					.then(ClientCommands.argument("befehl", StringArgumentType.greedyString()).suggests(baritoneVorschlaege())
							.executes(c -> bot("baritone " + StringArgumentType.getString(c, "befehl")))));
		}
		bot.then(ClientCommands.literal("inv").executes(c -> {
			mod.inventarOeffnen();
			return 1;
		}));
		bot.then(ClientCommands.literal("join")
				.executes(c -> {
					BotStarter.join(Minecraft.getInstance(), "", mod::lokal);
					return 1;
				})
				.then(ClientCommands.argument("profil", StringArgumentType.word()).suggests((c, b) ->
								SharedSuggestionProvider.suggest(BotStarter.profile(), b))
						.executes(c -> {
							BotStarter.join(Minecraft.getInstance(), wort(c, "profil"), mod::lokal);
							return 1;
						})));
		bot.then(ClientCommands.literal("leave").executes(c -> {
			mod.botRaus();
			return 1;
		}));
		// Freier Text (geht an Jev bzw. als "!..."-Befehl, z.B. /bot sag !treppe 12)
		bot.then(ClientCommands.literal("sag")
				.then(ClientCommands.argument("text", StringArgumentType.greedyString())
						.executes(c -> {
							return senden(StringArgumentType.getString(c, "text"));
						})));
		d.register(bot);

		LiteralArgumentBuilder<FabricClientCommandSource> arena = ClientCommands.literal("arena")
				.executes(c -> arena("hilfe"));
		for (String a : new String[]{"kit", "heil", "hunger", "wald", "flug", "stop", "hilfe"}) {
			arena.then(ClientCommands.literal(a).executes(c -> arena(a)));
		}
		for (String g : ARENA_GEGNER) arena.then(ClientCommands.literal(g).executes(c -> arena(g)));
		arena.then(ClientCommands.literal("welle")
				.executes(c -> arena("welle"))
				.then(ClientCommands.argument("typen", StringArgumentType.greedyString()).suggests((c, b) -> {
					// Mehrere Typen: nur das letzte Wort vervollstaendigen
					String bisher = b.getRemaining();
					int leer = bisher.lastIndexOf(' ');
					return SharedSuggestionProvider.suggest(ARENA_GEGNER, b.createOffset(b.getStart() + leer + 1));
				}).executes(c -> arena("welle " + StringArgumentType.getString(c, "typen")))));
		d.register(arena);
	}

	// ------------------------------------------------------------------ Ausfuehren
	private int bot(String befehl) {
		return senden("!" + befehl);
	}

	private int senden(String text) {
		Minecraft mc = Minecraft.getInstance();
		if (!mod.api().erreichbar()) {
			mod.lokal(mc, "Der Begleiter-Manager laeuft nicht. /bot join startet ihn samt Bot.");
			return 0;
		}
		JsonObject b = new JsonObject();
		b.addProperty("text", text);
		mod.api().post("/befehl", b);
		return 1;
	}

	private int greifAngeschaut() {
		Minecraft mc = Minecraft.getInstance();
		Entity ziel = ZielTaste.angeschaut(mc);
		if (ziel == null) {
			mod.lokal(mc, "Du schaust nichts an. /bot greif <spieler> oder Taste G.");
			return 0;
		}
		mod.ereignis(ZielTaste.ereignis(ziel));
		mod.lokal(mc, "Ziel: " + ziel.getName().getString());
		return 1;
	}

	private int arena(String befehl) {
		Minecraft mc = Minecraft.getInstance();
		mod.api().postText(47812, "#" + befehl).thenAccept(r -> {
			if (r == null) mod.lokal(mc, "Arena laeuft nicht (node arena/arena.js).");
		});
		return 1;
	}

	// ------------------------------------------------------------------ Vorschlaege
	private static String wort(CommandContext<FabricClientCommandSource> c, String name) {
		return StringArgumentType.getString(c, name);
	}

	private static SuggestionProvider<FabricClientCommandSource> vorschlag(String[] werte) {
		return (c, b) -> SharedSuggestionProvider.suggest(werte, b);
	}

	private SuggestionProvider<FabricClientCommandSource> spieler() {
		return (c, b) -> {
			List<String> namen = new ArrayList<>();
			Minecraft mc = Minecraft.getInstance();
			if (mc.getConnection() != null) {
				for (PlayerInfo p : mc.getConnection().getOnlinePlayers()) {
					String n = p.getProfile().name();
					if (mc.player != null && n.equals(mc.player.getName().getString())) continue;
					if (n.equals(mod.botName())) continue;
					namen.add(n);
				}
			}
			return SharedSuggestionProvider.suggest(namen, b);
		};
	}

	private SuggestionProvider<FabricClientCommandSource> freunde() {
		return (c, b) -> SharedSuggestionProvider.suggest(mod.freunde(), b);
	}

	private SuggestionProvider<FabricClientCommandSource> botItems() {
		return (c, b) -> {
			mod.inventarAktualisieren();
			return SharedSuggestionProvider.suggest(mod.inventarItemNamen(), b);
		};
	}

	private static final String[] BARITONE = {"goto", "goal", "path", "mine", "follow", "farm", "explore", "tunnel", "come", "thisway",
			"surface", "find", "stop", "cancel", "pause", "resume", "set", "status", "help"};

	/** Vorschlaege je nach Baritone-Befehl: Bloecke fuer mine/goto/find, Spieler/Wesen fuer follow, Einstellungen fuer set. */
	private SuggestionProvider<FabricClientCommandSource> baritoneVorschlaege() {
		return (c, b) -> {
			String rest = b.getRemaining();
			String[] w = rest.split(" ", -1);
			var ab = b.createOffset(b.getStart() + rest.lastIndexOf(' ') + 1);
			if (w.length == 1) return SharedSuggestionProvider.suggest(BARITONE, ab);
			String cmd = w[0].toLowerCase();
			java.util.List<String> v = new ArrayList<>();
			switch (cmd) {
				case "mine", "find" -> BuiltInRegistries.BLOCK.keySet().stream().map(id -> id.getPath()).sorted().forEach(v::add);
				case "goto", "goal" -> {
					if (w.length == 2) BuiltInRegistries.BLOCK.keySet().stream().map(id -> id.getPath()).sorted().forEach(v::add);
					Minecraft mc = Minecraft.getInstance();
					if (mc.player != null) {
						int i = Math.min(w.length - 2, 2);
						v.add(String.valueOf(new int[]{mc.player.getBlockX(), mc.player.getBlockY(), mc.player.getBlockZ()}[i]));
					}
				}
				case "follow" -> {
					if (w.length == 2) v.addAll(List.of("player", "players", "entity", "entities"));
					else if (w[1].equals("player")) {
						Minecraft mc = Minecraft.getInstance();
						if (mc.getConnection() != null) for (PlayerInfo p : mc.getConnection().getOnlinePlayers()) v.add(p.getProfile().name());
					} else if (w[1].equals("entity")) BuiltInRegistries.ENTITY_TYPE.keySet().stream().map(id -> id.getPath()).sorted().forEach(v::add);
				}
				case "set" -> {
					if (w.length == 2) v.addAll(List.of("allowBreak", "allowPlace", "allowSprint", "allowParkour"));
					else v.addAll(List.of("true", "false"));
				}
				case "tunnel" -> v.addAll(List.of("2", "3", "1"));
				case "thisway" -> v.addAll(List.of("16", "32", "64", "100"));
				default -> { }
			}
			return SharedSuggestionProvider.suggest(v, ab);
		};
	}

	private static SuggestionProvider<FabricClientCommandSource> bloecke() {
		return (c, b) -> SharedSuggestionProvider.suggest(
				BuiltInRegistries.BLOCK.keySet().stream().map(id -> id.getPath()).sorted(), b);
	}
}
