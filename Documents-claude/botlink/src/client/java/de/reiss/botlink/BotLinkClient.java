package de.reiss.botlink;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.TreeSet;

/**
 * Botlink: macht deinen Client zum "Kommandopult" fuer den Begleiter-Bot.
 * <ul>
 *   <li>meldet 10x pro Sekunde deinen Zustand (Position, Leben, Hunger, Totems, Gleiten) an den lokalen Manager</li>
 *   <li>meldet, wen du schlaegst, und deinen Tod</li>
 *   <li>zeigt Leben/Hunger des Bots neben deiner Hungerleiste</li>
 *   <li>zeigt Bot-Nachrichten lokal im Chat, Inventar klickbar</li>
 *   <li>/bot ... und /arena ... sind echte Client-Befehle mit Tab-Vorschlaegen (nie an den Server)</li>
 *   <li>/bot inv: Bot-Inventar als Kiste, Klick = er bringt es dir</li>
 *   <li>der Bot leuchtet immer; ist er nicht zu sehen oder in einer anderen Dimension, zeigt ein Wegweiser die Richtung</li>
 *   <li>Knoepfe im Mehrspieler- und Pausenmenue</li>
 * </ul>
 */
public class BotLinkClient implements ClientModInitializer {
	public static final String MOD_ID = "botlink";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	private final ManagerApi api = new ManagerApi(47811);
	private final Nachrichten nachrichten = new Nachrichten();
	private static BotLinkClient instanz;
	private volatile JsonObject botStatus; // Status des ersten laufenden Bots
	private volatile JsonObject inventar; // letzter Inventar-Schnappschuss (GET /inventar)
	private volatile String botName;
	private volatile boolean inventarLaeuft;
	private boolean inventarOeffnen;
	private boolean einstellungenOeffnen;
	private net.minecraft.client.KeyMapping einstellungenTaste;
	private int tick;
	private boolean warTot;
	private volatile boolean zustandLaeuft;
	private ZielTaste zielTaste;

