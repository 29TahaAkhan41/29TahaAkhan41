package com.tahaakhan.spellmod;

import com.tahaakhan.spellmod.gametest.ManaGameTests;
import com.tahaakhan.spellmod.registry.ModAttachments;
import com.tahaakhan.spellmod.registry.ModBlockEntities;
import com.tahaakhan.spellmod.registry.ModBlocks;
import com.tahaakhan.spellmod.registry.ModCreativeTabs;
import com.tahaakhan.spellmod.registry.ModDataComponents;
import com.tahaakhan.spellmod.registry.ModItems;
import com.tahaakhan.spellmod.registry.ModLootFunctions;
import com.tahaakhan.spellmod.registry.ModMenus;
import com.tahaakhan.spellmod.registry.ModWorldgen;
import com.mojang.logging.LogUtils;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

@Mod(SpellMod.MODID)
public class SpellMod {
    public static final String MODID = "spellmod";
    public static final Logger LOGGER = LogUtils.getLogger();

    public SpellMod(IEventBus modEventBus) {
        ModDataComponents.DATA_COMPONENTS.register(modEventBus);
        ModAttachments.ATTACHMENT_TYPES.register(modEventBus);
        ModBlocks.BLOCKS.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModBlockEntities.BLOCK_ENTITY_TYPES.register(modEventBus);
        ModMenus.MENUS.register(modEventBus);
        ModLootFunctions.LOOT_FUNCTIONS.register(modEventBus);
        ModWorldgen.POOL_ELEMENT_TYPES.register(modEventBus);
        ModCreativeTabs.CREATIVE_TABS.register(modEventBus);
        ManaGameTests.register(modEventBus);
    }

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MODID, path);
    }
}
