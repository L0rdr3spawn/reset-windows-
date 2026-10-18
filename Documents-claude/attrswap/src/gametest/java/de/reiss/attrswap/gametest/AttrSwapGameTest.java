package de.reiss.attrswap.gametest;

import de.reiss.attrswap.AttrSwap;
import de.reiss.attrswap.AttrSwapClient;
import de.reiss.attrswap.AttrSwapConfig;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.Minecraft;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemStack;
import net.minecraft.network.protocol.game.ServerboundPunchPacket;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.EntityHitResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.function.Consumer;

/**
 * Drops the player onto a 1000 HP pig and measures how much damage each way of swinging deals.
 * The integrated server is vanilla, which matches Paper with update-equipment-on-player-actions: false.
 */
public class AttrSwapGameTest implements FabricClientGameTest {
	private static final Logger LOGGER = LoggerFactory.getLogger("attrswap-gametest");
	private static final int SWORD = 0;
	private static final int MACE = 1;
	private static final double FALL_FROM = 208.0;

	@Override
	public void runTest(final ClientGameTestContext context) {
		try (TestSingleplayerContext singleplayer = context.worldBuilder().create()) {
			TestServerContext server = singleplayer.getServer();
			context.waitFor(mc -> mc.player != null && mc.level != null);

			server.runCommand("gamemode survival @a");
			server.runCommand("fill -3 199 -3 3 199 3 minecraft:stone");
			server.runCommand("effect give @a minecraft:resistance infinite 4 true");
			server.runCommand("effect give @a minecraft:saturation infinite 0 true");
			server.runCommand("item replace entity @a hotbar.0 with minecraft:netherite_sword");
			server.runCommand("item replace entity @a hotbar.1 with minecraft:mace");
			server.runCommand("item replace entity @a hotbar.2 with minecraft:iron_axe");

			StringBuilder report = new StringBuilder("\n==== attrswap damage (1000 HP pig, fall from " + (FALL_FROM - 200) + " blocks) ====\n");

			AttrSwapConfig live = AttrSwapClient.instance().config();
			live.onClick = false;

			float sword = scenario(context, server, report, "sword alone", SWORD, true, onClient(AttrSwapGameTest::plainAttack));
			float mace = scenario(context, server, report, "mace alone", MACE, true, onClient(AttrSwapGameTest::plainAttack));
			float doubleHit = scenario(context, server, report, "attrswap double (sword -> mace)", SWORD, true,
					onClient(mc -> AttrSwap.run(mc, config(AttrSwapConfig.MODE_DOUBLE))));
			float single = scenario(context, server, report, "attrswap single (hold sword, hit with mace)", SWORD, true,
					onClient(mc -> AttrSwap.run(mc, config(AttrSwapConfig.MODE_SINGLE))));
			int heldAfter = context.computeOnClient(mc -> mc.player.getInventory().getSelectedSlot());

			// Auto pick: the configured slot is the axe, but falling means the mace is the right call.
			float autoKey = scenario(context, server, report, "auto via key (configured slot = axe)", SWORD, true,
					onClient(mc -> {
						AttrSwapConfig config = config(AttrSwapConfig.MODE_SINGLE);
						config.secondSlot = 2;
						config.autoPick = true;
						AttrSwap.run(mc, config);
					}));

			// A real left click, through vanilla's input handling and the startAttack hook.
			live.onClick = true;
			live.autoPick = true;
			float clickFalling = scenario(context, server, report, "left click while falling (onclick)", SWORD, true,
					ctx -> ctx.getInput().pressKey(options -> options.keyAttack));
			int heldAfterClick = context.computeOnClient(mc -> mc.player.getInventory().getSelectedSlot());
			float clickStanding = scenario(context, server, report, "left click standing (must stay vanilla)", SWORD, false,
					ctx -> ctx.getInput().pressKey(options -> options.keyAttack));
			live.onClick = false;

			LOGGER.info(report.toString());

			check(mace > sword, "mace smash did not land (mace " + mace + " vs sword " + sword + ")");
			check(doubleHit > sword, "double mode second hit added nothing (" + doubleHit + ")");
			check(single > mace, "single mode should beat the plain mace (" + single + " vs " + mace + ")");
			check(heldAfter == SWORD, "single mode did not switch back to the sword");
			check(Math.abs(autoKey - single) < 0.5f, "auto pick did not choose the mace (" + autoKey + " vs " + single + ")");
			check(Math.abs(clickFalling - single) < 0.5f, "falling click did not smash (" + clickFalling + " vs " + single + ")");
			check(heldAfterClick == SWORD, "click swap did not switch back to the sword");
			check(Math.abs(clickStanding - 8.0f) < 0.5f, "standing click was not a plain sword hit (" + clickStanding + ")");

			// Spear lunge: slot 4 holds a Lunge III spear, slot 6 stays empty to charge on.
			server.runCommand("item replace entity @a hotbar.3 with minecraft:iron_spear[enchantments={\"minecraft:lunge\":3}]");
			server.runCommand("item replace entity @a hotbar.5 with minecraft:air");
			StringBuilder lunges = new StringBuilder("\n==== spear lunge (blocks moved forward) ====\n");

			double vanilla = lunge(context, server, lunges, "vanilla stab, spear just picked up", 3, 2, mc -> {
				ItemStack spear = mc.player.getMainHandItem();
				mc.gameMode.piercingAttack(spear.getAttackAnimation(), spear.get(DataComponents.PIERCING_WEAPON));
			});
			double fromSword = lunge(context, server, lunges, "lunge key from a charged sword", SWORD, 30,
					mc -> AttrSwapClient.instance().spearLunge().start(mc, AttrSwapClient.instance().config()));
			int afterSword = context.computeOnClient(mc -> mc.player.getInventory().getSelectedSlot());
			double fromSpear = lunge(context, server, lunges, "lunge key while holding the spear", 3, 2,
					mc -> AttrSwapClient.instance().spearLunge().start(mc, AttrSwapClient.instance().config()));
			int afterSpear = context.computeOnClient(mc -> mc.player.getInventory().getSelectedSlot());
			LOGGER.info(lunges.toString());

			check(vanilla < 0.5, "an uncharged vanilla stab should not lunge (" + vanilla + ")");
			check(fromSword > 1.5, "lunge from the sword did not move us (" + fromSword + ")");
			check(afterSword == SWORD, "lunge from the sword did not go back to the sword");
			check(fromSpear > 1.5, "lunge from the spear did not move us (" + fromSpear + ")");
			check(afterSpear == 3, "lunge from the spear did not end on the spear");
		}
	}

