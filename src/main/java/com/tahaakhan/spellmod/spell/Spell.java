package com.tahaakhan.spellmod.spell;

import com.tahaakhan.spellmod.mana.ManaStage;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

/**
 * A spell that can be learned from a book and cast.
 *
 * @param id            unique name, also used for the translation key {@code spell.<namespace>.<path>}
 * @param minStage      the stage a player must have reached to cast it at all
 * @param baseManaCost  mana cost at power 1; this is the least mana the spell can ever be cast with
 * @param cooldownTicks time before the player can cast anything again
 * @param effect        what the spell does
 */
public record Spell(Identifier id, ManaStage minStage, int baseManaCost, int cooldownTicks, Effect effect) {
    public MutableComponent displayName() {
        return Component.translatable("spell." + id.getNamespace() + "." + id.getPath());
    }

    /**
     * The highest power this spell can be cast with at the given stage: 1 at the spell's own
     * stage, one more for every stage above it, 0 if the stage is too low to cast it at all.
     */
    public int maxPower(ManaStage stage) {
        return Math.max(stage.ordinal() - minStage.ordinal() + 1, 0);
    }

    /** More power costs proportionally more mana. */
    public int manaCost(int power) {
        return baseManaCost * power;
    }

    @FunctionalInterface
    public interface Effect {
        /**
         * @param power 1 or more; the effect should get stronger with it
         * @return false if the spell could not be cast (no mana is spent in that case)
         */
        boolean cast(ServerLevel level, ServerPlayer caster, int power);
    }
}
