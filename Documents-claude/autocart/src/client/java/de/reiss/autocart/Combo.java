package de.reiss.autocart;

import de.reiss.autocart.mixin.MultiPlayerGameModeAccessor;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.component.SwingAnimation;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.vehicle.minecart.MinecartTNT;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * The individual steps of the combo. Each one is callable on its own, so a step that finds nothing
 * can say why and let the caller abort instead of firing a half combo.
 *
 * <p>Every step that uses an item switches the hotbar slot first and flushes that switch through
 * {@link MultiPlayerGameModeAccessor}. Without the flush the server would still hold the previous
 * item when the use packet arrives.
 */
public final class Combo {
	/** Vanilla block interaction reach. Anything past this is rejected server side. */
	private static final double BLOCK_REACH = 4.5;

	/** Rail flavours the cart can sit on, in the order we would rather spend them. */
	private static final Item[] RAIL_ITEMS = {
			Items.RAIL,
			Items.POWERED_RAIL,
			Items.DETECTOR_RAIL,
			Items.ACTIVATOR_RAIL
	};

	/** InventoryMenu maps container slots 9-35 straight onto inventory slots 9-35. */
	private static final int FIRST_STORAGE_SLOT = 9;
	private static final int LAST_STORAGE_SLOT = 35;

	private Combo() {
	}

	// ---------------------------------------------------------------- placing

	/**
	 * Works out where the cart should end up, without placing anything yet.
	 *
	 * <p>Shooting first needs this: the arrow has to be aimed at a spot that only becomes a cart
	 * afterwards.
	 *
	 * @return the block a rail would go into, or an existing rail already in reach
	 */
	public static BlockPos planRailSpot(
			final Minecraft minecraft,
			final LocalPlayer player,
			final AutoCartConfig config,
			final Vec3 aimPoint,
			final Entity target,
			final BlockPos lookedAt) {
		ClientLevel level = minecraft.level;

		if (level == null) {
			return null;
		}

		// Looking straight at a spot beats everything else: that is the player saying where they
		// want it, so it wins over both a nearby rail and the target's feet.
		// Looking at a rail, e.g. under a cart that is still standing after a miss: use it as it is.
		if (lookedAt != null && level.getBlockState(lookedAt).is(BlockTags.RAILS)
				&& player.getEyePosition().distanceToSqr(Vec3.atCenterOf(lookedAt)) <= BLOCK_REACH * BLOCK_REACH) {
			return lookedAt;
		}

		if (lookedAt != null && usable(level, player.getEyePosition(), lookedAt, config.minSelfDistance)) {
			return lookedAt;
		}

		BlockPos existing = findRail(level, player, config.railSearchRadius);

		if (existing != null) {
			return existing;
		}

		Vec3 eye = player.getEyePosition();

		if (!config.railAtTarget || target == null || aimPoint == null) {
			Vec3 direction = aimPoint == null ? player.getLookAngle() : aimPoint.subtract(eye).normalize();
			return findSpotAlong(level, eye, direction, config.railDistance, config.minSelfDistance);
		}

		// Aim at the target's feet: that is where a cart sits, not at its middle. Walking back from
		// there and taking the first hit puts the cart as close as reach allows.
		//
		// Not right into them, though: a minecart is pushed around by entities standing in it, so a
		// cart inside a moving target drifts out of the arrow's path before the arrow arrives. The
		// standoff keeps it just short of them, where it stays put.
		Vec3 feet = target.position();
		Vec3 direction = feet.subtract(eye).normalize();
		double reachable = Math.min(eye.distanceTo(feet) - config.targetStandoff, BLOCK_REACH);

		for (double distance = reachable; distance >= config.minSelfDistance; distance -= 0.25) {
			BlockPos candidate = spotAt(level, eye, direction, distance, config.minSelfDistance);

			if (candidate != null) {
				return candidate;
			}
		}

		return null;
	}

