package com.tahaakhan.spellmod.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.network.SpellActionPayload;
import com.tahaakhan.spellmod.network.SpellActionPayload.Action;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;

/** The keys for casting and setting up spells. All can be changed in Options > Controls. */
@EventBusSubscriber(modid = SpellMod.MODID, value = Dist.CLIENT)
public final class SpellKeys {
    private static final KeyMapping.Category CATEGORY = new KeyMapping.Category(SpellMod.id("spells"));

    private static final KeyMapping CAST = key("cast", InputConstants.KEY_R);
    private static final KeyMapping NEXT_SPELL = key("next_spell", InputConstants.KEY_G);
    private static final KeyMapping POWER_UP = key("power_up", InputConstants.KEY_V);
    private static final KeyMapping POWER_DOWN = key("power_down", InputConstants.KEY_C);

    private SpellKeys() {}

    private static KeyMapping key(String name, int keyCode) {
        return new KeyMapping("key.spellmod." + name, keyCode, CATEGORY);
    }

    @SubscribeEvent
    static void register(RegisterKeyMappingsEvent event) {
        event.registerCategory(CATEGORY);
        event.register(CAST);
        event.register(NEXT_SPELL);
        event.register(POWER_UP);
        event.register(POWER_DOWN);
    }

    @SubscribeEvent
    static void onClientTick(ClientTickEvent.Post event) {
        if (Minecraft.getInstance().player == null) {
            return;
        }
        send(CAST, Action.CAST);
        send(NEXT_SPELL, Action.NEXT_SPELL);
        send(POWER_UP, Action.POWER_UP);
        send(POWER_DOWN, Action.POWER_DOWN);
    }

    private static void send(KeyMapping key, Action action) {
        while (key.consumeClick()) {
            ClientPacketDistributor.sendToServer(new SpellActionPayload(action));
        }
    }
}
