package dev.lumina.block;

import dev.lumina.Lumina;
import dev.lumina.blockentity.CollectorBlockEntity;
import dev.lumina.blockentity.StarlightNodeBlockEntity;
import dev.lumina.starlight.Beam;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Block for every starlight node; behaviour differences live in the block entities. */
public class NodeBlock extends Block implements EntityBlock {
    private final VoxelShape shape;
    private final BlockEntityType.BlockEntitySupplier<? extends StarlightNodeBlockEntity> factory;

    public NodeBlock(Properties properties, VoxelShape shape,
            BlockEntityType.BlockEntitySupplier<? extends StarlightNodeBlockEntity> factory) {
        super(properties);
        this.shape = shape;
        this.factory = factory;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return factory.create(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state,
            BlockEntityType<T> type) {
        if (level.isClientSide) {
            return null;
        }
        return (tickLevel, pos, tickState, blockEntity) -> {
            if (blockEntity instanceof StarlightNodeBlockEntity node) {
                node.serverTick();
            }
        };
    }

    @Override
    protected boolean hasAnalogOutputSignal(BlockState state) {
        return true;
    }

    @Override
    protected int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {
        return level.getBlockEntity(pos) instanceof StarlightNodeBlockEntity node ? node.getComparatorSignal() : 0;
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        // The wand does its own thing in Item#useOn; don't let the status readout swallow the click.
        if (stack.is(Lumina.LINKING_WAND.get())) {
            return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION;
        }
        return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player,
            BlockHitResult hit) {
        if (!player.getMainHandItem().isEmpty()) {
            return InteractionResult.PASS;
        }
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof StarlightNodeBlockEntity node) {
            player.displayClientMessage(describe(node), true);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    /** Action bar readout shown when a node is clicked with an empty hand. */
    protected Component describe(StarlightNodeBlockEntity node) {
        int stored = Mth.floor(node.getStarlight());
        int capacity = Mth.floor(node.getCapacity());
        if (node instanceof CollectorBlockEntity collector) {
            return Component.translatable("message.lumina.status.collector", stored, capacity,
                    Math.round(collector.getIntensity() * 100.0F), node.getTargets().size(), node.getMaxTargets());
        }
        return Component.translatable("message.lumina.status.node", stored, capacity,
                node.getTargets().size(), node.getMaxTargets());
    }

    /** Client only: sparkles drifting along every active beam. */
    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!(level.getBlockEntity(pos) instanceof StarlightNodeBlockEntity node) || node.getStarlight() <= 0.0F) {
            return;
        }
        Vec3 start = Vec3.atCenterOf(pos);
        for (BlockPos target : node.getTargets()) {
            if (!Beam.inRange(pos, target)) {
                continue;
            }
            Vec3 delta = Vec3.atCenterOf(target).subtract(start);
            Vec3 speed = delta.normalize().scale(0.08);
            int count = 2 + (int) (delta.length() / 2.0);
            for (int i = 0; i < count; i++) {
                Vec3 at = start.add(delta.scale(random.nextDouble()));
                level.addParticle(ParticleTypes.END_ROD, at.x, at.y, at.z, speed.x, speed.y, speed.z);
            }
        }
    }
}
