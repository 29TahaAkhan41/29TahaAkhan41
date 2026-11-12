package dev.lumina.blockentity;

import dev.lumina.Lumina;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;

/** Splits incoming starlight evenly over up to three beams. */
public class PrismBlockEntity extends StarlightNodeBlockEntity {
    public PrismBlockEntity(BlockPos pos, BlockState state) {
        super(Lumina.PRISM_BE.get(), pos, state);
    }

    @Override
    public float getCapacity() {
        return 400.0F;
    }

    @Override
    public int getMaxTargets() {
        return 3;
    }

    @Override
    public float getTransferRate() {
        return 120.0F;
    }
}
