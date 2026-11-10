package com.tahaakhan.spellmod.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** The table raw mana will be refined on. For now it is only craftable and placeable. */
public class ManaTableBlock extends Block {
    private static final VoxelShape SHAPE = Block.column(16.0, 0.0, 12.0);

    public ManaTableBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected boolean useShapeForLightOcclusion(BlockState state) {
        return true;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPE;
    }

    /** Client only: motes of mana drifting up from the table top. */
    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (random.nextInt(3) == 0) {
            level.addParticle(ParticleTypes.END_ROD,
                    pos.getX() + 0.2 + random.nextDouble() * 0.6, pos.getY() + 0.8, pos.getZ() + 0.2 + random.nextDouble() * 0.6,
                    0.0, 0.01 + random.nextDouble() * 0.02, 0.0);
        }
    }
}
