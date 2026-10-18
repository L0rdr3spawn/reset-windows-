package de.reiss.jevbaritone.mixin;

import baritone.api.utils.BlockOptionalMeta;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Baritone ermittelt Drops ueber Loot-Tabellen eines Fake-Servers. Mit Fabric-API (Loot-API v3) kracht das auf dem
 * Client (NullPointerException in reloadableRegistries), Baritone kennt dann keine Drops und zaehlt "#mine 16 ..."
 * falsch. Ersatz: feste Tabelle fuer die wichtigen Bloecke, sonst das Block-Item selbst.
 */
@Mixin(value = BlockOptionalMeta.class, remap = false)
public class BlockOptionalMetaMixin {
	private static final Map<String, Item[]> JEV_DROPS = Map.ofEntries(
		Map.entry("coal_ore", new Item[]{Items.COAL}), Map.entry("deepslate_coal_ore", new Item[]{Items.COAL}),
		Map.entry("iron_ore", new Item[]{Items.RAW_IRON}), Map.entry("deepslate_iron_ore", new Item[]{Items.RAW_IRON}),
		Map.entry("copper_ore", new Item[]{Items.RAW_COPPER}), Map.entry("deepslate_copper_ore", new Item[]{Items.RAW_COPPER}),
		Map.entry("gold_ore", new Item[]{Items.RAW_GOLD}), Map.entry("deepslate_gold_ore", new Item[]{Items.RAW_GOLD}),
		Map.entry("nether_gold_ore", new Item[]{Items.GOLD_NUGGET}),
		Map.entry("diamond_ore", new Item[]{Items.DIAMOND}), Map.entry("deepslate_diamond_ore", new Item[]{Items.DIAMOND}),
		Map.entry("emerald_ore", new Item[]{Items.EMERALD}), Map.entry("deepslate_emerald_ore", new Item[]{Items.EMERALD}),
		Map.entry("redstone_ore", new Item[]{Items.REDSTONE}), Map.entry("deepslate_redstone_ore", new Item[]{Items.REDSTONE}),
		Map.entry("lapis_ore", new Item[]{Items.LAPIS_LAZULI}), Map.entry("deepslate_lapis_ore", new Item[]{Items.LAPIS_LAZULI}),
		Map.entry("nether_quartz_ore", new Item[]{Items.QUARTZ}),
		Map.entry("stone", new Item[]{Items.COBBLESTONE}), Map.entry("deepslate", new Item[]{Items.COBBLED_DEEPSLATE}),
		Map.entry("grass_block", new Item[]{Items.DIRT}), Map.entry("mycelium", new Item[]{Items.DIRT}), Map.entry("podzol", new Item[]{Items.DIRT}),
		Map.entry("gravel", new Item[]{Items.GRAVEL, Items.FLINT}), Map.entry("clay", new Item[]{Items.CLAY_BALL}),
		Map.entry("glowstone", new Item[]{Items.GLOWSTONE_DUST}), Map.entry("snow_block", new Item[]{Items.SNOWBALL}),
		Map.entry("amethyst_cluster", new Item[]{Items.AMETHYST_SHARD})
	);

	@Inject(method = "drops", at = @At("HEAD"), cancellable = true)
	private static void jev$drops(Block block, CallbackInfoReturnable<List<Item>> cir) {
		List<Item> liste = new ArrayList<>();
		Item eigen = block.asItem();
		if (eigen != Items.AIR) liste.add(eigen); // Behutsamkeit oder Bloecke, die sich selbst droppen
		Item[] extra = JEV_DROPS.get(BuiltInRegistries.BLOCK.getKey(block).getPath());
		if (extra != null) liste.addAll(List.of(extra));
		cir.setReturnValue(liste);
	}
}
