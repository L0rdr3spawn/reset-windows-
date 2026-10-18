package de.reiss.botlink;

import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;

/**
 * Leben und Hunger des Bots rechts neben deiner Hungerleiste (gleiche Hoehe), darueber klein, was er tut.
 */
public final class BotHud implements HudElement {
	private static final int ROT = 0xFFFF5555;
	private static final int ORANGE = 0xFFFFAA00;
	private static final int GRAU = 0xFFAAAAAA;
	private final BotLinkClient mod;

	public BotHud(BotLinkClient mod) {
		this.mod = mod;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null) return; // bei F1 (HUD aus) ruft Minecraft das Element gar nicht auf
		JsonObject s = mod.botStatus();
		if (s == null || !mod.managerErreichbar()) return;
		Font font = mc.font;
		int x = g.guiWidth() / 2 + 91 + 6; // rechts neben Hotbar/Hungerleiste
		int y = g.guiHeight() - 39;
		int leben = s.has("leben") ? s.get("leben").getAsInt() : 0;
		int hunger = s.has("hunger") ? s.get("hunger").getAsInt() : 0;
		String name = s.has("bot") ? s.get("bot").getAsString() : "Bot";
		g.text(font, "❤ " + leben, x, y, leben <= 6 ? ROT : 0xFFFF7777, true);
		g.text(font, "🍗 " + hunger, x + 34, y, hunger <= 6 ? ORANGE : 0xFFE0C080, true);
		String taetigkeit = s.has("ziel") && !s.get("ziel").isJsonNull() ? "⚔ " + s.get("ziel").getAsString()
				: s.has("fliegt") && s.get("fliegt").getAsBoolean() ? "fliegt"
				: s.has("aufgabe") && !"keine".equals(s.get("aufgabe").getAsString()) ? s.get("aufgabe").getAsString()
				: s.has("modus") ? s.get("modus").getAsString() : "";
		g.text(font, name + ": " + taetigkeit, x, y - 10, GRAU, true);
	}
}
