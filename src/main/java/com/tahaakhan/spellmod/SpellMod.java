package com.tahaakhan.spellmod;

import com.tahaakhan.spellmod.gametest.ManaGameTests;
import com.tahaakhan.spellmod.registry.ModAttachments;
import com.tahaakhan.spellmod.registry.ModBlocks;
import com.tahaakhan.spellmod.registry.ModCreativeTabs;
import com.tahaakhan.spellmod.registry.ModItems;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

@Mod(SpellMod.MODID)
public class SpellMod {
    public static final String MODID = "spellmod";

    public SpellMod(IEventBus modEventBus) {
        ModAttachments.ATTACHMENT_TYPES.register(modEventBus);
        ModBlocks.BLOCKS.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModCreativeTabs.CREATIVE_TABS.register(modEventBus);
        ManaGameTests.register(modEventBus);
    }

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MODID, path);
    }
}
