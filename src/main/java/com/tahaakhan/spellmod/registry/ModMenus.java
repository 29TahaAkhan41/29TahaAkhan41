package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.menu.ManaTableMenu;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModMenus {
    public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, SpellMod.MODID);

    public static final Supplier<MenuType<ManaTableMenu>> MANA_TABLE = MENUS.register("mana_table",
            () -> new MenuType<>(ManaTableMenu::new, FeatureFlags.DEFAULT_FLAGS));

    private ModMenus() {}
}
