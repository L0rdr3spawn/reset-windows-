package de.reiss.jevbaritone;

import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.inventory.AbstractFurnaceMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

import java.util.*;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;
import java.util.function.Predicate;

/**
 * Schmelzen wie ein Spieler: Ofen suchen (oder ueber die Werkbank bauen und hinstellen), hingehen, oeffnen,
 * Schmelzgut und genau so viel Brennstoff wie noetig hineinlegen, warten, Ergebnis per Shift-Klick nehmen.
 */
final class Ofen {
	// Was man schmelzen/braten kann, bevorzugte Reihenfolge, wenn der Spieler nichts Bestimmtes sagt
	static final List<Item> SCHMELZGUT = List.of(Items.RAW_IRON, Items.RAW_GOLD, Items.RAW_COPPER, Items.IRON_ORE, Items.GOLD_ORE,
		Items.COPPER_ORE, Items.DEEPSLATE_IRON_ORE, Items.BEEF, Items.PORKCHOP, Items.CHICKEN, Items.MUTTON, Items.RABBIT, Items.COD,
		Items.SALMON, Items.POTATO, Items.KELP, Items.SAND, Items.RED_SAND, Items.COBBLESTONE, Items.CLAY_BALL, Items.NETHERRACK,
		Items.ANCIENT_DEBRIS, Items.CACTUS, Items.WET_SPONGE);

	private final Minecraft mc = Minecraft.getInstance();
	private final Werkbank werkbank;
	private final Consumer<String> sag;
	private final Predicate<String> baritone;
	private final BooleanSupplier baritoneAktiv;
	private String phase;
	private Item eingabe;
	private int menge, ticks, warte, fertig;
	private BlockPos ofen;

	Ofen(Werkbank werkbank, Consumer<String> sag, Predicate<String> baritone, BooleanSupplier baritoneAktiv) {
		this.werkbank = werkbank;
		this.sag = sag;
		this.baritone = baritone;
		this.baritoneAktiv = baritoneAktiv;
	}

	boolean aktiv() {
		return phase != null;
	}

	/** Schmelzgut im Inventar fuer Jev. */
	Map<String, String> kandidaten() {
		Map<String, String> k = new LinkedHashMap<>();
		for (Item i : SCHMELZGUT) {
			int n = anzahl(i);
			if (n > 0) k.put("ding:" + BuiltInRegistries.ITEM.getKey(i).getPath(), name(i) + " (" + n + " im Inventar)");
		}
		k.put("unklar", "Nicht genannt, oder nichts davon.");
		return k;
	}

	/** item == null: das erste passende Schmelzgut aus dem Inventar. */
	void starten(Item item, int wieviel) {
		abbrechen();
		eingabe = item != null ? item : SCHMELZGUT.stream().filter(i -> anzahl(i) > 0).findFirst().orElse(null);
		if (eingabe == null || anzahl(eingabe) == 0) { sag.accept("Ich habe nichts zum Schmelzen."); return; }
		if (brennstoff() == null) { sag.accept("Ich habe keinen Brennstoff (Kohle oder Holz)."); return; }
		menge = Math.min(wieviel, Math.min(64, anzahl(eingabe)));
		fertig = 0;
		ofen = suchen(24);
		if (ofen != null) wechsel("hingehen");
		else if (anzahl(Items.FURNACE) > 0) wechsel("hinstellen");
		else {
			sag.accept("Kein Ofen da, ich baue einen.");
			werkbank.starten(Items.FURNACE, 1);
			wechsel("ofen_bauen");
		}
	}

	void abbrechen() {
		if (phase == null) return;
		phase = null;
		if (mc.player != null && mc.player.containerMenu != mc.player.inventoryMenu) mc.player.closeContainer();
	}

