package com.tahaakhan.spellmod.world;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.tahaakhan.spellmod.item.SpellBookItem;
import com.tahaakhan.spellmod.mana.ManaStage;
import com.tahaakhan.spellmod.spell.Spell;
import com.tahaakhan.spellmod.spell.Spells;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.functions.LootItemConditionalFunction;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.minecraft.world.phys.Vec3;

/**
 * Loot function for the wizard house chest: turns the item into a spell book with a random
 * spell, or into nothing if this village has already given out its book.
 */
public class VillageSpellBookFunction extends LootItemConditionalFunction {
    public static final MapCodec<VillageSpellBookFunction> MAP_CODEC = RecordCodecBuilder.mapCodec(
            i -> commonFields(i).apply(i, VillageSpellBookFunction::new));

    private VillageSpellBookFunction(Optional<Holder<LootItemCondition>> condition) {
        super(condition);
    }

    @Override
    public MapCodec<VillageSpellBookFunction> codec() {
        return MAP_CODEC;
    }

    @Override
    protected ItemStack run(ItemStack stack, LootContext context) {
        Vec3 origin = context.getOptional(LootContextParams.ORIGIN);
        if (origin != null && !VillageBooks.claimBookAt(context.getLevel(), BlockPos.containing(origin))) {
            return ItemStack.EMPTY;
        }
        return SpellBookItem.of(randomSpell(context.getRandom()));
    }

    /** Spells of lower stages are more common. */
    public static Spell randomSpell(RandomSource random) {
        int total = 0;
        for (Spell spell : Spells.all()) {
            total += weight(spell);
        }
        int roll = random.nextInt(total);
        for (Spell spell : Spells.all()) {
            roll -= weight(spell);
            if (roll < 0) {
                return spell;
            }
        }
        throw new IllegalStateException("No spells registered");
    }

    private static int weight(Spell spell) {
        return ManaStage.values().length - spell.minStage().ordinal();
    }
}
