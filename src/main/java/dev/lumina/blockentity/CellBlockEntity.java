package dev.lumina.blockentity;

import dev.lumina.Lumina;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;

/** A large buffer that keeps starlight for the daytime. */
public class CellBlockEntity extends StarlightNodeBlockEntity {
    public CellBlockEntity(BlockPos pos, BlockState state) {
        super(Lumina.CELL_BE.get(), pos, state);
    }

    @Override
    public float getCapacity() {
        return 20000.0F;
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
