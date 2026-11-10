package com.tahaakhan.spellmod.spell;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.entity.projectile.hurtingprojectile.SmallFireball;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

final class SpellEffects {
    private static final double BLINK_RANGE = 16.0;
    private static final double LIGHTNING_RANGE = 48.0;

    private SpellEffects() {}

    static boolean fireball(ServerLevel level, ServerPlayer caster) {
        Vec3 look = caster.getLookAngle();
        SmallFireball fireball = new SmallFireball(level, caster, look.scale(1.5));
        Vec3 spawn = caster.getEyePosition().add(look.scale(0.8));
        fireball.setPos(spawn.x, spawn.y - 0.2, spawn.z);
        level.addFreshEntity(fireball);
        sound(level, caster.position(), SoundEvents.BLAZE_SHOOT, 1.2F);
        return true;
    }

    static boolean heal(ServerLevel level, ServerPlayer caster) {
        if (caster.getHealth() >= caster.getMaxHealth()) {
            return false;
        }
        caster.heal(8.0F);
        caster.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 0));
        level.sendParticles(ParticleTypes.HEART, caster.getX(), caster.getY() + 1.0, caster.getZ(), 8, 0.4, 0.5, 0.4, 0.0);
        sound(level, caster.position(), SoundEvents.AMETHYST_BLOCK_CHIME, 1.0F);
        return true;
    }

    static boolean blink(ServerLevel level, ServerPlayer caster) {
        HitResult hit = caster.pick(BLINK_RANGE, 1.0F, false);
        BlockPos target = hit instanceof BlockHitResult blockHit && hit.getType() == HitResult.Type.BLOCK
                ? blockHit.getBlockPos().relative(blockHit.getDirection())
                : BlockPos.containing(hit.getLocation());

        // Try the target block and the one above it, so we never end up inside a wall.
        for (int dy = 0; dy <= 1; dy++) {
            Vec3 dest = Vec3.atBottomCenterOf(target.above(dy));
            if (level.noCollision(caster, caster.getBoundingBox().move(dest.subtract(caster.position())))) {
                Vec3 from = caster.position();
                level.sendParticles(ParticleTypes.PORTAL, from.x, from.y + 1.0, from.z, 30, 0.3, 0.6, 0.3, 0.2);
                sound(level, from, SoundEvents.ENDERMAN_TELEPORT, 1.0F);
                caster.teleportTo(dest.x, dest.y, dest.z);
                caster.resetFallDistance();
                level.sendParticles(ParticleTypes.PORTAL, dest.x, dest.y + 1.0, dest.z, 30, 0.3, 0.6, 0.3, 0.2);
                sound(level, dest, SoundEvents.ENDERMAN_TELEPORT, 1.0F);
                return true;
            }
        }
        return false;
    }

    static boolean lightning(ServerLevel level, ServerPlayer caster) {
        HitResult hit = ProjectileUtil.getHitResultOnViewVector(
                caster, entity -> entity instanceof LivingEntity && entity.isAlive() && !entity.isSpectator(), LIGHTNING_RANGE);
        if (hit.getType() == HitResult.Type.MISS) {
            return false;
        }
        LightningBolt bolt = EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
        if (bolt == null) {
            return false;
        }
        Vec3 pos = hit.getLocation();
        bolt.setPos(pos.x, pos.y, pos.z);
        bolt.setCause(caster);
        level.addFreshEntity(bolt);
        return true;
    }

    private static void sound(ServerLevel level, Vec3 pos, SoundEvent sound, float pitch) {
        level.playSound(null, pos.x, pos.y, pos.z, sound, SoundSource.PLAYERS, 1.0F, pitch);
    }
}
