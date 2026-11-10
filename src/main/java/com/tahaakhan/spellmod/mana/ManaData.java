package com.tahaakhan.spellmod.mana;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * Everything the mod remembers about a player's relationship with mana.
 *
 * @param mana       refined mana currently held in the body
 * @param capacity   how much mana the body can hold; grows as the body gets used to mana
 * @param experience familiarity with mana; raises the chance of finding raw mana in broken blocks
 * @param refined    how many pieces of raw mana this player has put through a mana table; makes refining faster
 */
public record ManaData(int mana, int capacity, int experience, int refined) {
    public static final ManaData EMPTY = new ManaData(0, 0, 0, 0);

    public static final MapCodec<ManaData> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Codec.INT.fieldOf("mana").forGetter(ManaData::mana),
            Codec.INT.fieldOf("capacity").forGetter(ManaData::capacity),
            Codec.INT.fieldOf("experience").forGetter(ManaData::experience),
            Codec.INT.optionalFieldOf("refined", 0).forGetter(ManaData::refined)
    ).apply(i, ManaData::new));

    public static final StreamCodec<ByteBuf, ManaData> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, ManaData::mana,
            ByteBufCodecs.VAR_INT, ManaData::capacity,
            ByteBufCodecs.VAR_INT, ManaData::experience,
            ByteBufCodecs.VAR_INT, ManaData::refined,
            ManaData::new);

    public ManaStage stage() {
        return ManaStage.forCapacity(capacity);
    }
}
