package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.spell.Spell;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModDataComponents {
    public static final DeferredRegister.DataComponents DATA_COMPONENTS =
            DeferredRegister.createDataComponents(Registries.DATA_COMPONENT_TYPE, SpellMod.MODID);

    /** Which spell a wand is currently set to. */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Spell>> SELECTED_SPELL =
            DATA_COMPONENTS.registerComponentType("selected_spell",
                    builder -> builder.persistent(Spell.CODEC).networkSynchronized(Spell.STREAM_CODEC));

    private ModDataComponents() {}
}
