package de.reiss.botlink;

import de.reiss.botlink.mixin.JoinMultiplayerScreenAccessor;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.Screens;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.multiplayer.JoinMultiplayerScreen;
import net.minecraft.client.gui.screens.multiplayer.ServerSelectionList;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.HttpUtil;

/**
 * Knoepfe:
 * <ul>
 *   <li>Mehrspieler-Menue (Kopfzeile links/rechts): "Mit Bot beitreten" (du + Bot auf den markierten Server), "Nur Bot schicken"</li>
 *   <li>Pausenmenue: "Bot holen" (auf deinen Server; im Singleplayer wird die Welt dafuer im LAN geoeffnet), "Bot rausschicken"</li>
 * </ul>
 */
public final class BotMenues {
	private static final int BREITE = 110;
	private final BotLinkClient mod;

	public BotMenues(BotLinkClient mod) {
		this.mod = mod;
	}

	public void registrieren() {
		ScreenEvents.AFTER_INIT.register((mc, screen, w, h) -> {
			if (screen instanceof JoinMultiplayerScreen mp) mehrspieler(mc, mp);
			else if (screen instanceof PauseScreen pause && pause.showsPauseMenu()) pause(mc, pause);
		});
	}

	private void mehrspieler(Minecraft mc, JoinMultiplayerScreen screen) {
		Button mit = Button.builder(Component.literal("Mit Bot beitreten"), b -> {
			ServerData s = markiert(screen);
			if (s == null) return;
			BotStarter.adresse(mc, s.ip, false, mod::lokal);
			screen.join(s);
		}).bounds(6, 6, BREITE, 20).tooltip(Tooltip.create(Component.literal("Du und der Bot betretet den markierten Server"))).build();
		// rechts oben in der Kopfzeile, damit nichts die Serverliste verdeckt
		Button nur = Button.builder(Component.literal("Nur Bot schicken"), b -> {
			ServerData s = markiert(screen);
			if (s == null) return;
			BotStarter.adresse(mc, s.ip, false, (m, text) -> BotLinkClient.LOGGER.info("[Bot] {}", text));
			b.setMessage(Component.literal("Bot geht los"));
		}).bounds(screen.width - BREITE - 6, 6, BREITE, 20).tooltip(Tooltip.create(Component.literal("Nur der Bot geht auf den markierten Server"))).build();
		Screens.getWidgets(screen).add(mit);
		Screens.getWidgets(screen).add(nur);
		// Nur aktiv, wenn ein Server markiert ist
		ScreenEvents.beforeTick(screen).register(s -> {
			boolean an = markiert(screen) != null;
			mit.active = an;
			nur.active = an;
		});
	}

	private static ServerData markiert(JoinMultiplayerScreen screen) {
		ServerSelectionList liste = ((JoinMultiplayerScreenAccessor) screen).botlink$serverListe();
		if (liste != null && liste.getSelected() instanceof ServerSelectionList.OnlineServerEntry e) return e.getServerData();
		return null;
	}

	private void pause(Minecraft mc, PauseScreen screen) {
		Button holen = Button.builder(Component.literal("Bot holen"), b -> {
			botHolen(mc);
			b.setMessage(Component.literal("Bot kommt ..."));
		}).bounds(6, 6, BREITE, 20).tooltip(Tooltip.create(Component.literal(mc.hasSingleplayerServer()
				? "Oeffnet die Welt im LAN (ohne Anmeldung) und holt den Bot" : "Bot auf diesen Server holen"))).build();
		Button raus = Button.builder(Component.literal("Bot rausschicken"), b -> {
			mod.botRaus();
			b.setMessage(Component.literal("Bot geht"));
		}).bounds(6, 28, BREITE, 20).build();
		Screens.getWidgets(screen).add(holen);
		Screens.getWidgets(screen).add(raus);
	}

	/** Pausenmenue "Bot holen": Mehrspieler = aktueller Server, Singleplayer = Welt im LAN oeffnen (offline). */
	public void botHolen(Minecraft mc) {
		IntegratedServer sp = mc.getSingleplayerServer();
		if (sp != null) {
			int port = sp.isPublished() ? sp.getPort() : HttpUtil.getAvailablePort();
			// Ohne Anmeldung, damit der Bot-Account ohne Microsoft-Login in DEINE Welt kommt (nur lokal im LAN).
			// Auch wenn die Welt schon ueber den normalen LAN-Knopf offen ist: der prueft beim Einloggen neu.
			sp.setUsesAuthentication(false);
			if (!sp.isPublished() && !sp.publishServer(MinecraftServer.MultiplayerScope.LAN, port)) {
				mod.lokal(mc, "Konnte die Welt nicht im LAN oeffnen.");
				return;
			}
			BotStarter.adresse(mc, "127.0.0.1:" + port, true, mod::lokal);
			return;
		}
		if (mc.getCurrentServer() != null) BotStarter.adresse(mc, mc.getCurrentServer().ip, false, mod::lokal);
		else mod.lokal(mc, "Kein Server.");
	}
}
