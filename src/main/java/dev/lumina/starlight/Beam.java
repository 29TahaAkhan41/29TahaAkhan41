package dev.lumina.starlight;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Geometry rules for a starlight beam travelling between two nodes. */
public final class Beam {
    /** Furthest distance (in blocks) a beam can bridge. */
    public static final double MAX_RANGE = 16.0;
    /** Fraction of the light lost per block travelled. */
    public static final float LOSS_PER_BLOCK = 0.015F;

    private Beam() {
    }

    public static double distance(BlockPos from, BlockPos to) {
        return Math.sqrt(from.distSqr(to));
    }

    public static boolean inRange(BlockPos from, BlockPos to) {
        return from.distSqr(to) <= MAX_RANGE * MAX_RANGE;
    }

    /** Share of the light that survives the trip. */
    public static float efficiency(BlockPos from, BlockPos to) {
        return Math.max(0.0F, 1.0F - LOSS_PER_BLOCK * (float) distance(from, to));
    }

    /**
     * A beam passes through air, glass, leaves and other non-opaque blocks, and is stopped by
     * any opaque full block lying between the two end points.
     */
    public static boolean hasLineOfSight(Level level, BlockPos from, BlockPos to) {
        Vec3 start = Vec3.atCenterOf(from);
        Vec3 delta = Vec3.atCenterOf(to).subtract(start);
        int steps = Math.max(1, (int) Math.ceil(delta.length() * 4.0));
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        long last = from.asLong();
        for (int i = 1; i < steps; i++) {
            double t = i / (double) steps;
            cursor.set(Math.floor(start.x + delta.x * t), Math.floor(start.y + delta.y * t),
                    Math.floor(start.z + delta.z * t));
            long key = cursor.asLong();
            if (key == last) {
                continue;
            }
            last = key;
            if (cursor.equals(from) || cursor.equals(to)) {
                continue;
            }
            if (!level.isLoaded(cursor)) {
                return false;
            }
            BlockState state = level.getBlockState(cursor);
            if (state.canOcclude() && state.isSolidRender(level, cursor)) {
                return false;
            }
        }
        return true;
    }
}
