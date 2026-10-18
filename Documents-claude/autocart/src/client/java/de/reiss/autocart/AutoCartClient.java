package de.reiss.autocart;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.vehicle.minecart.MinecartTNT;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.EnumSet;

/**
 * Runs the combo as a small state machine.
 *
 * <p>Two orders exist. The default one builds first and shoots at what it built. The other one
 * ({@code shootFirst}) aims at a spot that is still empty and puts the rail and the cart down in the
 * same tick as the shot, see {@link AutoCartConfig#shootFirst} for why that rarely works.
 * Either way, a crossbow that still has to be charged is charged before anything goes down, see
 * {@link #chargeFirst}.
 *
 * <p>A crossbow is aimed and fired in the same tick: the use packet carries the rotation and the
 * server snaps to it before spawning the arrow. A bow is different, its shot is the release packet,
 * which carries no rotation, so the new rotation has to reach the server in a movement packet first
 * and the bow keeps a tick between aiming and letting go.
 */
public class AutoCartClient implements ClientModInitializer {
	public static final String MOD_ID = "autocart";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	private static final KeyMapping.Category CATEGORY =
			KeyMapping.Category.register(Identifier.fromNamespaceAndPath(MOD_ID, "combo"));

	private AutoCartConfig config;
	private KeyMapping comboKey;

	private Step step = Step.IDLE;
	private int ticksUntilStep;
	private int startSlot = -1;
	private Entity target;
	private Vec3 aimPoint;

	/** Where the cart is going. Decided before anything is placed, so the shot can lead it. */
	private BlockPos cartSpot;

	/** True while the current run is only topping up the weapon in the background. */
	private boolean preloading;

	/**
	 * True when the crossbow has to be charged before anything goes down. Fire on stone burns out
	 * within the 25+ ticks a charge takes, and the arrow then bounces off the cart unlit, so the
	 * build waits until the shot is ready. It also stops the cart from sitting there as a warning.
	 */
	private boolean chargeFirst;

	/** The block face the crosshair was on when the run started, kept for re-planning after a charge. */
	private BlockPos lookedAt;

	/** Shots left after a miss, and whether the current pass is one of them. */
	private int retriesLeft;
	private boolean retrying;

	/** Ticks spent watching the cart since the shot. */
	private int verifyTicks;

	/** Cover blocks left open for the arrow still to be put up, see {@link AutoCartConfig#coverAfterShot}. */
	private boolean coverPending;

	private final AutoTotem autoTotem = new AutoTotem();

	/** Last explosion the server told us about, see ClientPacketListenerMixin. Main thread only. */
	private static Vec3 lastExplosion;
	private static float lastExplosionPower;
	private static int explosionCount;

	/** Explosions counted when the shot went out; a higher count near the cart means it went off. */
	private int explosionsAtShot;

	private EnumSet<Step> runMask = EnumSet.noneOf(Step.class);

	/** Set by the commands, picked up on the next tick. */
	private volatile Request pending;

