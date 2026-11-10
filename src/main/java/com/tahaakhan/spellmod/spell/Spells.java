package com.tahaakhan.spellmod.spell;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.mana.ManaStage;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** All spells in the game. To add one, write its effect and register it here, then translate its name. */
public final class Spells {
    private static final Map<Identifier, Spell> SPELLS = new LinkedHashMap<>();

    // PLACEHOLDERS: two simple spells so the learning and casting system can be used and tested.
    // They are meant to be replaced by the real spell list.
    public static final Spell MANA_BOLT = register("mana_bolt", ManaStage.AWAKENED, 2, 10, Spells::manaBolt);
    public static final Spell MANA_BURST = register("mana_burst", ManaStage.MAGE, 60, 60, Spells::manaBurst);

    private Spells() {}

    private static Spell register(String name, ManaStage minStage, int baseManaCost, int cooldownTicks, Spell.Effect effect) {
        Spell spell = new Spell(SpellMod.id(name), minStage, baseManaCost, cooldownTicks, effect);
        SPELLS.put(spell.id(), spell);
        return spell;
    }

    public static @Nullable Spell get(Identifier id) {
        return SPELLS.get(id);
    }

    public static Collection<Spell> all() {
        return Collections.unmodifiableCollection(SPELLS.values());
    }

    /** A beam that damages the first creature in its path. Power adds range and damage. */
    private static boolean manaBolt(ServerLevel level, ServerPlayer caster, int power) {
        double range = 12.0 + 4.0 * power;
        Vec3 from = caster.getEyePosition();
        Vec3 look = caster.getLookAngle();
        HitResult hit = ProjectileUtil.getHitResultOnViewVector(
                caster, entity -> entity instanceof LivingEntity && entity.isAlive() && !entity.isSpectator(), range);
        Vec3 to = hit.getType() == HitResult.Type.MISS ? from.add(look.scale(range)) : hit.getLocation();

        double length = from.distanceTo(to);
        for (double d = 1.0; d < length; d += 0.5) {
            Vec3 p = from.add(look.scale(d));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
        }
        level.playSound(null, caster.getX(), caster.getY(), caster.getZ(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 1.8F);
        if (hit instanceof EntityHitResult entityHit) {
            entityHit.getEntity().hurtServer(level, caster.damageSources().indirectMagic(caster, caster), 2.0F + 2.0F * power);
        }
        return true;
    }

    /** A blast around the caster that damages and pushes away every creature nearby. Power adds radius and damage. */
    private static boolean manaBurst(ServerLevel level, ServerPlayer caster, int power) {
        double radius = 4.0 + power;
        for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, caster.getBoundingBox().inflate(radius),
                entity -> entity != caster && entity.isAlive() && entity.distanceTo(caster) <= radius)) {
            target.hurtServer(level, caster.damageSources().indirectMagic(caster, caster), 8.0F + 4.0F * power);
            Vec3 away = target.position().subtract(caster.position()).normalize();
            target.push(away.x * 1.2, 0.5, away.z * 1.2);
        }
        level.sendParticles(ParticleTypes.END_ROD, caster.getX(), caster.getY() + 1.0, caster.getZ(), 150, radius / 3, 0.5, radius / 3, 0.3);
        level.playSound(null, caster.getX(), caster.getY(), caster.getZ(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.0F, 1.4F);
        return true;
    }
}
