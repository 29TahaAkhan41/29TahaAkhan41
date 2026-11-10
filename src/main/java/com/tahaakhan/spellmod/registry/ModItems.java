package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.item.ManaCrystalItem;
import com.tahaakhan.spellmod.item.WandItem;
import com.tahaakhan.spellmod.spell.Spell;
import net.minecraft.world.item.Rarity;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(SpellMod.MODID);

    public static final DeferredItem<WandItem> WAND = ITEMS.registerItem("wand", WandItem::new,
            props -> props.stacksTo(1).rarity(Rarity.RARE).component(ModDataComponents.SELECTED_SPELL, Spell.FIREBALL));

    public static final DeferredItem<ManaCrystalItem> MANA_CRYSTAL = ITEMS.registerItem("mana_crystal", ManaCrystalItem::new,
            props -> props.rarity(Rarity.UNCOMMON));

    private ModItems() {}
}