	/** Lays a rail into the planned spot, unless there is already one there. */
	public static StepResult placeRail(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AutoCartConfig config,
			final BlockPos spot) {
		ClientLevel level = minecraft.level;

		if (level == null || spot == null) {
			return StepResult.fail("no spot for a rail");
		}

		if (level.getBlockState(spot).is(BlockTags.RAILS)) {
			return StepResult.ok("rail already there");
		}

		int slot = -1;

		// Backpack stock counts too: minecarts do not stack, so the hotbar runs dry after one combo.
		for (Item rail : RAIL_ITEMS) {
			slot = ensureInHotbar(player, gameMode, config, rail);

			if (slot >= 0) {
				break;
			}
		}

		if (slot < 0) {
			return StepResult.fail("no rail in the hotbar");
		}

		return useOnGround(minecraft, player, gameMode, slot, spot, "rail");
	}

	/** Puts a TNT minecart onto the rail at the planned spot. */
	public static StepResult placeCart(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AutoCartConfig config,
			final BlockPos preferredRail) {
		ClientLevel level = minecraft.level;

		if (level == null) {
			return StepResult.fail("no level");
		}

		// Use the rail we planned rather than whatever is closest, otherwise the cart lands on some
		// old track behind us and the whole geometry is pointless.
		BlockPos rail = preferredRail != null && level.getBlockState(preferredRail).is(BlockTags.RAILS)
				? preferredRail
				: findRail(level, player, config.railSearchRadius);

		if (rail == null) {
			return StepResult.fail("no rail to put the cart on");
		}

		// A second cart on the same rail means two blasts nobody reckoned with. Shoot the one there.
		if (cartOn(level, rail) != null) {
			return StepResult.ok("cart already on the rail");
		}

		int slot = ensureInHotbar(player, gameMode, config, Items.TNT_MINECART);

		if (slot < 0) {
			return StepResult.fail("no TNT minecart in the hotbar or the backpack");
		}

		selectSlot(player, gameMode, slot);

		Vec3 hitLocation = new Vec3(rail.getX() + 0.5, rail.getY() + 0.5, rail.getZ() + 0.5);
		BlockHitResult hit = new BlockHitResult(hitLocation, Direction.UP, rail, false);
		InteractionResult result = useItemOn(player, gameMode, hit);

		return result.consumesAction()
				? StepResult.ok("cart placed")
				: StepResult.fail("server refused the cart (" + result + ")");
	}

	/**
	 * Sets a fire between us and the cart spot, keeping clear of both.
	 *
	 * <p>The gap to the cart matters: fire spreads to a TNT minecart and would prime it early, before
	 * the arrow ever gets there.
	 */
	public static StepResult placeFire(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AutoCartConfig config,
			final Vec3 aimPoint,
			final BlockPos cartSpot) {
		ClientLevel level = minecraft.level;

		if (level == null) {
			return StepResult.fail("no level");
		}

		int slot = ensureInHotbar(player, gameMode, config, Items.FLINT_AND_STEEL);

		if (slot < 0) {
			slot = ensureInHotbar(player, gameMode, config, Items.FIRE_CHARGE);
		}

		if (slot < 0) {
			return StepResult.fail("no flint and steel or fire charge");
		}

		Vec3 eye = player.getEyePosition();
		BlockPos spot;

		// Still burning from the last try: the arrow will pick it up again.
		if (cartSpot != null && fireOnLine(level, eye, Vec3.atCenterOf(cartSpot))) {
			return StepResult.ok("fire still burning");
		}

		if (cartSpot != null) {
			Vec3 cartPoint = Vec3.atCenterOf(cartSpot);
			Vec3 direction = cartPoint.subtract(eye).normalize();
			// Work inwards from the cart so the fire ends up as far from us as the gap allows.
			double start = Math.min(eye.distanceTo(cartPoint) - config.fireGap, BLOCK_REACH);
			spot = findSpotBackwards(level, eye, direction, start, Math.max(1.2, config.minSelfDistance * 0.5));
		} else {
			Vec3 direction = aimPoint.subtract(eye).normalize();
			spot = findSpotAlong(level, eye, direction, config.fireDistance, 1.2);
		}

		if (spot == null) {
			return StepResult.fail("no room for the fire");
		}

		return useOnGround(minecraft, player, gameMode, slot, spot, "fire");
	}

