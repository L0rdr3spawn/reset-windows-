package de.reiss.botlink;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * Wegweiser oben in der Mitte: ist der Bot nicht zu sehen (zu weit weg, nicht im Blickfeld) oder in einer anderen
 * Dimension, zeigt ein Pfeil die Richtung, dazu Entfernung und Dimension. Andere Dimension: Nether-Koordinaten
 * werden umgerechnet (1:8), damit der Pfeil zum passenden Ort in deiner Welt zeigt.
 */
public final class BotWegweiser implements HudElement {
	private static final String[] PFEILE = {"↑", "↗", "→", "↘", "↓", "↙", "←", "↖"};
	private static final int CYAN = 0xFF55FFFF;
	private static final int GRAU = 0xFFB0B0B0;
	private final BotLinkClient mod;
	/** Zuletzt angezeigter Text (leer = nichts angezeigt), fuer Tests. */
	public static volatile String zuletzt = "";

	public BotWegweiser(BotLinkClient mod) {
		this.mod = mod;
	}

	static String dimName(String dim) {
		return switch (dim == null ? "" : dim) {
			case "minecraft:the_nether" -> "Nether";
			case "minecraft:the_end" -> "End";
			case "minecraft:overworld" -> "Oberwelt";
			default -> dim == null ? "?" : dim.replace("minecraft:", "");
		};
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || mc.level == null) return;
		JsonObject s = mod.botStatus();
		if (s == null || !mod.managerErreichbar() || !s.has("pos") || !s.get("pos").isJsonArray()) return;
		String meineDim = mc.level.dimension().identifier().toString();
		String botDim = s.has("dim") && !s.get("dim").isJsonNull() ? s.get("dim").getAsString() : meineDim;
		boolean andereDim = !botDim.equals(meineDim);

		Vec3 ziel;
		Player botEntity = andereDim ? null : mod.botEntity(mc);
		if (botEntity != null) {
			ziel = botEntity.position();
		} else {
			JsonArray p = s.getAsJsonArray("pos");
			ziel = new Vec3(p.get(0).getAsDouble() + 0.5, p.get(1).getAsDouble(), p.get(2).getAsDouble() + 0.5);
			if (andereDim) ziel = umrechnen(ziel, botDim, meineDim);
		}
		Vec3 ich = mc.player.position();
		double dx = ziel.x - ich.x;
		double dz = ziel.z - ich.z;
		double entfernung = Math.sqrt(dx * dx + dz * dz + Math.pow(ziel.y - ich.y, 2));

		// Winkel zur Blickrichtung (Minecraft: Yaw 0 = Sueden/+z, 90 = Westen/-x)
		double zielYaw = Math.toDegrees(Math.atan2(-dx, dz));
		double rel = ((zielYaw - mc.player.getYRot()) % 360 + 540) % 360 - 180; // -180..180, + = rechts
		// Er ist zu sehen (und leuchtet): in der Naehe (Standplatz 2-9 Bloecke, auch hinter dir) oder im Blickfeld
		boolean sichtbar = botEntity != null && (entfernung < 24 || (Math.abs(rel) < 35 && entfernung < 96));
		if (!andereDim && sichtbar) {
			zuletzt = "";
			return;
		}

		String pfeil = PFEILE[(int) Math.floorMod(Math.round(rel / 45.0), 8)];
		String text = pfeil + " " + (s.has("bot") ? s.get("bot").getAsString() : "Bot") + "  " + Math.round(entfernung) + " m";
		if (andereDim) text += "  (" + dimName(botDim) + ")";
		double hoehe = ziel.y - ich.y;
		if (Math.abs(hoehe) > 6) text += hoehe > 0 ? "  ▲" + Math.round(hoehe) : "  ▼" + Math.round(-hoehe);
		Font font = mc.font;
		int x = g.guiWidth() / 2 - font.width(text) / 2;
		int y = 22; // unter der Bossleiste
		g.fill(x - 3, y - 2, x + font.width(text) + 3, y + 10, 0x80000000);
		g.text(font, text, x, y, andereDim ? GRAU : CYAN, true);
		zuletzt = text;
	}

	/** Position aus der Bot-Dimension in die eigene umrechnen (nur Oberwelt <-> Nether sinnvoll, End: unveraendert). */
	private static Vec3 umrechnen(Vec3 p, String von, String nach) {
		if (von.equals("minecraft:the_nether") && nach.equals("minecraft:overworld")) return new Vec3(p.x * 8, p.y, p.z * 8);
		if (von.equals("minecraft:overworld") && nach.equals("minecraft:the_nether")) return new Vec3(p.x / 8, p.y, p.z / 8);
		return p;
	}
}
