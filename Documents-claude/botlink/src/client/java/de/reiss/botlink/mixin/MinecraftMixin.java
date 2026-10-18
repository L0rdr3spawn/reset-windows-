package de.reiss.botlink.mixin;

import de.reiss.botlink.BotLinkClient;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Der Bot leuchtet in deinem Client immer (Umriss auch durch Waende) - nur bei dir, der Server merkt nichts. */
@Mixin(Minecraft.class)
public class MinecraftMixin {
	@Inject(method = "shouldEntityAppearGlowing", at = @At("HEAD"), cancellable = true)
	private void botlink$botLeuchtet(Entity entity, CallbackInfoReturnable<Boolean> cir) {
		if (BotLinkClient.istBot(entity)) cir.setReturnValue(true);
	}
}
