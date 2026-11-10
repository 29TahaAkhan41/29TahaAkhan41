package com.tahaakhan.spellmod.world;

import com.mojang.datafixers.util.Either;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.tahaakhan.spellmod.registry.ModWorldgen;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.StructureTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.pools.LegacySinglePoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElementType;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorList;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;

/**
 * A village house that is built at most once per village. The village layout may pick it for
 * several plots; only the first of them is actually built, the others stay empty.
 */
public class UniqueVillageHouseElement extends LegacySinglePoolElement {
    public static final MapCodec<UniqueVillageHouseElement> CODEC = RecordCodecBuilder.mapCodec(
            i -> i.group(templateCodec(), processorsCodec(), projectionCodec(), overrideLiquidSettingsCodec()).apply(i, UniqueVillageHouseElement::new));

    protected UniqueVillageHouseElement(Either<Identifier, StructureTemplate> template, Holder<StructureProcessorList> processors,
            StructureTemplatePool.Projection projection, Optional<LiquidSettings> liquidSettings) {
        super(template, processors, projection, liquidSettings);
    }

    public UniqueVillageHouseElement(Identifier template) {
        this(Either.left(template), Holder.direct(new StructureProcessorList(List.of())), StructureTemplatePool.Projection.RIGID, Optional.empty());
    }

    @Override
    public boolean place(StructureTemplateManager templateManager, WorldGenLevel level, StructureManager structureManager, ChunkGenerator generator,
            BlockPos position, BlockPos referencePos, Rotation rotation, BoundingBox chunkBox, RandomSource random, LiquidSettings liquidSettings,
            boolean keepJigsaws) {
        StructureStart village = structureManager.getStructureWithPieceAt(position, StructureTags.VILLAGE);
        if (village.isValid()) {
            for (StructurePiece piece : village.getPieces()) {
                if (piece instanceof PoolElementStructurePiece pooled && pooled.getElement() instanceof UniqueVillageHouseElement) {
                    if (!pooled.getPosition().equals(position)) {
                        return false; // Another plot of this village already has the house.
                    }
                    break;
                }
            }
        }
        return super.place(templateManager, level, structureManager, generator, position, referencePos, rotation, chunkBox, random, liquidSettings, keepJigsaws);
    }

    /** Whether this piece is the one of its kind that actually gets built in the given village. */
    public static boolean isBuilt(StructureStart village, PoolElementStructurePiece piece) {
        for (StructurePiece other : village.getPieces()) {
            if (other instanceof PoolElementStructurePiece pooled && pooled.getElement() instanceof UniqueVillageHouseElement) {
                return pooled == piece;
            }
        }
        return false;
    }

    @Override
    public StructurePoolElementType<?> getType() {
        return ModWorldgen.UNIQUE_VILLAGE_HOUSE.get();
    }

    @Override
    public String toString() {
        return "UniqueVillageHouse[" + this.template + "]";
    }
}
