package de.reiss.autocart.gametest;

import de.reiss.autocart.AutoCartClient;
import de.reiss.autocart.AutoCartConfig;
import de.reiss.autocart.Blast;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.entrypoint.EntrypointContainer;
import net.minecraft.client.Minecraft;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.vehicle.minecart.MinecartTNT;
import net.minecraft.world.phys.HitResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Field;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Runs the combo in a real singleplayer world and traces, tick by tick, what the server sees: the
 * cart, the arrows, the husk's health. Every run gets its own patch of ground 40 blocks apart.
 */
public class AutoCartGameTest implements FabricClientGameTest {
	private static final Logger LOGGER = LoggerFactory.getLogger("autocart-gametest");
	private static final String EMPTY_CROSSBOW = "minecraft:crossbow";
	private static final String LOADED_CROSSBOW =
			"minecraft:crossbow[charged_projectiles=[{id:\"minecraft:arrow\",count:1}]]";
	private static final String ARMOURED =
			",equipment:{chest:{id:\"minecraft:netherite_chestplate\",count:1,"
					+ "components:{\"minecraft:enchantments\":{\"minecraft:protection\":4}}}}";

	private static int run;

	/** One run: how to set it up, what to expect. */
	private static final class Scenario {
		String name;
		String crossbow = LOADED_CROSSBOW;
		Consumer<AutoCartConfig> tweak = config -> {
		};
		double huskZ = 5.5;
		String huskExtra = "";
		/** Server commands with {x} for this run's x offset, run before the combo. */
		String[] before = {};
		/** Called on every sampled tick with (tick, server state). */
		BiConsumer<Integer, String> onTick = (tick, state) -> {
		};
		boolean expectBlast = true;
		boolean checkEstimate;
		/** The crosshair ends up on a cart past entity reach, which vanilla reports as a miss. */
		boolean crosshairOnCart;

		Scenario(final String name) {
			this.name = name;
		}
	}

