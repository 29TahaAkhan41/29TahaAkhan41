package com.tahaakhan.spellmod.registry;

import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.mana.ManaData;
import com.tahaakhan.spellmod.spell.SpellData;
import java.util.function.Supplier;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

public final class ModAttachments {
    public static final DeferredRegister<AttachmentType<?>> ATTACHMENT_TYPES =
            DeferredRegister.create(NeoForgeRegistries.ATTACHMENT_TYPES, SpellMod.MODID);

    /** Saved with the player, kept on death and synced to the client so the HUD can draw it. */
    public static final Supplier<AttachmentType<ManaData>> MANA = ATTACHMENT_TYPES.register("mana",
            () -> AttachmentType.builder(() -> ManaData.EMPTY)
                    .serialize(ManaData.CODEC)
                    .copyOnDeath()
                    .sync(ManaData.STREAM_CODEC)
                    .build());

    /** Learned spells and the current spell setup. Saved, kept on death and synced for the HUD. */
    public static final Supplier<AttachmentType<SpellData>> SPELLS = ATTACHMENT_TYPES.register("spells",
            () -> AttachmentType.builder(() -> SpellData.EMPTY)
                    .serialize(SpellData.CODEC)
                    .copyOnDeath()
                    .sync(SpellData.STREAM_CODEC)
                    .build());

    private ModAttachments() {}
}
