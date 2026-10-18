package de.reiss.autocart;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.item.ItemStack;

/**
 * Keeps a totem in the offhand. A pop empties the offhand; the next totem from the inventory goes
 * in right after, see {@link AutoCartConfig#autoTotem}.
 *
 * <p>Uses the inventory menu's hotbar-swap click with button 40, which is the offhand. The server
 * accepts it with no screen open, the same way the F key swap reaches it as a menu action.
 */
public final class AutoTotem {
	/** InventoryMenu slot numbers: storage 9-35 as is, hotbar 0-8 at 36-44. */
	private static final int HOTBAR_MENU_OFFSET = 36;
	private static final int OFFHAND_BUTTON = 40;

	private int emptyTicks;
	private boolean warned;

	public void tick(final Minecraft minecraft, final AutoCartConfig config) {
		LocalPlayer player = minecraft.player;
		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (!config.autoTotem || player == null || gameMode == null || player.isDeadOrDying() || player.isSpectator()) {
			emptyTicks = 0;
			return;
		}

		ItemStack offhand = player.getOffhandItem();

		if (offhand.has(DataComponents.DEATH_PROTECTION)) {
			emptyTicks = 0;
			warned = false;
			return;
		}

		if (!offhand.isEmpty() && !config.totemReplaceOffhand) {
			emptyTicks = 0;
			return;
		}

		// Someone sorting items by hand: leave the inventory alone until the screen is closed.
		if (minecraft.gui.screen() != null || player.containerMenu != player.inventoryMenu) {
			return;
		}

		if (++emptyTicks <= config.autoTotemDelayTicks) {
			return;
		}

		int slot = findTotem(player.getInventory());

		if (slot < 0) {
			if (!warned) {
				warned = true;
				player.sendOverlayMessage(Component.literal("autocart: no totem left in the inventory"));
			}
			return;
		}

		int menuSlot = slot < 9 ? HOTBAR_MENU_OFFSET + slot : slot;
		gameMode.handleContainerInput(player.inventoryMenu.containerId, menuSlot, OFFHAND_BUTTON, ContainerInput.SWAP, player);
		emptyTicks = 0;
	}

	/** Backpack first, so the hotbar keeps its layout; the hotbar only when nothing else is left. */
	private static int findTotem(final Inventory inventory) {
		for (int slot = 9; slot <= 35; slot++) {
			if (inventory.getItem(slot).has(DataComponents.DEATH_PROTECTION)) {
				return slot;
			}
		}

		for (int slot = 0; slot <= 8; slot++) {
			if (inventory.getItem(slot).has(DataComponents.DEATH_PROTECTION)) {
				return slot;
			}
		}

		return -1;
	}

	/** How many totems we carry, offhand included, for the status line. */
	public static int count(final LocalPlayer player) {
		int count = player.getOffhandItem().has(DataComponents.DEATH_PROTECTION) ? 1 : 0;

		for (int slot = 0; slot <= 35; slot++) {
			ItemStack stack = player.getInventory().getItem(slot);

			if (stack.has(DataComponents.DEATH_PROTECTION)) {
				count += stack.getCount();
			}
		}

		return count;
	}
}
