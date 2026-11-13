package dev.teknikmod.block;

import dev.teknikmod.blockentity.SolarPanelBlockEntity;
import dev.teknikmod.Tier;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

public class SolarPanelBlock extends MachineBlock {
    private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 6, 16);

    public SolarPanelBlock(Properties props, Tier tier) {
        super(props, tier);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext ctx) {
        return SHAPE;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new SolarPanelBlockEntity(pos, state);
    }

    @Override
    public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.teknikmod.generation", tier.solarRate).withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("tooltip.teknikmod.capacity", tier.solarCapacity).withStyle(ChatFormatting.GRAY));
    }
}
