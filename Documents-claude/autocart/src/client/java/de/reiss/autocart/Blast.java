package de.reiss.autocart;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.vehicle.minecart.MinecartTNT;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.BlocksAttacks;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.item.enchantment.ItemEnchantments;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The explosion maths of a TNT minecart, for any living thing: us, the target, a bystander.
 *
 * <p>A cart set off by a burning arrow does not blow up at a fixed power.
 * {@code MinecartTNT#explode} uses {@code 4 + random * 1.5 * min(arrowSpeed, 5)}, and a crossbow
 * arrow still flies at about 3.15 blocks per tick when it lands. So the power is anywhere from 4 to
 * 8.7 and the blast radius (twice the power) from 8 to 17 blocks. Reckoning with a flat 4, as this
 * mod used to, underestimated the average hit by half and the worst one by two thirds.
 *
 * <p>Everything else mirrors the server: {@code ServerExplosion#hurtEntities} for distance and
 * exposure, {@code Player#hurtServer} for difficulty, {@code CombatRules} for armour, then
 * protection enchantments, Resistance and a raised shield.
 */
public final class Blast {
	/** Protection counts once per level against everything, Blast Protection twice against explosions. */
	private static final EquipmentSlot[] ARMOUR_SLOTS = {
			EquipmentSlot.HEAD,
			EquipmentSlot.CHEST,
			EquipmentSlot.LEGS,
			EquipmentSlot.FEET
	};

	private Blast() {
	}

	/** The spread of explosion power this shot can produce. */
	public record Power(double min, double avg, double max) {
	}

	/** Every stage of one damage calculation, so a wrong number can be traced to its cause. */
	public record Hit(
			double distance,
			double exposure,
			double raw,
			double afterArmour,
			double afterProtection,
			double finalDamage) {

		static final Hit NONE = new Hit(0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
	}

	/** Damage at the lowest, average and highest power the cart can go off with. */
	public record Spread(double min, double avg, double max) {
	}

	public static Power power(final AutoCartConfig config) {
		// Bow arrows leave at 3 per tick when fully drawn, crossbow arrows at 3.15.
		double speed = Math.min(config.usesBow() ? 3.0 : 3.15, 5.0);
		double base = config.blastPower;
		return new Power(base, base + 0.75 * speed, base + 1.5 * speed);
	}

	/** Where the blast starts: the cart itself, or where it will sit on the planned rail. */
	public static Vec3 centre(final BlockPos spot, final MinecartTNT cart) {
		if (cart != null) {
			return cart.position();
		}
		// A minecart sits a sixteenth of a block above the rail's base.
		return new Vec3(spot.getX() + 0.5, spot.getY() + 0.0625, spot.getZ() + 0.5);
	}

	public static Spread spread(final Minecraft minecraft, final LivingEntity entity, final Vec3 centre, final Power power) {
		return new Spread(
				damage(minecraft, entity, centre, power.min()).finalDamage(),
				damage(minecraft, entity, centre, power.avg()).finalDamage(),
				damage(minecraft, entity, centre, power.max()).finalDamage());
	}

	public static Hit damage(final Minecraft minecraft, final LivingEntity entity, final Vec3 centre, final double power) {
		ClientLevel level = minecraft.level;

		if (level == null || entity == null) {
			return Hit.NONE;
		}

		double diameter = power * 2.0;
		double distance = Math.sqrt(entity.distanceToSqr(centre));
		double normalised = distance / diameter;

		if (normalised > 1.0) {
			return new Hit(distance, 0.0, 0.0, 0.0, 0.0, 0.0);
		}

		double exposure = seenPercent(level, centre, entity);
		double impact = (1.0 - normalised) * exposure;
		// The server truncates to whole points before anything else touches it.
		double raw = (int) ((impact * impact + impact) / 2.0 * 7.0 * diameter + 1.0);

		if (exposure <= 0.0) {
			return new Hit(distance, 0.0, 0.0, 0.0, 0.0, 0.0);
		}

		double scaled = difficulty(minecraft, entity, raw);
		double armoured = armour(entity, scaled);
		double enchanted = protection(level, entity, armoured);
		double resisted = resistance(entity, enchanted);
		double shielded = shield(minecraft, entity, centre, resisted);

		return new Hit(distance, exposure, raw, armoured, enchanted, shielded);
	}

	/**
	 * The share of the hitbox the blast can see, 0 to 1. Same sampling as
	 * {@code ServerExplosion.getSeenPercent}: a grid over the bounding box, each point traced to the
	 * blast, counting the ones nothing blocks. A block we put in the way shows up here.
	 */
	public static double seenPercent(final ClientLevel level, final Vec3 centre, final LivingEntity entity) {
		AABB box = entity.getBoundingBox();
		double stepX = 1.0 / ((box.maxX - box.minX) * 2.0 + 1.0);
		double stepY = 1.0 / ((box.maxY - box.minY) * 2.0 + 1.0);
		double stepZ = 1.0 / ((box.maxZ - box.minZ) * 2.0 + 1.0);

		if (stepX < 0.0 || stepY < 0.0 || stepZ < 0.0) {
			return 0.0;
		}

		double offsetX = (1.0 - Math.floor(1.0 / stepX) * stepX) / 2.0;
		double offsetZ = (1.0 - Math.floor(1.0 / stepZ) * stepZ) / 2.0;
		int clear = 0;
		int total = 0;

		for (double x = 0.0; x <= 1.0; x += stepX) {
			for (double y = 0.0; y <= 1.0; y += stepY) {
				for (double z = 0.0; z <= 1.0; z += stepZ) {
					Vec3 from = new Vec3(
							Mth.lerp(x, box.minX, box.maxX) + offsetX,
							Mth.lerp(y, box.minY, box.maxY),
							Mth.lerp(z, box.minZ, box.maxZ) + offsetZ);
					ClipContext clip = new ClipContext(from, centre, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, entity);

					if (level.clip(clip).getType() == HitResult.Type.MISS) {
						clear++;
					}

					total++;
				}
			}
		}

		return total == 0 ? 1.0 : (double) clear / total;
	}

	/** {@code Player#hurtServer}: explosions scale with difficulty for players only. */
	private static double difficulty(final Minecraft minecraft, final LivingEntity entity, final double damage) {
		if (!(entity instanceof Player) || minecraft.level == null) {
			return damage;
		}

		Difficulty difficulty = minecraft.level.getDifficulty();
		return switch (difficulty) {
			case PEACEFUL -> 0.0;
			case EASY -> Math.min(damage / 2.0 + 1.0, damage);
			case NORMAL -> damage;
			case HARD -> damage * 1.5;
		};
	}

	/** Factor the difficulty applies, for the diagnosis output. */
	public static double difficultyFactor(final Minecraft minecraft) {
		return minecraft.level != null && minecraft.level.getDifficulty() == Difficulty.HARD ? 1.5 : 1.0;
	}

	/** {@code CombatRules#getDamageAfterAbsorb}. */
	private static double armour(final LivingEntity entity, final double damage) {
		double armour = entity.getArmorValue();
		double toughness = entity.getAttributeValue(Attributes.ARMOR_TOUGHNESS);
		double real = Mth.clamp(armour - damage / (2.0 + toughness / 4.0), armour * 0.2, 20.0);
		return damage * (1.0 - real / 25.0);
	}

	/** Protection points, capped at 20 for 80 percent off. */
	private static double protection(final ClientLevel level, final LivingEntity entity, final double damage) {
		int points = protectionPoints(level, entity);
		return damage * (1.0 - Math.min(20, points) / 25.0);
	}

	public static int protectionPoints(final ClientLevel level, final LivingEntity entity) {
		int points = 0;

		try {
			HolderLookup.RegistryLookup<Enchantment> lookup = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
			Holder<Enchantment> blast = lookup.getOrThrow(Enchantments.BLAST_PROTECTION);
			Holder<Enchantment> plain = lookup.getOrThrow(Enchantments.PROTECTION);

			for (EquipmentSlot slot : ARMOUR_SLOTS) {
				ItemEnchantments enchantments = entity.getItemBySlot(slot).get(DataComponents.ENCHANTMENTS);

				if (enchantments != null) {
					points += enchantments.getLevel(blast) * 2 + enchantments.getLevel(plain);
				}
			}
		} catch (RuntimeException e) {
			return 0;
		}

		return points;
	}

	/** Resistance takes a fifth per level. Only our own effects are known on the client. */
	private static double resistance(final LivingEntity entity, final double damage) {
		MobEffectInstance effect = entity.getEffect(MobEffects.RESISTANCE);

		if (effect == null) {
			return damage;
		}

		return damage * Math.max(0.0, 1.0 - (effect.getAmplifier() + 1) * 0.2);
	}

	/** A raised shield only helps against what it faces, same condition as the server. */
	private static double shield(final Minecraft minecraft, final LivingEntity entity, final Vec3 centre, final double damage) {
		if (!entity.isBlocking() || minecraft.level == null) {
			return damage;
		}

		BlocksAttacks blocks = entity.getItemBlockingWith().get(DataComponents.BLOCKS_ATTACKS);

		if (blocks == null) {
			return damage;
		}

		Vec3 toBlast = centre.subtract(entity.position()).normalize();
		Vec3 facing = entity.getLookAngle().normalize();

		if (toBlast.dot(facing) <= 0.0) {
			return damage;
		}

		try {
			double angle = Math.acos(Mth.clamp(toBlast.dot(facing), -1.0, 1.0));
			return blocks.resolveBlockedDamage(minecraft.level.damageSources().explosion(null, null), (float) damage, angle);
		} catch (RuntimeException e) {
			return damage;
		}
	}

	/** Health plus absorption hearts. */
	public static double effectiveHealth(final LivingEntity entity) {
		return entity.getHealth() + entity.getAbsorptionAmount();
	}

	/** Holds anything that saves from death (a totem) in either hand, so a lethal hit only pops it. */
	public static boolean holdsTotem(final LivingEntity entity) {
		return entity.getMainHandItem().has(DataComponents.DEATH_PROTECTION)
				|| entity.getOffhandItem().has(DataComponents.DEATH_PROTECTION);
	}

	/**
	 * What the target wears, the way you would size someone up: armour material per slot,
	 * protection levels and whether a totem is in hand.
	 */
	public static String describeGear(final ClientLevel level, final LivingEntity entity) {
		StringBuilder gear = new StringBuilder();

		for (EquipmentSlot slot : ARMOUR_SLOTS) {
			ItemStack stack = entity.getItemBySlot(slot);
			gear.append(stack.isEmpty() ? "-" : material(stack)).append(' ');
		}

		gear.append(String.format("| Rüstung %.0f, Härte %.0f, Schutz %d",
				(double) entity.getArmorValue(), entity.getAttributeValue(Attributes.ARMOR_TOUGHNESS),
				protectionPoints(level, entity)));
		gear.append(holdsTotem(entity) ? " | TOTEM" : " | kein Totem");
		return gear.toString();
	}

	/** "netherite_chestplate" -> "Netherite", "elytra" -> "Elytra". */
	private static String material(final ItemStack stack) {
		String path = stack.getItem().builtInRegistryHolder().key().identifier().getPath();
		String first = path.contains("_") ? path.substring(0, path.indexOf('_')) : path;
		return Character.toUpperCase(first.charAt(0)) + first.substring(1);
	}
}