	private static AttrSwapConfig config(final String mode) {
		AttrSwapConfig config = new AttrSwapConfig();
		config.mode = mode;
		config.firstSlot = SWORD;
		config.secondSlot = MACE;
		config.swapBack = true;
		config.swapElytra = false;
		config.autoPick = false;
		return config;
	}

	private static void check(final boolean condition, final String message) {
		if (!condition) {
			throw new AssertionError(message);
		}
	}

	/** Stands still facing +z holding {@code slot} for {@code holdTicks}, triggers, and measures the push. */
	private static double lunge(
			final ClientGameTestContext context,
			final TestServerContext server,
			final StringBuilder report,
			final String name,
			final int slot,
			final int holdTicks,
			final Consumer<Minecraft> trigger) {
		server.runCommand("kill @e[tag=target]");
		server.runCommand("tp @a 0.5 200 -2.5 0 0");
		context.waitFor(mc -> mc.player.onGround(), 100);
		context.runOnClient(mc -> mc.player.getInventory().setSelectedSlot(slot));
		context.waitTicks(holdTicks);

		double startZ = server.computeOnServer(s -> s.getPlayerList().getPlayers().getFirst().getZ());
		context.runOnClient(trigger::accept);
		context.waitTicks(15);
		double moved = server.computeOnServer(s -> s.getPlayerList().getPlayers().getFirst().getZ()) - startZ;
		report.append(String.format("%-40s moved %5.2f%n", name, moved));
		return moved;
	}

	private static Consumer<ClientGameTestContext> onClient(final Consumer<Minecraft> action) {
		return ctx -> ctx.runOnClient(action::accept);
	}

	private static void plainAttack(final Minecraft mc) {
		Entity target = ((EntityHitResult) mc.hitResult).getEntity();
		mc.gameMode.attack(mc.player, target);
		mc.player.swing(InteractionHand.MAIN_HAND, mc.player.getMainHandItem().getAttackAnimation(), false);
		mc.player.connection.send(ServerboundPunchPacket.INSTANCE);
	}

	private static float scenario(
			final ClientGameTestContext context,
			final TestServerContext server,
			final StringBuilder report,
			final String name,
			final int heldSlot,
			final boolean falling,
			final Consumer<ClientGameTestContext> strike) {
		server.runCommand("kill @e[tag=target]");
		server.runCommand("summon minecraft:pig 0.5 200 0.5 {NoAI:1b,Silent:1b,Tags:[\"target\"],Health:1000.0f,"
				+ "attributes:[{id:\"minecraft:max_health\",base:1000.0},{id:\"minecraft:knockback_resistance\",base:1.0}]}");
		server.runCommand("tp @a 0.5 200 3.5");
		context.runOnClient(mc -> mc.player.getInventory().setSelectedSlot(heldSlot));
		// Full charge for every weapon (mace: 1 / 0.6 * 20 = 34 ticks).
		context.waitTicks(50);

		if (falling) {
			server.runCommand("tp @a 0.5 " + FALL_FROM + " 0.5 0 90");
			context.waitFor(mc -> mc.player.getY() < FALL_FROM - 1);
			context.waitFor(mc -> mc.player.getY() < 202.8 && mc.hitResult instanceof EntityHitResult, 100);
		} else {
			// Two blocks south of the pig, looking at its middle.
			server.runCommand("tp @a 0.5 200 -1.5 0 30");
			context.waitFor(mc -> mc.hitResult instanceof EntityHitResult, 100);
		}

		double y = context.computeOnClient(mc -> mc.player.getY());
		strike.accept(context);
		context.waitTicks(3);

		float health = server.computeOnServer(s -> {
			for (Entity entity : s.overworld().getAllEntities()) {
				if (entity.entityTags().contains("target") && entity instanceof LivingEntity living) {
					return living.getHealth();
				}
			}
			return Float.NaN;
		});

		context.waitFor(mc -> mc.player.onGround(), 100);
		float damage = 1000.0f - health;
		report.append(String.format("%-45s damage %6.2f  (struck at y=%.2f)%n", name, damage, y));
		return damage;
	}
}
