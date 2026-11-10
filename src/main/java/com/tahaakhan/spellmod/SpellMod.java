package com.tahaakhan.spellmod;

import com.tahaakhan.spellmod.gametest.SpellGameTests;
import com.tahaakhan.spellmod.registry.ModAttachments;
import com.tahaakhan.spellmod.registry.ModCreativeTabs;
import com.tahaakhan.spellmod.registry.ModDataComponents;
import com.tahaakhan.spellmod.registry.ModItems;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

@Mod(SpellMod.MODID)
public class SpellMod {
    public static final String MODID = "spellmod";

    public SpellMod(IEventBus modEventBus) {
        ModDataComponents.DATA_COMPONENTS.register(modEventBus);
        ModAttachments.ATTACHMENT_TYPES.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModCreativeTabs.CREATIVE_TABS.register(modEventBus);
        SpellGameTests.register(modEventBus);
    }

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MODID, path);
    }
}
