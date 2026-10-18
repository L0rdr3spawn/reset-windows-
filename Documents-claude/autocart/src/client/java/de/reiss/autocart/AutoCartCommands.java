package de.reiss.autocart;

import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.brigadier.arguments.DoubleArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.fabricmc.fabric.api.client.command.v2.ClientCommands;
import net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;

import java.util.function.BiConsumer;

/**
 * Client-side commands, so everything is reachable without a spare key.
 *
 * <p>These never reach the server: Fabric dispatches them locally and swallows the chat line.
 */
public final class AutoCartCommands {
	private AutoCartCommands() {
	}

	public static void register(final AutoCartClient mod) {
		ClientCommandRegistrationCallback.EVENT.register((dispatcher, access) -> dispatcher.register(
				ClientCommands.literal("autocart")
						.executes(context -> run(mod, context, AutoCartClient.Request.FULL))
						.then(ClientCommands.literal("run")
								.executes(context -> run(mod, context, AutoCartClient.Request.FULL)))
						.then(ClientCommands.literal("rail")
								.executes(context -> run(mod, context, AutoCartClient.Request.RAIL)))
						.then(ClientCommands.literal("cart")
								.executes(context -> run(mod, context, AutoCartClient.Request.CART)))
						.then(ClientCommands.literal("fire")
								.executes(context -> run(mod, context, AutoCartClient.Request.FIRE)))
						.then(ClientCommands.literal("shoot")
								.executes(context -> run(mod, context, AutoCartClient.Request.SHOOT)))
						.then(ClientCommands.literal("load")
								.executes(context -> run(mod, context, AutoCartClient.Request.LOAD)))
						.then(ClientCommands.literal("check")
								.executes(context -> {
									mod.diagnose(line -> reply(context, line));
									return 1;
								}))
						.then(ClientCommands.literal("status")
								.executes(context -> status(mod, context)))
						.then(ClientCommands.literal("reload")
								.executes(context -> {
									mod.reloadConfig();
									applyKey(mod);
									reply(context, "config reloaded from disk");
									return 1;
								}))
						.then(ClientCommands.literal("key")
								.then(ClientCommands.argument("name", StringArgumentType.word())
										.executes(context -> setKey(mod, context,
												StringArgumentType.getString(context, "name")))))
						.then(ClientCommands.literal("set")
								.then(ClientCommands.literal("weapon")
										.then(ClientCommands.literal("crossbow")
												.executes(context -> setWeapon(mod, context, "crossbow")))
										.then(ClientCommands.literal("bow")
												.executes(context -> setWeapon(mod, context, "bow"))))
								.then(ClientCommands.literal("aimat")
										.then(ClientCommands.literal("cart")
												.executes(context -> setAim(mod, context, "cart")))
										.then(ClientCommands.literal("target")
												.executes(context -> setAim(mod, context, "target"))))
								.then(boolOption(mod, "advantage",
										(config, value) -> config.requireAdvantage = value))
								.then(boolOption(mod, "ownpop",
										(config, value) -> config.allowOwnPop = value))
								.then(boolOption(mod, "coverafter",
										(config, value) -> config.coverAfterShot = value))
								.then(boolOption(mod, "autototem",
										(config, value) -> config.autoTotem = value))
								.then(boolOption(mod, "totemreplace",
										(config, value) -> config.totemReplaceOffhand = value))
								.then(intOption(mod, "retries", 0, 5,
										(config, value) -> config.retries = value))
								.then(intOption(mod, "misstimeout", 3, 40,
										(config, value) -> config.missTimeoutTicks = value))
								.then(boolOption(mod, "burst",
										(config, value) -> config.burst = value))
								.then(boolOption(mod, "shootfirst",
										(config, value) -> config.shootFirst = value))
								.then(boolOption(mod, "railattarget",
										(config, value) -> config.railAtTarget = value))
								.then(boolOption(mod, "preload",
										(config, value) -> config.preload = value))
								.then(boolOption(mod, "refill",
										(config, value) -> config.refillFromInventory = value))
								.then(boolOption(mod, "placerail",
										(config, value) -> config.placeRail = value))
								.then(boolOption(mod, "placecart",
										(config, value) -> config.placeCart = value))
								.then(boolOption(mod, "placefire",
										(config, value) -> config.placeFire = value))
								.then(boolOption(mod, "shootcrossbow",
										(config, value) -> config.shootCrossbow = value))
								.then(boolOption(mod, "loadcrossbow",
										(config, value) -> config.loadCrossbow = value))
								.then(boolOption(mod, "cover",
										(config, value) -> config.placeCover = value))
								.then(intOption(mod, "coverheight", 1, 3,
										(config, value) -> config.coverHeight = value))
								.then(boolOption(mod, "safehealth",
										(config, value) -> config.safeHealth = value))
								.then(doubleOption(mod, "healthbuffer", 0.0, 20.0,
										(config, value) -> config.healthBuffer = value))
								.then(doubleOption(mod, "blastpower", 1.0, 16.0,
										(config, value) -> config.blastPower = value))
								.then(boolOption(mod, "aimatblocks",
										(config, value) -> config.aimAtBlocks = value))
								.then(boolOption(mod, "requiretarget",
										(config, value) -> config.requireTarget = value))
								.then(boolOption(mod, "returnslot",
										(config, value) -> config.returnToStartSlot = value))
								.then(boolOption(mod, "debug",
										(config, value) -> config.debugMessages = value))
								.then(doubleOption(mod, "minselfdistance", 0.0, 4.5,
										(config, value) -> config.minSelfDistance = value))
								.then(doubleOption(mod, "standoff", 0.0, 4.0,
										(config, value) -> config.targetStandoff = value))
								.then(doubleOption(mod, "firegap", 0.0, 3.0,
										(config, value) -> config.fireGap = value))
								.then(doubleOption(mod, "firedistance", 1.0, 4.5,
										(config, value) -> config.fireDistance = value))
								.then(doubleOption(mod, "raildistance", 1.0, 4.5,
										(config, value) -> config.railDistance = value))
								.then(doubleOption(mod, "railradius", 1.0, 4.5,
										(config, value) -> config.railSearchRadius = value))
								.then(doubleOption(mod, "preloadrange", 0.0, 32.0,
										(config, value) -> config.preloadSafeRange = value))
								.then(intOption(mod, "stepdelay", 1, 40,
										(config, value) -> config.stepDelayTicks = value))
								.then(intOption(mod, "chargeextra", 0, 40,
										(config, value) -> config.chargeExtraTicks = value))
								.then(intOption(mod, "bowdraw", 1, 60,
										(config, value) -> config.bowDrawTicks = value))
								.then(intOption(mod, "refillslot", 0, 8,
										(config, value) -> config.refillSlot = value)))));
	}