	@Override
	public void runTest(final ClientGameTestContext context) {
		AutoCartClient mod = findMod();
		// Every step the mod reports goes to the log too, see AutoCartClient#report.
		org.apache.logging.log4j.core.config.Configurator.setLevel("autocart", org.apache.logging.log4j.Level.DEBUG);

		try (TestSingleplayerContext singleplayer = context.worldBuilder().create()) {
			TestServerContext server = singleplayer.getServer();
			context.waitFor(mc -> mc.player != null && mc.level != null);

			server.runCommand("gamemode survival @a");
			// Enough health to shrug off a point blank cart, so what the blast takes can be measured.
			server.runCommand("attribute @p minecraft:max_health base set 500");
			server.runCommand("effect give @a minecraft:saturation infinite 0 true");
			server.runCommand("forceload add -16 -16 460 31");
			server.waitFor(s -> s.overworld().isLoaded(new net.minecraft.core.BlockPos(440, 200, 14)), 1200);
			// Ground first everywhere, so no teleport ever lands the player over thin air.
			for (int x = 0; x <= 440; x += 40) {
				server.runCommand("fill " + (x - 6) + " 198 -4 " + (x + 6) + " 199 14 minecraft:stone");
			}

			StringBuilder report = new StringBuilder("\n==== autocart (crosshair on the ground 4 blocks out) ====\n");
			boolean ok = true;

			Scenario s;

			s = new Scenario("build first, empty crossbow");
			s.crossbow = EMPTY_CROSSBOW;
			s.tweak = config -> config.preload = false;
			ok &= scenario(context, server, mod, report, s);

			s = new Scenario("build first, loaded crossbow");
			ok &= scenario(context, server, mod, report, s);

			s = new Scenario("shoot first, loaded crossbow");
			s.tweak = config -> config.shootFirst = true;
			ok &= scenario(context, server, mod, report, s);

			s = new Scenario("burst, loaded crossbow");
			s.tweak = config -> config.burst = true;
			ok &= scenario(context, server, mod, report, s);

			s = new Scenario("burst, empty crossbow");
			s.crossbow = EMPTY_CROSSBOW;
			s.tweak = config -> {
				config.burst = true;
				config.preload = false;
			};
			ok &= scenario(context, server, mod, report, s);

			s = new Scenario("estimate vs real, armoured husk");
			s.huskExtra = ARMOURED;
			s.checkEstimate = true;
			// The armour makes the husk take less than unarmoured us; that trade is refused on purpose.
			s.tweak = config -> config.requireAdvantage = false;
			ok &= scenario(context, server, mod, report, s);

			s = new Scenario("no advantage: husk behind us -> abort");
			s.huskZ = -2.5;
			s.expectBlast = false;
			ok &= scenario(context, server, mod, report, s);

			s = new Scenario("cart already on the rail -> no second cart");
			s.before = new String[] {
					"setblock {x} 200 4 minecraft:rail",
					"summon minecraft:tnt_minecart {x}.5 200 4.5"
			};
			s.crosshairOnCart = true;
			ok &= scenario(context, server, mod, report, s);

			// A barrier soaks up the first arrow; it goes once the arrow sits in it, so the retry gets through.
			s = new Scenario("first shot blocked -> retry");
			s.before = new String[] {
					"setblock {x} 200 4 minecraft:rail",
					"summon minecraft:tnt_minecart {x}.5 200 4.5",
					"setblock {x} 200 3 minecraft:barrier"
			};
			s.crosshairOnCart = true;
			final int[] barrierX = {0};
			s.onTick = (tick, state) -> {
				if (state.contains("arrows=1") && barrierX[0] == 0) {
					barrierX[0] = 1;
					server.runCommand("fill -6 200 3 460 200 3 minecraft:air replace minecraft:barrier");
				}
			};
			ok &= scenario(context, server, mod, report, s);

			ok &= autoTotem(context, server, report);

			LOGGER.info(report.toString());

			if (!ok) {
				throw new AssertionError("at least one run did not do what it should, see the report above");
			}
		}
	}

	private static AutoCartClient findMod() {
		for (EntrypointContainer<ClientModInitializer> container
				: FabricLoader.getInstance().getEntrypointContainers("client", ClientModInitializer.class)) {
			if (container.getEntrypoint() instanceof AutoCartClient mod) {
				return mod;
			}
		}
		throw new AssertionError("AutoCartClient entrypoint not found");
	}