	/**
	 * Walls ourselves off from the blast with whatever blocks are in the hotbar.
	 *
	 * <p>A burning arrow does not light a fuse, it blows the cart up on contact
	 * ({@code MinecartTNT#hurtServer}), one or two ticks after the shot. Cover put up after the shot
	 * therefore races the blast, and if the server handles it in the same tick as the shot it stops
	 * our own arrow right in front of us. So the crossbow builds it in the same tick just before
	 * shooting, and every spot the arrow would pass through is left open.
	 *
	 * <p>Cover is worth more than armour here: the explosion measures how much of you it can see, so
	 * a single block between you and the cart cuts the damage far harder than any enchantment.
	 *
	 * @param shotFrom where the arrow starts, or null if nothing is flying through here
	 * @param shotTo   where the arrow is aimed
	 */
	public static StepResult placeCover(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AutoCartConfig config,
			final BlockPos cartSpot,
			final Vec3 shotFrom,
			final Vec3 shotTo) {
		ClientLevel level = minecraft.level;

		if (level == null || cartSpot == null) {
			return StepResult.fail("nothing to hide from");
		}

		int slot = findSturdiestBlock(player);

		if (slot < 0) {
			return StepResult.fail("no blocks in the hotbar to hide behind");
		}

		// Straight towards the blast, at our own feet: the wall goes up between us and the cart.
		Vec3 toBlast = Vec3.atCenterOf(cartSpot).subtract(player.position());
		Direction facing = Direction.getApproximateNearest(toBlast.x, 0.0, toBlast.z);
		BlockPos feet = player.blockPosition().relative(facing);
		int placed = 0;
		int inTheWay = 0;

		for (int height = 0; height < config.coverHeight; height++) {
			BlockPos spot = feet.above(height);

			if (!isFree(level, spot)) {
				continue;
			}

			// Arrows collide with blocks along a plain ray, so a thin margin is enough.
			if (shotFrom != null && shotTo != null
					&& new AABB(spot).inflate(0.1).clip(shotFrom, shotTo).isPresent()) {
				inTheWay++;
				continue;
			}

			BlockPos support = spot.below();

			// The first block stands on the ground; the second one stands on the first.
			if (!level.getBlockState(support).isFaceSturdy(level, support, Direction.UP)) {
				continue;
			}

			selectSlot(player, gameMode, slot);

			Vec3 hitLocation = new Vec3(spot.getX() + 0.5, support.getY() + 1.0, spot.getZ() + 0.5);
			BlockHitResult hit = new BlockHitResult(hitLocation, Direction.UP, support, false);

			if (useItemOn(player, gameMode, hit).consumesAction()) {
				placed++;
			}
		}

		String skipped = inTheWay > 0 ? ", " + inTheWay + " left open for the arrow" : "";

		return placed > 0
				? StepResult.ok("took cover behind " + placed + " block" + (placed == 1 ? "" : "s") + skipped)
				: StepResult.fail("no room for cover" + skipped);
	}

	/**
	 * The most blast resistant block in the hotbar.
	 *
	 * <p>Any block breaks line of sight, but one that survives the explosion keeps doing it for the
	 * next cart too. Rails are skipped, they are needed elsewhere.
	 */
	private static int findSturdiestBlock(final LocalPlayer player) {
		Inventory inventory = player.getInventory();
		int best = -1;
		float bestResistance = -1.0F;

		for (int slot = 0; slot <= 8; slot++) {
			ItemStack stack = inventory.getItem(slot);

			if (!(stack.getItem() instanceof BlockItem blockItem) || stack.isEmpty()) {
				continue;
			}

			if (isComboItem(stack) || stack.is(Items.TNT)) {
				continue;
			}

			float resistance = blockItem.getBlock().getExplosionResistance();

			if (resistance > bestResistance) {
				best = slot;
				bestResistance = resistance;
			}
		}

		return best;
	}

	/** Shared tail of rail and fire placement: aim at the top face of the block underneath. */
	private static StepResult useOnGround(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final int slot,
			final BlockPos spot,
			final String what) {
		BlockPos support = spot.below();
		selectSlot(player, gameMode, slot);

		Vec3 hitLocation = new Vec3(spot.getX() + 0.5, support.getY() + 1.0, spot.getZ() + 0.5);
		BlockHitResult hit = new BlockHitResult(hitLocation, Direction.UP, support, false);
		InteractionResult result = useItemOn(player, gameMode, hit);

		return result.consumesAction()
				? StepResult.ok(what + " placed")
				: StepResult.fail("server refused the " + what + " (" + result + ")");
	}

