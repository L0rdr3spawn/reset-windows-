package de.reiss.jevbaritone;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.recipebook.RecipeCollection;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.StackedItemContents;
import net.minecraft.world.inventory.AbstractCraftingMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.display.RecipeDisplay;
import net.minecraft.world.item.crafting.display.RecipeDisplayEntry;
import net.minecraft.world.item.crafting.display.ShapedCraftingRecipeDisplay;
import net.minecraft.world.item.crafting.display.ShapelessCraftingRecipeDisplay;
import net.minecraft.world.item.crafting.display.SlotDisplayContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

import java.util.*;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;
import java.util.function.Predicate;
import java.util.regex.Pattern;

/**
 * Herstellen ueber das Rezeptbuch, wie ein Spieler: Rezept ins Raster legen lassen (handlePlaceRecipe), Ergebnis
 * per Shift-Klick nehmen. Laeuft Schritt fuer Schritt im Client-Tick. Rezepte werden erst beim jeweiligen Schritt
 * gesucht, weil der Server sie freischaltet, sobald die Zutaten im Inventar sind (Bretter -> Stoecke -> Werkzeug).
 * 3x3-Rezepte an einer Werkbank, die notfalls selbst gebaut und hingestellt wird.
 */
final class Werkbank {
	/** item == null bei "bretter": irgendeine Brettersorte aus dem vorhandenen Holz. */
	private record Schritt(String art, Item item, int menge, boolean ziel) {}

	// Braucht Stoecke (grobe Regel reicht: fehlt etwas, meldet das Rezept es ohnehin)
	private static final Pattern MIT_STOECKEN = Pattern.compile(".*(_pickaxe|_axe|_shovel|_sword|_hoe|torch|ladder|fence|_sign|bow|fishing_rod|arrow|lever|rail|banner|painting|item_frame|armor_stand|spear)$");

	// Haeufige Items, die Jev immer kennt, auch wenn das Rezeptbuch sie noch nicht freigeschaltet hat
	private static final List<String> BEKANNT = List.of("stick", "oak_planks", "crafting_table", "chest", "barrel", "furnace", "torch",
		"ladder", "bowl", "oak_boat", "white_bed", "shield", "bucket", "shears", "flint_and_steel", "fishing_rod", "bow", "arrow",
		"bread", "iron_ingot", "iron_block", "gold_ingot", "compass", "clock", "stone_bricks", "glass_pane", "oak_door", "oak_fence",
		"wooden_pickaxe", "wooden_axe", "wooden_shovel", "wooden_sword", "wooden_hoe",
		"stone_pickaxe", "stone_axe", "stone_shovel", "stone_sword", "stone_hoe",
		"iron_pickaxe", "iron_axe", "iron_shovel", "iron_sword", "iron_hoe",
		"diamond_pickaxe", "diamond_axe", "diamond_shovel", "diamond_sword", "diamond_hoe",
		"iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots",
		"diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots");

	private final Minecraft mc = Minecraft.getInstance();
	private final Consumer<String> sag;
	private final Consumer<String> fehlschlag;
	private final Predicate<String> baritone;
	private final BooleanSupplier baritoneAktiv;
	private final Deque<Schritt> schritte = new ArrayDeque<>();
	private BlockPos tisch;
	private String zielName = "";
	private int warte, ticksImSchritt, imSchritt, gemacht;
	private boolean gelegt;

	Werkbank(Consumer<String> sag, Consumer<String> fehlschlag, Predicate<String> baritone, BooleanSupplier baritoneAktiv) {
		this.sag = sag;
		this.fehlschlag = fehlschlag;
		this.baritone = baritone;
		this.baritoneAktiv = baritoneAktiv;
	}

	boolean aktiv() {
		return !schritte.isEmpty();
	}

	// ---------------- Rezepte ----------------

	private List<RecipeDisplayEntry> alleRezepte() {
		List<RecipeDisplayEntry> r = new ArrayList<>();
		for (RecipeCollection c : mc.player.getRecipeBook().getCollections()) r.addAll(c.getRecipes());
		return r;
	}

	private StackedItemContents inventar() {
		StackedItemContents s = new StackedItemContents();
		mc.player.getInventory().fillStackedContents(s);
		return s;
	}

	private List<ItemStack> ergebnis(RecipeDisplayEntry r) {
		try {
			return r.resultItems(SlotDisplayContext.fromLevel(mc.level));
		} catch (Exception e) {
			return List.of();
		}
	}