	@Override
	public void onInitializeClient() {
		instanz = this;
		zielTaste = new ZielTaste();
		einstellungenTaste = ZielTaste.taste("key.botlink.einstellungen", com.mojang.blaze3d.platform.InputConstants.KEY_B);
		ClientTickEvents.END_CLIENT_TICK.register(this::onTick);

		AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) -> {
			if (level.isClientSide()) {
				JsonObject e = new JsonObject();
				e.addProperty("art", "angriff");
				e.addProperty("id", entity.getId());
				e.addProperty("uuid", entity.getUUID().toString());
				ereignis(e);
			}
			return InteractionResult.PASS;
		});

		HudElementRegistry.attachElementAfter(VanillaHudElements.FOOD_BAR,
				Identifier.fromNamespaceAndPath(MOD_ID, "bot_status"), new BotHud(this));
		HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(MOD_ID, "wegweiser"), new BotWegweiser(this));

		BotBefehle befehle = new BotBefehle(this);
		ClientCommandRegistrationCallback.EVENT.register((dispatcher, access) -> befehle.registrieren(dispatcher));
		new BotMenues(this).registrieren();

		LOGGER.info("Botlink bereit (Manager auf 127.0.0.1:47811, /bot hilfe)");
	}

	public JsonObject botStatus() {
		return botStatus;
	}

	public boolean managerErreichbar() {
		return api.erreichbar();
	}

	public static BotLinkClient instanz() {
		return instanz;
	}

	public ManagerApi api() {
		return api;
	}

	public String botName() {
		return botName;
	}

	/** Ist das der Begleiter-Bot? (fuer Leuchten und Farbe, nur im Client) */
	public static boolean istBot(Entity e) {
		BotLinkClient m = instanz;
		return m != null && m.botName != null && e instanceof Player p && e.level().isClientSide()
				&& m.botName.equals(p.getGameProfile().name());
	}

	/** Das Spieler-Objekt des Bots in deiner Welt (null, wenn er nicht geladen ist). */
	public Player botEntity(Minecraft mc) {
		if (mc.level == null || botName == null) return null;
		for (Player p : mc.level.players()) if (botName.equals(p.getGameProfile().name())) return p;
		return null;
	}

	public List<String> freunde() {
		List<String> l = new ArrayList<>();
		JsonObject s = botStatus;
		if (s != null && s.has("freunde") && s.get("freunde").isJsonArray()) s.getAsJsonArray("freunde").forEach(e -> l.add(e.getAsString()));
		return l;
	}

	public JsonObject inventar() {
		return inventar;
	}

	/** Neuen Inventar-Schnappschuss holen (asynchron, hoechstens einer gleichzeitig). */
	public void inventarAktualisieren() {
		if (inventarLaeuft || !api.erreichbar()) return;
		inventarLaeuft = true;
		api.get("/inventar").whenComplete((r, e) -> {
			if (r != null && r.has("slots")) inventar = r;
			inventarLaeuft = false;
		});
	}

	public List<String> inventarItemNamen() {
		TreeSet<String> namen = new TreeSet<>();
		JsonObject inv = inventar;
		if (inv != null && inv.has("slots")) inv.getAsJsonArray("slots").forEach(e -> namen.add(e.getAsJsonObject().get("name").getAsString()));
		return new ArrayList<>(namen);
	}

	/** /bot inv: im naechsten Tick oeffnen (der Chat schliesst sich erst nach dem Befehl). */
	public void einstellungenOeffnen() {
		einstellungenOeffnen = true;
	}

	public void inventarOeffnen() {
		inventarAktualisieren();
		inventarOeffnen = true;
	}

	/** Ereignis an den Manager; "name" = du, damit er es an DEINEN Bot weiterleitet (nicht an fremde Test-Bots). */
	public void ereignis(JsonObject e) {
		LocalPlayer p = Minecraft.getInstance().player;
		if (p != null) e.addProperty("name", p.getName().getString());
		api.post("/ereignis", e);
	}

	public void befehl(String text) {
		JsonObject b = new JsonObject();
		b.addProperty("text", text);
		api.post("/befehl", b);
	}

	public void botRaus() {
		JsonObject b = new JsonObject();
		b.addProperty("grund", "auf Befehl");
		api.post("/leave", b);
		lokal(Minecraft.getInstance(), "Bot loggt aus.");
	}

	// ------------------------------------------------------------------ Tick
	private void onTick(Minecraft mc) {
		tick++;
		LocalPlayer p = mc.player;
		if (p == null) {
			warTot = false;
			return;
		}
		if (zielTaste.gedrueckt()) {
			JsonObject b = ZielTaste.befehl(mc);
			if (b != null) {
				ereignis(b);
				String art = b.get("art").getAsString();
				lokal(mc, switch (art) {
					case "ziel" -> "Ziel: " + b.get("zielName").getAsString();
					case "gehe" -> "Geh zu " + b.get("x").getAsInt() + " " + b.get("y").getAsInt() + " " + b.get("z").getAsInt();
					default -> "Folge mir";
				});
			}
		}

		// Ohne Manager nur alle 2 s anklopfen, sonst 10x pro Sekunde den Zustand melden
		boolean melden = api.erreichbar() ? tick % 2 == 0 : tick % 40 == 0;
		if (melden && !zustandLaeuft) {
			zustandLaeuft = true;
			api.post("/ereignis", zustand(mc, p)).whenComplete((r, e) -> zustandLaeuft = false);
		}

		float leben = p.getHealth();
		if (leben <= 0 && !warTot) {
			JsonObject e = new JsonObject();
			e.addProperty("art", "tod");
			ereignis(e);
		}
		warTot = leben <= 0;

		if (api.erreichbar() && tick % 10 == 0) {
			api.get("/nachrichten?seit=" + nachrichten.seit()).thenAccept(r -> {
				if (r != null) mc.execute(() -> nachrichten.anzeigen(mc, r));
			});
		}
		if (api.erreichbar() && tick % 20 == 5) {
			api.get("/status").thenAccept(r -> {
				botStatus = ersterBot(r);
				JsonObject s = botStatus;
				if (s != null && s.has("bot")) botName = s.get("bot").getAsString();
			});
		}
		if (api.erreichbar() && botStatus != null && tick % 40 == 15) inventarAktualisieren();
		if (inventarOeffnen) {
			inventarOeffnen = false;
			if (botStatus == null) lokal(mc, "Kein Bot online.");
			else mc.gui.setScreen(BotInventarScreen.erstellen(this));
		}
		while (einstellungenTaste.consumeClick()) einstellungenOeffnen = true;
		if (einstellungenOeffnen && mc.gui.screen() == null) {
			einstellungenOeffnen = false;
			BotEinstellungenScreen.oeffnen(this);
		}
	}

	private JsonObject zustand(Minecraft mc, LocalPlayer p) {
		JsonObject z = new JsonObject();
		z.addProperty("art", "zustand");
		z.addProperty("name", p.getName().getString());
		z.addProperty("x", p.getX());
		z.addProperty("y", p.getY());
		z.addProperty("z", p.getZ());
		z.addProperty("yaw", p.getYRot());
		z.addProperty("dim", mc.level != null ? mc.level.dimension().identifier().toString() : "");
		z.addProperty("leben", p.getHealth());
		z.addProperty("absorption", p.getAbsorptionAmount());
		z.addProperty("hunger", p.getFoodData().getFoodLevel());
		z.addProperty("saettigung", p.getFoodData().getSaturationLevel());
		z.addProperty("gleitet", p.isFallFlying());
		int totems = 0;
		for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
			ItemStack s = p.getInventory().getItem(i);
			if (s.is(Items.TOTEM_OF_UNDYING)) totems += s.getCount();
		}
		z.addProperty("totems", totems);
		if (mc.getCurrentServer() != null) z.addProperty("server", mc.getCurrentServer().ip);
		return z;
	}

	private static JsonObject ersterBot(JsonObject status) {
		if (status == null || !status.has("bots")) return null;
		JsonArray bots = status.getAsJsonArray("bots");
		for (JsonElement b : bots) {
			JsonObject o = b.getAsJsonObject();
			if (o.has("online") && o.get("online").getAsBoolean() && o.has("status") && o.get("status").isJsonObject()) {
				return o.getAsJsonObject("status");
			}
		}
		return null;
	}

	public void lokal(Minecraft mc, String text) {
		mc.execute(() -> {
			if (mc.player != null) mc.player.sendSystemMessage(Nachrichten.praefix().append(Component.literal(text)));
		});
	}
}