	/**
	 * Uses the held item on a block and swings the way {@code Minecraft#startUseItem} does.
	 *
	 * <p>The swing is only the local animation; the server swings for itself. The animation is read
	 * before the use, because placing the last item of a stack leaves an empty hand behind.
	 */
	private static InteractionResult useItemOn(
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final BlockHitResult hit) {
		SwingAnimation animation = player.getMainHandItem().getInteractAnimation();
		InteractionResult result = gameMode.useItemOn(player, InteractionHand.MAIN_HAND, hit);

		if (result instanceof InteractionResult.Success success
				&& success.swingSource() == InteractionResult.SwingSource.PREDICTED) {
			player.swing(InteractionHand.MAIN_HAND, animation, false);
		}

		return result;
	}

	// ---------------------------------------------------------------- weapons

	/**
	 * Makes sure a weapon of the wanted kind sits in the hotbar, fetching one from the backpack.
	 *
	 * <p>Sends the same container interaction the inventory screen would send for a hotbar swap. The
	 * player's own menu stays open behind every screen, so this works with no GUI showing.
	 *
	 * @return the hotbar slot holding one, or -1 if the whole inventory has none
	 */
	public static int ensureInHotbar(
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AutoCartConfig config,
			final Item item) {
		int slot = findHotbarSlot(player, item);

		if (slot >= 0 || !config.refillFromInventory) {
			return slot;
		}

		Inventory inventory = player.getInventory();
		AbstractContainerMenu menu = player.containerMenu;

		// If a real screen is open the server tracks that menu instead; don't fight it.
		if (menu != player.inventoryMenu) {
			return -1;
		}

		for (int storage = FIRST_STORAGE_SLOT; storage <= LAST_STORAGE_SLOT; storage++) {
			if (!inventory.getItem(storage).is(item)) {
				continue;
			}

			int hotbarSlot = freeHotbarSlot(player, config);
			gameMode.handleContainerInput(menu.containerId, storage, hotbarSlot, ContainerInput.SWAP, player);
			return hotbarSlot;
		}

		return -1;
	}

	/**
	 * Gets a crossbow that is ready to fire into the hotbar, without charging anything.
	 *
	 * <p>Checked in the order that costs the least time: one already in the hotbar, then a loaded one
	 * out of the backpack. Swapping takes a tick, charging takes over a second, so a loaded crossbow
	 * sitting in the inventory is always the better answer than reloading an empty one.
	 *
	 * @return the hotbar slot holding a loaded crossbow, or -1 if there is none anywhere
	 */
	public static int ensureLoadedCrossbow(
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AutoCartConfig config) {
		int ready = findLoadedCrossbow(player);

		if (ready >= 0 || !config.refillFromInventory) {
			return ready;
		}

		AbstractContainerMenu menu = player.containerMenu;

		// If a real screen is open the server tracks that menu instead; don't fight it.
		if (menu != player.inventoryMenu) {
			return -1;
		}

		Inventory inventory = player.getInventory();

		for (int storage = FIRST_STORAGE_SLOT; storage <= LAST_STORAGE_SLOT; storage++) {
			if (!isLoadedCrossbow(inventory.getItem(storage))) {
				continue;
			}

			int hotbarSlot = freeHotbarSlot(player, config);
			gameMode.handleContainerInput(menu.containerId, storage, hotbarSlot, ContainerInput.SWAP, player);
			return hotbarSlot;
		}

		return -1;
	}

	/**
	 * An empty hotbar slot if there is one, otherwise the configured dump slot.
	 *
	 * <p>Unless the dump slot holds something the combo needs: swapping the TNT minecart into the
	 * backpack to make room for a crossbow would only trade one abort for another. Then the first
	 * slot holding nothing the combo uses is taken instead.
	 */
	private static int freeHotbarSlot(final LocalPlayer player, final AutoCartConfig config) {
		Inventory inventory = player.getInventory();

		for (int slot = 0; slot <= 8; slot++) {
			if (inventory.getItem(slot).isEmpty()) {
				return slot;
			}
		}

		int dump = Mth.clamp(config.refillSlot, 0, 8);

		if (!isComboItem(inventory.getItem(dump))) {
			return dump;
		}

		for (int slot = 0; slot <= 8; slot++) {
			if (!isComboItem(inventory.getItem(slot))) {
				return slot;
			}
		}

		return dump;
	}