	private static boolean istCrafting(RecipeDisplay d) {
		return d instanceof ShapedCraftingRecipeDisplay || d instanceof ShapelessCraftingRecipeDisplay;
	}

	/** Passt ins 2x2-Raster im Inventar? */
	private static boolean klein(RecipeDisplayEntry r) {
		if (r.display() instanceof ShapedCraftingRecipeDisplay s) return s.width() <= 2 && s.height() <= 2;
		if (r.display() instanceof ShapelessCraftingRecipeDisplay s) return s.ingredients().size() <= 4;
		return false;
	}

	/** Herstellbares Rezept fuer das Item (bei item == null: irgendwelche Bretter), sonst null. */
	private RecipeDisplayEntry rezept(Item item) {
		StackedItemContents inv = inventar();
		for (RecipeDisplayEntry r : alleRezepte()) {
			if (!istCrafting(r.display()) || !r.canCraft(inv)) continue;
			for (ItemStack s : ergebnis(r)) {
				if (item == null ? s.is(ItemTags.PLANKS) : s.is(item)) return r;
			}
		}
		return null;
	}

	/** Kandidaten fuer Jev: bekannte Items plus alles aus dem Rezeptbuch; was jetzt geht, ist markiert. */
	Map<String, String> kandidaten() {
		StackedItemContents inv = inventar();
		Map<Item, Boolean> items = new LinkedHashMap<>();
		for (RecipeDisplayEntry r : alleRezepte()) {
			if (!istCrafting(r.display())) continue;
			boolean geht = r.canCraft(inv);
			for (ItemStack s : ergebnis(r)) items.merge(s.getItem(), geht, Boolean::logicalOr);
		}
		for (String n : BEKANNT) {
			BuiltInRegistries.ITEM.getOptional(Identifier.withDefaultNamespace(n)).ifPresent(i -> items.putIfAbsent(i, false));
		}
		Map<String, String> k = new LinkedHashMap<>();
		items.entrySet().stream()
			.sorted((a, b) -> Boolean.compare(b.getValue(), a.getValue()))
			.limit(150)
			.forEach(e -> k.put("item:" + BuiltInRegistries.ITEM.getKey(e.getKey()).getPath(),
				name(e.getKey()) + (e.getValue() ? " (Material reicht)" : "")));
		k.put("unklar", "Nicht genannt, oder keine dieser Optionen passt.");
		return k;
	}

	private static String name(Item i) {
		return new ItemStack(i).getHoverName().getString();
	}

	private int anzahl(Predicate<ItemStack> p) {
		Inventory inv = mc.player.getInventory();
		int n = 0;
		for (int i = 0; i < inv.getContainerSize(); i++) if (p.test(inv.getItem(i))) n += inv.getItem(i).getCount();
		return n;
	}

	// ---------------- Ablauf ----------------

	/** Plant die Schritte (Bretter und Stoecke vorab, wenn noetig) und legt los. */
	void starten(Item item, int menge) {
		abbrechen();
		zielName = name(item);
		gemacht = 0;
		String id = BuiltInRegistries.ITEM.getKey(item).getPath();
		boolean istHolz = new ItemStack(item).is(ItemTags.PLANKS) || new ItemStack(item).is(ItemTags.LOGS);
		int bretter = anzahl(s -> s.is(ItemTags.PLANKS));
		int staemme = anzahl(s -> s.is(ItemTags.LOGS));
		if (!istHolz && staemme > 0 && bretter < 8) schritte.add(new Schritt("craft", null, Math.min(staemme * 4, 16), false));
		int stoecke = anzahl(s -> s.is(Items.STICK));
		if (item != Items.STICK && MIT_STOECKEN.matcher(id).matches() && stoecke < 2 * menge) {
			schritte.add(new Schritt("craft", Items.STICK, 2 * menge - stoecke, false));
		}
		schritte.add(new Schritt("craft", item, menge, true));
		schritte.add(new Schritt("fertig", null, 0, false));
		neuerSchritt();
	}

	void abbrechen() {
		if (schritte.isEmpty()) return;
		schritte.clear();
		aufraeumen();
	}

