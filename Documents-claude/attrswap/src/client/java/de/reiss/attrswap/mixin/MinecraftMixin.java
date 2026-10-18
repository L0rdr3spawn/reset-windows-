package de.reiss.attrswap.mixin;

import de.reiss.attrswap.AttrSwap;
import de.reiss.attrswap.AttrSwapClient;
import de.reiss.attrswap.AttrSwapConfig;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Lets an ordinary left click at an entity run the auto pick, see {@link AttrSwapConfig#onClick}.
 * Hooked in front of vanilla's own attack so the swap replaces the click instead of adding a hit.
 */
@Mixin(Minecraft.class)
public abstract class MinecraftMixin {
	@Shadow
	protected int missTime;

	@Inject(method = "startAttack", at = @At("HEAD"), cancellable = true)
	private void attrswap$swapOnClick(final CallbackInfoReturnable<Boolean> cir) {
		AttrSwapClient mod = AttrSwapClient.instance();

		if (mod == null || this.missTime > 0) {
			return;
		}

		AttrSwapConfig config = mod.config();

		if (config.onClick && config.autoPick && AttrSwap.runOnClick((Minecraft) (Object) this, config)) {
			// Same answer vanilla gives after hitting an entity: the attack did not end a block break.
			cir.setReturnValue(false);
		}
	}
}
