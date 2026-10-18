package de.reiss.jevbaritone.mixin;

import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Hotbar-Wechsel sofort an den Server schicken, sonst benutzt er beim naechsten Klick noch das alte Item. */
@Mixin(MultiPlayerGameMode.class)
public interface MultiPlayerGameModeAccessor {
	@Invoker("ensureHasSentCarriedItem")
	void jevbaritone$ensureHasSentCarriedItem();
}
