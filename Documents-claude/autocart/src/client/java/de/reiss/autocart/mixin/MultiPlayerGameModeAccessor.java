package de.reiss.autocart.mixin;

import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/**
 * Flushes the pending "held slot changed" packet immediately instead of waiting for the next
 * MultiPlayerGameMode#tick.
 *
 * <p>Every step of the combo switches the hotbar slot and then uses the item in the same client
 * tick. MultiPlayerGameMode#tick has already run by then, so without this flush the server would
 * still believe the previous slot is held and would resolve the use packet against the wrong item.
 */
@Mixin(MultiPlayerGameMode.class)
public interface MultiPlayerGameModeAccessor {
	@Invoker("ensureHasSentCarriedItem")
	void autocart$ensureHasSentCarriedItem();
}
