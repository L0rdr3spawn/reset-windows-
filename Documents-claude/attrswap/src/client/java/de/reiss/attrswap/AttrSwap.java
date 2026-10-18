package de.reiss.attrswap;

import de.reiss.attrswap.mixin.MultiPlayerGameModeAccessor;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPunchPacket;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.AttackRange;
import net.minecraft.world.item.component.PiercingWeapon;
import net.minecraft.world.item.component.SwingAnimation;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

/**
 * Switches hotbar slot and attacks inside a single client tick, so the server resolves the hit
 * with one item while the player's attributes still belong to another.
 *
 * <p>Held-item attribute modifiers only change in the server's entity tick
 * ({@code LivingEntity#collectEquipmentChanges}), and the "main hand item changed" check that
 * clears the attack strength ticker lives in {@code Player#tick}. Packets are handled before
 * either, so {@code SetCarriedItem(mace), Attack, SetCarriedItem(sword)} hits with the mace
 * (its smash bonus and enchantments) using the sword's attack damage, attack speed and charge.
 * Swapping back in the same tick means the server never sees the main hand change at all.
 * Paper needs {@code update-equipment-on-player-actions: false} for this, vanilla behaves so.
 *
 * <p>Double mode attacks with the first slot and then the second. {@code Player#attack} clears
 * the ticker through {@code onAttack}, so the second hit runs at about 4 % charge: 20 % base
 * damage, no enchantment damage, only flat bonuses like the mace smash survive. Measured in the
 * game test (8 block fall onto a pig): sword 12, mace 37.8, double sword->mace 20.8, single 40.8.
 *
 * <p>Each attack mirrors the checks {@code Minecraft#startAttack} performs, because the game
 * gates attacks per held item: {@code minimum_attack_charge} is enforced server side, and
 * {@code attack_range} is item dependent, so the slots can disagree about reach. Vanilla sends
 * one {@link ServerboundPunchPacket} per click; this sends exactly one per combo.
 */
public final class AttrSwap {
	private AttrSwap() {
	}

	/** The swap key: the auto pick if it finds something, otherwise the configured slots. */
	public static void run(final Minecraft minecraft, final AttrSwapConfig config) {
		LocalPlayer player = minecraft.player;
		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (!canAct(minecraft, player, gameMode)) {
			return;
		}

		HitResult hitResult = minecraft.hitResult;
		Entity target = hitResult instanceof EntityHitResult entityHit ? entityHit.getEntity() : null;

		if (target == null && config.requireTarget) {
			return;
		}

		int startSlot = player.getInventory().getSelectedSlot();
		AutoPick.Plan plan = config.autoPick ? AutoPick.plan(player, target, startSlot) : null;

		if (plan != null) {
			execute(minecraft, player, gameMode, config, plan.breakerSlot(), plan.hitSlot(), true, plan.reason());
			return;
		}

		int secondSlot = config.secondSlot;
		// Single mode borrows the attributes of whatever the server saw held last tick, which is
		// the current slot; selecting another one now would not change them in time.
		int firstSlot = config.isDoubleMode() && config.firstSlot >= 0 ? config.firstSlot : startSlot;

		if (firstSlot == secondSlot) {
			// Always shown: pressing the key and seeing nothing happen is otherwise a mystery.
			player.sendOverlayMessage(Component.literal("attrswap: already holding slot "
					+ (secondSlot + 1) + ", nothing to swap"));
			return;
		}

		execute(minecraft, player, gameMode, config, config.isDoubleMode() ? firstSlot : -1, secondSlot,
				config.swapBack || !config.isDoubleMode(), config.mode);
	}

	/**
	 * A plain left click on an entity. Takes the click over only when the auto pick has something
	 * better than the held item; otherwise vanilla handles it as usual.
	 *
	 * @return true when the click was used up here
	 */
	public static boolean runOnClick(final Minecraft minecraft, final AttrSwapConfig config) {
		LocalPlayer player = minecraft.player;
		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (!canAct(minecraft, player, gameMode) || !(minecraft.hitResult instanceof EntityHitResult entityHit)) {
			return false;
		}

		// Vanilla would refuse this click (weapon not charged enough); so do we.
		if (player.cannotAttackWithItem(player.getMainHandItem(), 0)) {
			return false;
		}

		AutoPick.Plan plan = AutoPick.plan(player, entityHit.getEntity(), player.getInventory().getSelectedSlot());

		if (plan == null) {
			return false;
		}

		execute(minecraft, player, gameMode, config, plan.breakerSlot(), plan.hitSlot(), true, "click " + plan.reason());
		return true;
	}

