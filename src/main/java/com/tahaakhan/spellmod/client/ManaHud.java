package com.tahaakhan.spellmod.client;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.item.WandItem;
import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.spell.Spell;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;

/** Draws the mana bar and the selected spell while a wand is held. */
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
        ItemStack wand = player.getMainHandItem();
        if (!(wand.getItem() instanceof WandItem)) {
            wand = player.getOffhandItem();
            if (!(wand.getItem() instanceof WandItem)) {
                return;
            }
        }

        int mana = Mana.get(player);
        Spell spell = WandItem.getSpell(wand);
        int x = 8;
        int y = 8;

        graphics.text(minecraft.font, spell.displayName(), x, y, 0xFFFFFFFF, true);
        y += 11;
        graphics.fill(x - 1, y - 1, x + BAR_WIDTH + 1, y + BAR_HEIGHT + 1, 0xFF000000);
        graphics.fill(x, y, x + BAR_WIDTH, y + BAR_HEIGHT, 0xFF1B1B4B);
        int filled = Math.round(BAR_WIDTH * (mana / (float) Mana.MAX));
        // Turns red when the selected spell is not affordable.
        int color = mana >= spell.manaCost() ? 0xFF3F7BFF : 0xFFC0392B;
        graphics.fill(x, y, x + filled, y + BAR_HEIGHT, color);
        graphics.text(minecraft.font, Component.literal(mana + " / " + Mana.MAX), x + BAR_WIDTH + 5, y, 0xFFAEC6FF, true);
    }
}