	private static boolean isComboItem(final ItemStack stack) {
		for (Item rail : RAIL_ITEMS) {
			if (stack.is(rail)) {
				return true;
			}
		}

		return stack.is(Items.TNT_MINECART) || stack.is(Items.FLINT_AND_STEEL) || stack.is(Items.FIRE_CHARGE)
				|| stack.is(Items.CROSSBOW) || stack.is(Items.BOW);
	}

	/**
	 * Starts charging a crossbow or drawing a bow, and reports how many ticks to hold.
	 *
	 * <p>Vanilla releases whatever the player is using as soon as the use key is up, so the key is
	 * held down artificially for the duration. {@link #releaseUse} lets go of it again.
	 *
	 * @return ticks to hold, or -1 when there is nothing to charge
	 */
	public static int startUsing(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AutoCartConfig config,
			final int slot) {
		if (slot < 0) {
			return -1;
		}

		selectSlot(player, gameMode, slot);

		ItemStack stack = player.getInventory().getItem(slot);
		minecraft.options.keyUse.setDown(true);
		gameMode.useItem(player, InteractionHand.MAIN_HAND);

		return stack.is(Items.CROSSBOW)
				? CrossbowItem.getChargeDuration(stack, player)
				: config.bowDrawTicks;
	}

	/**
	 * Lets go of the use key.
	 *
	 * <p>For a crossbow this is what loads the bolt; for a bow it is the shot itself.
	 */
	public static void releaseUse(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode) {
		gameMode.releaseUsingItem(player);
		minecraft.options.keyUse.setDown(false);
	}

	/** Safety net: never leave the use key stuck down if a run is aborted mid-charge. */
	public static void releaseUseKey(final Minecraft minecraft) {
		minecraft.options.keyUse.setDown(false);
	}

	/** Pulls the trigger on a loaded crossbow. Bows shoot on release instead, see releaseUse. */
	public static StepResult shootCrossbow(
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode) {
		ItemStack held = player.getItemInHand(InteractionHand.MAIN_HAND);

		if (!isLoadedCrossbow(held)) {
			return StepResult.fail("crossbow is not loaded any more");
		}

		gameMode.useItem(player, InteractionHand.MAIN_HAND);
		return StepResult.ok("shot");
	}

	public static int findHotbarSlot(final LocalPlayer player, final Item item) {
		Inventory inventory = player.getInventory();

		for (int slot = 0; slot <= 8; slot++) {
			if (inventory.getItem(slot).is(item)) {
				return slot;
			}
		}

		return -1;
	}

	/** A crossbow that still needs charging. Prefers an empty one so a loaded one stays ready. */
	public static int findEmptyCrossbow(final LocalPlayer player) {
		Inventory inventory = player.getInventory();

		for (int slot = 0; slot <= 8; slot++) {
			ItemStack stack = inventory.getItem(slot);

			if (stack.is(Items.CROSSBOW) && !isLoadedCrossbow(stack)) {
				return slot;
			}
		}

		return -1;
	}

	public static int findLoadedCrossbow(final LocalPlayer player) {
		Inventory inventory = player.getInventory();

		for (int slot = 0; slot <= 8; slot++) {
			if (isLoadedCrossbow(inventory.getItem(slot))) {
				return slot;
			}
		}

		return -1;
	}

	/** Whether a loaded crossbow sits anywhere in the hotbar or the backpack. Moves nothing. */
	public static boolean hasLoadedCrossbow(final LocalPlayer player) {
		Inventory inventory = player.getInventory();

		for (int slot = 0; slot <= LAST_STORAGE_SLOT; slot++) {
			if (isLoadedCrossbow(inventory.getItem(slot))) {
				return true;
			}
		}

		return false;
	}

	private static boolean isLoadedCrossbow(final ItemStack stack) {
		if (!stack.is(Items.CROSSBOW)) {
			return false;
		}

		ChargedProjectiles charged = stack.get(DataComponents.CHARGED_PROJECTILES);
		return charged != null && !charged.isEmpty();
	}

	// ---------------------------------------------------------------- lookups

