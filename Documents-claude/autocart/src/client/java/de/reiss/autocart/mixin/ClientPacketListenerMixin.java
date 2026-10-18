package de.reiss.autocart.mixin;

import de.reiss.autocart.AutoCartClient;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.network.protocol.game.ClientboundExplodePacket;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Tells the mod where an explosion went off and how strong it was. That is the only reliable sign
 * the cart blew up: a cart placed and blown up in the same server tick never shows up on the
 * client at all, and a missing cart can also mean an unlit arrow just knocked it off the rail.
 *
 * <p>At the tail, because the handler first bounces from the network thread to the main thread by
 * throwing; only the main-thread pass gets this far.
 */
@Mixin(ClientPacketListener.class)
public abstract class ClientPacketListenerMixin {
	@Inject(method = "handleExplosion", at = @At("TAIL"))
	private void autocart$recordExplosion(final ClientboundExplodePacket packet, final CallbackInfo ci) {
		AutoCartClient.recordExplosion(packet.center(), packet.radius());
	}
}
