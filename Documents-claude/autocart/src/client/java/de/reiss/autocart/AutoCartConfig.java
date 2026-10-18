package de.reiss.autocart;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Plain JSON config, written to .minecraft/config/autocart.json on first launch.
 */
public class AutoCartConfig {
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static final Path PATH = FabricLoader.getInstance().getConfigDir().resolve("autocart.json");

	/** Key that fires the combo, e.g. "b", "j", "unknown" for none. Also settable in Controls. */
	public String key = "b";

	/** Only start the combo when the crosshair is on something: an entity or, below, a block. */
	public boolean requireTarget = true;

	/**
	 * Treat the block under the crosshair as a target as well.
	 *
	 * <p>Lets you look at a patch of ground and have the cart go off right there, instead of needing
	 * someone to aim at.
	 */
	public boolean aimAtBlocks = true;

	/**
	 * Aim at the empty spot and put rail and cart down in the tick of the shot, instead of building first.
	 *
	 * <p>It works as long as rail, cart and shot share one tick: the server handles the packets in
	 * order, so the cart exists before the arrow is spawned. The game test measured it hitting.
	 */
	public boolean shootFirst = false;

	/**
	 * Rail, cart, fire and the crossbow shot all in one single tick, instead of a step every
	 * {@link #stepDelayTicks}. The whole combo lands before the target can see a cart and step away.
	 * Crossbow only. Off by default: four actions in one tick are the kind of thing an anticheat
	 * may look at, so try it on your server first.
	 */
	public boolean burst = false;

	/** "crossbow" or "bow". A bow shoots on release, a crossbow is loaded first and fired after. */
	public String weapon = "crossbow";

	/** Ticks to draw a bow before letting go. 20 is a full-power shot. */
	public int bowDrawTicks = 20;

	/** Lay a rail down first when there is none in reach. */
	public boolean placeRail = true;

	/** Place the TNT minecart. */
	public boolean placeCart = true;

	/** Set the fire on the shooting line. */
	public boolean placeFire = true;

	/** Take the shot. */
	public boolean shootCrossbow = true;

	/** Charge an empty weapon instead of giving up on the shot. */
	public boolean loadCrossbow = true;

	/**
	 * Keep a crossbow loaded while no player is within {@link #preloadSafeRange}.
	 *
	 * <p>Charging takes over a second, which is time you do not have once someone is on top of you.
	 */
	public boolean preload = true;

	/** Only preload while every other player is at least this far away. */
	public double preloadSafeRange = 6.0;

	/** Fetch a weapon out of the backpack when the hotbar has none left. */
	public boolean refillFromInventory = true;

	/** Hotbar slot to dump a fetched weapon into when the whole hotbar is full. */
	public int refillSlot = 8;

	/** How far to search for an existing rail, in blocks. Kept under the block reach of 4.5. */
	public double railSearchRadius = 4.0;

	/** How far in front to lay the rail. Ignored while railAtTarget is on. */
	public double railDistance = 2.0;

	/**
	 * Lay the rail as deep into the target as reach allows instead of at railDistance.
	 *
	 * <p>A TNT minecart's blast falls off with distance, so the cart standing in the target while you
	 * stand back is what decides who takes the damage.
	 */
	public boolean railAtTarget = true;

	/**
	 * Blocks to stay short of the target when placing the cart.
	 *
	 * <p>A minecart is shoved around by entities that stand in it. Placed inside a moving target it
	 * drifts out of the arrow's path before the arrow gets there, so it goes just in front instead.
	 */
	public double targetStandoff = 1.5;

	/** Where the fire goes when there is no cart spot to work back from. */
	public double fireDistance = 2.0;

	/** Blocks of clearance between cart and fire, so the fire cannot prime the cart early. */
	public double fireGap = 1.0;

	/**
	 * Never put the cart or the fire closer to us than this.
	 *
	 * <p>Set it to 0 to allow placing right at your feet. That is your own blast radius, so the
	 * default keeps a little room.
	 */
	public double minSelfDistance = 2.5;

	/**
	 * Wall ourselves off from the blast. With a crossbow the wall goes up in the same tick just before
	 * the shot (a burning arrow sets the cart off on contact), with a bow right after; either way any
	 * block that would stand in the arrow's path is left out.
	 *
	 * <p>Breaking the blast's line of sight is the strongest protection there is, stronger than any
	 * armour: the damage scales with how much of you the explosion can actually see.
	 */
	public boolean placeCover = true;

	/** How many blocks high the cover goes. Two covers the whole body. */
	public int coverHeight = 2;

	/**
	 * Put up the cover blocks that had to stay open for the arrow one tick after the shot, when the
	 * arrow is past them. Only helps if the cart has not gone off by then (cart 3+ blocks away).
	 */
	public boolean coverAfterShot = false;

	/** Refuse to run when the blast would take us too close to death. */
	public boolean safeHealth = true;

	/**
	 * Only fire when the target takes more than we do. The target is the entity under the crosshair,
	 * or else the living thing closest to the cart. Compared at the average blast power.
	 */
	public boolean requireAdvantage = true;

