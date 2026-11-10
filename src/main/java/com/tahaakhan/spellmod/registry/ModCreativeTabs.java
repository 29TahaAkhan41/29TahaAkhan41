package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModCreativeTabs {
    public static final DeferredRegister<CreativeModeTab> CREATIVE_TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, SpellMod.MODID);

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> MAIN = CREATIVE_TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.spellmod"))
                    .icon(() -> ModItems.REFINED_MANA.get().getDefaultInstance())
                    .displayItems((parameters, output) -> {
                        output.accept(ModItems.RAW_MANA.get());
                        output.accept(ModItems.REFINED_MANA.get());
                        output.accept(ModItems.MANA_CAPSULE.get());
                        output.accept(ModItems.MANA_TABLE.get());
                    })
                    .build());

    private ModCreativeTabs() {}
}
