package com.tahaakhan.spellmod.client;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.mana.ManaData;
import com.tahaakhan.spellmod.menu.ManaTableMenu;
import com.tahaakhan.spellmod.registry.ModMenus;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;

/** The blue mana table window. Everything is drawn with plain rectangles, no texture file. */
@EventBusSubscriber(modid = SpellMod.MODID, value = Dist.CLIENT)
public class ManaTableScreen extends AbstractContainerScreen<ManaTableMenu> {
    private static final int PANEL = 0xFF1B2A6B;
    private static final int PANEL_LIGHT = 0xFF4F7BFF;
    private static final int PANEL_DARK = 0xFF0B1238;
    private static final int INSET = 0xFF14204F;
    private static final int SLOT = 0xFF0E1740;
    private static final int TEXT = 0xFFDCE8FF;
    private static final int TEXT_DIM = 0xFF9DB4F0;
    private static final int BAR_FILL = 0xFF5FB4FF;
    private static final int BAR_TIP = 0xFFE6F4FF;

    private static final int BAR_X = 62, BAR_Y = 39, BAR_WIDTH = 54, BAR_HEIGHT = 8;
    private static final int INFO_X = 62, INFO_Y = 17;

    private Button refineButton;

    public ManaTableScreen(ManaTableMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
    }

    @SubscribeEvent
    static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(ModMenus.MANA_TABLE.get(), ManaTableScreen::new);
    }

    @Override
    protected void init() {
        super.init();
        titleLabelX = (imageWidth - font.width(title)) / 2;
        refineButton = addRenderableWidget(Button.builder(Component.translatable("gui.spellmod.refine"), button -> {
            if (menu.clickMenuButton(minecraft.player, ManaTableMenu.BUTTON_REFINE)) {
                minecraft.gameMode.handleInventoryButtonClick(menu.containerId, ManaTableMenu.BUTTON_REFINE);
            }
        }).bounds(leftPos + BAR_X, topPos + 53, BAR_WIDTH, 16).build());
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        refineButton.active = menu.canStart();
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float a) {
        super.extractBackground(graphics, mouseX, mouseY, a);
        int x = leftPos;
        int y = topPos;

        // Window: dark outline, raised blue panel.
        graphics.fill(x, y, x + imageWidth, y + imageHeight, PANEL_DARK);
        graphics.fill(x + 1, y + 1, x + imageWidth - 1, y + imageHeight - 1, PANEL_LIGHT);
        graphics.fill(x + 2, y + 2, x + imageWidth - 1, y + imageHeight - 1, PANEL_DARK);
        graphics.fill(x + 2, y + 2, x + imageWidth - 2, y + imageHeight - 2, PANEL);
        // Working area behind the table slots.
        graphics.fill(x + 7, y + 14, x + imageWidth - 7, y + 73, PANEL_DARK);
        graphics.fill(x + 8, y + 15, x + imageWidth - 8, y + 72, INSET);

        for (Slot slot : menu.slots) {
            int sx = x + slot.x;
            int sy = y + slot.y;
            graphics.fill(sx - 1, sy - 1, sx + 17, sy + 17, PANEL_DARK);
            graphics.fill(sx, sy, sx + 17, sy + 17, PANEL_LIGHT);
            graphics.fill(sx, sy, sx + 16, sy + 16, SLOT);
        }

        // Progress bar.
        int bx = x + BAR_X;
        int by = y + BAR_Y;
        graphics.fill(bx - 1, by - 1, bx + BAR_WIDTH + 1, by + BAR_HEIGHT + 1, PANEL_DARK);
        graphics.fill(bx, by, bx + BAR_WIDTH, by + BAR_HEIGHT, SLOT);
        if (menu.isRunning() && menu.total() > 0) {
            int filled = Math.clamp((long) BAR_WIDTH * menu.progress() / menu.total(), 0, BAR_WIDTH);
            graphics.fill(bx, by, bx + filled, by + BAR_HEIGHT, BAR_FILL);
            if (filled > 0) {
                graphics.fill(bx + filled - 1, by, bx + filled, by + BAR_HEIGHT, BAR_TIP);
            }
        }
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
        graphics.text(font, title, titleLabelX, titleLabelY, TEXT, false);
        graphics.text(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, TEXT, false);

        // While refining: time left and the risk of the piece on the table.
        // While idle: what the next piece would cost this player.
        int ticks;
        int lossPermille;
        if (menu.isRunning()) {
            ticks = Math.max(menu.total() - menu.progress(), 0);
            lossPermille = menu.lossPermille();
        } else {
            ManaData data = Mana.get(minecraft.player);
            ticks = Mana.refineTicks(data.refined());
            lossPermille = Math.round(Mana.lossChance(data) * 1000);
        }
        graphics.text(font, Component.translatable(menu.isRunning() ? "gui.spellmod.time_left" : "gui.spellmod.time", formatTime(ticks)),
                INFO_X, INFO_Y, TEXT, false);
        graphics.text(font, Component.translatable("gui.spellmod.loss", (lossPermille + 5) / 10),
                INFO_X, INFO_Y + 10, TEXT_DIM, false);
    }

    private static Component formatTime(int ticks) {
        int seconds = (ticks + 19) / 20;
        return seconds >= 60
                ? Component.translatable("gui.spellmod.minutes_seconds", seconds / 60, seconds % 60)
                : Component.translatable("gui.spellmod.seconds", seconds);
    }
}
