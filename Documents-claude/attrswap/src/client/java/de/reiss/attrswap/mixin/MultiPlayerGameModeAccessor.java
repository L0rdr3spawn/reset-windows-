package de.reiss.attrswap.mixin;

import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/**
 * Flushes the pending "held slot changed" packet immediately instead of waiting for the
 * next MultiPlayerGameMode#tick, so a swap-back still lands inside the current tick.
 */
@Mixin(MultiPlayerGameMode.class)
public interface MultiPlayerGameModeAccessor {
	@Invoker("ensureHasSentCarriedItem")
	void attrswap$ensureHasSentCarriedItem();
}
