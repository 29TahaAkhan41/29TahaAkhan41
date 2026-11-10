package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.world.UniqueVillageHouseElement;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElementType;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModWorldgen {
    public static final DeferredRegister<StructurePoolElementType<?>> POOL_ELEMENT_TYPES =
            DeferredRegister.create(Registries.STRUCTURE_POOL_ELEMENT, SpellMod.MODID);

    public static final Supplier<StructurePoolElementType<UniqueVillageHouseElement>> UNIQUE_VILLAGE_HOUSE =
            POOL_ELEMENT_TYPES.register("unique_village_house", () -> () -> UniqueVillageHouseElement.CODEC);

    private ModWorldgen() {}
}
