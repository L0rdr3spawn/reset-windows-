package de.reiss.botlink.mixin;

import de.reiss.botlink.BotLinkClient;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Leuchtfarbe des Bots: tuerkis (sonst weiss bzw. Teamfarbe). */
@Mixin(Entity.class)
public class EntityMixin {
	@Inject(method = "getTeamColor", at = @At("HEAD"), cancellable = true)
	private void botlink$botFarbe(CallbackInfoReturnable<Integer> cir) {
		if (BotLinkClient.istBot((Entity) (Object) this)) cir.setReturnValue(0x55FFFF);
	}
}
