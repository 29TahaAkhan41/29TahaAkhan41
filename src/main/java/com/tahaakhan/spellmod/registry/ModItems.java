package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.item.RefinedManaItem;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.ItemLore;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(SpellMod.MODID);

    /** Drops from broken blocks. Useless until it has been refined. */
    public static final DeferredItem<Item> RAW_MANA = ITEMS.registerSimpleItem("raw_mana",
            props -> props.rarity(Rarity.UNCOMMON).component(DataComponents.LORE, lore("tooltip.spellmod.raw_mana")));

    /** Made from raw mana; can be absorbed by the player. */
    public static final DeferredItem<RefinedManaItem> REFINED_MANA = ITEMS.registerItem("refined_mana", RefinedManaItem::new,
            props -> props.rarity(Rarity.RARE).component(DataComponents.LORE, lore("tooltip.spellmod.refined_mana")));

    /** Crafted around raw mana; the heart of the mana table. */
    public static final DeferredItem<Item> MANA_CAPSULE = ITEMS.registerSimpleItem("mana_capsule",
            props -> props.rarity(Rarity.UNCOMMON));

    public static final DeferredItem<BlockItem> MANA_TABLE = ITEMS.registerSimpleBlockItem(ModBlocks.MANA_TABLE,
            props -> props.rarity(Rarity.RARE));

    private ModItems() {}

    private static ItemLore lore(String key) {
        return new ItemLore(List.of(Component.translatable(key).withStyle(style -> style.withColor(ChatFormatting.GRAY).withItalic(false))));
    }
}