	/** The TNT minecart the crosshair points at within block reach, even past the 3 blocks entity reach. */
	public static MinecartTNT cartInView(final Minecraft minecraft, final LocalPlayer player) {
		ClientLevel level = minecraft.level;

		if (level == null) {
			return null;
		}

		Vec3 eye = player.getEyePosition();
		Vec3 end = eye.add(player.getLookAngle().scale(BLOCK_REACH));
		MinecartTNT closest = null;
		double bestDistance = Double.MAX_VALUE;

		for (MinecartTNT cart : level.getEntitiesOfClass(MinecartTNT.class, player.getBoundingBox().inflate(BLOCK_REACH))) {
			if (cart.getBoundingBox().inflate(0.3).clip(eye, end).isPresent() && cart.distanceToSqr(eye) < bestDistance) {
				closest = cart;
				bestDistance = cart.distanceToSqr(eye);
			}
		}

		return closest;
	}

	/** The TNT minecart standing on that rail block, if any. */
	public static MinecartTNT cartOn(final ClientLevel level, final BlockPos rail) {
		List<MinecartTNT> carts = level.getEntitiesOfClass(MinecartTNT.class, new AABB(rail).inflate(0.5));
		return carts.isEmpty() ? null : carts.getFirst();
	}

	/** Any fire block the straight line from us to the cart passes through. */
	private static boolean fireOnLine(final ClientLevel level, final Vec3 from, final Vec3 to) {
		Vec3 step = to.subtract(from);
		int samples = (int) Math.ceil(step.length() * 4.0);

		for (int i = 1; i < samples; i++) {
			BlockPos pos = BlockPos.containing(from.add(step.scale((double) i / samples)));

			if (level.getBlockState(pos).is(BlockTags.FIRE)) {
				return true;
			}
		}

		return false;
	}

	/** Is another player close enough to be swinging at us? Preloading then is a bad idea. */
	public static boolean playerNearby(final Minecraft minecraft, final LocalPlayer player, final double range) {
		ClientLevel level = minecraft.level;

		if (level == null) {
			return false;
		}

		for (Player other : level.players()) {
			if (other != player && other.distanceToSqr(player) <= range * range) {
				return true;
			}
		}

		return false;
	}

	/** The point to aim at: the planned cart spot, the cart itself, or the target entity. */
	public static Vec3 aimPoint(
			final Minecraft minecraft,
			final LocalPlayer player,
			final AutoCartConfig config,
			final Entity target,
			final BlockPos plannedSpot) {
		if (config.aimAtCart()) {
			MinecartTNT cart = findCart(minecraft, player, config.railSearchRadius + 2.0);

			if (cart != null) {
				return cart.position().add(0.0, 0.3, 0.0);
			}

			if (plannedSpot != null) {
				// Where the cart will sit once it exists: just above the rail.
				return new Vec3(plannedSpot.getX() + 0.5, plannedSpot.getY() + 0.4, plannedSpot.getZ() + 0.5);
			}
		}

		if (target != null) {
			return target.position().add(0.0, target.getBbHeight() * 0.5, 0.0);
		}

		return null;
	}

	public static MinecartTNT findCart(final Minecraft minecraft, final LocalPlayer player, final double radius) {
		ClientLevel level = minecraft.level;

		if (level == null) {
			return null;
		}

		AABB box = player.getBoundingBox().inflate(radius);
		List<MinecartTNT> carts = level.getEntitiesOfClass(MinecartTNT.class, box);
		MinecartTNT closest = null;
		double bestDistance = Double.MAX_VALUE;

		for (MinecartTNT cart : carts) {
			double distance = cart.distanceToSqr(player);

			if (distance < bestDistance) {
				closest = cart;
				bestDistance = distance;
			}
		}

		return closest;
	}

	/** Closest rail within the radius that has room for a cart and is inside block reach. */
	private static BlockPos findRail(final ClientLevel level, final LocalPlayer player, final double radius) {
		Vec3 eye = player.getEyePosition();
		BlockPos origin = player.blockPosition();
		int range = Mth.ceil(radius);
		BlockPos closest = null;
		double bestDistance = Double.MAX_VALUE;

		for (BlockPos pos : BlockPos.betweenClosed(origin.offset(-range, -range, -range), origin.offset(range, range, range))) {
			if (!level.getBlockState(pos).is(BlockTags.RAILS)) {
				continue;
			}

			if (!isFree(level, pos.above())) {
				continue;
			}

			double distance = eye.distanceToSqr(Vec3.atCenterOf(pos));

			if (distance > BLOCK_REACH * BLOCK_REACH || distance >= bestDistance) {
				continue;
			}

			closest = pos.immutable();
			bestDistance = distance;
		}

		return closest;
	}

