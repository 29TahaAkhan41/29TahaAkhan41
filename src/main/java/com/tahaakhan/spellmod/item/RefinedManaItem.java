package com.tahaakhan.spellmod.item;

import com.tahaakhan.spellmod.mana.Mana;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/** Right click to absorb the mana into your body. */
public class RefinedManaItem extends Item {
    public RefinedManaItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (!(level instanceof ServerLevel serverLevel)) {
            return InteractionResult.SUCCESS;
        }
        if (Mana.get(player).capacity() >= Mana.MAX_CAPACITY && Mana.get(player).mana() >= Mana.MAX_CAPACITY) {
            return InteractionResult.FAIL;
        }

        Mana.AbsorbResult result = Mana.absorb(player);
        player.getItemInHand(hand).consume(1, player);
        player.getCooldowns().addCooldown(player.getItemInHand(hand), 20);

        serverLevel.sendParticles(ParticleTypes.ENCHANT, player.getX(), player.getY() + 1.0, player.getZ(), 30, 0.4, 0.6, 0.4, 0.5);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 0.8F);

        if (result.damage() > 0.0F) {
            // The body is not used to this much mana yet.
            player.hurtServer(serverLevel, player.damageSources().magic(), result.damage());
            if (result.damage() >= 1.0F) {
                player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 140, 0));
                player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 200, 0));
                player.sendOverlayMessage(Component.translatable("message.spellmod.overflow").withStyle(ChatFormatting.RED));
            }
        }
        if (result.stageChanged()) {
            player.sendSystemMessage(Component.translatable("message.spellmod.stage_up", result.stageAfter().displayName()));
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8F, 1.0F);
        }
        return InteractionResult.SUCCESS_SERVER;
    }
}