	private static boolean scenario(
			final ClientGameTestContext context,
			final TestServerContext server,
			final AutoCartClient mod,
			final StringBuilder report,
			final Scenario scenario) {
		int x = 40 * run++;
		server.runCommand("kill @e[type=!player]");
		server.runCommand("tp @a " + x + ".5 200 0.5 0 22");
		context.waitFor(mc -> mc.player.onGround() && Math.abs(mc.player.getX() - (x + 0.5)) < 0.01, 200);
		server.runCommand("fill " + (x - 6) + " 200 -4 " + (x + 6) + " 206 14 minecraft:air");
		server.runCommand("fill " + (x - 6) + " 198 -4 " + (x + 6) + " 199 14 minecraft:stone");
		server.runCommand("clear @a");
		server.runCommand("item replace entity @a hotbar.0 with minecraft:iron_sword");
		server.runCommand("item replace entity @a hotbar.1 with minecraft:rail 16");
		server.runCommand("item replace entity @a hotbar.3 with minecraft:flint_and_steel");
		server.runCommand("item replace entity @a hotbar.4 with " + scenario.crossbow);
		server.runCommand("item replace entity @a hotbar.5 with minecraft:cobblestone 32");
		server.runCommand("item replace entity @a inventory.0 with minecraft:arrow 32");
		// Carts only in the backpack: the mod has to fetch them.
		server.runCommand("item replace entity @a inventory.1 with minecraft:tnt_minecart");
		server.runCommand("item replace entity @a inventory.2 with minecraft:tnt_minecart");
		server.runCommand("summon minecraft:husk " + x + ".5 200 " + scenario.huskZ
				+ " {NoAI:1b,Silent:1b,PersistenceRequired:1b,Tags:[\"target\"],"
				+ "Health:1000.0f,attributes:[{id:\"minecraft:max_health\",base:1000.0},"
				+ "{id:\"minecraft:knockback_resistance\",base:1.0}]" + scenario.huskExtra + "}");

		for (String command : scenario.before) {
			server.runCommand(command.replace("{x}", String.valueOf(x)));
		}

		server.runCommand("tp @a " + x + ".5 200 0.5 0 22");
		server.runOnServer(s -> s.getPlayerList().getPlayers().forEach(p -> p.setHealth(p.getMaxHealth())));

		context.runOnClient(mc -> {
			mod.reloadConfig();
			// Our own survival is not what these runs test; the player has 500 health.
			mod.config().safeHealth = false;
			scenario.tweak.accept(mod.config());
			mc.player.getInventory().setSelectedSlot(0);
		});
		context.waitTicks(10);
		context.waitFor(mc -> mc.hitResult != null
				&& (scenario.crosshairOnCart || mc.hitResult.getType() == HitResult.Type.BLOCK), 200);

		boolean queued = context.computeOnClient(mc -> mod.request(AutoCartClient.Request.FULL));
		StringBuilder trace = new StringBuilder();
		String last = "";
		int maxCarts = 0;
		boolean blast = false;
		float startHealth = health(server);
		float playerStart = playerHealth(server);
		double[] estimate = null;

		for (int tick = 1; tick <= 160; tick++) {
			context.waitTick();
			String step = context.computeOnClient(mc -> step(mod));
			String state = server.computeOnServer(AutoCartGameTest::serverState);
			String line = "step=" + step + " " + state;

			if (!line.equals(last)) {
				trace.append(String.format("    t%-3d %s%n", tick, line));
				last = line;
			}

			maxCarts = Math.max(maxCarts, state.contains("cart=2") ? 2 : state.contains("cart=1") ? 1 : 0);
			scenario.onTick.accept(tick, state);

			if (scenario.checkEstimate && estimate == null) {
				estimate = context.computeOnClient(AutoCartGameTest::estimateNow);
			}

			if (!state.endsWith("husk=" + String.format("%.0f", startHealth))) {
				blast = true;
				trace.append(String.format("    t%-3d blast%n", tick));
				break;
			}

			if ("IDLE".equals(step) && tick > 3 && !scenario.expectBlast) {
				break;
			}
		}

		context.waitTicks(5);
		float lost = startHealth - health(server);
		float playerLost = playerStart - playerHealth(server);
		boolean ok = queued && blast == scenario.expectBlast && maxCarts <= 1;
		String estimateText = "";

		if (estimate != null) {
			boolean inRange = within(playerLost, estimate[0], estimate[1]) && within(lost, estimate[2], estimate[3]);
			ok &= inRange;
			estimateText = String.format(" | estimate you %.1f-%.1f, husk %.1f-%.1f%s",
					estimate[0], estimate[1], estimate[2], estimate[3], inRange ? "" : " OUT OF RANGE");
		}

		report.append(String.format("%s %-44s husk lost %.1f, you lost %.1f, most carts %d%s%n",
				ok ? "PASS" : "FAIL", scenario.name, lost, playerLost, maxCarts, estimateText));
		report.append(trace);

		context.waitFor(mc -> "IDLE".equals(step(mod)), 400);
		return ok;
	}

	/** One point either side: the server rounds before armour, we do not know which way. */
	private static boolean within(final double value, final double min, final double max) {
		return value >= min - 1.0 && value <= max + 1.0;
	}