	void tick() {
		if (schritte.isEmpty() || mc.player == null || mc.gameMode == null) return;
		if (warte > 0) { warte--; return; }
		Schritt s = schritte.peek();
		if (++ticksImSchritt > 20 * 90) { sag.accept("Herstellen haengt (" + s.art() + "), breche ab."); abbrechen(); return; }

		switch (s.art()) {
			case "hinstellen" -> {
				if (hinstellen()) weiter(10);
				else { sag.accept("Ich finde keinen Platz fuer die Werkbank."); abbrechen(); }
			}
			case "hingehen" -> {
				if (tisch == null) tisch = tischSuchen(24);
				if (tisch == null) { sag.accept("Keine Werkbank gefunden."); abbrechen(); return; }
				if (mc.player.getEyePosition().distanceTo(Vec3.atCenterOf(tisch)) <= 4.2) {
					if (baritoneAktiv.getAsBoolean()) baritone.test("stop");
					weiter(4);
				} else if (ticksImSchritt == 1) {
					baritone.test("goto crafting_table");
				} else if (ticksImSchritt > 60 && !baritoneAktiv.getAsBoolean()) {
					sag.accept("Ich komme nicht zur Werkbank.");
					abbrechen();
				}
			}
			case "oeffnen" -> {
				if (mc.player.containerMenu instanceof CraftingMenu) { weiter(3); return; }
				if (baritoneAktiv.getAsBoolean()) { baritone.test("stop"); return; }
				if (!mc.level.getBlockState(tisch).is(Blocks.CRAFTING_TABLE)) tisch = tischSuchen(24);
				if (tisch == null) { sag.accept("Keine Werkbank gefunden."); abbrechen(); return; }
				if (ticksImSchritt == 60 && mc.player.getEyePosition().distanceTo(Vec3.atCenterOf(tisch)) > 3.5) {
					baritone.test("goto crafting_table"); // naeher ran und nochmal
				}
				if (ticksImSchritt % 15 == 1) {
					mc.player.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, Vec3.atCenterOf(tisch));
					mc.gameMode.useItemOn(mc.player, InteractionHand.MAIN_HAND,
						new BlockHitResult(Vec3.atCenterOf(tisch).add(0, 0.5, 0), Direction.UP, tisch, false));
				}
				if (ticksImSchritt > 200) { sag.accept("Die Werkbank geht nicht auf."); abbrechen(); }
			}
			case "craft" -> craften(s);
			case "fertig" -> {
				aufraeumen();
				schritte.clear();
				sag.accept(gemacht + "x " + zielName + " hergestellt.");
			}
			default -> abbrechen();
		}
	}

	private void craften(Schritt s) {
		String was = s.item() == null ? "Bretter" : name(s.item());
		if (!gelegt) {
			RecipeDisplayEntry r = rezept(s.item());
			if (r == null) {
				// Freischaltung vom Server kann ein paar Ticks dauern, nachdem die Zutaten ins Inventar kamen
				if (ticksImSchritt < 40) return;
				if (imSchritt > 0) { weiter(2); return; }
				String grund = "Fuer " + was + " fehlt mir Material.";
				abbrechen();
				fehlschlag.accept(grund);
				return;
			}
			// 3x3-Rezept, aber keine Werkbank offen: Werkbank-Schritte davorschieben
			if (!klein(r) && !(mc.player.containerMenu instanceof CraftingMenu)) {
				List<Schritt> vorher = new ArrayList<>();
				tisch = tischSuchen(24);
				if (tisch == null) {
					if (!hat(Items.CRAFTING_TABLE)) vorher.add(new Schritt("craft", Items.CRAFTING_TABLE, 1, false));
					vorher.add(new Schritt("hinstellen", null, 0, false));
				}
				vorher.add(new Schritt("hingehen", null, 0, false));
				vorher.add(new Schritt("oeffnen", null, 0, false));
				for (int i = vorher.size() - 1; i >= 0; i--) schritte.addFirst(vorher.get(i));
				int schon = imSchritt;
				neuerSchritt();
				imSchritt = schon;
				return;
			}
			AbstractCraftingMenu menu = mc.player.containerMenu instanceof CraftingMenu c ? c : mc.player.inventoryMenu;
			mc.gameMode.handlePlaceRecipe(menu.containerId, r.id(), false);
			gelegt = true;
			warte = 3;
			return;
		}
		AbstractCraftingMenu menu = mc.player.containerMenu instanceof CraftingMenu c ? c : mc.player.inventoryMenu;
		Slot ergebnis = menu.getResultSlot();
		ItemStack st = ergebnis.getItem();
		gelegt = false;
		if (st.isEmpty()) { // Material alle
			if (imSchritt > 0) { weiter(2); return; }
			String grund = "Fuer " + was + " fehlt mir Material.";
			abbrechen();
			fehlschlag.accept(grund);
			return;
		}
		int n = st.getCount();
		// Das Raster enthaelt genau einen Satz Zutaten, Shift-Klick stellt also genau einmal her
		mc.gameMode.handleContainerInput(menu.containerId, ergebnis.index, 0, ContainerInput.QUICK_MOVE, mc.player);
		imSchritt += n;
		if (s.ziel()) gemacht += n;
		warte = 3;
		if (imSchritt >= s.menge()) weiter(2);
	}

	private void weiter(int pause) {
		schritte.poll();
		neuerSchritt();
		warte = pause;
	}

	private void neuerSchritt() {
		ticksImSchritt = 0;
		imSchritt = 0;
		gelegt = false;
	}

	/** Reste aus dem Raster zurueck ins Inventar, Werkbank-Fenster schliessen. */
	private void aufraeumen() {
		if (mc.player == null || mc.gameMode == null) return;
		AbstractCraftingMenu menu = mc.player.containerMenu instanceof CraftingMenu c ? c : mc.player.inventoryMenu;
		for (Slot sl : menu.getInputGridSlots()) {
			if (sl.hasItem()) mc.gameMode.handleContainerInput(menu.containerId, sl.index, 0, ContainerInput.QUICK_MOVE, mc.player);
		}
		if (mc.player.containerMenu != mc.player.inventoryMenu) mc.player.closeContainer();
	}

	// ---------------- Werkbank finden / hinstellen ----------------

	private BlockPos tischSuchen(int r) {
		BlockPos mitte = mc.player.blockPosition();
		BlockPos best = null;
		double bestD = Double.MAX_VALUE;
		for (BlockPos p : BlockPos.betweenClosed(mitte.offset(-r, -8, -r), mitte.offset(r, 8, r))) {
			if (!mc.level.getBlockState(p).is(Blocks.CRAFTING_TABLE)) continue;
			double d = p.distSqr(mitte);
			if (d < bestD) { bestD = d; best = p.immutable(); }
		}
		return best;
	}

	private boolean hat(Item item) {
		return mc.player.getInventory().findSlotMatchingItem(new ItemStack(item)) >= 0;
	}

	private boolean hinstellen() {
		BlockPos p = hinstellen(Items.CRAFTING_TABLE);
		if (p == null) return false;
		tisch = p;
		return true;
	}

	/** Block-Item aus dem Inventar neben den Bot stellen; gibt die Stelle zurueck oder null. */
	BlockPos hinstellen(Item item) {
		Inventory inv = mc.player.getInventory();
		int slot = inv.findSlotMatchingItem(new ItemStack(item));
		if (slot < 0) return null;
		if (slot >= 9) { // aus dem Inventar in den letzten Hotbar-Platz tauschen
			mc.gameMode.handleContainerInput(mc.player.inventoryMenu.containerId, slot, 8, ContainerInput.SWAP, mc.player);
			slot = 8;
		}
		inv.setSelectedSlot(slot);
		((de.reiss.jevbaritone.mixin.MultiPlayerGameModeAccessor) mc.gameMode).jevbaritone$ensureHasSentCarriedItem();
		BlockPos fuss = mc.player.blockPosition();
		List<BlockPos> plaetze = new ArrayList<>();
		for (BlockPos p : BlockPos.betweenClosed(fuss.offset(-3, -1, -3), fuss.offset(3, 1, 3))) plaetze.add(p.immutable());
		plaetze.sort(Comparator.comparingDouble(p -> p.distSqr(fuss)));
		for (BlockPos platz : plaetze) {
			BlockPos boden = platz.below();
			if (platz.equals(fuss) || platz.equals(fuss.above())) continue; // nicht in sich selbst
			if (!mc.level.getBlockState(platz).canBeReplaced()) continue;
			if (!mc.level.getBlockState(boden).isFaceSturdy(mc.level, boden, Direction.UP)) continue;
			if (mc.player.getEyePosition().distanceTo(Vec3.atCenterOf(boden).add(0, 0.5, 0)) > 4.3) continue;
			mc.player.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, Vec3.atCenterOf(boden).add(0, 0.5, 0));
			mc.gameMode.useItemOn(mc.player, InteractionHand.MAIN_HAND,
				new BlockHitResult(Vec3.atCenterOf(boden).add(0, 0.5, 0), Direction.UP, boden, false));
			return platz;
		}
		return null;
	}
}
