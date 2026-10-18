package de.reiss.botlink;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.Potion;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;

import java.util.List;
import java.util.Optional;

/**
 * Das echte Inventar des Bots als Kiste: oben Ruestung + Nebenhand, darunter Rucksack und Hotbar, ganz unten
 * dein eigenes Inventar. Rein lokal - Klicks gehen nicht an den Server, sondern als "!gib slot ..." an den Bot.
 * Linksklick/Shift = ganzer Stapel, Rechtsklick = eins.
 */
public final class BotInventarScreen extends ContainerScreen {
	/** Platz in der Kiste -> Slot im Bot-Inventar (Mineflayer-/Vanilla-Fensternummern). */
	private static final int[] BOT_SLOT = new int[45];

	static {
		for (int i = 0; i < 45; i++) BOT_SLOT[i] = i >= 9 ? i : -1; // 9..44: Rucksack + Hotbar, gleiche Nummer
		for (int i = 0; i < 4; i++) BOT_SLOT[i] = 5 + i; // Kopf, Brust, Beine, Fuesse
		BOT_SLOT[5] = 45; // Nebenhand
	}

	private final BotLinkClient mod;
	private final SimpleContainer kiste;
	private int tick;

	private BotInventarScreen(BotLinkClient mod, ChestMenu menu, SimpleContainer kiste, Component titel) {
		super(menu, Minecraft.getInstance().player.getInventory(), titel);
		this.mod = mod;
		this.kiste = kiste;
	}

	public static BotInventarScreen erstellen(BotLinkClient mod) {
		Minecraft mc = Minecraft.getInstance();
		SimpleContainer kiste = new SimpleContainer(45);
		ChestMenu menu = new ChestMenu(MenuType.GENERIC_9x5, -7, mc.player.getInventory(), kiste, 5);
		String name = mod.botName() != null ? mod.botName() : "Bot";
		BotInventarScreen s = new BotInventarScreen(mod, menu, kiste, Component.literal(name + " (Bot)"));
		s.fuellen(mod.inventar());
		return s;
	}

	/** Inhalt aus dem Schnappschuss des Managers (GET /inventar). */
	void fuellen(JsonObject stand) {
		kiste.clearContent();
		if (stand == null || !stand.has("slots")) return;
		for (JsonElement el : stand.getAsJsonArray("slots")) {
			JsonObject s = el.getAsJsonObject();
			if (!s.has("slot")) continue;
			int botSlot = s.get("slot").getAsInt();
			for (int i = 0; i < BOT_SLOT.length; i++) {
				if (BOT_SLOT[i] == botSlot) kiste.setItem(i, stack(s));
			}
		}
	}

	/** Echter ItemStack mit Verzauberungen, Haltbarkeit und Trank -> Vanilla-Tooltip zeigt alles an. */
	static ItemStack stack(JsonObject s) {
		Minecraft mc = Minecraft.getInstance();
		Identifier id = s.has("name") ? Identifier.tryParse(s.get("name").getAsString()) : null;
		Item item = id == null ? Items.BARRIER : BuiltInRegistries.ITEM.getOptional(id).orElse(Items.BARRIER);
		ItemStack st = new ItemStack(item, Math.max(1, s.has("anzahl") ? s.get("anzahl").getAsInt() : 1));
		if (mc.level == null) return st;
		HolderLookup.RegistryLookup<Enchantment> verz = mc.level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
		for (String feld : new String[]{"verz", "buch"}) {
			if (!s.has(feld)) continue;
			EnchantmentHelper.updateEnchantments(st, m -> {
				for (JsonElement e : s.getAsJsonArray(feld)) {
					JsonObject o = e.getAsJsonObject();
					// Mineflayer kennt nicht jede Verzauberung: dann fehlt "name"
					Identifier vid = o.has("name") ? Identifier.tryParse(o.get("name").getAsString()) : null;
					if (vid == null || !o.has("lvl")) continue;
					Optional<Holder.Reference<Enchantment>> h = verz.get(ResourceKey.create(Registries.ENCHANTMENT, vid));
					h.ifPresent(holder -> m.set(holder, o.get("lvl").getAsInt()));
				}
			});
		}
		if (s.has("schaden") && st.isDamageableItem()) st.setDamageValue(s.get("schaden").getAsInt());
		Identifier trank = s.has("trank") ? Identifier.tryParse(s.get("trank").getAsString()) : null;
		if (trank != null) {
			Optional<Holder.Reference<Potion>> p = BuiltInRegistries.POTION.get(trank);
			p.ifPresent(holder -> st.set(DataComponents.POTION_CONTENTS, new PotionContents(holder)));
		}
		return st;
	}

	@Override
	protected void containerTick() {
		super.containerTick();
		if (++tick % 10 == 0) mod.inventarAktualisieren();
		if (tick % 10 == 5) fuellen(mod.inventar());
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doppelt) {
		// Klick in die obere Kiste selbst auswerten (der Vanilla-Weg wuerde Pakete an den Server schicken)
		Slot slot = hoveredSlot;
		if (slot != null && slot.container == kiste) {
			klick(slot, event.button() == 1);
			return true;
		}
		return super.mouseClicked(event, doppelt);
	}

	@Override
	protected void slotClicked(Slot slot, int slotId, int button, ContainerInput input) {
		// Nie an den Server. Tastatur (Q, Zahlentasten) und Shift-Klick landen hier.
		if (slot != null && slot.container == kiste && (input == ContainerInput.QUICK_MOVE || input == ContainerInput.THROW)) klick(slot, false);
	}

	/** Linksklick = ganzer Stapel, Rechtsklick = eins: der Bot kommt und wirft es dir zu. */
	private void klick(Slot slot, boolean eins) {
		if (!slot.hasItem()) return;
		int botSlot = BOT_SLOT[slot.getContainerSlot()];
		if (botSlot < 0) return;
		ItemStack st = slot.getItem();
		String name = BuiltInRegistries.ITEM.getKey(st.getItem()).getPath();
		int menge = eins ? 1 : st.getCount();
		BotLinkClient.LOGGER.info("Inventar-Klick: Slot {} ({}), {}x", botSlot, name, menge);
		mod.befehl("!gib slot " + botSlot + " " + menge + " " + name);
		mod.lokal(Minecraft.getInstance(), "Bot bringt dir " + menge + "x " + st.getHoverName().getString() + ".");
	}

	@Override
	protected List<Component> getTooltipFromContainerItem(ItemStack stack) {
		List<Component> zeilen = super.getTooltipFromContainerItem(stack);
		if (hoveredSlot != null && hoveredSlot.container == kiste) {
			zeilen.add(Component.literal("Linksklick: ganzer Stapel, Rechtsklick: 1").withStyle(ChatFormatting.GRAY));
			if (stack.is(Items.TOTEM_OF_UNDYING)) zeilen.add(Component.literal("2 Totems behaelt er immer").withStyle(ChatFormatting.DARK_GRAY));
		}
		return zeilen;
	}

	@Override
	public void onClose() {
		// kein closeContainer(): diese Kiste gibt es auf dem Server nicht
		Minecraft.getInstance().gui.setScreen(null);
	}
}
