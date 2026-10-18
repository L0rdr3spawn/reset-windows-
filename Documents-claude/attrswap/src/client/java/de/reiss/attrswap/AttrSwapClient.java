package de.reiss.attrswap;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Drives the combo as a small state machine.
 *
 * <p>Slot switches and attacks always run inside one invocation of {@link AttrSwap#run}, so they
 * are in the same client tick by construction; there is no path that spreads them over two ticks.
 * The elytra swap is the one thing that cannot share that tick, because the server only drops
 * the fall-flying flag in the entity tick after the chestplate has arrived.
 */
public class AttrSwapClient implements ClientModInitializer {
	public static final String MOD_ID = "attrswap";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	private static final KeyMapping.Category CATEGORY =
			KeyMapping.Category.register(Identifier.fromNamespaceAndPath(MOD_ID, "swap"));

	private static AttrSwapClient instance;

	private AttrSwapConfig config;
	private KeyMapping swapKey;
	private KeyMapping lungeKey;
	private final SpearLunge spearLunge = new SpearLunge();

	/** Ticks until the pending combo fires, or 0 when nothing is pending. */
	private int pendingComboTicks;

	@Override
	public void onInitializeClient() {
		instance = this;
		config = AttrSwapConfig.load();

		swapKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.attrswap.swap",
				InputConstants.Type.KEYBOARD,
				InputConstants.KEY_V,
				CATEGORY
		));

		lungeKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.attrswap.lunge",
				InputConstants.Type.KEYBOARD,
				InputConstants.KEY_R,
				CATEGORY
		));

		ClientTickEvents.END_CLIENT_TICK.register(this::onEndTick);
		AttrSwapCommands.register(this);

		LOGGER.info("Attribute Swap ready: auto={}, onClick={}, {} mode, slot {} -> {}, swapBack={}, swapElytra={} (lead {} ticks)",
				config.autoPick, config.onClick, config.mode, config.firstSlot < 0 ? "current" : config.firstSlot,
				config.secondSlot, config.swapBack, config.swapElytra, config.elytraSwapLeadTicks);
	}

	/** The loaded mod, for mixins. Null before client init. */
	public static AttrSwapClient instance() {
		return instance;
	}

	/** The lunge logic, for the game test. */
	public SpearLunge spearLunge() {
		return spearLunge;
	}

	public AttrSwapConfig config() {
		return config;
	}

	public void reloadConfig() {
		config = AttrSwapConfig.load();
	}

	private void onEndTick(final Minecraft minecraft) {
		LocalPlayer player = minecraft.player;

		if (player == null) {
			pendingComboTicks = 0;
			return;
		}

		spearLunge.tick(minecraft, config);

		while (lungeKey.consumeClick()) {
			spearLunge.start(minecraft, config);
		}

		boolean pressed = false;

		// consumeClick drains every press queued since the last tick. One combo per tick is
		// the most the game can act on, so collapse them.
		while (swapKey.consumeClick()) {
			pressed = true;
		}

		if (pendingComboTicks > 0) {
			pendingComboTicks--;

			if (pendingComboTicks == 0) {
				AttrSwap.run(minecraft, config);
			}

			// Ignore new presses while a combo is already in flight.
			return;
		}

		if (!pressed) {
			return;
		}

		if (config.swapElytra && ElytraSwap.isWearingGlider(player)) {
			int chestplateSlot = ElytraSwap.findChestplate(player, config.chestplateSlot);

			if (chestplateSlot < 0) {
				report(player, "attrswap: elytra on, no chestplate in the hotbar");
			} else if (ElytraSwap.perform(minecraft, player, chestplateSlot)) {
				report(player, "attrswap: elytra -> chestplate from slot " + chestplateSlot);

				if (config.elytraSwapLeadTicks > 0) {
					pendingComboTicks = config.elytraSwapLeadTicks;
					return;
				}
			}
		}

		AttrSwap.run(minecraft, config);
	}

	private void report(final LocalPlayer player, final String text) {
		if (config.debugMessages) {
			player.sendOverlayMessage(Component.literal(text));
		}
	}
}
