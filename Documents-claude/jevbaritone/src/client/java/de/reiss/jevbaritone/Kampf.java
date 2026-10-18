package de.reiss.jevbaritone;

import baritone.api.BaritoneAPI;
import baritone.api.pathing.goals.GoalNear;
import net.minecraft.client.Minecraft;
import net.minecraft.commands.arguments.EntityAnchorArgument;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import java.util.Comparator;
import java.util.function.Supplier;

/**
 * Beschuetzt den Besitzer: greift Monster in seiner oder der eigenen Naehe an, wie ein Spieler (volle Schlagkraft
 * abwarten, beste Waffe in der Hand). Creeper werden gemieden statt geschlagen. Unterbricht Baritone nur fuer den Kampf.
 */
final class Kampf {
	private static final double RADIUS = 14;
	private static final double REICHWEITE = 3.0;

	private final Minecraft mc = Minecraft.getInstance();
	private final Supplier<Player> besitzer;
	private final Runnable nachDemKampf;
	private boolean an = true;
	private LivingEntity ziel;
	private int jagdTicks;

	Kampf(Supplier<Player> besitzer, Runnable nachDemKampf) {
		this.besitzer = besitzer;
		this.nachDemKampf = nachDemKampf;
	}

	void setAn(boolean an) {
		this.an = an;
		if (!an) ziel = null;
	}

	boolean istAn() {
		return an;
	}

	/** Gerade im Kampf? Dann soll der Rest (Plan, Fertig-Meldung) warten. */
	boolean kaempft() {
		return ziel != null;
	}

	void tick() {
		if (!an || mc.player == null || mc.level == null || mc.gameMode == null) return;
		if (ziel != null && (!ziel.isAlive() || ziel.distanceTo(mc.player) > RADIUS * 1.5)) {
			ziel = null;
			BaritoneAPI.getProvider().getPrimaryBaritone().getCustomGoalProcess().setGoal(null);
			nachDemKampf.run();
		}
		if (ziel == null) {
			ziel = sucheZiel();
			jagdTicks = 0;
			if (ziel == null) return;
			JevBaritoneClient.LOG.info("Kampf: greife {} an", ziel.getName().getString());
		}

		waffeNehmen();
		double d = mc.player.distanceTo(ziel);
		mc.player.lookAt(EntityAnchorArgument.Anchor.EYES, ziel.getEyePosition());
		if (d <= REICHWEITE) {
			if (mc.player.getAttackStrengthScale(0.5f) >= 0.95f) {
				mc.gameMode.attack(mc.player, ziel);
				mc.player.swing(InteractionHand.MAIN_HAND);
			}
		} else if (jagdTicks++ % 10 == 0) {
			// Hinlaufen mit Baritone (klettert, springt, umgeht Hindernisse)
			BaritoneAPI.getProvider().getPrimaryBaritone().getCustomGoalProcess()
				.setGoalAndPath(new GoalNear(ziel.blockPosition(), 1));
		}
	}

	private LivingEntity sucheZiel() {
		Player b = besitzer.get();
		return mc.level.getEntitiesOfClass(LivingEntity.class, mc.player.getBoundingBox().inflate(RADIUS), e ->
				e instanceof Enemy && e.isAlive() && !(e instanceof Creeper)
					&& (e.distanceTo(mc.player) < 8 || (b != null && e.distanceTo(b) < 8)))
			.stream()
			.min(Comparator.comparingDouble(e -> e.distanceTo(mc.player)))
			.orElse(null);
	}

	/** Beste Nahkampfwaffe aus der Hotbar in die Hand. */
	private void waffeNehmen() {
		Inventory inv = mc.player.getInventory();
		int bester = -1;
		int besterRang = -1;
		for (int i = 0; i < 9; i++) {
			int r = rang(inv.getItem(i));
			if (r > besterRang) { besterRang = r; bester = i; }
		}
		if (bester >= 0 && besterRang > 0 && inv.getSelectedSlot() != bester) {
			inv.setSelectedSlot(bester);
			((de.reiss.jevbaritone.mixin.MultiPlayerGameModeAccessor) mc.gameMode).jevbaritone$ensureHasSentCarriedItem();
		}
	}

	private static int rang(ItemStack s) {
		if (s.isEmpty()) return 0;
		String n = s.getItem().toString();
		int material = n.contains("netherite") ? 6 : n.contains("diamond") ? 5 : n.contains("iron") ? 4
			: n.contains("stone") ? 3 : n.contains("golden") ? 2 : n.contains("wooden") ? 1 : 0;
		if (n.endsWith("_sword")) return 10 + material * 2;
		if (n.endsWith("_axe")) return 9 + material * 2;
		return 0;
	}

	/** Weglaufen, wenn ein Creeper nah ist. */
	void creeperMeiden() {
		if (!an || mc.player == null || mc.level == null) return;
		Entity c = mc.level.getEntitiesOfClass(Creeper.class, mc.player.getBoundingBox().inflate(5)).stream().findFirst().orElse(null);
		if (c == null) return;
		var weg = mc.player.position().subtract(c.position()).normalize().scale(8).add(mc.player.position());
		BaritoneAPI.getProvider().getPrimaryBaritone().getCustomGoalProcess()
			.setGoalAndPath(new GoalNear(net.minecraft.core.BlockPos.containing(weg), 2));
	}
}
