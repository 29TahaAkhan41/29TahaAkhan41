package com.tahaakhan.spellmod.mana;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;

/** How used to mana a player's body is. Decided purely by mana capacity. */
public enum ManaStage {
    UNAWAKENED("unawakened", 0, ChatFormatting.GRAY),
    AWAKENED("awakened", 1, ChatFormatting.WHITE),
    APPRENTICE("apprentice", 20, ChatFormatting.GREEN),
    ADEPT("adept", 50, ChatFormatting.AQUA),
    MAGE("mage", 100, ChatFormatting.LIGHT_PURPLE),
    ARCHMAGE("archmage", 200, ChatFormatting.GOLD);

    private static final ManaStage[] VALUES = values();

    private final String name;
    private final int minCapacity;
    private final ChatFormatting color;

    ManaStage(String name, int minCapacity, ChatFormatting color) {
        this.name = name;
        this.minCapacity = minCapacity;
        this.color = color;
    }

    public int minCapacity() {
        return minCapacity;
    }

    public Component displayName() {
        return Component.translatable("stage.spellmod." + name).withStyle(color);
    }

    public static ManaStage forCapacity(int capacity) {
        ManaStage result = UNAWAKENED;
        for (ManaStage stage : VALUES) {
            if (capacity >= stage.minCapacity) {
                result = stage;
            }
        }
        return result;
    }
}
