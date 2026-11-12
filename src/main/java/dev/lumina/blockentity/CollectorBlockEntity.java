package dev.lumina.blockentity;

import dev.lumina.Lumina;
import dev.lumina.starlight.StarlightSky;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;

/** Gathers starlight from the open night sky. */
public class CollectorBlockEntity extends StarlightNodeBlockEntity {
    /** Starlight gathered per tick at full intensity. */
    public static final float BASE_RATE = 4.0F;

    public CollectorBlockEntity(BlockPos pos, BlockState state) {
        super(Lumina.COLLECTOR_BE.get(), pos, state);
    }

    @Override
    public float getCapacity() {
        return 2000.0F;
    }

    @Override
    public int getMaxTargets() {
        return 1;
    }

    @Override
    public float getTransferRate() {
        return 60.0F;
    }

    public float getIntensity() {
        return level == null ? 0.0F : StarlightSky.intensity(level, worldPosition);
    }

    @Override
    protected void tickNode() {
        if (starlight < getCapacity()) {
            receive(BASE_RATE * getIntensity());
        }
    }
}
