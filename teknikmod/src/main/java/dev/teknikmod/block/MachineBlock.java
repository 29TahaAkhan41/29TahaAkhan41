package dev.teknikmod.block;

import dev.teknikmod.Tier;
import dev.teknikmod.blockentity.MachineBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

import javax.annotation.Nullable;

/** Sunucu tarafinda her tick calisan, enerji tutan cihazlarin ortak blogu. */
public abstract class MachineBlock extends Block implements EntityBlock {
    protected final Tier tier;

    protected MachineBlock(Properties props, Tier tier) {
        super(props);
        this.tier = tier;
    }

    public Tier tier() {
        return tier;
    }

    /** Yaratici kademede sayilar yerine tek satir aciklama ekler. */
    protected boolean creativeTooltip(java.util.List<Component> tooltip) {
        if (!tier.creative) return false;
        tooltip.add(Component.translatable("tooltip.teknikmod.creative").withStyle(net.minecraft.ChatFormatting.LIGHT_PURPLE));
        return true;
    }

    public static Tier tierOf(BlockState state) {
        return state.getBlock() instanceof MachineBlock machine ? machine.tier : Tier.BASIC;
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide) return null;
        return (lvl, pos, st, be) -> {
            if (be instanceof MachineBlockEntity machine) machine.serverTick(lvl, pos, st);
        };
    }

    /** Varsayilan: sag tikta enerji miktarini aksiyon cubugunda goster. */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof MachineBlockEntity machine) {
            player.displayClientMessage(Component.translatable("message.teknikmod.energy",
                    machine.energy().getEnergyStored(), machine.energy().getMaxEnergyStored()), true);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }
}
