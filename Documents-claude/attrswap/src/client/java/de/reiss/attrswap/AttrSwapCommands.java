package de.reiss.attrswap;

import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.builder.RequiredArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.fabricmc.fabric.api.client.command.v2.ClientCommands;
import net.fabricmc.fabric.api.client.command.v2.FabricClientCommandSource;
import net.minecraft.network.chat.Component;

import java.util.function.BiConsumer;

/**
 * Client-side commands, so the slots can be changed in game instead of editing the JSON and
 * restarting. Fabric dispatches these locally; they never reach the server.
 *
 * <p>Slots are typed the way the hotbar is labelled, 1 to 9, and stored 0 to 8.
 */
public final class AttrSwapCommands {
	private AttrSwapCommands() {
	}

	public static void register(final AttrSwapClient mod) {
		ClientCommandRegistrationCallback.EVENT.register((dispatcher, access) -> dispatcher.register(
				ClientCommands.literal("attrswap")
						.executes(context -> status(mod, context))
						.then(ClientCommands.literal("status")
								.executes(context -> status(mod, context)))
						.then(ClientCommands.literal("reload")
								.executes(context -> {
									mod.reloadConfig();
									reply(context, "config reloaded from disk");
									return 1;
								}))
						.then(ClientCommands.literal("set")
								.then(ClientCommands.literal("mode")
										.then(modeOption(mod, AttrSwapConfig.MODE_SINGLE))
										.then(modeOption(mod, AttrSwapConfig.MODE_DOUBLE)))
								.then(ClientCommands.literal("first")
										.then(ClientCommands.literal("current")
												.executes(context -> {
													mod.config().firstSlot = -1;
													return saved(mod, context, "first = current slot");
												}))
										.then(slotArgument(mod, (config, slot) -> config.firstSlot = slot, "first")))
								.then(ClientCommands.literal("second")
										.then(slotArgument(mod, (config, slot) -> config.secondSlot = slot, "second")))
								.then(ClientCommands.literal("chestplate")
										.then(ClientCommands.literal("search")
												.executes(context -> {
													mod.config().chestplateSlot = -1;
													return saved(mod, context, "chestplate = search the hotbar");
												}))
										.then(slotArgument(mod, (config, slot) -> config.chestplateSlot = slot, "chestplate")))
								.then(ClientCommands.literal("elytralead")
										.then(ClientCommands.argument("ticks", IntegerArgumentType.integer(0, 20))
												.executes(context -> {
													int ticks = IntegerArgumentType.getInteger(context, "ticks");
													mod.config().elytraSwapLeadTicks = ticks;
													return saved(mod, context, "elytralead = " + ticks);
												})))
								.then(ClientCommands.literal("lungerest")
										.then(ClientCommands.literal("auto")
												.executes(context -> {
													mod.config().lungeRestSlot = -1;
													return saved(mod, context, "lungerest = auto (empty slot, wind charge, totem...)");
												}))
										.then(slotArgument(mod, (config, slot) -> config.lungeRestSlot = slot, "lungerest")))
								.then(ClientCommands.literal("lungeticks")
										.then(ClientCommands.argument("ticks", IntegerArgumentType.integer(0, 20))
												.executes(context -> {
													int ticks = IntegerArgumentType.getInteger(context, "ticks");
													mod.config().lungeRestTicks = ticks;
													return saved(mod, context, "lungeticks = " + ticks);
												})))
								.then(boolOption(mod, "lungereturnrest", (config, value) -> config.lungeReturnToRest = value))
								.then(boolOption(mod, "auto", (config, value) -> config.autoPick = value))
								.then(boolOption(mod, "onclick", (config, value) -> config.onClick = value))
								.then(boolOption(mod, "swapback", (config, value) -> config.swapBack = value))
								.then(boolOption(mod, "requiretarget", (config, value) -> config.requireTarget = value))
								.then(boolOption(mod, "elytra", (config, value) -> config.swapElytra = value))
								.then(boolOption(mod, "debug", (config, value) -> config.debugMessages = value)))));
	}

	private static int status(final AttrSwapClient mod, final CommandContext<FabricClientCommandSource> context) {
		AttrSwapConfig config = mod.config();

		reply(context, "mode=" + config.mode
				+ ", auto=" + config.autoPick
				+ ", onclick=" + config.onClick
				+ ", first=" + (config.firstSlot < 0 || !config.isDoubleMode() ? "current" : config.firstSlot + 1)
				+ ", second=" + (config.secondSlot + 1)
				+ ", swapBack=" + config.swapBack
				+ ", requireTarget=" + config.requireTarget
				+ ", elytra=" + config.swapElytra
				+ " (chestplate " + (config.chestplateSlot < 0 ? "search" : config.chestplateSlot + 1)
				+ ", lead " + config.elytraSwapLeadTicks + " ticks)"
				+ ", lunge: rest " + (config.lungeRestSlot < 0 ? "auto" : config.lungeRestSlot + 1)
				+ " for " + config.lungeRestTicks + " ticks, back to " + (config.lungeReturnToRest ? "rest" : "previous")
				+ ", debug=" + config.debugMessages);
		return 1;
	}

	private static RequiredArgumentBuilder<FabricClientCommandSource, Integer> slotArgument(
			final AttrSwapClient mod,
			final BiConsumer<AttrSwapConfig, Integer> setter,
			final String name) {
		return ClientCommands.argument("slot", IntegerArgumentType.integer(1, 9))
				.executes(context -> {
					int slot = IntegerArgumentType.getInteger(context, "slot");
					setter.accept(mod.config(), slot - 1);
					return saved(mod, context, name + " = slot " + slot);
				});
	}

	private static LiteralArgumentBuilder<FabricClientCommandSource> modeOption(final AttrSwapClient mod, final String mode) {
		return ClientCommands.literal(mode)
				.executes(context -> {
					mod.config().mode = mode;
					return saved(mod, context, "mode = " + mode);
				});
	}

	private static LiteralArgumentBuilder<FabricClientCommandSource> boolOption(
			final AttrSwapClient mod,
			final String name,
			final BiConsumer<AttrSwapConfig, Boolean> setter) {
		return ClientCommands.literal(name)
				.then(ClientCommands.argument("value", BoolArgumentType.bool())
						.executes(context -> {
							boolean value = BoolArgumentType.getBool(context, "value");
							setter.accept(mod.config(), value);
							return saved(mod, context, name + " = " + value);
						}));
	}

	private static int saved(
			final AttrSwapClient mod,
			final CommandContext<FabricClientCommandSource> context,
			final String text) {
		mod.config().save();
		reply(context, text);
		return 1;
	}

	private static void reply(final CommandContext<FabricClientCommandSource> context, final String text) {
		context.getSource().sendFeedback(Component.literal("attrswap: " + text));
	}
}
