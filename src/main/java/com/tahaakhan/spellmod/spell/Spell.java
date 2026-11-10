package com.tahaakhan.spellmod.spell;

import com.mojang.serialization.Codec;
import io.netty.buffer.ByteBuf;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.StringRepresentable;

/**
 * Every spell the wand can cast. To add a new spell, add a constant here with its
 * mana cost, cooldown and effect, then add its name to the lang files.
 */
public enum Spell implements StringRepresentable {
    FIREBALL("fireball", 20, 15, ChatFormatting.GOLD, SpellEffects::fireball),
    HEAL("heal", 30, 40, ChatFormatting.GREEN, SpellEffects::heal),
    BLINK("blink", 25, 30, ChatFormatting.LIGHT_PURPLE, SpellEffects::blink),
    LIGHTNING("lightning", 40, 60, ChatFormatting.AQUA, SpellEffects::lightning);

    private static final Spell[] VALUES = values();
    public static final Codec<Spell> CODEC = StringRepresentable.fromEnum(Spell::values);
    public static final StreamCodec<ByteBuf, Spell> STREAM_CODEC = ByteBufCodecs.idMapper(i -> VALUES[Math.floorMod(i, VALUES.length)], Spell::ordinal);

    private final String name;
    private final int manaCost;
    private final int cooldownTicks;
    private final ChatFormatting color;
    private final Effect effect;

    Spell(String name, int manaCost, int cooldownTicks, ChatFormatting color, Effect effect) {
        this.name = name;
        this.manaCost = manaCost;
        this.cooldownTicks = cooldownTicks;
        this.color = color;
        this.effect = effect;
    }

    public int manaCost() {
        return manaCost;
    }

    public int cooldownTicks() {
        return cooldownTicks;
    }

    public Spell next() {
        return VALUES[(ordinal() + 1) % VALUES.length];
    }

    public Component displayName() {
        return Component.translatable("spell.spellmod." + name).withStyle(color);
    }

    /** @return false if the spell could not be cast (no mana is spent in that case). */
    public boolean cast(ServerLevel level, ServerPlayer caster) {
        return effect.cast(level, caster);
    }

    @Override
    public String getSerializedName() {
        return name;
    }

    @FunctionalInterface
    public interface Effect {
        boolean cast(ServerLevel level, ServerPlayer caster);
    }
}
