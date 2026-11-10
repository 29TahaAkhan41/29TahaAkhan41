package com.tahaakhan.spellmod.client;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.mana.ManaData;
import com.tahaakhan.spellmod.spell.Spell;
import com.tahaakhan.spellmod.spell.SpellCasting;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;

/** Draws the stage and mana bar once the player has awakened to mana. */
@EventBusSubscriber(modid = SpellMod.MODID, value = Dist.CLIENT)
public final class ManaHud {
    private static final int BAR_WIDTH = 82;
    private static final int BAR_HEIGHT = 7;

    private ManaHud() {}

    @SubscribeEvent
    static void registerLayers(RegisterGuiLayersEvent event) {
        event.registerAbove(VanillaGuiLayers.HOTBAR, SpellMod.id("mana_bar"), ManaHud::render);
    }

    private static void render(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
        Minecraft minecraft = Minecraft.getInstance();
        LocalPlayer player = minecraft.player;
        if (player == null || minecraft.gui.hud.isHidden() || player.isSpectator()) {
            return;
        }
        ManaData data = Mana.get(player);
        if (data.capacity() <= 0) {
            return;
        }

        int x = 8;
        int y = 8;
        graphics.text(minecraft.font, data.stage().displayName(), x, y, 0xFFFFFFFF, true);
        y += 11;
        graphics.fill(x - 1, y - 1, x + BAR_WIDTH + 1, y + BAR_HEIGHT + 1, 0xFF000000);
        graphics.fill(x, y, x + BAR_WIDTH, y + BAR_HEIGHT, 0xFF1B1B4B);
        int filled = Math.round(BAR_WIDTH * (data.mana() / (float) data.capacity()));
        graphics.fill(x, y, x + filled, y + BAR_HEIGHT, 0xFF3F7BFF);
        graphics.text(minecraft.font, Component.literal(data.mana() + " / " + data.capacity()), x + BAR_WIDTH + 5, y, 0xFFAEC6FF, true);

        Spell spell = SpellCasting.selected(player);
        if (spell != null) {
            y += 11;
            int power = SpellCasting.effectivePower(SpellCasting.get(player), data, spell);
            if (power <= 0) {
                graphics.text(minecraft.font, Component.translatable("hud.spellmod.spell_locked", spell.displayName(), spell.minStage().displayName()),
                        x, y, 0xFF9A9A9A, true);
            } else {
                int cost = spell.manaCost(power);
                graphics.text(minecraft.font, Component.translatable("hud.spellmod.spell", spell.displayName(), power, cost),
                        x, y, data.mana() >= cost ? 0xFFFFFFFF : 0xFFFF6B6B, true);
            }
        }
    }
}
