package dev.lumina.blockentity;

import dev.lumina.Lumina;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;

/** Catches a beam and re-aims it at one other node. */
public class LensBlockEntity extends StarlightNodeBlockEntity {
    public LensBlockEntity(BlockPos pos, BlockState state) {
        super(Lumina.LENS_BE.get(), pos, state);
    }

    @Override
    public float getCapacity() {
        return 400.0F;
    }

    @Override
    public int getMaxTargets() {
        return 1;
    }

    @Override
    public float getTransferRate() {
        return 80.0F;
    }
}
