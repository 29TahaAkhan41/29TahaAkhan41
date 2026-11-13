package dev.teknikmod.client;

import dev.teknikmod.ModRegistry;
import dev.teknikmod.TeknikMod;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;

@EventBusSubscriber(modid = TeknikMod.MODID, value = Dist.CLIENT)
public final class ClientSetup {
    @SubscribeEvent
    public static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(ModRegistry.COAL_GENERATOR_MENU.get(), CoalGeneratorScreen::new);
        event.register(ModRegistry.ELECTRIC_FURNACE_MENU.get(), ProcessingScreen::new);
        event.register(ModRegistry.CRUSHER_MENU.get(), ProcessingScreen::new);
    }

    private ClientSetup() {}
}
