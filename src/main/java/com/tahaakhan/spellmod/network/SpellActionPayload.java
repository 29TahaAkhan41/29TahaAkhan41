package com.tahaakhan.spellmod.network;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.spell.SpellCasting;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Sent by the client when one of the spell keys is pressed. */
public record SpellActionPayload(Action action) implements CustomPacketPayload {
    public enum Action {
        CAST, NEXT_SPELL, POWER_UP, POWER_DOWN;

        private static final Action[] VALUES = values();
    }

    public static final Type<SpellActionPayload> TYPE = new Type<>(SpellMod.id("spell_action"));
    public static final StreamCodec<ByteBuf, SpellActionPayload> STREAM_CODEC = ByteBufCodecs.VAR_INT.map(
            i -> new SpellActionPayload(Action.VALUES[Math.floorMod(i, Action.VALUES.length)]),
            payload -> payload.action().ordinal());

    @Override
    public Type<SpellActionPayload> type() {
        return TYPE;
    }

    private static void handle(SpellActionPayload payload, IPayloadContext context) {
        if (!(context.player() instanceof ServerPlayer player) || player.isSpectator()) {
            return;
        }
        switch (payload.action()) {
            case CAST -> SpellCasting.castSelected(player);
            case NEXT_SPELL -> SpellCasting.selectNext(player);
            case POWER_UP -> SpellCasting.changePower(player, 1);
            case POWER_DOWN -> SpellCasting.changePower(player, -1);
        }
    }

    @EventBusSubscriber(modid = SpellMod.MODID)
    static final class Registration {
        private Registration() {}

        @SubscribeEvent
        static void register(RegisterPayloadHandlersEvent event) {
            event.registrar("1").playToServer(TYPE, STREAM_CODEC, SpellActionPayload::handle);
        }
    }
}