	/**
	 * Samples around a wanted distance, nearer and further, and takes the first usable spot.
	 *
	 * <p>Uneven ground is the normal case, so insisting on exactly one distance would fail far more
	 * often than it needs to.
	 */
	private static BlockPos findSpotAlong(
			final ClientLevel level,
			final Vec3 eye,
			final Vec3 direction,
			final double wanted,
			final double minimum) {
		for (double offset = 0.0; offset <= 2.0; offset += 0.25) {
			for (double sign : new double[]{1.0, -1.0}) {
				BlockPos candidate = spotAt(level, eye, direction, wanted + sign * offset, minimum);

				if (candidate != null) {
					return candidate;
				}
			}
		}

		return null;
	}

	/** Walks inwards from a starting distance towards us and takes the furthest usable spot. */
	private static BlockPos findSpotBackwards(
			final ClientLevel level,
			final Vec3 eye,
			final Vec3 direction,
			final double start,
			final double minimum) {
		for (double distance = Math.min(start, BLOCK_REACH); distance >= minimum; distance -= 0.25) {
			BlockPos candidate = spotAt(level, eye, direction, distance, minimum);

			if (candidate != null) {
				return candidate;
			}
		}

		return null;
	}

	/** One sample: something we may build into, something sturdy under it, and inside reach. */
	private static BlockPos spotAt(
			final ClientLevel level,
			final Vec3 eye,
			final Vec3 direction,
			final double distance,
			final double minimum) {
		if (distance < Math.max(1.0, minimum)) {
			return null;
		}

		BlockPos pos = BlockPos.containing(eye.add(direction.scale(distance)));
		return usable(level, eye, pos, minimum) ? pos.immutable() : null;
	}

	/** Can a rail go here: free space, sturdy floor, within reach and not on top of us. */
	private static boolean usable(
			final ClientLevel level,
			final Vec3 eye,
			final BlockPos pos,
			final double minimum) {
		if (!isFree(level, pos)) {
			return false;
		}

		BlockPos support = pos.below();

		if (!level.getBlockState(support).isFaceSturdy(level, support, Direction.UP)) {
			return false;
		}

		if (eye.distanceToSqr(Vec3.atCenterOf(support)) > BLOCK_REACH * BLOCK_REACH) {
			return false;
		}

		return eye.distanceToSqr(Vec3.atCenterOf(pos)) >= minimum * minimum;
	}

	/**
	 * Air, or something a placed block would replace anyway.
	 *
	 * <p>Insisting on plain air was too strict: grass, snow layers and the like cover most ground and
	 * would have turned every field into "no spot found".
	 */
	private static boolean isFree(final ClientLevel level, final BlockPos pos) {
		return level.getBlockState(pos).canBeReplaced();
	}

	// ---------------------------------------------------------------- plumbing

	public static void selectSlot(final LocalPlayer player, final MultiPlayerGameMode gameMode, final int slot) {
		player.getInventory().setSelectedSlot(slot);
		// MultiPlayerGameMode#tick has already run this tick, so push the slot packet ourselves.
		((MultiPlayerGameModeAccessor) gameMode).autocart$ensureHasSentCarriedItem();
	}

	public static void lookAt(final LocalPlayer player, final Vec3 point) {
		Vec3 eye = player.getEyePosition();
		double dx = point.x - eye.x;
		double dy = point.y - eye.y;
		double dz = point.z - eye.z;
		double horizontal = Math.sqrt(dx * dx + dz * dz);

		float yaw = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
		float pitch = (float) (-(Mth.atan2(dy, horizontal) * (180.0 / Math.PI)));

		player.setYRot(yaw);
		player.setXRot(pitch);
		player.setYHeadRot(yaw);
	}

	/** Outcome of one step, with a line of text for the action bar. */
	public record StepResult(boolean success, String message) {
		static StepResult ok(final String message) {
			return new StepResult(true, message);
		}

		static StepResult fail(final String message) {
			return new StepResult(false, message);
		}
	}
}
