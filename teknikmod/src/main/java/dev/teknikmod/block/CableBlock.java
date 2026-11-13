package dev.teknikmod.block;

import dev.teknikmod.blockentity.CableBlockEntity;
import dev.teknikmod.energy.CableNetwork;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.shapes.BooleanOp;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.neoforged.neoforge.capabilities.Capabilities;

import java.util.EnumMap;
import java.util.Map;

public class CableBlock extends Block implements EntityBlock {
    public static final Map<Direction, BooleanProperty> SIDES = new EnumMap<>(Map.of(
            Direction.NORTH, BlockStateProperties.NORTH, Direction.SOUTH, BlockStateProperties.SOUTH,
            Direction.EAST, BlockStateProperties.EAST, Direction.WEST, BlockStateProperties.WEST,
            Direction.UP, BlockStateProperties.UP, Direction.DOWN, BlockStateProperties.DOWN));

    private static final VoxelShape CORE = Block.box(5, 5, 5, 11, 11, 11);
    private static final Map<Direction, VoxelShape> ARMS = new EnumMap<>(Map.of(
            Direction.NORTH, Block.box(5, 5, 0, 11, 11, 5), Direction.SOUTH, Block.box(5, 5, 11, 11, 11, 16),
            Direction.WEST, Block.box(0, 5, 5, 5, 11, 11), Direction.EAST, Block.box(11, 5, 5, 16, 11, 11),
            Direction.DOWN, Block.box(5, 0, 5, 11, 5, 11), Direction.UP, Block.box(5, 11, 5, 11, 16, 11)));
    private final VoxelShape[] shapes = new VoxelShape[64];

    private final int transferRate;

    public CableBlock(Properties props, int transferRate) {
        super(props);
        this.transferRate = transferRate;
        BlockState def = stateDefinition.any();
        for (BooleanProperty p : SIDES.values()) def = def.setValue(p, false);
        registerDefaultState(def);
    }

    public int transferRate() {
        return transferRate;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        SIDES.values().forEach(builder::add);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        int index = 0;
        for (Direction d : Direction.values()) if (state.getValue(SIDES.get(d))) index |= 1 << d.ordinal();
        VoxelShape shape = shapes[index];
        if (shape == null) {
            shape = CORE;
            for (Direction d : Direction.values()) {
                if (state.getValue(SIDES.get(d))) shape = Shapes.joinUnoptimized(shape, ARMS.get(d), BooleanOp.OR);
            }
            shapes[index] = shape = shape.optimize();
        }
        return shape;
    }

    private static boolean connectsTo(LevelAccessor level, BlockPos pos, Direction dir) {
        BlockPos other = pos.relative(dir);
        if (level.getBlockState(other).getBlock() instanceof CableBlock) return true;
        return level instanceof Level lvl
                && lvl.getCapability(Capabilities.EnergyStorage.BLOCK, other, dir.getOpposite()) != null;
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        BlockState state = defaultBlockState();
        for (Direction d : Direction.values()) {
            state = state.setValue(SIDES.get(d), connectsTo(ctx.getLevel(), ctx.getClickedPos(), d));
        }
        return state;
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction dir, BlockState neighbor, LevelAccessor level,
                                     BlockPos pos, BlockPos neighborPos) {
        return state.setValue(SIDES.get(dir), connectsTo(level, pos, dir));
    }

    @Override
    protected void neighborChanged(BlockState state, Level level, BlockPos pos, Block block, BlockPos from, boolean moved) {
        CableNetwork.invalidate();
        super.neighborChanged(state, level, pos, block, from, moved);
    }

    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moved) {
        CableNetwork.invalidate();
        super.onPlace(state, level, pos, old, moved);
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moved) {
        CableNetwork.invalidate();
        super.onRemove(state, level, pos, newState, moved);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CableBlockEntity(pos, state);
    }

    @Override
    public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, List<Component> tooltip, TooltipFlag flag) {
        if (transferRate == Integer.MAX_VALUE) {
            tooltip.add(Component.translatable("tooltip.teknikmod.creative").withStyle(ChatFormatting.LIGHT_PURPLE));
            return;
        }
        tooltip.add(Component.translatable("tooltip.teknikmod.transfer", transferRate).withStyle(ChatFormatting.GRAY));
    }
}
