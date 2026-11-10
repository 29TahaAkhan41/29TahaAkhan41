package com.tahaakhan.spellmod.spell;

import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.mana.ManaData;
import com.tahaakhan.spellmod.mana.ManaStage;
import com.tahaakhan.spellmod.registry.ModAttachments;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import org.jspecify.annotations.Nullable;

/** Learning, selecting and casting spells. */
public final class SpellCasting {
    /** Game time before which each player cannot cast again. Not saved: cooldowns end on restart. */
    private static final Map<UUID, Long> NEXT_CAST_TIME = new ConcurrentHashMap<>();

    private SpellCasting() {}

    public enum CastResult {
        SUCCESS, NO_SPELL, STAGE_TOO_LOW, NOT_ENOUGH_MANA, ON_COOLDOWN, FAILED
    }

    public static SpellData get(Player player) {
        return player.getData(ModAttachments.SPELLS);
    }

    private static void set(Player player, SpellData data) {
        if (!data.equals(get(player))) {
            player.setData(ModAttachments.SPELLS, data);
        }
    }

    /** @return false if the player already knew the spell */
    public static boolean learn(Player player, Spell spell) {
        SpellData data = get(player);
        if (data.knows(spell.id())) {
            return false;
        }
        set(player, data.withLearned(spell.id()));
        return true;
    }

    public static @Nullable Spell selected(Player player) {
        return get(player).selected().map(Spells::get).orElse(null);
    }

    /**
     * The power the player would cast the selected spell with right now: what they asked for,
     * but never more than their stage allows. 0 means their stage is too low for the spell.
     */
    public static int effectivePower(SpellData spells, ManaData mana, Spell spell) {
        return Math.min(Math.max(spells.power(), 1), spell.maxPower(mana.stage()));
    }

    /** Switches to the next known spell. */
    public static void selectNext(ServerPlayer player) {
        SpellData data = get(player);
        List<Identifier> known = data.known();
        if (known.isEmpty()) {
            player.sendOverlayMessage(Component.translatable("message.spellmod.no_spells").withStyle(ChatFormatting.GRAY));
            return;
        }
        int index = data.selected().map(known::indexOf).orElse(-1);
        set(player, data.withSelected(known.get((index + 1) % known.size())));
        announce(player);
    }

    /** Raises or lowers the power the player casts with, within what their stage allows for the selected spell. */
    public static void changePower(ServerPlayer player, int delta) {
        Spell spell = selected(player);
        if (spell == null) {
            player.sendOverlayMessage(Component.translatable("message.spellmod.no_spells").withStyle(ChatFormatting.GRAY));
            return;
        }
        SpellData data = get(player);
        int max = Math.max(spell.maxPower(Mana.get(player).stage()), 1);
        set(player, data.withPower(Math.clamp(data.power() + delta, 1, max)));
        announce(player);
    }

    private static void announce(ServerPlayer player) {
        Spell spell = selected(player);
        if (spell == null) {
            return;
        }
        ManaStage stage = Mana.get(player).stage();
        int power = effectivePower(get(player), Mana.get(player), spell);
        if (power <= 0) {
            player.sendOverlayMessage(Component.translatable("message.spellmod.selected_locked",
                    spell.displayName(), spell.minStage().displayName()).withStyle(ChatFormatting.GRAY));
        } else {
            player.sendOverlayMessage(Component.translatable("message.spellmod.selected",
                    spell.displayName(), power, spell.maxPower(stage), spell.manaCost(power)));
        }
    }

    /** Casts the selected spell and tells the player why if it did not work. */
    public static CastResult castSelected(ServerPlayer player) {
        Spell spell = selected(player);
        CastResult result = spell == null ? CastResult.NO_SPELL : cast(player, spell, get(player).power());
        switch (result) {
            case NO_SPELL -> player.sendOverlayMessage(Component.translatable("message.spellmod.no_spells").withStyle(ChatFormatting.GRAY));
            case STAGE_TOO_LOW -> player.sendOverlayMessage(Component.translatable("message.spellmod.stage_too_low",
                    spell.displayName(), spell.minStage().displayName()).withStyle(ChatFormatting.RED));
            case NOT_ENOUGH_MANA -> player.sendOverlayMessage(Component.translatable("message.spellmod.no_mana",
                    spell.manaCost(effectivePower(get(player), Mana.get(player), spell))).withStyle(ChatFormatting.RED));
            case FAILED -> player.sendOverlayMessage(Component.translatable("message.spellmod.fizzle").withStyle(ChatFormatting.GRAY));
            default -> {}
        }
        return result;
    }

    /**
     * Casts a spell the player knows.
     *
     * @param wantedPower the power asked for; lowered to what the player's stage allows
     */
    public static CastResult cast(ServerPlayer player, Spell spell, int wantedPower) {
        if (!get(player).knows(spell.id())) {
            return CastResult.NO_SPELL;
        }
        ManaData mana = Mana.get(player);
        int power = Math.min(Math.max(wantedPower, 1), spell.maxPower(mana.stage()));
        if (power <= 0) {
            return CastResult.STAGE_TOO_LOW;
        }
        ServerLevel level = player.level();
        long now = level.getGameTime();
        if (now < NEXT_CAST_TIME.getOrDefault(player.getUUID(), 0L)) {
            return CastResult.ON_COOLDOWN;
        }
        boolean free = player.hasInfiniteMaterials();
        int cost = spell.manaCost(power);
        if (!free && mana.mana() < cost) {
            return CastResult.NOT_ENOUGH_MANA;
        }
        if (!spell.effect().cast(level, player, power)) {
            return CastResult.FAILED;
        }
        if (!free) {
            Mana.set(player, new ManaData(mana.mana() - cost, mana.capacity(), mana.experience(), mana.refined()));
        }
        NEXT_CAST_TIME.put(player.getUUID(), now + spell.cooldownTicks());
        return CastResult.SUCCESS;
    }

    /** For tests. */
    public static void clearCooldown(Player player) {
        NEXT_CAST_TIME.remove(player.getUUID());
    }
}
