package com.tahaakhan.spellmod.world;

import com.mojang.serialization.Codec;
import com.tahaakhan.spellmod.SpellMod;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import it.unimi.dsi.fastutil.longs.LongSet;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.StructureTags;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/** Remembers, per dimension, which villages have already given out their one spell book. */
public class VillageBooks extends SavedData {
    private static final Codec<VillageBooks> CODEC = Codec.LONG.listOf().xmap(VillageBooks::new, books -> List.copyOf(books.claimed));
    public static final SavedDataType<VillageBooks> TYPE = new SavedDataType<>(SpellMod.id("village_books"), VillageBooks::new, CODEC);

    private final LongSet claimed = new LongOpenHashSet();

    public VillageBooks() {}

    private VillageBooks(List<Long> claimed) {
        this.claimed.addAll(claimed);
    }

    public static VillageBooks get(ServerLevel level) {
        return level.getDataStorage().computeIfAbsent(TYPE);
    }

    /**
     * Marks a village as having given out its book.
     *
     * @param villageKey identifies the village (the packed chunk position where it starts)
     * @return true the first time for each village, false afterwards
     */
    public boolean claim(long villageKey) {
        if (!claimed.add(villageKey)) {
            return false;
        }
        setDirty();
        return true;
    }

    /**
     * Whether a chest at this position may contain a spell book. True once per village;
     * always true outside villages (for example a wizard house placed by hand).
     */
    public static boolean claimBookAt(ServerLevel level, BlockPos pos) {
        StructureStart village = level.structureManager().getStructureWithPieceAt(pos, StructureTags.VILLAGE);
        return !village.isValid() || get(level).claim(village.getChunkPos().pack());
    }
}