	void tick() {
		if (phase == null || mc.player == null || mc.gameMode == null) return;
		if (warte > 0) { warte--; return; }
		ticks++;
		switch (phase) {
			case "ofen_bauen" -> {
				if (werkbank.aktiv()) return;
				if (anzahl(Items.FURNACE) == 0) { sag.accept("Ofen bauen ging nicht (8 Bruchstein noetig)."); abbrechen(); return; }
				wechsel("hinstellen");
			}
			case "hinstellen" -> {
				ofen = werkbank.hinstellen(Items.FURNACE);
				if (ofen == null) { sag.accept("Kein Platz fuer den Ofen."); abbrechen(); return; }
				wechsel("hingehen");
				warte = 10;
			}
			case "hingehen" -> {
				if (mc.player.getEyePosition().distanceTo(Vec3.atCenterOf(ofen)) <= 4.2) {
					if (baritoneAktiv.getAsBoolean()) baritone.test("stop");
					wechsel("oeffnen");
				} else if (ticks == 1) {
					baritone.test("goto furnace");
				} else if (ticks > 60 && !baritoneAktiv.getAsBoolean()) {
					sag.accept("Ich komme nicht zum Ofen.");
					abbrechen();
				}
			}
			case "oeffnen" -> {
				if (mc.player.containerMenu instanceof AbstractFurnaceMenu) { wechsel("befuellen"); warte = 3; return; }
				if (baritoneAktiv.getAsBoolean()) { baritone.test("stop"); return; }
				if (ticks == 60 && mc.player.getEyePosition().distanceTo(Vec3.atCenterOf(ofen)) > 3.5) baritone.test("goto furnace");
				if (ticks % 15 == 1) {
					mc.player.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, Vec3.atCenterOf(ofen));
					mc.gameMode.useItemOn(mc.player, InteractionHand.MAIN_HAND,
						new BlockHitResult(Vec3.atCenterOf(ofen).add(0, 0.5, 0), Direction.UP, ofen, false));
				}
				if (ticks > 200) { sag.accept("Der Ofen geht nicht auf."); abbrechen(); }
			}
			case "befuellen" -> {
				if (!(mc.player.containerMenu instanceof AbstractFurnaceMenu m)) { abbrechen(); return; }
				legen(m, eingabe, 0, menge);
				Item brenn = brennstoff();
				if (brenn != null && m.getSlot(1).getItem().isEmpty()) {
					int proStueck = brenn == Items.COAL || brenn == Items.CHARCOAL ? 8 : brenn == Items.COAL_BLOCK ? 80 : brenn == Items.STICK ? 1 : 2;
					legen(m, brenn, 1, Math.max(1, (int) Math.ceil(menge / (double) proStueck)));
				}
				sag.accept("Schmelze " + menge + "x " + name(eingabe) + " (ca. " + (menge * 10) + " s).");
				wechsel("warten");
				warte = 20;
			}
			case "warten" -> {
				if (!(mc.player.containerMenu instanceof AbstractFurnaceMenu m)) { abbrechen(); return; }
				ItemStack aus = m.getSlot(2).getItem();
				if (!aus.isEmpty()) {
					fertig += aus.getCount();
					mc.gameMode.handleContainerInput(m.containerId, 2, 0, ContainerInput.QUICK_MOVE, mc.player);
				}
				boolean leer = m.getSlot(0).getItem().isEmpty() && m.getSlot(2).getItem().isEmpty();
				boolean ausgebrannt = !m.isLit() && !m.getSlot(0).getItem().isEmpty() && m.getSlot(1).getItem().isEmpty() && ticks > 60;
				if (leer || ausgebrannt || ticks > (menge * 10 + 30) * 20 / 20) {
					if (ausgebrannt) sag.accept("Der Brennstoff hat nicht gereicht.");
					sag.accept(fertig + "x geschmolzen.");
					abbrechen();
				}
				warte = 20;
			}
			default -> abbrechen();
		}
	}

	private void wechsel(String neu) {
		phase = neu;
		ticks = 0;
	}

	/** Genau `n` Stueck von `item` aus dem Inventar in den Ofen-Slot legen (Rechtsklick = 1 Stueck). */
	private void legen(AbstractFurnaceMenu m, Item item, int zielSlot, int n) {
		int gelegt = 0;
		for (Slot s : m.slots) {
			if (gelegt >= n || s.index <= 2 || !s.getItem().is(item)) continue;
			int stapel = s.getItem().getCount();
			int hier = Math.min(stapel, n - gelegt);
			mc.gameMode.handleContainerInput(m.containerId, s.index, 0, ContainerInput.PICKUP, mc.player);
			if (hier == stapel) {
				mc.gameMode.handleContainerInput(m.containerId, zielSlot, 0, ContainerInput.PICKUP, mc.player);
			} else {
				for (int i = 0; i < hier; i++) mc.gameMode.handleContainerInput(m.containerId, zielSlot, 1, ContainerInput.PICKUP, mc.player);
			}
			// Rest zurueck in den Ursprungsslot
			if (!m.getCarried().isEmpty()) mc.gameMode.handleContainerInput(m.containerId, s.index, 0, ContainerInput.PICKUP, mc.player);
			gelegt += hier;
		}
	}

	private Item brennstoff() {
		for (Item i : List.of(Items.COAL, Items.CHARCOAL, Items.COAL_BLOCK)) if (anzahl(i) > 0 && i != eingabe) return i;
		var inv = mc.player.getInventory();
		for (int s = 0; s < inv.getContainerSize(); s++) {
			ItemStack st = inv.getItem(s);
			if ((st.is(ItemTags.PLANKS) || st.is(ItemTags.LOGS)) && st.getItem() != eingabe) return st.getItem();
		}
		return anzahl(Items.STICK) > 0 ? Items.STICK : null;
	}

	private BlockPos suchen(int r) {
		BlockPos mitte = mc.player.blockPosition();
		BlockPos best = null;
		double bestD = Double.MAX_VALUE;
		for (BlockPos p : BlockPos.betweenClosed(mitte.offset(-r, -8, -r), mitte.offset(r, 8, r))) {
			if (!mc.level.getBlockState(p).is(Blocks.FURNACE)) continue;
			double d = p.distSqr(mitte);
			if (d < bestD) { bestD = d; best = p.immutable(); }
		}
		return best;
	}

	private int anzahl(Item item) {
		var inv = mc.player.getInventory();
		int n = 0;
		for (int i = 0; i < inv.getContainerSize(); i++) if (inv.getItem(i).is(item)) n += inv.getItem(i).getCount();
		return n;
	}

	private static String name(Item i) {
		return new ItemStack(i).getHoverName().getString();
	}
}