	/** Applies the key from the config to the actual mapping and saves the game options. */
	public static void applyKey(final AutoCartClient mod) {
		Minecraft minecraft = Minecraft.getInstance();
		KeyMapping mapping = mod.comboKey();

		if (minecraft == null || mapping == null) {
			return;
		}

		InputConstants.Key key = InputConstants.getKey(mod.config().keyId());
		mapping.setKey(key);
		KeyMapping.resetMapping();
		minecraft.options.save();
	}

	private static int setKey(
			final AutoCartClient mod,
			final CommandContext<FabricClientCommandSource> context,
			final String name) {
		AutoCartConfig config = mod.config();
		String previous = config.key;
		config.key = name;

		try {
			InputConstants.getKey(config.keyId());
		} catch (IllegalArgumentException e) {
			config.key = previous;
			reply(context, "no key called " + name + ", try b, j, or key.mouse.4");
			return 0;
		}

		config.save();
		applyKey(mod);
		reply(context, "key = " + config.keyId());
		return 1;
	}

	private static int run(
			final AutoCartClient mod,
			final CommandContext<FabricClientCommandSource> context,
			final AutoCartClient.Request request) {
		if (!mod.request(request)) {
			reply(context, "a combo is already running");
			return 0;
		}

		return 1;
	}