	/** The mod's own numbers for the cart that is standing right now: you min/max, husk min/max. */
	private static double[] estimateNow(final Minecraft mc) {
		MinecartTNT cart = null;

		for (Entity entity : mc.level.entitiesForRendering()) {
			if (entity instanceof MinecartTNT found) {
				cart = found;
			}
		}

		if (cart == null) {
			return null;
		}

		LivingEntity husk = null;

		for (Entity entity : mc.level.entitiesForRendering()) {
			if (entity instanceof net.minecraft.world.entity.monster.zombie.Husk found) {
				husk = found;
			}
		}

		Blast.Power power = Blast.power(new AutoCartConfig());
		Blast.Spread you = Blast.spread(mc, mc.player, cart.position(), power);
		Blast.Spread them = Blast.spread(mc, husk, cart.position(), power);
		return new double[] {you.min(), you.max(), them.min(), them.max()};
	}

	/** Pops a totem with lethal damage and checks the next one lands in the offhand. */
	private static boolean autoTotem(final ClientGameTestContext context, final TestServerContext server, final StringBuilder report) {
		server.runCommand("kill @e[type=!player]");
		server.runCommand("clear @a");
		server.runCommand("item replace entity @a weapon.offhand with minecraft:totem_of_undying");
		server.runCommand("item replace entity @a inventory.5 with minecraft:totem_of_undying");
		server.runCommand("item replace entity @a inventory.6 with minecraft:totem_of_undying");
		context.waitTicks(10);
		server.runCommand("damage @p 2000 minecraft:generic");

		int waited = context.waitFor(mc -> mc.player.getOffhandItem().has(DataComponents.DEATH_PROTECTION)
				&& countTotems(mc) == 2, 40);
		context.waitTicks(5);
		boolean alive = context.computeOnClient(mc -> mc.player.isAlive());
		int left = context.computeOnClient(AutoCartGameTest::countTotems);
		boolean ok = alive && left == 2;
		report.append(String.format("%s %-44s refilled after %d ticks, alive %s, totems left %d%n",
				ok ? "PASS" : "FAIL", "auto totem after a pop", waited, alive, left));
		return ok;
	}

	private static int countTotems(final Minecraft mc) {
		int count = mc.player.getOffhandItem().has(DataComponents.DEATH_PROTECTION) ? 1 : 0;

		for (int slot = 0; slot <= 35; slot++) {
			if (mc.player.getInventory().getItem(slot).has(DataComponents.DEATH_PROTECTION)) {
				count += mc.player.getInventory().getItem(slot).getCount();
			}
		}

		return count;
	}

	private static String serverState(final MinecraftServer server) {
		int carts = 0;
		int arrows = 0;
		String fuse = "";
		String arrow = "";

		for (Entity entity : server.overworld().getAllEntities()) {
			if (entity instanceof MinecartTNT cart) {
				carts++;
				fuse = cart.isPrimed() ? " fuse=" + cart.getFuse() : "";
			} else if (entity instanceof AbstractArrow a) {
				arrows++;
				arrow = String.format(" arrow@%.1f,%.1f,%.1f%s", a.getX(), a.getY(), a.getZ(), a.isOnFire() ? " burning" : "");
			}
		}

		return String.format("cart=%d%s arrows=%d%s husk=%.0f", carts, fuse, arrows, arrow, health(server));
	}

	private static float playerHealth(final TestServerContext server) {
		return server.computeOnServer(s -> s.getPlayerList().getPlayers().getFirst().getHealth());
	}

	private static float health(final TestServerContext server) {
		return server.computeOnServer(AutoCartGameTest::health);
	}

	private static float health(final MinecraftServer server) {
		for (Entity entity : server.overworld().getAllEntities()) {
			if (entity.entityTags().contains("target") && entity instanceof LivingEntity living && living.isAlive()) {
				return living.getHealth();
			}
		}
		return Float.NaN;
	}

	private static String step(final AutoCartClient mod) {
		try {
			Field field = AutoCartClient.class.getDeclaredField("step");
			field.setAccessible(true);
			return String.valueOf(field.get(mod));
		} catch (ReflectiveOperationException e) {
			return "?";
		}
	}
}
