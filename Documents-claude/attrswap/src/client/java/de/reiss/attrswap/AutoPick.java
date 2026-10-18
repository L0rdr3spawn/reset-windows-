package de.reiss.attrswap;

import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.MaceItem;
import net.minecraft.world.item.component.Weapon;

/**
 * Picks the hotbar item that beats the held one for this particular hit.
 *
 * <ul>
 *   <li>Falling far enough for a smash ({@link MaceItem#canSmashAttack}: over 1.5 blocks, not
 *       gliding): the mace. Its fall bonus does not scale with charge, the held weapon's damage and
 *       charge come along through the attribute swap.</li>
 *   <li>Target holding up a shield: the item that disables shields longest (an axe, via the
 *       {@code weapon} component's {@code disable_blocking_for_seconds}).</li>
 *   <li>Both at once: axe first to knock the shield down, mace straight after in the same tick.
 *       The mace hit has no charge left then, but the smash bonus does not need any.</li>
 * </ul>
 *
 * <p>The client tracks its own fall distance the same way the server does, so the smash check
 * agrees with what the server will decide.
 */
public final class AutoPick {
	private AutoPick() {
	}

	/**
	 * @param breakerSlot slot to hit with first, or -1 for a single hit
	 * @param hitSlot     slot to hit with (last)
	 * @param reason      shown in the debug line
	 */
	public record Plan(int breakerSlot, int hitSlot, String reason) {
	}

	/** @return what to do, or null when the held item is already the best choice */
	public static Plan plan(final LocalPlayer player, final Entity target, final int heldSlot) {
		boolean blocking = target instanceof LivingEntity living && living.isBlocking();
		int breaker = blocking ? findShieldBreaker(player) : -1;
		int mace = MaceItem.canSmashAttack(player) ? findMace(player) : -1;
		Plan plan;

		if (breaker >= 0 && mace >= 0 && breaker != mace) {
			plan = new Plan(breaker, mace, "stun slam");
		} else if (mace >= 0) {
			plan = new Plan(-1, mace, "smash");
		} else if (breaker >= 0) {
			plan = new Plan(-1, breaker, "shield break");
		} else {
			return null;
		}

		// Already holding it and nothing to do first: an ordinary hit is exactly that.
		return plan.breakerSlot() < 0 && plan.hitSlot() == heldSlot ? null : plan;
	}

	private static int findMace(final LocalPlayer player) {
		Inventory inventory = player.getInventory();
		int selected = inventory.getSelectedSlot();

		// Keep the one in hand if it is a mace, so the plan collapses to an ordinary hit.
		if (inventory.getItem(selected).getItem() instanceof MaceItem) {
			return selected;
		}

		for (int slot = 0; slot <= 8; slot++) {
			if (inventory.getItem(slot).getItem() instanceof MaceItem) {
				return slot;
			}
		}

		return -1;
	}

	private static int findShieldBreaker(final LocalPlayer player) {
		Inventory inventory = player.getInventory();
		int best = -1;
		float bestSeconds = 0.0F;

		for (int slot = 0; slot <= 8; slot++) {
			ItemStack stack = inventory.getItem(slot);
			Weapon weapon = stack.get(DataComponents.WEAPON);

			if (weapon != null && weapon.disableBlockingForSeconds() > bestSeconds) {
				best = slot;
				bestSeconds = weapon.disableBlockingForSeconds();
			}
		}

		return best;
	}
}
