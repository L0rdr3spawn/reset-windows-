package de.reiss.attrswap;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.equipment.Equippable;

/**
 * Swaps a worn glider for a chestplate from the hotbar without opening the inventory.
 *
 * <p>{@code MaceItem.canSmashAttack} refuses to smash while {@code isFallFlying()}, and that
 * is shared flag 7, not something derived from the worn item. Only {@code updateFallFlying}
 * clears it, and that runs in the entity tick, so the swap has to land at least one tick
 * before the mace hit. See {@link AttrSwapClient} for the timing.
 */
public final class ElytraSwap {
	/** InventoryMenu slots: 0 crafting result, 1-4 grid, 5-8 armor (head, chest, legs, feet). */
	private static final int CHEST_ARMOR_MENU_SLOT = 6;

	private ElytraSwap() {
	}

	public static boolean isWearingGlider(final LocalPlayer player) {
		return LivingEntity.canGlideUsing(player.getItemBySlot(EquipmentSlot.CHEST), EquipmentSlot.CHEST);
	}

	/**
	 * @param configuredSlot hotbar slot to take the chestplate from, or -1 to search the hotbar
	 * @return the hotbar slot holding a usable chestplate, or -1 if there is none
	 */
	public static int findChestplate(final LocalPlayer player, final int configuredSlot) {
		Inventory inventory = player.getInventory();

		if (configuredSlot >= 0 && configuredSlot <= 8) {
			return isChestplate(inventory.getItem(configuredSlot)) ? configuredSlot : -1;
		}

		for (int slot = 0; slot <= 8; slot++) {
			if (isChestplate(inventory.getItem(slot))) {
				return slot;
			}
		}

		return -1;
	}

	private static boolean isChestplate(final ItemStack stack) {
		Equippable equippable = stack.get(DataComponents.EQUIPPABLE);
		// A second elytra would equip fine and keep us gliding, so exclude gliders.
		return equippable != null && equippable.slot() == EquipmentSlot.CHEST && !stack.has(DataComponents.GLIDER);
	}

	/**
	 * Sends the same container interaction the inventory screen would send for a hotbar swap.
	 * The player's own menu stays open behind every screen, so this works with no GUI showing.
	 */
	public static boolean perform(final Minecraft minecraft, final LocalPlayer player, final int hotbarSlot) {
		MultiPlayerGameMode gameMode = minecraft.gameMode;

		if (gameMode == null) {
			return false;
		}

		AbstractContainerMenu menu = player.containerMenu;

		// If a real screen is open the server is tracking that menu instead; don't fight it.
		if (menu != player.inventoryMenu) {
			return false;
		}

		gameMode.handleContainerInput(menu.containerId, CHEST_ARMOR_MENU_SLOT, hotbarSlot, ContainerInput.SWAP, player);
		return true;
	}
}
