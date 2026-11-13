package dev.teknikmod.client;

import dev.teknikmod.TeknikMod;
import dev.teknikmod.menu.ProcessingMenu;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;

public class ProcessingScreen extends AbstractContainerScreen<ProcessingMenu> {
    private static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath(TeknikMod.MODID, "textures/gui/processing.png");
    private static final int BAR_X = 152, BAR_Y = 17, BAR_W = 12, BAR_H = 52;
    // Ilerleme seridi (GUI'ye gore)
    private static final int ARROW_X = 77, ARROW_Y = 40, ARROW_W = 22, ARROW_H = 6;

    public ProcessingScreen(ProcessingMenu menu, Inventory inv, Component title) {
        super(menu, inv, title);
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        g.blit(TEXTURE, leftPos, topPos, 0, 0, imageWidth, imageHeight);
        int filled = menu.maxEnergy() == 0 ? 0 : (int) ((long) menu.energy() * BAR_H / menu.maxEnergy());
        if (filled > 0) {
            g.fillGradient(leftPos + BAR_X, topPos + BAR_Y + BAR_H - filled,
                    leftPos + BAR_X + BAR_W, topPos + BAR_Y + BAR_H, 0xFF5CF2F5, 0xFF1C8FB4);
        }
        if (menu.maxProgress() > 0 && menu.progress() > 0) {
            int w = Math.min(ARROW_W, menu.progress() * ARROW_W / menu.maxProgress());
            g.fill(leftPos + ARROW_X, topPos + ARROW_Y, leftPos + ARROW_X + w, topPos + ARROW_Y + ARROW_H, 0xFFFFC83C);
            g.fill(leftPos + ARROW_X, topPos + ARROW_Y, leftPos + ARROW_X + w, topPos + ARROW_Y + 1, 0xFFFFEFA0);
        }
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        g.drawString(font, title, titleLabelX, titleLabelY, 0xFFE2E6EE, false);
        g.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, 0xFF9AA2B2, false);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
        if (isHovering(BAR_X, BAR_Y, BAR_W, BAR_H, mouseX, mouseY)) {
            g.renderTooltip(font, Component.translatable("message.teknikmod.energy", menu.energy(), menu.maxEnergy()), mouseX, mouseY);
        } else if (isHovering(ARROW_X, ARROW_Y - 2, ARROW_W, ARROW_H + 4, mouseX, mouseY)) {
            int percent = menu.maxProgress() > 0 ? menu.progress() * 100 / menu.maxProgress() : 0;
            g.renderTooltip(font, Component.translatable("message.teknikmod.progress", percent, menu.usage()), mouseX, mouseY);
        }
    }
}
