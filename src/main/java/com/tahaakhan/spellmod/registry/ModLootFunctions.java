package com.tahaakhan.spellmod.registry;

import com.mojang.serialization.MapCodec;
import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.world.VillageSpellBookFunction;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.storage.loot.functions.LootItemFunction;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModLootFunctions {
    public static final DeferredRegister<MapCodec<? extends LootItemFunction>> LOOT_FUNCTIONS =
            DeferredRegister.create(Registries.LOOT_FUNCTION_TYPE, SpellMod.MODID);

    static {
        LOOT_FUNCTIONS.register("village_spell_book", () -> VillageSpellBookFunction.MAP_CODEC);
    }

    private ModLootFunctions() {}
}
