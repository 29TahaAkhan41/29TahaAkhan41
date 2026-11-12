package dev.lumina.client;

import dev.lumina.Lumina;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

@EventBusSubscriber(modid = Lumina.MODID, value = Dist.CLIENT)
public final class LuminaClient {
    private LuminaClient() {
    }

    @SubscribeEvent
    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(Lumina.PEDESTAL_BE.get(), PedestalRenderer::new);
    }
}
