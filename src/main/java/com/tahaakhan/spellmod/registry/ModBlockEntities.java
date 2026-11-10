package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.block.ManaTableBlockEntity;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModBlockEntities {
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITY_TYPES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, SpellMod.MODID);

    public static final Supplier<BlockEntityType<ManaTableBlockEntity>> MANA_TABLE = BLOCK_ENTITY_TYPES.register("mana_table",
            () -> new BlockEntityType<>(ManaTableBlockEntity::new, ModBlocks.MANA_TABLE.get()));

    private ModBlockEntities() {}
}
