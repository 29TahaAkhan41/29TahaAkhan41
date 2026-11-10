package com.tahaakhan.spellmod.spell;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import io.netty.buffer.ByteBuf;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.Identifier;

/**
 * The spells a player has learned and how they are set up to cast.
 *
 * @param known    learned spells, in the order they were learned
 * @param selected the spell the cast key uses
 * @param power    the power the player wants to cast with (limited by their stage when casting)
 */
public record SpellData(List<Identifier> known, Optional<Identifier> selected, int power) {
    public static final SpellData EMPTY = new SpellData(List.of(), Optional.empty(), 1);

    public static final MapCodec<SpellData> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Identifier.CODEC.listOf().fieldOf("known").forGetter(SpellData::known),
            Identifier.CODEC.optionalFieldOf("selected").forGetter(SpellData::selected),
            Codec.INT.optionalFieldOf("power", 1).forGetter(SpellData::power)
    ).apply(i, SpellData::new));

    public static final StreamCodec<ByteBuf, SpellData> STREAM_CODEC = StreamCodec.composite(
            Identifier.STREAM_CODEC.apply(ByteBufCodecs.list()), SpellData::known,
            ByteBufCodecs.optional(Identifier.STREAM_CODEC), SpellData::selected,
            ByteBufCodecs.VAR_INT, SpellData::power,
            SpellData::new);

    public SpellData {
        known = List.copyOf(known);
    }

    public boolean knows(Identifier spell) {
        return known.contains(spell);
    }

    /** Adds the spell; the first spell learned is selected automatically. */
    public SpellData withLearned(Identifier spell) {
        List<Identifier> list = new ArrayList<>(known);
        list.add(spell);
        return new SpellData(list, selected.isPresent() ? selected : Optional.of(spell), power);
    }

    public SpellData withSelected(Identifier spell) {
        return new SpellData(known, Optional.of(spell), power);
    }

    public SpellData withPower(int newPower) {
        return new SpellData(known, selected, newPower);
    }
}