	private static int status(final AutoCartClient mod, final CommandContext<FabricClientCommandSource> context) {
		AutoCartConfig config = mod.config();

		reply(context, "key=" + config.keyId()
				+ ", weapon=" + config.weapon
				+ ", burst=" + config.burst
				+ ", shootFirst=" + config.shootFirst
				+ ", rail=" + config.placeRail + (config.railAtTarget ? " at target" : " at " + config.railDistance)
				+ ", cart=" + config.placeCart
				+ ", fire=" + config.placeFire + " gap " + config.fireGap
				+ ", standoff=" + config.targetStandoff
				+ ", minSelf=" + config.minSelfDistance
				+ ", cover=" + config.placeCover + " x" + config.coverHeight
				+ ", safeHealth=" + config.safeHealth + " buffer " + config.healthBuffer
				+ ", advantage=" + config.requireAdvantage
				+ ", ownPop=" + config.allowOwnPop
				+ ", retries=" + config.retries + " after " + config.missTimeoutTicks + " ticks"
				+ ", coverAfter=" + config.coverAfterShot
				+ ", autoTotem=" + config.autoTotem + (config.totemReplaceOffhand ? " (replaces offhand)" : "")
				+ ", preload=" + config.preload + " beyond " + config.preloadSafeRange
				+ ", refill=" + config.refillFromInventory + " into slot " + config.refillSlot
				+ ", aimAt=" + config.aimAt
				+ ", stepDelay=" + config.stepDelayTicks
				+ ", requireTarget=" + config.requireTarget + ", aimAtBlocks=" + config.aimAtBlocks
				+ ", debug=" + config.debugMessages);
		return 1;
	}

	private static int setAim(
			final AutoCartClient mod,
			final CommandContext<FabricClientCommandSource> context,
			final String value) {
		mod.config().aimAt = value;
		mod.config().save();
		reply(context, "aimAt = " + value);
		return 1;
	}

	private static int setWeapon(
			final AutoCartClient mod,
			final CommandContext<FabricClientCommandSource> context,
			final String value) {
		mod.config().weapon = value;
		mod.config().save();
		reply(context, "weapon = " + value);
		return 1;
	}

	private static LiteralArgumentBuilder<FabricClientCommandSource> doubleOption(
			final AutoCartClient mod,
			final String name,
			final double min,
			final double max,
			final BiConsumer<AutoCartConfig, Double> setter) {
		return ClientCommands.literal(name)
				.then(ClientCommands.argument("value", DoubleArgumentType.doubleArg(min, max))
						.executes(context -> {
							double value = DoubleArgumentType.getDouble(context, "value");
							setter.accept(mod.config(), value);
							mod.config().save();
							reply(context, name + " = " + value);
							return 1;
						}));
	}

	private static LiteralArgumentBuilder<FabricClientCommandSource> intOption(
			final AutoCartClient mod,
			final String name,
			final int min,
			final int max,
			final BiConsumer<AutoCartConfig, Integer> setter) {
		return ClientCommands.literal(name)
				.then(ClientCommands.argument("value", IntegerArgumentType.integer(min, max))
						.executes(context -> {
							int value = IntegerArgumentType.getInteger(context, "value");
							setter.accept(mod.config(), value);
							mod.config().save();
							reply(context, name + " = " + value);
							return 1;
						}));
	}

	private static LiteralArgumentBuilder<FabricClientCommandSource> boolOption(
			final AutoCartClient mod,
			final String name,
			final BiConsumer<AutoCartConfig, Boolean> setter) {
		return ClientCommands.literal(name)
				.then(ClientCommands.argument("value", BoolArgumentType.bool())
						.executes(context -> {
							boolean value = BoolArgumentType.getBool(context, "value");
							setter.accept(mod.config(), value);
							mod.config().save();
							reply(context, name + " = " + value);
							return 1;
						}));
	}

	private static void reply(final CommandContext<FabricClientCommandSource> context, final String text) {
		context.getSource().sendFeedback(Component.literal("autocart: " + text));
	}
}
