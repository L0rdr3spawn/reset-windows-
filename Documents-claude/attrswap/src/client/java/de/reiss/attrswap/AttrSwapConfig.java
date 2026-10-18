package de.reiss.attrswap;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Plain JSON config, written to .minecraft/config/attrswap.json on first launch.
 */
public class AttrSwapConfig {
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static final Path PATH = FabricLoader.getInstance().getConfigDir().resolve("attrswap.json");

	public static final String MODE_SINGLE = "single";
	public static final String MODE_DOUBLE = "double";

	/**
	 * {@value #MODE_SINGLE}: one hit with the second slot's item while the server still applies the
	 * held item's attributes and charge, then straight back. This is the real attribute swap and hits
	 * hardest (sword held, mace hit: sword damage, sword recharge time, full smash bonus).
	 *
	 * <p>{@value #MODE_DOUBLE}: hit with the first slot, then with the second. The server clears the
	 * charge in {@code Player#attack}, so the second hit only keeps flat bonuses like the mace smash.
	 * Worth it when the first hit does something on its own, e.g. an axe disabling a shield.
	 */
	public String mode = MODE_SINGLE;

	/** Hotbar slot (0-8) to attack from first in double mode. -1 keeps whatever is currently selected. */
	public int firstSlot = -1;

	/**
	 * Let {@link AutoPick} choose per hit: mace when a smash is on, axe against a raised shield, both
	 * (axe then mace) when both apply. Falls back to the slots below when it finds nothing.
	 */
	public boolean autoPick = true;

	/**
	 * Run the auto pick on every normal left click at an entity, no extra key needed. Only steps in
	 * when it finds something better than the held item; every other click stays vanilla.
	 */
	public boolean onClick = true;

	public boolean isDoubleMode() {
		return MODE_DOUBLE.equals(mode);
	}

	/** Hotbar slot (0-8) holding the item to hit with (the second attack in double mode). */
	public int secondSlot = 1;

	/** Switch back to the slot held before the combo, still inside the same tick. Single mode always does. */
	public boolean swapBack = false;

	/** Only fire when the crosshair is actually on an entity. */
	public boolean requireTarget = true;

	/** Swap a worn elytra for a chestplate before the combo. */
	public boolean swapElytra = true;

	/** Hotbar slot holding the chestplate. -1 searches the hotbar for one. */
	public int chestplateSlot = -1;

	/**
	 * Ticks to wait between the elytra swap and the attacks.
	 *
	 * <p>Must be at least 1: the server clears the fall-flying flag in the entity tick, and
	 * MaceItem refuses to smash while that flag is set. At 0 the swap and the mace hit land in
	 * the same server tick, the flag is still set, and the smash bonus is silently skipped.
	 */
	public int elytraSwapLeadTicks = 1;

	/** Lunge key: hotbar slot (0-8) to charge on before stabbing. -1 finds one (empty, wind charge, totem...). */
	public int lungeRestSlot = -1;

	/** Lunge key: ticks to stay on the resting slot once its attributes are in place. */
	public int lungeRestTicks = 2;

	/**
	 * Lunge key: end up on the resting slot instead of the one held before. The next lunge then
	 * needs no rest at all, so you can lunge again right away.
	 */
	public boolean lungeReturnToRest = false;

	/** Print what each step did to the action bar, for testing. */
	public boolean debugMessages = false;

	public static AttrSwapConfig load() {
		AttrSwapConfig config = new AttrSwapConfig();

		if (Files.exists(PATH)) {
			try {
				String json = Files.readString(PATH, StandardCharsets.UTF_8);
				AttrSwapConfig loaded = GSON.fromJson(json, AttrSwapConfig.class);
				if (loaded != null) {
					config = loaded;
				}
			} catch (IOException | RuntimeException e) {
				AttrSwapClient.LOGGER.warn("Could not read {}, falling back to defaults", PATH, e);
			}
		}

		config.clamp();
		config.save();
		return config;
	}

	public void save() {
		try {
			Files.createDirectories(PATH.getParent());
			Files.writeString(PATH, GSON.toJson(this), StandardCharsets.UTF_8);
		} catch (IOException e) {
			AttrSwapClient.LOGGER.warn("Could not write {}", PATH, e);
		}
	}

	private void clamp() {
		if (firstSlot < -1 || firstSlot > 8) {
			firstSlot = -1;
		}
		if (secondSlot < 0 || secondSlot > 8) {
			secondSlot = 1;
		}
		if (lungeRestSlot < -1 || lungeRestSlot > 8) {
			lungeRestSlot = -1;
		}
		if (lungeRestTicks < 0 || lungeRestTicks > 20) {
			lungeRestTicks = 2;
		}
		if (chestplateSlot < -1 || chestplateSlot > 8) {
			chestplateSlot = -1;
		}
		if (elytraSwapLeadTicks < 0) {
			elytraSwapLeadTicks = 1;
		}
		if (elytraSwapLeadTicks > 20) {
			elytraSwapLeadTicks = 20;
		}
	}
}
