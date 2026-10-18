package de.reiss.botlink;

import com.google.gson.JsonObject;
import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/**
 * Taste (Standard G): das Wesen, das du anschaust, soll der Bot angreifen. Erst das Wesen unter dem
 * Fadenkreuz, sonst das mit dem kleinsten Winkel zur Blickrichtung (bis 64 Bloecke, max. ~4 Grad).
 */
public final class ZielTaste {
	private static final KeyMapping.Category KATEGORIE =
			KeyMapping.Category.register(Identifier.fromNamespaceAndPath(BotLinkClient.MOD_ID, "bot"));
	private final KeyMapping taste;

	public ZielTaste() {
		taste = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.botlink.angriff", InputConstants.Type.KEYBOARD, InputConstants.KEY_G, KATEGORIE));
	}

	/** Weitere Taste in der Botlink-Kategorie (Steuerung -> Tastenbelegung). */
	public static KeyMapping taste(String name, int standard) {
		return KeyMappingHelper.registerKeyMapping(new KeyMapping(name, InputConstants.Type.KEYBOARD, standard, KATEGORIE));
	}

	/** Gibt das Ziel zurueck, falls die Taste gedrueckt wurde (sonst null). */
	/** Wurde die Taste seit dem letzten Tick gedrueckt? */
	public boolean gedrueckt() {
		boolean gedrueckt = false;
		while (taste.consumeClick()) gedrueckt = true;
		return gedrueckt;
	}

	/**
	 * Was soll der Bot tun? Wesen im Blick -> angreifen, Block im Blick -> dorthin gehen,
	 * nichts im Blick (Himmel) -> wieder folgen. Liegt ein Block vor dem Wesen, zaehlt der Block.
	 */
	public static JsonObject befehl(Minecraft mc) {
		if (mc.player == null || mc.level == null) return null;
		Entity e = angeschaut(mc);
		net.minecraft.world.phys.HitResult treffer = mc.player.pick(128, 1.0f, false);
		boolean block = treffer != null && treffer.getType() == net.minecraft.world.phys.HitResult.Type.BLOCK;
		double blockWeg = block ? treffer.getLocation().distanceTo(mc.player.getEyePosition()) : Double.MAX_VALUE;
		if (e != null && e.getBoundingBox().getCenter().distanceTo(mc.player.getEyePosition()) <= blockWeg + 0.5) return ereignis(e);
		JsonObject j = new JsonObject();
		if (block) {
			net.minecraft.core.BlockPos pos = ((net.minecraft.world.phys.BlockHitResult) treffer).getBlockPos();
			j.addProperty("art", "gehe");
			j.addProperty("x", pos.getX());
			j.addProperty("y", pos.getY());
			j.addProperty("z", pos.getZ());
		} else {
			j.addProperty("art", "folgen");
		}
		return j;
	}

	/** Wesen unter dem Fadenkreuz, sonst das mit dem kleinsten Winkel zur Blickrichtung (oder null). */
	public static Entity angeschaut(Minecraft mc) {
		Entity ziel = null;
		if (mc.player == null || mc.level == null) return null;
		if (mc.crosshairPickEntity instanceof LivingEntity e) return e;
		Vec3 auge = mc.player.getEyePosition();
		Vec3 blick = mc.player.getViewVector(1.0f);
		double besterWinkel = Math.toRadians(4);
		for (Entity e : mc.level.entitiesForRendering()) {
			if (e == mc.player || !(e instanceof LivingEntity) || !e.isAlive()) continue;
			Vec3 zu = e.getBoundingBox().getCenter().subtract(auge);
			double len = zu.length();
			if (len > 64 || len < 0.5) continue;
			double winkel = Math.acos(Math.max(-1, Math.min(1, zu.dot(blick) / len)));
			// weiter entfernte Ziele sind kleiner -> etwas Toleranz je nach Groesse
			double toleranz = besterWinkel + Math.atan2(e.getBbWidth(), len) * 0.5;
			if (winkel < toleranz && (ziel == null || winkel < besterWinkel)) {
				ziel = e;
				besterWinkel = winkel;
			}
		}
		return ziel;
	}

	public static JsonObject ereignis(Entity e) {
		JsonObject j = new JsonObject();
		j.addProperty("art", "ziel");
		j.addProperty("id", e.getId());
		j.addProperty("uuid", e.getUUID().toString());
		j.addProperty("zielName", e.getName().getString());
		return j;
	}
}
