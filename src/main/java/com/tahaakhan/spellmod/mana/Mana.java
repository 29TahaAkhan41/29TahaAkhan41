package com.tahaakhan.spellmod.mana;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.registry.ModAttachments;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** Player mana: stored as a synced data attachment, regenerates over time. */
@EventBusSubscriber(modid = SpellMod.MODID)
public final class Mana {
    public static final int MAX = 100;
    /** One mana point every this many ticks (5 ticks = 4 mana per second). */
    private static final int REGEN_INTERVAL_TICKS = 5;

    private Mana() {}

    public static int get(Player player) {
        return player.getData(ModAttachments.MANA);
    }

    public static void set(Player player, int mana) {
        int clamped = Math.clamp(mana, 0, MAX);
        if (clamped != get(player)) {
            player.setData(ModAttachments.MANA, clamped);
        }
    }

    public static void add(Player player, int amount) {
        set(player, get(player) + amount);
    }

    @SubscribeEvent
    static void onPlayerTick(PlayerTickEvent.Post event) {
        if (event.getEntity() instanceof ServerPlayer player && player.tickCount % REGEN_INTERVAL_TICKS == 0) {
            add(player, 1);
        }
    }
}