	@Override
	public void onInitializeClient() {
		config = AutoCartConfig.load();

		// The config key is the default; a binding changed in Controls still wins via options.txt.
		InputConstants.Key defaultKey = defaultKey(config);
		comboKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.autocart.combo",
				defaultKey.getType(),
				defaultKey.getValue(),
				CATEGORY
		));

		ClientTickEvents.END_CLIENT_TICK.register(this::onEndTick);
		AutoCartCommands.register(this);

		LOGGER.info("Auto Cart ready: weapon={}, shootFirst={}, railAtTarget={}, minSelf={}, preload={} beyond {} blocks",
				config.weapon, config.shootFirst, config.railAtTarget,
				config.minSelfDistance, config.preload, config.preloadSafeRange);
	}

	private static InputConstants.Key defaultKey(final AutoCartConfig config) {
		try {
			return InputConstants.getKey(config.keyId());
		} catch (IllegalArgumentException e) {
			LOGGER.warn("Unknown key '{}' in autocart.json, leaving the combo unbound", config.key);
			return InputConstants.UNKNOWN;
		}
	}

	/** Called for every explosion packet. */
	public static void recordExplosion(final Vec3 centre, final float power) {
		lastExplosion = centre;
		lastExplosionPower = power;
		explosionCount++;
	}

	public AutoCartConfig config() {
		return config;
	}

	public KeyMapping comboKey() {
		return comboKey;
	}

	public void reloadConfig() {
		config = AutoCartConfig.load();
	}

	/** Queues a run. Returns false when a combo is already in flight. */
	public boolean request(final Request request) {
		if (step != Step.IDLE) {
			return false;
		}

		pending = request;
		return true;
	}

	private void onEndTick(final Minecraft minecraft) {
		LocalPlayer player = minecraft.player;
		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (player == null || gameMode == null || minecraft.level == null) {
			// Left the world mid-charge: the use key would otherwise still be held on the next join.
			if (step != Step.IDLE) {
				Combo.releaseUseKey(minecraft);
			}
			reset();
			return;
		}

		autoTotem.tick(minecraft, config);

		boolean pressed = false;

		while (comboKey.consumeClick()) {
			pressed = true;
		}

		if (step != Step.IDLE) {
			if (--ticksUntilStep <= 0) {
				advance(minecraft, player, gameMode);
			}
			pending = null;
			return;
		}

		Request request = pending;
		pending = null;

		if (request == null && pressed) {
			request = Request.FULL;
		}

		if (request == null) {
			maybePreload(minecraft, player);
			return;
		}

		if (gameMode.isSpectator()) {
			return;
		}

		begin(minecraft, player, gameMode, request, false);
	}

	/**
	 * Tops the crossbow up between fights.
	 *
	 * <p>Only while nobody is close: the charge locks the hand for over a second, which is exactly
	 * the moment you would rather be hitting back.
	 */
	private void maybePreload(final Minecraft minecraft, final LocalPlayer player) {
		// Any open screen, the plain inventory included, means the player is sorting items by hand,
		// and a swap sent now would pull the rug out from under the cursor.
		if (!config.preload || config.usesBow() || minecraft.gui.screen() != null
				|| player.containerMenu != player.inventoryMenu) {
			return;
		}

		// Never take the hand away from someone who is busy with it.
		if (player.isDeadOrDying() || player.isUsingItem()
				|| minecraft.options.keyUse.isDown() || minecraft.options.keyAttack.isDown()) {
			return;
		}

		if (Combo.findLoadedCrossbow(player) >= 0) {
			return;
		}

		// A loaded one in the backpack is enough; bring it up rather than standing here charging.
		if (Combo.ensureLoadedCrossbow(player, gameMode(minecraft), config) >= 0) {
			return;
		}

		int empty = Combo.findEmptyCrossbow(player);

		// No arrows: the charge would never start, and the preload would grab the hand again every tick.
		if (empty < 0 || player.getProjectile(player.getInventory().getItem(empty)).isEmpty()
				|| Combo.playerNearby(minecraft, player, config.preloadSafeRange)) {
			return;
		}

		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (gameMode != null && !gameMode.isSpectator()) {
			begin(minecraft, player, gameMode, Request.LOAD, true);
		}
	}

	/**
	 * Prints the whole blast calculation for whatever the crosshair is on right now.
	 *
	 * <p>Every reason the safety check can stay silent is listed explicitly, because "nothing
	 * happened" and "nothing needed to happen" look identical from the outside.
	 */
	public void diagnose(final java.util.function.Consumer<String> out) {
		Minecraft minecraft = Minecraft.getInstance();
		LocalPlayer player = minecraft.player;

		if (player == null || minecraft.level == null) {
			out.accept("no world");
			return;
		}

		HitResult hitResult = minecraft.hitResult;
		Entity aimedAt = hitResult instanceof EntityHitResult entityHit ? entityHit.getEntity() : null;
		BlockPos lookedAt = aimedAt == null ? lookedAtSpot(hitResult) : null;

		Vec3 point = aimedAt != null
				? aimedAt.position().add(0.0, aimedAt.getBbHeight() * 0.5, 0.0)
				: lookedAt != null ? Vec3.atCenterOf(lookedAt) : null;
		BlockPos spot = Combo.planRailSpot(minecraft, player, config, point, aimedAt, lookedAt);

		out.accept("crosshair: " + (aimedAt != null ? "entity " + aimedAt.getName().getString()
				: lookedAt != null ? "block " + lookedAt.toShortString() : "nothing"));
		out.accept("cart spot: " + (spot == null ? "none found" : spot.toShortString()));

		if (spot == null) {
			out.accept("verdict: no spot, so nothing to check");
			return;
		}

		// The two states that switch the check off entirely.
		if (!config.safeHealth) {
			out.accept("CHECK IS OFF: safehealth=false");
		}

		if (player.isCreative() || player.isSpectator()) {
			out.accept("CHECK IS OFF: creative or spectator takes no blast damage");
		}

		Vec3 centre = Blast.centre(spot, Combo.cartOn(minecraft.level, spot));
		Blast.Power power = Blast.power(config);
		Blast.Hit worst = Blast.damage(minecraft, player, centre, power.max());
		Blast.Spread mine = Blast.spread(minecraft, player, centre, power);
		double health = Blast.effectiveHealth(player);

		out.accept(String.format("power %.1f to %.1f (avg %.1f): a burning arrow adds up to 1.5 x its speed",
				power.min(), power.max(), power.avg()));
		out.accept(String.format("YOU: distance %.2f, exposure %.0f%%, takes %.1f / %.1f / %.1f (min/avg/max)",
				worst.distance(), worst.exposure() * 100.0, mine.min(), mine.avg(), mine.max()));
		out.accept(String.format("  worst case: raw %.0f -> difficulty x%.1f -> armour %.1f -> enchants %.1f -> final %.1f",
				worst.raw(), Blast.difficultyFactor(minecraft), worst.afterArmour(),
				worst.afterProtection(), worst.finalDamage()));
		out.accept(String.format("  health %.1f (+%.1f absorption), buffer %.1f, totems %d%s",
				player.getHealth(), player.getAbsorptionAmount(), config.healthBuffer, AutoTotem.count(player),
				Blast.holdsTotem(player) ? " (one in hand)" : " (none in hand!)"));

		LivingEntity victim = victim(minecraft, player, aimedAt, centre);

		if (victim != null) {
			Blast.Spread theirs = Blast.spread(minecraft, victim, centre, power);
			out.accept(String.format("TARGET %s: %s", victim.getName().getString(), Blast.describeGear(minecraft.level, victim)));
			out.accept(String.format("  takes %.1f / %.1f / %.1f of %.1f health%s",
					theirs.min(), theirs.avg(), theirs.max(), Blast.effectiveHealth(victim), verdict(victim, theirs)));
			out.accept(theirs.avg() > mine.avg()
					? String.format("  trade: target takes %.1f more than you", theirs.avg() - mine.avg())
					: String.format("  trade: you take %.1f more%s", mine.avg() - theirs.avg(),
							config.requireAdvantage ? ", so it WOULD ABORT" : ""));
		} else {
			out.accept("TARGET: nobody within 6 blocks of the cart spot");
		}

		boolean lethal = mine.max() + config.healthBuffer >= health;
		out.accept(!lethal ? "verdict: would allow"
				: config.allowOwnPop && Blast.holdsTotem(player) ? "verdict: would allow, your totem may pop"
				: "verdict: WOULD ABORT (worst case)");
	}

	private static MultiPlayerGameMode gameMode(final Minecraft minecraft) {
		return minecraft.gameMode;
	}

	private void begin(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final Request request,
			final boolean background) {
		runMask = request.steps();
		preloading = background;
		retriesLeft = config.retries;
		retrying = false;

		HitResult hitResult = minecraft.hitResult;
		target = hitResult instanceof EntityHitResult entityHit ? entityHit.getEntity() : null;

		// Looking at the ground counts as a target too: the cart then goes where the crosshair is,
		// which is the whole point of "put one over there and set it off".
		lookedAt = target == null ? lookedAtSpot(hitResult) : null;

		// A cart further out than the 3 blocks entity reach leaves the crosshair empty (or on the
		// ground in front of it), yet it is exactly what you look at after a miss. Any cart on the
		// line of sight wins: its rail becomes the spot, so that cart gets shot instead of a new one.
		MinecartTNT cartInView = target == null ? Combo.cartInView(minecraft, player) : null;

		if (cartInView != null) {
			lookedAt = cartInView.blockPosition();
		}

		boolean needsAim = runMask.contains(Step.FIRE) || runMask.contains(Step.AIM);

		if (target == null && lookedAt == null && needsAim && config.requireTarget) {
			report(player, "autocart: nothing under the crosshair");
			return;
		}

		startSlot = player.getInventory().getSelectedSlot();
		aimPoint = target != null
				? target.position().add(0.0, target.getBbHeight() * 0.5, 0.0)
				: lookedAt != null
						? Vec3.atCenterOf(lookedAt)
						: player.getEyePosition().add(player.getLookAngle().scale(4.0));

		// Decide the cart spot up front. Shooting first depends on it, and building first is no
		// worse off for knowing early.
		cartSpot = runMask.contains(Step.RAIL) || runMask.contains(Step.CART)
				? Combo.planRailSpot(minecraft, player, config, aimPoint, target, lookedAt)
				: null;

		if (cartSpot != null) {
			report(player, String.format("autocart: cart spot %.1f blocks out", distanceTo(player, cartSpot)));
		}

		if (!background && !survivable(minecraft, player, "too close")) {
			return;
		}

		chargeFirst = !background && runMask.contains(Step.LOAD) && runMask.contains(Step.AIM)
				&& config.shootCrossbow && config.loadCrossbow && !config.usesBow()
				&& !Combo.hasLoadedCrossbow(player);

		// A background top-up has nothing to build, so it goes straight to the charge.
		step = background || chargeFirst || burst() ? Step.LOAD : firstBuildStep();
		ticksUntilStep = 1;
	}

	/** The spot a block would be placed in, i.e. on top of the face under the crosshair. */
	private BlockPos lookedAtSpot(final HitResult hitResult) {
		if (config.aimAtBlocks && hitResult instanceof BlockHitResult blockHit
				&& blockHit.getType() == HitResult.Type.BLOCK) {
			return blockHit.getBlockPos().relative(blockHit.getDirection());
		}

		return null;
	}

	private void advance(final Minecraft minecraft, final LocalPlayer player, final MultiPlayerGameMode gameMode) {
		ticksUntilStep = config.stepDelayTicks;

		switch (step) {
			case RAIL -> {
				// Rail and cart go down in the same tick. The server handles the packets in order,
				// so the rail is already there when the cart lands on it, and the whole build costs
				// one tick instead of two.
				if (runMask.contains(Step.RAIL) && config.placeRail && !run(minecraft, player,
						Combo.placeRail(minecraft, player, gameMode, config, cartSpot))) {
					return;
				}
				if (runMask.contains(Step.CART) && config.placeCart && !run(minecraft, player,
						Combo.placeCart(minecraft, player, gameMode, config, cartSpot))) {
					return;
				}
				step = Step.FIRE;
			}
			case FIRE -> {
				Vec3 point = Combo.aimPoint(minecraft, player, config, target, cartSpot);

				if (point != null) {
					aimPoint = point;
				}

				if (runMask.contains(Step.FIRE) && config.placeFire) {
					if (aimPoint == null) {
						abort(minecraft, player, "nothing to aim at, so no line for the fire");
						return;
					}
					if (!run(minecraft, player,
							Combo.placeFire(minecraft, player, gameMode, config, aimPoint, cartSpot))) {
						return;
					}
				}
				step = Step.LOAD;
			}
			case LOAD -> {
				if (!runMask.contains(Step.LOAD) || !config.shootCrossbow || !config.loadCrossbow
						|| config.usesBow()) {
					// A bow is drawn as part of aiming, so there is nothing to prepare here.
					step = Step.AIM;
					return;
				}

				// A crossbow that is already loaded, wherever it sits, beats charging an empty one:
				// fetching it up costs a tick, charging costs over a second.
				if (Combo.ensureLoadedCrossbow(player, gameMode, config) >= 0) {
					step = Step.AIM;

					// Burst builds and shoots in this very tick; no reason to wait for the next one.
					if (burst()) {
						advance(minecraft, player, gameMode);
					}
					return;
				}

				// Nothing loaded anywhere, so an empty one has to be charged. Fetch one up if the
				// hotbar has none left.
				if (Combo.ensureInHotbar(player, gameMode, config, Items.CROSSBOW) < 0) {
					abort(minecraft, player, "no crossbow in the hotbar or the backpack");
					return;
				}

				int ticks = Combo.startUsing(minecraft, player, gameMode, config, Combo.findEmptyCrossbow(player));

				if (ticks < 0) {
					abort(minecraft, player, "no crossbow to charge");
					return;
				}

				if (!player.isUsingItem()) {
					abort(minecraft, player, "crossbow does not charge (no arrows?)");
					return;
				}

				report(player, "autocart: charging " + ticks + " ticks");
				step = Step.CHARGE;
				ticksUntilStep = ticks + config.chargeExtraTicks;
			}
			case CHARGE -> {
				Combo.releaseUse(minecraft, player, gameMode);

				if (preloading) {
					report(player, "autocart: crossbow ready");
					finish(player, gameMode);
					return;
				}

				if (chargeFirst) {
					// Loaded now, so build. The LOAD step comes round again and finds it ready.
					chargeFirst = false;
					replan(minecraft, player);

					if (!survivable(minecraft, player, "target came in too close")) {
						return;
					}

					step = burst() ? Step.AIM : retrying && !runMask.contains(Step.CART) ? Step.FIRE : firstBuildStep();
					return;
				}

				step = Step.AIM;
			}
			case AIM -> {
				if (!runMask.contains(Step.AIM) || !config.shootCrossbow) {
					step = Step.DONE;
					ticksUntilStep = 1;
					return;
				}

				if (aimPoint == null) {
					abort(minecraft, player, "nothing to aim at");
					return;
				}

				if (config.usesBow()) {
					int slot = Combo.ensureInHotbar(player, gameMode, config, Items.BOW);

					if (slot < 0) {
						abort(minecraft, player, "no bow in the hotbar or the backpack");
						return;
					}

					Combo.lookAt(player, aimPoint);
					int ticks = Combo.startUsing(minecraft, player, gameMode, config, slot);
					report(player, "autocart: drawing " + ticks + " ticks");
					step = Step.PREP;
					ticksUntilStep = ticks;
					return;
				}

				if (Combo.findLoadedCrossbow(player) < 0) {
					abort(minecraft, player, "no loaded crossbow in the hotbar");
					return;
				}

				// The crossbow's use packet brings its own rotation along, so there is no need to
				// wait a tick for the aim to reach the server. Straight on to the shot.
				step = Step.STRIKE;
				advance(minecraft, player, gameMode);
			}
			case PREP -> {
				// Bow only. The release packet has no rotation of its own, so the final correction
				// has to go out a tick ahead in the movement packet LocalPlayer#tick sends.
				if (aimPoint != null) {
					Combo.lookAt(player, aimPoint);
				}

				step = Step.STRIKE;
				ticksUntilStep = 1;
			}
			case STRIKE -> {
				// You may have walked closer while the weapon was charging.
				if (!survivable(minecraft, player, "moved in too close")) {
					return;
				}

				// Everything in one tick, cart before shot. The server handles the packets in the
				// order they arrive, so the cart entity exists by the time the arrow is spawned.
				//
				// Splitting this across ticks is what made the arrow sail past the empty spot and hit
				// the target instead: an arrow covers about three blocks per tick, and the cart can
				// never be further away than the 4.5 blocks of block reach.
				if (!buildFirst() || burst()) {
					if (runMask.contains(Step.RAIL) && config.placeRail && !run(minecraft, player,
							Combo.placeRail(minecraft, player, gameMode, config, cartSpot))) {
						return;
					}
					if (runMask.contains(Step.CART) && config.placeCart && !run(minecraft, player,
							Combo.placeCart(minecraft, player, gameMode, config, cartSpot))) {
						return;
					}
				}

				// Burst lays the fire in the same tick too. It exists before the arrow's first move,
				// so the arrow still flies through it and comes out burning.
				if (burst() && runMask.contains(Step.FIRE) && config.placeFire) {
					Vec3 point = Combo.aimPoint(minecraft, player, config, target, cartSpot);

					if (point != null) {
						aimPoint = point;
					}
					if (!run(minecraft, player, Combo.placeFire(minecraft, player, gameMode, config, aimPoint, cartSpot))) {
						return;
					}
				}

				if (config.usesBow()) {
					// Letting go of a drawn bow is the shot.
					Combo.releaseUse(minecraft, player, gameMode);
					report(player, "autocart: loosed");

					// Switching slots would have let the drawn bow go early, so the cover comes after.
					if (config.placeCover) {
						step = Step.COVER;
						ticksUntilStep = 1;
						return;
					}

					startVerify(player, gameMode);
					return;
				}

				// Aim at the cart as it stands right now; a target leaning on it may have moved it.
				Vec3 point = Combo.aimPoint(minecraft, player, config, target, cartSpot);

				if (point != null) {
					aimPoint = point;
				}

				// The burning arrow sets the cart off on contact, a tick or two from now. Cover has to
				// be up before that, so it goes down first, clear of the arrow's path.
				if (config.placeCover) {
					Combo.StepResult cover = Combo.placeCover(minecraft, player, gameMode, config, cartSpot,
							player.getEyePosition(), aimPoint);
					report(player, "autocart: " + cover.message());
				}

				// Placing may have switched the hotbar away from the weapon; take it back.
				int weaponSlot = Combo.findLoadedCrossbow(player);

				if (weaponSlot < 0) {
					abort(minecraft, player, "crossbow went missing mid-combo");
					return;
				}

				Combo.selectSlot(player, gameMode, weaponSlot);
				Combo.lookAt(player, aimPoint);

				if (!run(minecraft, player, Combo.shootCrossbow(player, gameMode))) {
					return;
				}

				startVerify(player, gameMode);
			}
			case COVER -> {
				// Bow only; the arrow is already on its way, the path check keeps the wall out of it.
				Combo.StepResult cover = Combo.placeCover(minecraft, player, gameMode, config, cartSpot,
						player.getEyePosition(), aimPoint);
				report(player, "autocart: " + cover.message());
				startVerify(player, gameMode);
			}
			case VERIFY -> {
				ticksUntilStep = 1;
				verifyTicks++;

				if (minecraft.level == null) {
					finish(player, gameMode);
					return;
				}

				// Only an explosion packet near the cart counts. A missing cart is not proof: one placed
				// and blown up in the same tick never reaches us, and an unlit arrow just breaks it.
				if (explosionCount > explosionsAtShot && lastExplosion != null
						&& lastExplosion.distanceTo(Vec3.atCenterOf(cartSpot)) < 3.0) {
					report(player, String.format("autocart: boom, power %.1f", lastExplosionPower));
					finish(player, gameMode);
					return;
				}

				boolean cartStanding = Combo.cartOn(minecraft.level, cartSpot) != null;

				// The arrow is past us by now; close the gaps it needed, if asked to.
				if (coverPending && cartStanding) {
					coverPending = false;
					Combo.StepResult cover = Combo.placeCover(minecraft, player, gameMode, config, cartSpot, null, null);
					report(player, "autocart: " + cover.message());
				}

				if (verifyTicks < config.missTimeoutTicks) {
					return;
				}

				if (retriesLeft <= 0) {
					abort(minecraft, player, "missed, the cart is still standing");
					return;
				}

				// Missed. A cart still standing gets shot again; one the arrow knocked off the rail
				// gets replaced first. Either way: relight if needed, reload, shoot.
				retriesLeft--;
				report(player, "autocart: missed" + (cartStanding ? "" : ", cart gone without a bang")
						+ ", trying again (" + retriesLeft + " more after this)");
				retrying = true;

				if (cartStanding) {
					runMask.remove(Step.RAIL);
					runMask.remove(Step.CART);
				} else {
					runMask.add(Step.RAIL);
					runMask.add(Step.CART);
				}

				chargeFirst = !config.usesBow() && !Combo.hasLoadedCrossbow(player);
				// Burst builds, lights and shoots in one tick from LOAD on, same as a fresh run.
				step = chargeFirst || burst() ? Step.LOAD : cartStanding ? Step.FIRE : firstBuildStep();
			}
			default -> finish(player, gameMode);
		}
	}

	/** Reports a step and says whether the run may continue. */
	private boolean run(final Minecraft minecraft, final LocalPlayer player, final Combo.StepResult result) {
		if (!result.success()) {
			abort(minecraft, player, result.message());
			return false;
		}

		report(player, "autocart: " + result.message());
		return true;
	}

	/** After the shot: watch whether the cart goes off, see {@link Step#VERIFY}. */
	private void startVerify(final LocalPlayer player, final MultiPlayerGameMode gameMode) {
		if (cartSpot == null || !runMask.contains(Step.AIM)) {
			finish(player, gameMode);
			return;
		}

		step = Step.VERIFY;
		ticksUntilStep = 1;
		verifyTicks = 0;
		explosionsAtShot = explosionCount;
		coverPending = config.placeCover && config.coverAfterShot;
	}

	private void finish(final LocalPlayer player, final MultiPlayerGameMode gameMode) {
		if (config.returnToStartSlot && startSlot >= 0) {
			Combo.selectSlot(player, gameMode, startSlot);
		}

		reset();
	}

	private void abort(final Minecraft minecraft, final LocalPlayer player, final String reason) {
		// A run that dies mid-charge would otherwise leave right-click stuck down.
		Combo.releaseUseKey(minecraft);
		LOGGER.info("{} aborted at {}: {}", preloading ? "Preload" : "Combo", step, reason);

		// A background top-up failing is not worth interrupting anyone over.
		if (preloading) {
			report(player, "autocart: preload stopped, " + reason);
		} else {
			player.sendOverlayMessage(Component.literal("autocart: " + reason));
		}

		reset();
	}

	private void reset() {
		step = Step.IDLE;
		ticksUntilStep = 0;
		startSlot = -1;
		target = null;
		aimPoint = null;
		cartSpot = null;
		preloading = false;
		chargeFirst = false;
		lookedAt = null;
		runMask = EnumSet.noneOf(Step.class);
		retrying = false;
		retriesLeft = 0;
		verifyTicks = 0;
		coverPending = false;
	}

	private void report(final LocalPlayer player, final String text) {
		LOGGER.debug("{} {}", step, text);

		if (config.debugMessages) {
			player.sendOverlayMessage(Component.literal(text));
		}
	}

	/**
	 * Sizes the blast up for both sides before anything irreversible happens: refuses a run the
	 * target would come off better from ({@link AutoCartConfig#requireAdvantage}), and one that could
	 * kill us, unless a totem in hand turns that into a pop ({@link AutoCartConfig#allowOwnPop}).
	 *
	 * <p>Our own worst case is taken at the highest power the cart can go off with, see {@link Blast}.
	 *
	 * @return true when it is fine to carry on
	 */
	private boolean survivable(final Minecraft minecraft, final LocalPlayer player, final String when) {
		// Every way out of this check says so out loud. Silence used to be ambiguous: "the check
		// passed", "the check is off" and "the check never ran" all looked the same from in game.
		if (cartSpot == null || minecraft.level == null) {
			return true;
		}

		boolean immune = player.isCreative() || player.isSpectator();
		Vec3 centre = Blast.centre(cartSpot, Combo.cartOn(minecraft.level, cartSpot));
		Blast.Power power = Blast.power(config);
		Blast.Spread mine = immune ? new Blast.Spread(0.0, 0.0, 0.0) : Blast.spread(minecraft, player, centre, power);

		if (!advantage(minecraft, player, centre, power, mine)) {
			return false;
		}

		if (!config.safeHealth) {
			report(player, "autocart: safety check is off (safehealth=false)");
			return true;
		}

		if (immune) {
			report(player, "autocart: creative/spectator, no blast damage to guard against");
			return true;
		}

		double health = Blast.effectiveHealth(player);

		if (mine.max() + config.healthBuffer >= health) {
			if (config.allowOwnPop && Blast.holdsTotem(player)) {
				report(player, String.format("autocart: worst case %.1f on %.1f health, your totem would pop",
						mine.max(), health));
				return true;
			}

			abort(minecraft, player, String.format("%s: blast up to %.1f (avg %.1f) on %.1f health, backing out",
					when, mine.max(), mine.avg(), health));
			return false;
		}

		report(player, String.format("autocart: you take %.1f-%.1f of %.1f", mine.min(), mine.max(), health));
		return true;
	}

	/** The target's side of the trade. Stops the run when it would not come off worse than us. */
	private boolean advantage(
			final Minecraft minecraft,
			final LocalPlayer player,
			final Vec3 centre,
			final Blast.Power power,
			final Blast.Spread mine) {
		LivingEntity victim = victim(minecraft, player, target, centre);

		if (victim == null) {
			return true;
		}

		Blast.Spread theirs = Blast.spread(minecraft, victim, centre, power);
		Blast.Hit theirHit = Blast.damage(minecraft, victim, centre, power.avg());
		Blast.Hit myHit = Blast.damage(minecraft, player, centre, power.avg());
		String name = victim.getName().getString();
		report(player, String.format("autocart: %s takes %.1f (%.1f-%.1f) of %.1f%s [%.1fm, %.0f%% seen] | you %.1f [%.1fm, %.0f%% seen]",
				name, theirs.avg(), theirs.min(), theirs.max(), Blast.effectiveHealth(victim),
				verdict(victim, theirs), theirHit.distance(), theirHit.exposure() * 100.0,
				mine.avg(), myHit.distance(), myHit.exposure() * 100.0));

		if (config.requireAdvantage && theirs.avg() <= mine.avg()) {
			abort(minecraft, player, String.format("no advantage: %s takes ~%.1f, you ~%.1f",
					name, theirs.avg(), mine.avg()));
			return false;
		}

		return true;
	}

	/** Whether the blast pops or kills: sure when even the weakest blast does it, possible at the strongest. */
	static String verdict(final LivingEntity victim, final Blast.Spread damage) {
		double health = Blast.effectiveHealth(victim);
		boolean totem = Blast.holdsTotem(victim);

		if (damage.min() >= health) {
			return totem ? ", pops the totem" : ", lethal";
		}
		if (damage.max() >= health) {
			return totem ? ", may pop the totem" : ", may be lethal";
		}
		return "";
	}

	/**
	 * Who the cart is meant for: the entity under the crosshair, or else the living thing closest to
	 * the blast within six blocks, players first.
	 */
	static LivingEntity victim(final Minecraft minecraft, final LocalPlayer player, final Entity aimed, final Vec3 centre) {
		if (aimed instanceof LivingEntity living && living.isAlive() && living != player) {
			return living;
		}

		if (minecraft.level == null) {
			return null;
		}

		LivingEntity best = null;
		double bestScore = Double.MAX_VALUE;

		for (Entity entity : minecraft.level.getEntities(player, new AABB(centre, centre).inflate(6.0))) {
			if (!(entity instanceof LivingEntity living) || !living.isAlive() || entity instanceof ArmorStand) {
				continue;
			}

			// Players win over mobs anywhere inside the box.
			double score = entity.distanceToSqr(centre) + (entity instanceof Player ? 0.0 : 1000.0);

			if (score < bestScore) {
				best = living;
				bestScore = score;
			}
		}

		return best;
	}

	/**
	 * Whether the cart has to be standing before we start aiming.
	 *
	 * <p>A drawn bow is cancelled by any hotbar switch, so with a bow the building cannot happen
	 * between aiming and the shot the way it can with a crossbow.
	 */
	private boolean buildFirst() {
		return !config.shootFirst || config.usesBow();
	}

	/**
	 * Rail, cart, fire and shot all in one tick, see {@link AutoCartConfig#burst}. Crossbow only:
	 * a drawn bow would be let go by the first slot switch.
	 */
	private boolean burst() {
		return config.burst && !config.usesBow() && config.shootCrossbow && runMask.contains(Step.AIM);
	}

	private Step firstBuildStep() {
		return buildFirst() ? Step.RAIL : Step.FIRE;
	}

	/** The charge took over a second; a target that walked off meanwhile gets a fresh cart spot. */
	private void replan(final Minecraft minecraft, final LocalPlayer player) {
		Entity live = target != null && target.isAlive() ? target : null;

		if (live != null) {
			aimPoint = live.position().add(0.0, live.getBbHeight() * 0.5, 0.0);
		}

		if (cartSpot != null) {
			BlockPos spot = Combo.planRailSpot(minecraft, player, config, aimPoint, live, lookedAt);

			if (spot != null) {
				cartSpot = spot;
			}
		}
	}

	private static double distanceTo(final LocalPlayer player, final BlockPos pos) {
		return pos == null ? 0.0 : player.position().distanceTo(Vec3.atCenterOf(pos));
	}

	/** What a single invocation should do. */
	public enum Request {
		FULL,
		RAIL,
		CART,
		FIRE,
		SHOOT,
		LOAD;

		EnumSet<Step> steps() {
			return switch (this) {
				case RAIL -> EnumSet.of(Step.RAIL);
				// A cart needs something to stand on, so this brings the rail along.
				case CART -> EnumSet.of(Step.RAIL, Step.CART);
				case FIRE -> EnumSet.of(Step.FIRE);
				case SHOOT -> EnumSet.of(Step.LOAD, Step.AIM);
				case LOAD -> EnumSet.of(Step.LOAD);
				case FULL -> EnumSet.of(Step.RAIL, Step.CART, Step.FIRE, Step.LOAD, Step.AIM);
			};
		}
	}

	private enum Step {
		IDLE,
		RAIL,
		CART,
		FIRE,
		LOAD,
		CHARGE,
		AIM,
		PREP,
		STRIKE,
		COVER,
		/** Watching the cart after the shot; still standing after the timeout means a miss and a retry. */
		VERIFY,
		DONE
	}
}
