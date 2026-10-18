package de.reiss.attrswap;

import de.reiss.attrswap.mixin.MultiPlayerGameModeAccessor;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.PiercingWeapon;

/**
 * One key for a spear lunge without the spear's long wind-up.
 *
 * <p>The server lets a spear stab through when {@code (ticker + 5) / delay >= 1}
 * ({@code ServerGamePacketListenerImpl#handlePlayerAction}, STAB), where {@code delay} comes from
 * the attack speed attribute the player has <em>right now</em>. Attributes only follow the held
 * item in the entity tick, so a spear selected and stabbed in the same tick is judged by the item
 * held before it. A spear needs 19 ticks on its own; an empty hand (attack speed 4, delay 5)
 * passes the check the moment its attributes are in place.
 *
 * <p>So: if the held item is charged enough, select the spear, stab, and go back, all in one
 * tick; the server never even sees the spear in hand. Otherwise step onto a resting slot first
 * (empty hand, wind charge, totem: anything with no attack of its own), wait until its attributes
 * have arrived plus {@link AttrSwapConfig#lungeRestTicks}, then do the same.
 */
public final class SpearLunge {
	/** The server's own leeway in ticks; one less, so a client tick ahead does not get refused. */
	private static final int SERVER_TOLERANCE = 4;

	private enum Phase {
		IDLE,
		RESTING
	}

	private Phase phase = Phase.IDLE;
	private int returnSlot;
	private int restSlot;
	private int restedTicks;
	private int waitedTicks;

	/** Key pressed. */
	public void start(final Minecraft minecraft, final AttrSwapConfig config) {
		LocalPlayer player = minecraft.player;
		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (phase != Phase.IDLE || player == null || gameMode == null || gameMode.isSpectator() || player.isHandsBusy()) {
			return;
		}

		Inventory inventory = player.getInventory();
		int spear = findSpear(inventory);

		if (spear < 0) {
			player.sendOverlayMessage(Component.literal("attrswap: no spear in the hotbar"));
			return;
		}

		int held = inventory.getSelectedSlot();

		if (held != spear && serverWouldAccept(player)) {
			stab(minecraft, player, gameMode, config, spear, held, held);
			return;
		}

		int rest = config.lungeRestSlot >= 0 ? config.lungeRestSlot : findRestSlot(inventory, spear);

		if (rest < 0 || rest == spear) {
			player.sendOverlayMessage(Component.literal("attrswap: no free slot to charge on (empty hand, wind charge, totem...)"));
			return;
		}

		returnSlot = held;
		restSlot = rest;
		restedTicks = 0;
		waitedTicks = 0;
		phase = Phase.RESTING;
		inventory.setSelectedSlot(rest);
		((MultiPlayerGameModeAccessor) gameMode).attrswap$ensureHasSentCarriedItem();
		report(player, config, "attrswap lunge: resting on slot " + (rest + 1));
	}

	/** Every client tick. */
	public void tick(final Minecraft minecraft, final AttrSwapConfig config) {
		if (phase == Phase.IDLE) {
			return;
		}

		LocalPlayer player = minecraft.player;
		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (player == null || gameMode == null) {
			phase = Phase.IDLE;
			return;
		}

		Inventory inventory = player.getInventory();

		// Scrolled away by hand, or waited far too long: give up quietly.
		if (inventory.getSelectedSlot() != restSlot || ++waitedTicks > 40) {
			phase = Phase.IDLE;
			return;
		}

		// "Am I on it yet": the resting item's attack speed has replaced the old one. The entity tick
		// that does this runs on the server at the same point, so from here on it counts.
		if (restedTicks == 0 && !restAttributesApplied(player)) {
			return;
		}

		if (++restedTicks <= config.lungeRestTicks) {
			return;
		}

		int spear = findSpear(inventory);
		phase = Phase.IDLE;

		if (spear < 0) {
			return;
		}

		int back = config.lungeReturnToRest ? restSlot : returnSlot;
		stab(minecraft, player, gameMode, config, spear, back, restSlot);
	}

	private void stab(
			final Minecraft minecraft,
			final LocalPlayer player,
			final MultiPlayerGameMode gameMode,
			final AttrSwapConfig config,
			final int spear,
			final int back,
			final int from) {
		Inventory inventory = player.getInventory();
		inventory.setSelectedSlot(spear);
		ItemStack stack = inventory.getItem(spear);
		PiercingWeapon weapon = stack.get(DataComponents.PIERCING_WEAPON);

		// Sends the slot change first, then the stab, like a normal click would.
		gameMode.piercingAttack(stack.getAttackAnimation(), weapon);

		inventory.setSelectedSlot(back);
		((MultiPlayerGameModeAccessor) gameMode).attrswap$ensureHasSentCarriedItem();
		report(player, config, "attrswap lunge: " + (from + 1) + " -> spear " + (spear + 1) + " -> " + (back + 1));
	}

	/** The server check for a stab, judged with the attributes of what we hold right now. */
	private static boolean serverWouldAccept(final LocalPlayer player) {
		double delay = player.getCurrentItemAttackStrengthDelay();
		double ticker = player.getAttackStrengthScale(0.0F) * delay;
		return (ticker + SERVER_TOLERANCE) / delay >= 1.0;
	}

	/** An empty hand and every item without attack modifiers attack at speed 4. */
	private static boolean restAttributesApplied(final LocalPlayer player) {
		return player.getAttributeValue(Attributes.ATTACK_SPEED) >= 3.99;
	}

	/** Prefers one with Lunge on it; any spear otherwise. */
	private static int findSpear(final Inventory inventory) {
		int any = -1;

		for (int slot = 0; slot <= 8; slot++) {
			ItemStack stack = inventory.getItem(slot);

			if (!stack.has(DataComponents.PIERCING_WEAPON)) {
				continue;
			}

			if (stack.isEnchanted()) {
				return slot;
			}

			if (any < 0) {
				any = slot;
			}
		}

		return any;
	}

	/**
	 * A slot whose item does nothing on its own when held: empty first, then anything without attack
	 * modifiers (wind charge, totem, blocks...). Those all leave attack speed at the base 4.
	 */
	private static int findRestSlot(final Inventory inventory, final int spear) {
		for (int slot = 0; slot <= 8; slot++) {
			if (inventory.getItem(slot).isEmpty()) {
				return slot;
			}
		}

		for (int slot = 0; slot <= 8; slot++) {
			ItemStack stack = inventory.getItem(slot);

			if (slot != spear && stack.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS,
					net.minecraft.world.item.component.ItemAttributeModifiers.EMPTY).modifiers().isEmpty()
					&& !stack.has(DataComponents.WEAPON)) {
				return slot;
			}
		}

		return -1;
	}

	private static void report(final LocalPlayer player, final AttrSwapConfig config, final String text) {
		if (config.debugMessages) {
			player.sendOverlayMessage(Component.literal(text));
		}
	}
}