	private static boolean canAct(final Minecraft minecraft, final LocalPlayer player, final MultiPlayerGameMode gameMode) {
		return player != null && gameMode != null && minecraft.level != null
				&& !gameMode.isSpectator() && !player.isHandsBusy();
	}

	/**
	 * Hits with {@code firstSlot} (skipped when -1), then with {@code secondSlot}, then optionally
	 * goes back to the slot held before. All in the current tick.
	 */
	private static void execute(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AttrSwapConfig config,
			final int firstSlot,
			final int secondSlot,
			final boolean swapBack,
			final String label) {
		HitResult hitResult = minecraft.hitResult;
		Entity target = hitResult instanceof EntityHitResult entityHit ? entityHit.getEntity() : null;
		Inventory inventory = player.getInventory();
		int startSlot = inventory.getSelectedSlot();
		Result first = null;

		if (firstSlot >= 0) {
			inventory.setSelectedSlot(firstSlot);
			first = attackWithHeldItem(minecraft, player, gameMode, hitResult, target);
		}

		inventory.setSelectedSlot(secondSlot);
		Result second = attackWithHeldItem(minecraft, player, gameMode, hitResult, target);

		if ((first != null && first.swung()) || second.swung()) {
			player.connection.send(ServerboundPunchPacket.INSTANCE);
		}

		if (swapBack) {
			inventory.setSelectedSlot(startSlot);
			// MultiPlayerGameMode only flushes the slot packet in its own tick, which has
			// already run by the time this fires. Flush it now so the server never observes
			// a changed main hand item and never resets the attack strength ticker.
			((MultiPlayerGameModeAccessor) gameMode).attrswap$ensureHasSentCarriedItem();
		}

		report(player, config, "attrswap " + label + ": "
				+ (first != null ? (firstSlot + 1) + " " + first + " -> " : "")
				+ (secondSlot + 1) + " " + second
				+ (swapBack ? " -> " + (startSlot + 1) : ""));
	}

	/**
	 * The entity branch of {@code Minecraft#startAttack}, minus the miss-time bookkeeping that
	 * only applies to block breaking.
	 */
	private static Result attackWithHeldItem(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final HitResult hitResult,
			final Entity target) {
		ItemStack heldItem = player.getItemInHand(InteractionHand.MAIN_HAND);

		if (!heldItem.isItemEnabled(minecraft.level.enabledFeatures())) {
			return Result.ITEM_DISABLED;
		}

		// Spears carry minimum_attack_charge 1.0. The server drops those packets with a
		// 5 tick tolerance, so sending them anyway would only produce noise on the wire.
		if (player.cannotAttackWithItem(heldItem, 0)) {
			return Result.NOT_CHARGED;
		}

		SwingAnimation animation = heldItem.getAttackAnimation();
		PiercingWeapon piercingWeapon = heldItem.get(DataComponents.PIERCING_WEAPON);

		// Swings itself and needs no punch, same as in startAttack.
		if (piercingWeapon != null) {
			gameMode.piercingAttack(animation, piercingWeapon);
			return Result.PIERCED;
		}

		// The swing is only the local animation now; the server hears about it through the punch.
		if (target == null) {
			player.swing(InteractionHand.MAIN_HAND, animation, false);
			return Result.NO_TARGET;
		}

		AttackRange attackRange = heldItem.get(DataComponents.ATTACK_RANGE);

		if (attackRange != null && !attackRange.isInRange(player, hitResult.getLocation())) {
			player.swing(InteractionHand.MAIN_HAND, animation, false);
			return Result.OUT_OF_RANGE;
		}

		gameMode.attack(player, target);
		player.swing(InteractionHand.MAIN_HAND, animation, false);
		return Result.HIT;
	}

	private static void report(final LocalPlayer player, final AttrSwapConfig config, final String text) {
		if (config.debugMessages) {
			player.sendOverlayMessage(Component.literal(text));
		}
	}

	private enum Result {
		HIT,
		PIERCED,
		NO_TARGET,
		OUT_OF_RANGE,
		NOT_CHARGED,
		ITEM_DISABLED;

		/** Took the swing branch of startAttack, which vanilla follows up with a punch. */
		boolean swung() {
			return this == HIT || this == NO_TARGET || this == OUT_OF_RANGE;
		}
	}
}
