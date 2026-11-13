package dev.teknikmod.client;

import dev.teknikmod.Config;
import dev.teknikmod.TeknikMod;
import dev.teknikmod.menu.CoalGeneratorMenu;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;

public class CoalGeneratorScreen extends AbstractContainerScreen<CoalGeneratorMenu> {
    private static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath(TeknikMod.MODID, "textures/gui/coal_generator.png");
    // Enerji cubugu (GUI'ye gore)
    private static final int BAR_X = 152, BAR_Y = 17, BAR_W = 12, BAR_H = 52;

    public CoalGeneratorScreen(CoalGeneratorMenu menu, Inventory inv, Component title) {
        super(menu, inv, title);
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        g.blit(TEXTURE, leftPos, topPos, 0, 0, imageWidth, imageHeight);
        // Enerji cubugu
        int filled = menu.maxEnergy() == 0 ? 0 : (int) ((long) menu.energy() * BAR_H / menu.maxEnergy());
        if (filled > 0) {
            g.fillGradient(leftPos + BAR_X, topPos + BAR_Y + BAR_H - filled,
                    leftPos + BAR_X + BAR_W, topPos + BAR_Y + BAR_H, 0xFFFF5A3C, 0xFFB01E1E);
        }
        // Yanma gostergesi (yakit yuvasinin ustunde, asagidan yukari azalir)
        if (menu.burnTime() > 0 && menu.burnTimeTotal() > 0) {
            int h = Math.max(1, menu.burnTime() * 14 / menu.burnTimeTotal());
            g.fillGradient(leftPos + 81, topPos + 26 + 14 - h, leftPos + 95, topPos + 40, 0xFFFFD83C, 0xFFFF7A00);
        }
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
        if (isHovering(BAR_X, BAR_Y, BAR_W, BAR_H, mouseX, mouseY)) {
            g.renderTooltip(font, Component.translatable("message.teknikmod.energy", menu.energy(), menu.maxEnergy()), mouseX, mouseY);
        } else if (isHovering(81, 26, 14, 14, mouseX, mouseY)) {
            g.renderTooltip(font, Component.translatable("message.teknikmod.rate",
                    menu.burnTime() > 0 ? Config.COAL_GENERATOR_RATE : 0), mouseX, mouseY);
        }
    }
}