	/**
	 * Let the combo run even if the worst case would kill us, as long as we hold a totem: the blast
	 * then only pops it, and {@link #autoTotem} puts the next one in.
	 */
	public boolean allowOwnPop = true;

	/** Shoot again when the cart is still standing after a shot, up to this many times. */
	public int retries = 2;

	/** Ticks to wait for the bang before a shot counts as a miss. */
	public int missTimeoutTicks = 8;

	/** Refill the offhand with a totem from the inventory whenever it is empty, e.g. right after a pop. */
	public boolean autoTotem = true;

	/** Also swap out whatever else is in the offhand (a shield, say). Off: only an empty offhand is filled. */
	public boolean totemReplaceOffhand = false;

	/** Ticks to wait after the offhand went empty before refilling it. */
	public int autoTotemDelayTicks = 1;

	/** Hearts that have to be left over after the estimated blast, or the combo is called off. */
	public double healthBuffer = 4.0;

	/**
	 * Explosion power to reckon with. A standing TNT minecart is 4.
	 *
	 * <p>A rolling one is stronger, so raise this if you send carts down a slope.
	 */
	public double blastPower = 4.0;

	/** What to aim at: "cart" for the cart or its planned spot, "target" for the entity. */
	public String aimAt = "cart";

	/** Ticks between the steps. One tick is the minimum for a new rotation to reach the server. */
	public int stepDelayTicks = 2;

	/** Extra ticks to keep holding after the charge time has passed. */
	public int chargeExtraTicks = 2;

	/** Switch back to the slot held before the combo once it is done. */
	public boolean returnToStartSlot = true;

	/** Print what each step did to the action bar. Handy while tuning the geometry. */
	public boolean debugMessages = true;

	public static AutoCartConfig load() {
		AutoCartConfig config = new AutoCartConfig();

		if (Files.exists(PATH)) {
			try {
				String json = Files.readString(PATH, StandardCharsets.UTF_8);
				AutoCartConfig loaded = GSON.fromJson(json, AutoCartConfig.class);
				if (loaded != null) {
					config = loaded;
				}
			} catch (IOException | RuntimeException e) {
				AutoCartClient.LOGGER.warn("Could not read {}, falling back to defaults", PATH, e);
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
			AutoCartClient.LOGGER.warn("Could not write {}", PATH, e);
		}
	}

	public boolean aimAtCart() {
		return !"target".equalsIgnoreCase(aimAt);
	}

	public boolean usesBow() {
		return "bow".equalsIgnoreCase(weapon);
	}

	/** The full key id the game expects, built from the short name in the config. */
	public String keyId() {
		if (key == null || key.isBlank()) {
			return "key.keyboard.unknown";
		}

		String trimmed = key.trim().toLowerCase();
		return trimmed.startsWith("key.") ? trimmed : "key.keyboard." + trimmed;
	}

	private void clamp() {
		// The server rejects block interactions past its reach, so never search beyond it.
		if (railSearchRadius < 1.0 || railSearchRadius > 4.5) {
			railSearchRadius = 4.0;
		}
		if (railDistance < 1.0 || railDistance > 4.5) {
			railDistance = 2.0;
		}
		if (fireDistance < 1.0 || fireDistance > 4.5) {
			fireDistance = 2.0;
		}
		if (targetStandoff < 0.0 || targetStandoff > 4.0) {
			targetStandoff = 1.5;
		}
		if (fireGap < 0.0 || fireGap > 3.0) {
			fireGap = 1.0;
		}
		if (minSelfDistance < 0.0 || minSelfDistance > 4.5) {
			minSelfDistance = 2.5;
		}
		if (stepDelayTicks < 1 || stepDelayTicks > 40) {
			stepDelayTicks = 2;
		}
		if (chargeExtraTicks < 0 || chargeExtraTicks > 40) {
			chargeExtraTicks = 2;
		}
		if (bowDrawTicks < 1 || bowDrawTicks > 60) {
			bowDrawTicks = 20;
		}
		if (coverHeight < 1 || coverHeight > 3) {
			coverHeight = 2;
		}
		if (healthBuffer < 0.0 || healthBuffer > 20.0) {
			healthBuffer = 4.0;
		}
		if (blastPower < 1.0 || blastPower > 16.0) {
			blastPower = 4.0;
		}
		if (preloadSafeRange < 0.0 || preloadSafeRange > 32.0) {
			preloadSafeRange = 6.0;
		}
		if (refillSlot < 0 || refillSlot > 8) {
			refillSlot = 8;
		}
		if (weapon == null || (!weapon.equalsIgnoreCase("bow") && !weapon.equalsIgnoreCase("crossbow"))) {
			weapon = "crossbow";
		}
		if (aimAt == null || (!aimAt.equalsIgnoreCase("cart") && !aimAt.equalsIgnoreCase("target"))) {
			aimAt = "cart";
		}
		if (retries < 0 || retries > 5) {
			retries = 2;
		}
		if (missTimeoutTicks < 3 || missTimeoutTicks > 40) {
			missTimeoutTicks = 8;
		}
		if (autoTotemDelayTicks < 0 || autoTotemDelayTicks > 20) {
			autoTotemDelayTicks = 1;
		}
	}
}
