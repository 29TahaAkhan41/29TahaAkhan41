package com.tahaakhan.spellmod.registry;

import com.mojang.serialization.Codec;
import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.mana.Mana;
import java.util.function.Supplier;
import net.minecraft.network.codec.ByteBufCodecs;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

public final class ModAttachments {
    public static final DeferredRegister<AttachmentType<?>> ATTACHMENT_TYPES =
            DeferredRegister.create(NeoForgeRegistries.ATTACHMENT_TYPES, SpellMod.MODID);

    /** Saved with the player and synced to the client so the HUD can draw it. */
    public static final Supplier<AttachmentType<Integer>> MANA = ATTACHMENT_TYPES.register("mana",
            () -> AttachmentType.builder(() -> Mana.MAX)
                    .serialize(Codec.INT.fieldOf("mana"))
                    .sync(ByteBufCodecs.VAR_INT)
                    .build());

    private ModAttachments() {}
}
